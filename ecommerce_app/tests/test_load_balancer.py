import json
import threading
import time

import pytest

from load_balancer import HealthMonitor, RoundRobinSelector, TargetRegistry, create_load_balancer_app


def write_targets(path, targets):
    path.write_text(
        json.dumps({"targets": targets}),
        encoding="utf-8",
    )


def test_registry_loads_named_targets(tmp_path):
    config_path = tmp_path / "targets.json"
    targets = [
        {
            "name": "Instance 1",
            "url": "http://127.0.0.1:5000",
        },
        {
            "name": "Instance 2",
            "url": "http://127.0.0.1:5001",
        },
    ]
    write_targets(config_path, targets)

    registry = TargetRegistry(config_path)

    assert registry.snapshot() == targets
    assert registry.config_error is None


def test_invalid_json_keeps_last_valid_targets(tmp_path):
    config_path = tmp_path / "targets.json"
    valid_targets = [
        {
            "name": "Instance 1",
            "url": "http://127.0.0.1:5000",
        }
    ]
    write_targets(config_path, valid_targets)
    registry = TargetRegistry(config_path)

    config_path.write_text(
        "{not valid json",
        encoding="utf-8",
    )
    result = registry.reload()

    assert result == valid_targets
    assert registry.snapshot() == valid_targets
    assert registry.config_error is not None


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"targets": "not-a-list"},
        {
            "targets": [
                {
                    "name": "",
                    "url": "http://x",
                }
            ]
        },
        {
            "targets": [
                {
                    "name": "A",
                    "url": "ftp://x",
                }
            ]
        },
        {
            "targets": [
                {
                    "name": "A",
                    "url": "http://x",
                },
                {
                    "name": "A",
                    "url": "http://y",
                },
            ]
        },
    ],
)
def test_invalid_target_shape_is_rejected(
    tmp_path,
    payload,
):
    config_path = tmp_path / "targets.json"
    config_path.write_text(
        json.dumps(payload),
        encoding="utf-8",
    )

    registry = TargetRegistry(config_path)

    assert registry.snapshot() == []
    assert registry.config_error is not None



class FakeHealthResponse:
    def __init__(self, status_code):
        self.status_code = status_code


def test_health_monitor_marks_target_health(tmp_path):
    config_path = tmp_path / "targets.json"

    write_targets(
        config_path,
        [
            {
                "name": "Instance 1",
                "url": "http://127.0.0.1:5000",
            },
            {
                "name": "Instance 2",
                "url": "http://127.0.0.1:5001",
            },
        ],
    )

    def fake_get(url, timeout):
        if "5000" in url:
            return FakeHealthResponse(200)
        return FakeHealthResponse(503)

    monitor = HealthMonitor(
        TargetRegistry(config_path),
        request_get=fake_get,
        timeout=1.5,
    )

    states = monitor.check_once()

    assert states[0]["healthy"] is True
    assert states[0]["error"] is None
    assert states[0]["last_checked"] is not None

    assert states[1]["healthy"] is False
    assert "503" in states[1]["error"]


def test_round_robin_uses_only_healthy_targets():
    selector = RoundRobinSelector()

    states = [
        {
            "name": "Instance 1",
            "url": "http://127.0.0.1:5000",
            "healthy": True,
        },
        {
            "name": "Instance 2",
            "url": "http://127.0.0.1:5001",
            "healthy": False,
        },
        {
            "name": "Instance 3",
            "url": "http://127.0.0.1:5002",
            "healthy": True,
        },
    ]

    selected = [
        selector.choose(states)["name"]
        for _ in range(4)
    ]

    assert selected == [
        "Instance 1",
        "Instance 3",
        "Instance 1",
        "Instance 3",
    ]

    assert selector.choose([]) is None


def test_health_monitor_runs_in_background_and_stops(
    tmp_path,
):
    config_path = tmp_path / "targets.json"
    write_targets(config_path, [])

    monitor = HealthMonitor(
        TargetRegistry(config_path),
        request_get=lambda url, timeout: None,
        interval=0.01,
    )

    check_happened = threading.Event()
    calls = []

    def fake_check_once():
        calls.append("checked")
        check_happened.set()
        return []

    monitor.check_once = fake_check_once

    monitor.start()

    assert check_happened.wait(timeout=0.5)
    assert monitor.is_running is True

    monitor.stop()

    assert monitor.is_running is False

    calls_after_stop = len(calls)
    time.sleep(0.03)

    assert len(calls) == calls_after_stop



class FakeProxyResponse:
    def __init__(
        self,
        content,
        status_code=200,
        headers=None,
    ):
        self.content = content
        self.status_code = status_code
        self.headers = headers or {
            "Content-Type": "text/plain",
        }


class FakeProxySession:
    def __init__(self, healthy=True):
        self.healthy = healthy
        self.proxy_calls = []

    def get(self, url, timeout):
        status_code = 200 if self.healthy else 503
        return FakeHealthResponse(status_code)

    def request(self, method, url, **kwargs):
        self.proxy_calls.append(
            {
                "method": method,
                "url": url,
                **kwargs,
            }
        )

        if "5000" in url:
            instance = "Instance 1"
        else:
            instance = "Instance 2"

        return FakeProxyResponse(
            content=instance.encode("utf-8"),
            headers={
                "Content-Type": "text/plain",
                "X-App-Instance": instance,
            },
        )


def test_proxy_round_robins_between_healthy_targets(
    tmp_path,
):
    config_path = tmp_path / "targets.json"

    write_targets(
        config_path,
        [
            {
                "name": "Instance 1",
                "url": "http://127.0.0.1:5000",
            },
            {
                "name": "Instance 2",
                "url": "http://127.0.0.1:5001",
            },
        ],
    )

    proxy_session = FakeProxySession()

    app = create_load_balancer_app(
        config_path=config_path,
        request_session=proxy_session,
        start_monitor=False,
    )

    app.extensions["health_monitor"].check_once()
    client = app.test_client()

    first_response = client.get("/products")
    second_response = client.get("/products")

    assert first_response.status_code == 200
    assert first_response.get_data(as_text=True) == (
        "Instance 1"
    )
    assert first_response.headers["X-App-Instance"] == (
        "Instance 1"
    )

    assert second_response.status_code == 200
    assert second_response.get_data(as_text=True) == (
        "Instance 2"
    )
    assert second_response.headers["X-App-Instance"] == (
        "Instance 2"
    )

    assert [
        call["url"]
        for call in proxy_session.proxy_calls
    ] == [
        "http://127.0.0.1:5000/products",
        "http://127.0.0.1:5001/products",
    ]


def test_proxy_returns_503_when_no_target_is_healthy(
    tmp_path,
):
    config_path = tmp_path / "targets.json"

    write_targets(
        config_path,
        [
            {
                "name": "Instance 1",
                "url": "http://127.0.0.1:5000",
            }
        ],
    )

    proxy_session = FakeProxySession(
        healthy=False,
    )

    app = create_load_balancer_app(
        config_path=config_path,
        request_session=proxy_session,
        start_monitor=False,
    )

    app.extensions["health_monitor"].check_once()
    client = app.test_client()

    response = client.get("/")

    assert response.status_code == 503
    assert response.get_json() == {
        "error": (
            "No healthy backend instances are available."
        )
    }
    assert proxy_session.proxy_calls == []


class RecordingProxySession:
    def __init__(self, upstream_response):
        self.upstream_response = upstream_response
        self.proxy_calls = []

    def get(self, url, timeout):
        return FakeHealthResponse(200)

    def request(self, method, url, **kwargs):
        self.proxy_calls.append(
            {
                "method": method,
                "url": url,
                **kwargs,
            }
        )
        return self.upstream_response


def test_proxy_forwards_post_body_query_headers_and_cookie(
    tmp_path,
):
    config_path = tmp_path / "targets.json"

    write_targets(
        config_path,
        [
            {
                "name": "Instance 1",
                "url": "http://127.0.0.1:5000",
            }
        ],
    )

    proxy_session = RecordingProxySession(
        FakeProxyResponse(
            content=b"cart updated",
            status_code=200,
            headers={
                "Content-Type": "text/plain",
                "X-App-Instance": "Instance 1",
            },
        )
    )

    app = create_load_balancer_app(
        config_path=config_path,
        request_session=proxy_session,
        start_monitor=False,
    )

    app.extensions["health_monitor"].check_once()
    client = app.test_client()
    client.set_cookie("session", "cart-cookie")

    response = client.post(
        "/cart/add?source=home&item=1&item=2",
        data={
            "product_id": "10",
            "quantity": "2",
        },
        headers={
            "X-Test-Header": "forward-me",
        },
    )

    assert response.status_code == 200
    assert response.get_data(as_text=True) == (
        "cart updated"
    )

    assert len(proxy_session.proxy_calls) == 1
    call = proxy_session.proxy_calls[0]

    assert call["method"] == "POST"
    assert call["url"] == (
        "http://127.0.0.1:5000/cart/add"
    )
    assert call["params"] == {
        "source": ["home"],
        "item": ["1", "2"],
    }

    body = call["data"].decode("utf-8")
    assert "product_id=10" in body
    assert "quantity=2" in body

    assert call["headers"]["X-Test-Header"] == (
        "forward-me"
    )
    assert "session=cart-cookie" in (
        call["headers"]["Cookie"]
    )
    assert call["allow_redirects"] is False


def test_proxy_preserves_redirect_and_set_cookie(
    tmp_path,
):
    config_path = tmp_path / "targets.json"

    write_targets(
        config_path,
        [
            {
                "name": "Instance 1",
                "url": "http://127.0.0.1:5000",
            }
        ],
    )

    proxy_session = RecordingProxySession(
        FakeProxyResponse(
            content=b"",
            status_code=302,
            headers={
                "Content-Type": "text/html",
                "Location": "/order-success",
                "Set-Cookie": (
                    "checkout=done; Path=/; HttpOnly"
                ),
            },
        )
    )

    app = create_load_balancer_app(
        config_path=config_path,
        request_session=proxy_session,
        start_monitor=False,
    )

    app.extensions["health_monitor"].check_once()
    client = app.test_client()

    response = client.post(
        "/checkout",
        data={"customer_name": "Test User"},
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert response.headers["Location"] == (
        "/order-success"
    )
    assert "checkout=done" in (
        response.headers["Set-Cookie"]
    )


class StatusProxySession:
    def __init__(self):
        self.proxy_calls = []

    def get(self, url, timeout):
        if "5000" in url:
            return FakeHealthResponse(200)

        return FakeHealthResponse(503)

    def request(self, method, url, **kwargs):
        self.proxy_calls.append(
            {
                "method": method,
                "url": url,
                **kwargs,
            }
        )
        raise AssertionError(
            "Status page must not be forwarded."
        )


def test_status_page_displays_backend_health(
    tmp_path,
):
    config_path = tmp_path / "targets.json"

    write_targets(
        config_path,
        [
            {
                "name": "Instance 1",
                "url": "http://127.0.0.1:5000",
            },
            {
                "name": "Instance 2",
                "url": "http://127.0.0.1:5001",
            },
        ],
    )

    proxy_session = StatusProxySession()

    app = create_load_balancer_app(
        config_path=config_path,
        request_session=proxy_session,
        start_monitor=False,
    )

    app.extensions["health_monitor"].check_once()
    client = app.test_client()

    response = client.get("/load-balancer-status")
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Load Balancer Status" in html
    assert "Instance 1" in html
    assert "http://127.0.0.1:5000" in html
    assert "Healthy" in html

    assert "Instance 2" in html
    assert "http://127.0.0.1:5001" in html
    assert "Unhealthy" in html
    assert "Health check returned HTTP 503." in html
    assert "Last checked" in html

    assert proxy_session.proxy_calls == []


def test_status_page_displays_configuration_error(
    tmp_path,
):
    config_path = tmp_path / "targets.json"

    write_targets(
        config_path,
        [
            {
                "name": "Instance 1",
                "url": "http://127.0.0.1:5000",
            }
        ],
    )

    proxy_session = StatusProxySession()

    app = create_load_balancer_app(
        config_path=config_path,
        request_session=proxy_session,
        start_monitor=False,
    )

    config_path.write_text(
        "{invalid json",
        encoding="utf-8",
    )

    app.extensions["health_monitor"].check_once()
    client = app.test_client()

    response = client.get("/load-balancer-status")
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Configuration error" in html
    assert "Instance 1" in html
    assert proxy_session.proxy_calls == []


class FailoverProxySession:
    def __init__(self, outcomes):
        self.outcomes = {
            url: list(values)
            for url, values in outcomes.items()
        }
        self.proxy_calls = []

    def get(self, url, timeout):
        return FakeHealthResponse(200)

    def request(self, method, url, **kwargs):
        self.proxy_calls.append(
            {
                "method": method,
                "url": url,
                **kwargs,
            }
        )

        outcome = self.outcomes[url].pop(0)

        if isinstance(outcome, Exception):
            raise outcome

        return outcome


def test_proxy_tries_another_healthy_target_after_connection_failure(
    tmp_path,
):
    config_path = tmp_path / "targets.json"

    write_targets(
        config_path,
        [
            {
                "name": "Instance 1",
                "url": "http://127.0.0.1:5000",
            },
            {
                "name": "Instance 2",
                "url": "http://127.0.0.1:5001",
            },
        ],
    )

    proxy_session = FailoverProxySession(
        {
            "http://127.0.0.1:5000/products": [
                ConnectionError("Instance 1 unavailable")
            ],
            "http://127.0.0.1:5001/products": [
                FakeProxyResponse(
                    content=b"Instance 2",
                    status_code=200,
                    headers={
                        "Content-Type": "text/plain",
                        "X-App-Instance": "Instance 2",
                    },
                )
            ],
        }
    )

    app = create_load_balancer_app(
        config_path=config_path,
        request_session=proxy_session,
        start_monitor=False,
    )

    app.extensions["health_monitor"].check_once()
    client = app.test_client()

    response = client.get("/products")

    assert response.status_code == 200
    assert response.get_data(as_text=True) == "Instance 2"

    assert [
        call["url"]
        for call in proxy_session.proxy_calls
    ] == [
        "http://127.0.0.1:5000/products",
        "http://127.0.0.1:5001/products",
    ]


def test_proxy_does_not_retry_after_http_response(
    tmp_path,
):
    config_path = tmp_path / "targets.json"

    write_targets(
        config_path,
        [
            {
                "name": "Instance 1",
                "url": "http://127.0.0.1:5000",
            },
            {
                "name": "Instance 2",
                "url": "http://127.0.0.1:5001",
            },
        ],
    )

    proxy_session = FailoverProxySession(
        {
            "http://127.0.0.1:5000/checkout": [
                FakeProxyResponse(
                    content=b"backend error",
                    status_code=500,
                    headers={
                        "Content-Type": "text/plain",
                    },
                )
            ],
            "http://127.0.0.1:5001/checkout": [
                FakeProxyResponse(
                    content=b"must not be called",
                    status_code=200,
                )
            ],
        }
    )

    app = create_load_balancer_app(
        config_path=config_path,
        request_session=proxy_session,
        start_monitor=False,
    )

    app.extensions["health_monitor"].check_once()
    client = app.test_client()

    response = client.post("/checkout")

    assert response.status_code == 500
    assert len(proxy_session.proxy_calls) == 1
    assert proxy_session.proxy_calls[0]["url"] == (
        "http://127.0.0.1:5000/checkout"
    )


def test_proxy_returns_502_only_after_all_targets_fail(
    tmp_path,
):
    config_path = tmp_path / "targets.json"

    write_targets(
        config_path,
        [
            {
                "name": "Instance 1",
                "url": "http://127.0.0.1:5000",
            },
            {
                "name": "Instance 2",
                "url": "http://127.0.0.1:5001",
            },
        ],
    )

    proxy_session = FailoverProxySession(
        {
            "http://127.0.0.1:5000/products": [
                ConnectionError("Instance 1 unavailable")
            ],
            "http://127.0.0.1:5001/products": [
                ConnectionError("Instance 2 unavailable")
            ],
        }
    )

    app = create_load_balancer_app(
        config_path=config_path,
        request_session=proxy_session,
        start_monitor=False,
    )

    app.extensions["health_monitor"].check_once()
    client = app.test_client()

    response = client.get("/products")

    assert response.status_code == 502
    assert len(proxy_session.proxy_calls) == 2
    assert response.get_json()["error"] == (
        "All healthy backend instances could not be reached."
    )
