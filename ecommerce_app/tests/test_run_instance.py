import run_instance


class FakeApp:
    def __init__(self):
        self.run_kwargs = None

    def run(self, **kwargs):
        self.run_kwargs = kwargs


def test_runner_creates_named_instance_and_starts_selected_port(
    monkeypatch,
):
    fake_app = FakeApp()
    received_config = {}

    def fake_create_app(config):
        received_config.update(config)
        return fake_app

    monkeypatch.setattr(
        run_instance,
        "create_app",
        fake_create_app,
    )

    run_instance.main(
        [
            "--name",
            "Instance 2",
            "--port",
            "5001",
        ]
    )

    assert received_config == {
        "INSTANCE_NAME": "Instance 2",
    }
    assert fake_app.run_kwargs == {
        "host": "0.0.0.0",
        "port": 5001,
        "debug": False,
        "use_reloader": False,
    }


def test_runner_accepts_custom_host(monkeypatch):
    fake_app = FakeApp()

    monkeypatch.setattr(
        run_instance,
        "create_app",
        lambda config: fake_app,
    )

    run_instance.main(
        [
            "--name",
            "Instance 1",
            "--port",
            "5000",
            "--host",
            "127.0.0.1",
        ]
    )

    assert fake_app.run_kwargs["host"] == "127.0.0.1"
