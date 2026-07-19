import json

from serverless import get_order_confirmation


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


def test_get_order_confirmation_uses_serverless_response(
    monkeypatch,
):
    captured = {}

    def fake_urlopen(http_request, timeout):
        captured["payload"] = json.loads(
            http_request.data.decode("utf-8")
        )
        captured["timeout"] = timeout

        return FakeResponse({
            "message": (
                "DigitalOcean confirmed order #42."
            )
        })

    monkeypatch.setattr(
        "serverless.request.urlopen",
        fake_urlopen,
    )

    message = get_order_confirmation(
        function_url="https://example.com/function",
        order_id=42,
        customer_name="Michael",
    )

    assert message == "DigitalOcean confirmed order #42."
    assert captured["payload"] == {
        "order_id": 42,
        "customer_name": "Michael",
    }
    assert captured["timeout"] == 5
