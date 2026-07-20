from pathlib import Path


def test_cloudflare_worker_contract():
    source = Path(
        "cloudflare_worker/worker.js"
    ).read_text(encoding="utf-8")

    assert "export default" in source
    assert "async fetch(request)" in source
    assert "request.json()" in source
    assert "Response.json" in source
    assert "message:" in source
    assert "Cloudflare confirmed order" in source
