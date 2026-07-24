from app import create_app


def build_app():
    return create_app(
        {
            "TESTING": True,
            "ADMIN_PASSWORD": "test-admin-password",
        }
    )


def sign_in_admin(client):
    with client.session_transaction() as admin_session:
        admin_session["is_admin"] = True


def test_public_navigation_shows_admin_login():
    app = build_app()
    client = app.test_client()

    response = client.get("/")

    assert response.status_code == 200
    assert b"Admin Login" in response.data
    assert b'href="/admin/login"' in response.data


def test_admin_navigation_shows_management_links():
    app = build_app()
    client = app.test_client()
    sign_in_admin(client)

    response = client.get("/")

    assert response.status_code == 200
    assert b"Orders" in response.data
    assert b"Monitoring" in response.data
    assert b"Audit Log" in response.data
    assert b"Logout" in response.data
    assert b'href="/admin/monitor"' in response.data
    assert b'href="/admin/logs"' in response.data
    assert b'action="/admin/logout"' in response.data
