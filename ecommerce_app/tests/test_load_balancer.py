import json

import pytest

from load_balancer import TargetRegistry


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
