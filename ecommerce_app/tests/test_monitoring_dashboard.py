from app import create_app


def build_app():
    return create_app(
        {
            "TESTING": True,
            "ADMIN_PASSWORD": "test-admin-password",
            "INSTANCE_NAME": "Monitoring Test Instance",
        }
    )


def sign_in_admin(client):
    with client.session_transaction() as admin_session:
        admin_session["is_admin"] = True


def normalize_html(response):
    return " ".join(
        response.get_data(as_text=True).split()
    )


def test_monitoring_dashboard_requires_admin_login():
    app = build_app()
    client = app.test_client()

    response = client.get("/admin/monitor")

    assert response.status_code == 302
    assert response.headers["Location"].endswith(
        "/admin/login?next=/admin/monitor"
    )


def test_monitoring_dashboard_displays_application_metrics():
    app = build_app()
    client = app.test_client()
    sign_in_admin(client)

    client.get("/")
    client.get("/missing-monitoring-page")

    response = client.get("/admin/monitor")
    html = normalize_html(response)

    assert response.status_code == 200
    assert "Application Monitoring" in html
    assert "Monitoring Test Instance" in html
    assert "Application Status: Healthy" in html
    assert "Database Status: Connected" in html
    assert "Application Uptime:" in html
    assert "Total Requests:" in html
    assert "Average Response Time:" in html
    assert "403 Responses:" in html
    assert "404 Responses: 1" in html
    assert "500 Responses:" in html
    assert "Failed Admin Logins: 0" in html
    assert "Total Orders:" in html


def test_failed_admin_login_is_counted_on_monitoring_dashboard():
    app = build_app()
    client = app.test_client()

    failed_response = client.post(
        "/admin/login",
        data={"password": "wrong-password"},
    )

    assert failed_response.status_code == 401

    sign_in_admin(client)

    response = client.get("/admin/monitor")
    html = normalize_html(response)

    assert response.status_code == 200
    assert "Failed Admin Logins: 1" in html


def test_monitoring_state_records_request_response_data():
    app = build_app()
    client = app.test_client()

    client.get("/")
    client.get("/missing-monitoring-page")

    monitoring = app.extensions["monitoring_state"]

    assert monitoring["total_requests"] == 2
    assert monitoring["successful_responses"] == 1
    assert monitoring["responses_404"] == 1
    assert monitoring["responses_403"] == 0
    assert monitoring["responses_500"] == 0
    assert monitoring["total_response_time_ms"] >= 0
