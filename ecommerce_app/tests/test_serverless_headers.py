import serverless


class FakeResponse:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def read(self):
        return b'{"message": "ok"}'


def test_serverless_request_includes_user_agent(monkeypatch):
    captured = {}

    def fake_urlopen(http_request, timeout):
        captured["request"] = http_request
        return FakeResponse()

    monkeypatch.setattr(
        "serverless.request.urlopen",
        fake_urlopen,
    )

    serverless.get_order_confirmation(
        function_url="https://example.com/function",
        order_id=1,
        customer_name="Michael",
    )

    assert (
        captured["request"].get_header("User-agent")
        == "EcommerceApp/1.0"
    )
