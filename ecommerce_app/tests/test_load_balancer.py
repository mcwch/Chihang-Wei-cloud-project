import json
import threading
import time

import pytest

from load_balancer import HealthMonitor, RoundRobinSelector, TargetRegistry


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
