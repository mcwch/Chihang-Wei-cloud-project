from logging.handlers import RotatingFileHandler

from load_balancer import create_load_balancer_app


def write_single_target(path):
    path.write_text(
        """
{
  "targets": [
    {
      "name": "Instance 1",
      "url": "http://127.0.0.1:5000"
    }
  ]
}
""".strip(),
        encoding="utf-8",
    )


class FakeHealthResponse:
    def __init__(self, status_code):
        self.status_code = status_code


class SequencedHealthSession:
    def __init__(self, status_codes):
        self.status_codes = list(status_codes)
        self.health_calls = []

    def get(self, url, timeout):
        self.health_calls.append(
            {
                "url": url,
                "timeout": timeout,
            }
        )

        if not self.status_codes:
            raise AssertionError(
                "No health response remains in the sequence."
            )

        return FakeHealthResponse(
            self.status_codes.pop(0)
        )

    def request(self, method, url, **kwargs):
        raise AssertionError(
            "Proxy request should not run in health logging tests."
        )


def create_logging_load_balancer(
    tmp_path,
    status_codes,
):
    config_path = tmp_path / "targets.json"
    log_directory = tmp_path / "logs"

    write_single_target(config_path)

    app = create_load_balancer_app(
        config_path=config_path,
        request_session=SequencedHealthSession(
            status_codes
        ),
        start_monitor=False,
        log_dir=log_directory,
    )

    return (
        app,
        log_directory / "load_balancer.log",
    )


def flush_load_balancer_logger(app):
    logger = app.extensions["load_balancer_logger"]

    for handler in logger.handlers:
        handler.flush()


def test_load_balancer_creates_rotating_log_file(tmp_path):
    app, log_file = create_logging_load_balancer(
        tmp_path,
        [200],
    )

    logger = app.extensions["load_balancer_logger"]

    assert log_file.parent.is_dir()
    assert log_file.is_file()

    assert any(
        isinstance(handler, RotatingFileHandler)
        for handler in logger.handlers
    )


def test_first_healthy_observation_is_logged_once(tmp_path):
    app, log_file = create_logging_load_balancer(
        tmp_path,
        [200, 200],
    )

    monitor = app.extensions["health_monitor"]

    monitor.check_once()
    monitor.check_once()

    flush_load_balancer_logger(app)

    log_text = log_file.read_text(encoding="utf-8")

    expected_event = (
        "event=health_observed "
        "backend=Instance 1 status=healthy"
    )

    assert expected_event in log_text
    assert log_text.count(expected_event) == 1


def test_healthy_to_unhealthy_transition_is_logged_once(
    tmp_path,
):
    app, log_file = create_logging_load_balancer(
        tmp_path,
        [200, 503, 503],
    )

    monitor = app.extensions["health_monitor"]

    monitor.check_once()
    monitor.check_once()
    monitor.check_once()

    flush_load_balancer_logger(app)

    log_text = log_file.read_text(encoding="utf-8")

    expected_event = (
        "event=became_unhealthy "
        "backend=Instance 1"
    )

    assert expected_event in log_text
    assert log_text.count(expected_event) == 1
    assert "HTTP 503" in log_text


def test_unhealthy_to_healthy_transition_logs_recovery(
    tmp_path,
):
    app, log_file = create_logging_load_balancer(
        tmp_path,
        [503, 200, 200],
    )

    monitor = app.extensions["health_monitor"]

    monitor.check_once()
    monitor.check_once()
    monitor.check_once()

    flush_load_balancer_logger(app)

    log_text = log_file.read_text(encoding="utf-8")

    expected_event = (
        "event=recovered "
        "backend=Instance 1"
    )

    assert expected_event in log_text
    assert log_text.count(expected_event) == 1


def write_two_logging_targets(path):
    path.write_text(
        """
{
  "targets": [
    {
      "name": "Instance 1",
      "url": "http://127.0.0.1:5000"
    },
    {
      "name": "Instance 2",
      "url": "http://127.0.0.1:5001"
    }
  ]
}
""".strip(),
        encoding="utf-8",
    )


class LoggingProxyResponse:
    def __init__(
        self,
        content=b"OK",
        status_code=200,
        headers=None,
    ):
        self.content = content
        self.status_code = status_code
        self.headers = headers or {
            "Content-Type": "text/plain",
        }


class LoggingProxySession:
    def __init__(
        self,
        health_statuses,
        request_outcomes=None,
    ):
        self.health_statuses = health_statuses
        self.request_outcomes = {
            url: list(outcomes)
            for url, outcomes in (
                request_outcomes or {}
            ).items()
        }
        self.proxy_calls = []

    def get(self, url, timeout):
        for url_fragment, status_code in (
            self.health_statuses.items()
        ):
            if url_fragment in url:
                return FakeHealthResponse(status_code)

        raise AssertionError(
            f"No health status configured for {url}"
        )

    def request(self, method, url, **kwargs):
        self.proxy_calls.append(
            {
                "method": method,
                "url": url,
                **kwargs,
            }
        )

        outcomes = self.request_outcomes.get(url)

        if not outcomes:
            raise AssertionError(
                f"No proxy outcome configured for {url}"
            )

        outcome = outcomes.pop(0)

        if isinstance(outcome, BaseException):
            raise outcome

        return outcome


def create_proxy_logging_app(tmp_path, session):
    config_path = tmp_path / "targets.json"
    log_directory = tmp_path / "logs"

    write_two_logging_targets(config_path)

    app = create_load_balancer_app(
        config_path=config_path,
        request_session=session,
        start_monitor=False,
        log_dir=log_directory,
    )

    app.extensions["health_monitor"].check_once()

    return (
        app,
        log_directory / "load_balancer.log",
    )


def test_no_healthy_backend_is_logged(tmp_path):
    session = LoggingProxySession(
        health_statuses={
            "5000": 503,
            "5001": 503,
        }
    )

    app, log_file = create_proxy_logging_app(
        tmp_path,
        session,
    )

    client = app.test_client()
    response = client.get("/products")

    flush_load_balancer_logger(app)

    assert response.status_code == 503
    assert session.proxy_calls == []

    log_text = log_file.read_text(encoding="utf-8")

    assert "ERROR" in log_text
    assert "event=no_healthy_backend" in log_text
    assert "method=GET" in log_text
    assert "path=/products" in log_text
    assert "status=503" in log_text


def test_connection_failure_and_rerouting_are_logged(
    tmp_path,
):
    session = LoggingProxySession(
        health_statuses={
            "5000": 200,
            "5001": 200,
        },
        request_outcomes={
            "http://127.0.0.1:5000/products": [
                ConnectionError(
                    "Instance 1 unavailable"
                )
            ],
            "http://127.0.0.1:5001/products": [
                LoggingProxyResponse(
                    content=b"Instance 2",
                )
            ],
        },
    )

    app, log_file = create_proxy_logging_app(
        tmp_path,
        session,
    )

    client = app.test_client()
    response = client.get("/products")

    flush_load_balancer_logger(app)

    assert response.status_code == 200
    assert response.get_data(as_text=True) == "Instance 2"

    log_text = log_file.read_text(encoding="utf-8")

    assert (
        "event=backend_connection_failed "
        "backend=Instance 1"
        in log_text
    )
    assert "Instance 1 unavailable" in log_text

    assert (
        "event=request_rerouted "
        "failed_backend=Instance 1 "
        "selected_backend=Instance 2"
        in log_text
    )

    assert "method=GET" in log_text
    assert "path=/products" in log_text


def test_all_unreachable_backends_are_logged(
    tmp_path,
):
    session = LoggingProxySession(
        health_statuses={
            "5000": 200,
            "5001": 200,
        },
        request_outcomes={
            "http://127.0.0.1:5000/products": [
                ConnectionError(
                    "Instance 1 connection failed"
                )
            ],
            "http://127.0.0.1:5001/products": [
                ConnectionError(
                    "Instance 2 connection failed"
                )
            ],
        },
    )

    app, log_file = create_proxy_logging_app(
        tmp_path,
        session,
    )

    client = app.test_client()
    response = client.get("/products")

    flush_load_balancer_logger(app)

    assert response.status_code == 502

    log_text = log_file.read_text(encoding="utf-8")

    assert log_text.count(
        "event=backend_connection_failed"
    ) == 2

    assert (
        "event=all_backends_unreachable"
        in log_text
    )
    assert "method=GET" in log_text
    assert "path=/products" in log_text
    assert "attempts=2" in log_text
    assert "status=502" in log_text
