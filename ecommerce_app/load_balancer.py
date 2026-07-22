import json
import threading
from datetime import datetime, timezone
from copy import deepcopy
from pathlib import Path

from flask import Flask, Response, jsonify, request


class TargetRegistry:
    def __init__(self, config_path):
        self.config_path = Path(config_path)
        self._lock = threading.Lock()
        self._targets = []
        self._config_error = None
        self.reload()

    @property
    def config_error(self):
        with self._lock:
            return self._config_error

    def snapshot(self):
        with self._lock:
            return deepcopy(self._targets)

    def reload(self):
        try:
            payload = json.loads(
                self.config_path.read_text(
                    encoding="utf-8-sig",
                )
            )
            targets = self._validate(payload)
        except (OSError, ValueError, TypeError) as error:
            with self._lock:
                self._config_error = str(error)
                return deepcopy(self._targets)

        with self._lock:
            self._targets = targets
            self._config_error = None
            return deepcopy(self._targets)

    @staticmethod
    def _validate(payload):
        if not isinstance(payload, dict):
            raise ValueError(
                "Target configuration must be a JSON object."
            )

        targets = payload.get("targets")

        if not isinstance(targets, list):
            raise ValueError(
                "'targets' must be a JSON list."
            )

        validated = []
        names = set()
        urls = set()

        for item in targets:
            if not isinstance(item, dict):
                raise ValueError(
                    "Every target must be a JSON object."
                )

            name = item.get("name")
            url = item.get("url")

            if not isinstance(name, str) or not name.strip():
                raise ValueError(
                    "Every target requires a non-empty name."
                )

            if (
                not isinstance(url, str)
                or not url.startswith(
                    ("http://", "https://")
                )
            ):
                raise ValueError(
                    "Every target requires an HTTP or HTTPS URL."
                )

            name = name.strip()
            url = url.rstrip("/")

            if name in names:
                raise ValueError(
                    f"Duplicate target name: {name}"
                )

            if url in urls:
                raise ValueError(
                    f"Duplicate target URL: {url}"
                )

            names.add(name)
            urls.add(url)

            validated.append(
                {
                    "name": name,
                    "url": url,
                }
            )

        return validated


def default_health_request(url, timeout):
    import requests

    return requests.get(url, timeout=timeout)


class HealthMonitor:
    def __init__(
        self,
        registry,
        request_get=None,
        timeout=2.0,
        interval=5.0,
    ):
        if interval <= 0:
            raise ValueError(
                "Health-check interval must be positive."
            )

        self.registry = registry
        self.request_get = (
            request_get or default_health_request
        )
        self.timeout = timeout
        self.interval = interval

        self._lock = threading.Lock()
        self._states = []
        self._stop_event = threading.Event()
        self._thread = None

    def snapshot(self):
        with self._lock:
            return deepcopy(self._states)

    def check_once(self):
        self.registry.reload()
        targets = self.registry.snapshot()
        states = []

        for target in targets:
            health_url = f'{target["url"]}/health'
            checked_at = datetime.now(
                timezone.utc
            ).isoformat()

            try:
                response = self.request_get(
                    health_url,
                    timeout=self.timeout,
                )

                if response.status_code == 200:
                    healthy = True
                    error = None
                else:
                    healthy = False
                    error = (
                        "Health check returned HTTP "
                        f"{response.status_code}."
                    )

            except Exception as exc:
                healthy = False
                error = str(exc)

            states.append(
                {
                    "name": target["name"],
                    "url": target["url"],
                    "healthy": healthy,
                    "last_checked": checked_at,
                    "error": error,
                }
            )

        with self._lock:
            self._states = states
            return deepcopy(self._states)


    @property
    def is_running(self):
        with self._lock:
            return (
                self._thread is not None
                and self._thread.is_alive()
            )

    def start(self):
        with self._lock:
            if (
                self._thread is not None
                and self._thread.is_alive()
            ):
                return

            self._stop_event.clear()

            thread = threading.Thread(
                target=self._run,
                name="load-balancer-health-monitor",
                daemon=True,
            )
            self._thread = thread

        thread.start()

    def stop(self):
        with self._lock:
            thread = self._thread

            if thread is None:
                return

            self._stop_event.set()

        thread.join()

        with self._lock:
            if self._thread is thread:
                self._thread = None

    def _run(self):
        while not self._stop_event.is_set():
            self.check_once()

            if self._stop_event.wait(self.interval):
                break


class RoundRobinSelector:
    def __init__(self):
        self._index = 0
        self._lock = threading.Lock()

    def choose(self, states):
        healthy_targets = [
            state
            for state in states
            if state.get("healthy") is True
        ]

        if not healthy_targets:
            return None

        with self._lock:
            selected = healthy_targets[
                self._index % len(healthy_targets)
            ]
            self._index += 1

        return deepcopy(selected)


HOP_BY_HOP_HEADERS = {
    "connection",
    "content-encoding",
    "content-length",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailer",
    "transfer-encoding",
    "upgrade",
}


def _default_request_session():
    import requests

    return requests.Session()


def _forward_request_headers():
    return {
        name: value
        for name, value in request.headers.items()
        if name.lower() not in {
            "host",
            "content-length",
        }
    }


def _forward_response_headers(headers):
    return [
        (name, value)
        for name, value in headers.items()
        if name.lower() not in HOP_BY_HOP_HEADERS
    ]


def create_load_balancer_app(
    config_path=None,
    request_session=None,
    start_monitor=True,
):
    app = Flask(
        __name__,
        static_folder=None,
    )

    resolved_config_path = (
        Path(config_path)
        if config_path is not None
        else Path(__file__).with_name("targets.json")
    )

    session = (
        request_session
        if request_session is not None
        else _default_request_session()
    )

    registry = TargetRegistry(resolved_config_path)
    monitor = HealthMonitor(
        registry,
        request_get=session.get,
        interval=5.0,
    )
    selector = RoundRobinSelector()

    app.extensions["target_registry"] = registry
    app.extensions["health_monitor"] = monitor
    app.extensions["round_robin_selector"] = selector
    app.extensions["proxy_session"] = session

    if start_monitor:
        monitor.start()

    def proxy_request(path):
        target = selector.choose(
            monitor.snapshot()
        )

        if target is None:
            return (
                jsonify(
                    {
                        "error": (
                            "No healthy backend instances "
                            "are available."
                        )
                    }
                ),
                503,
            )

        backend_url = (
            f'{target["url"]}/'
            f'{path.lstrip("/")}'
        )

        try:
            upstream_response = session.request(
                method=request.method,
                url=backend_url,
                headers=_forward_request_headers(),
                params=request.args.to_dict(
                    flat=False
                ),
                data=request.get_data(),
                allow_redirects=False,
                timeout=10.0,
            )
        except Exception as error:
            return (
                jsonify(
                    {
                        "error": (
                            "The selected backend instance "
                            "could not be reached."
                        ),
                        "backend": target["name"],
                        "details": str(error),
                    }
                ),
                502,
            )

        return Response(
            upstream_response.content,
            status=upstream_response.status_code,
            headers=_forward_response_headers(
                upstream_response.headers
            ),
        )

    app.add_url_rule(
        "/",
        defaults={"path": ""},
        endpoint="proxy_root",
        view_func=proxy_request,
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    )

    app.add_url_rule(
        "/<path:path>",
        endpoint="proxy_path",
        view_func=proxy_request,
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    )

    return app


def main():
    app = create_load_balancer_app()
    app.run(
        host="0.0.0.0",
        port=8000,
        debug=False,
        use_reloader=False,
    )


if __name__ == "__main__":
    main()
