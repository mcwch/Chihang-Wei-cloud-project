from flask import render_template

from app import create_app


def build_app():
    return create_app(
        {
            "TESTING": True,
            "INSTANCE_NAME": "Test Instance",
        }
    )


def test_health_endpoint_returns_instance_identity():
    app = build_app()
    client = app.test_client()

    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json() == {
        "status": "healthy",
        "instance": "Test Instance",
    }


def test_every_response_contains_instance_header():
    app = build_app()
    client = app.test_client()

    response = client.get("/health")

    assert response.headers["X-App-Instance"] == "Test Instance"


def test_base_template_displays_instance_identity():
    app = build_app()

    with app.test_request_context("/"):
        html = render_template("base.html")

    assert "Served by Test Instance" in html


def test_standalone_instance_name_is_the_default():
    app = create_app({"TESTING": True})

    assert app.config["INSTANCE_NAME"] == "Standalone Instance"
