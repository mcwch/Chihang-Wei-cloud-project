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


def test_public_navigation_shows_public_links_only():
    app = build_app()
    client = app.test_client()

    response = client.get("/")

    assert response.status_code == 200
    assert b"Products" in response.data
    assert b"Admin Login" in response.data
    assert b"Cart" in response.data
    assert b'href="/admin/login"' in response.data

    assert b"Orders" not in response.data
    assert b'href="/orders"' not in response.data
    assert b"Manage Products" not in response.data
    assert b"Monitoring" not in response.data
    assert b"Admin Logs" not in response.data


def test_admin_navigation_shows_management_links():
    app = build_app()
    client = app.test_client()
    sign_in_admin(client)

    response = client.get("/")

    assert response.status_code == 200
    assert b"Products" in response.data
    assert b"Orders" in response.data
    assert b"Manage Products" in response.data
    assert b"Monitoring" in response.data
    assert b"Admin Logs" in response.data
    assert b"Logout" in response.data
    assert b"Cart" in response.data

    assert b'href="/orders"' in response.data
    assert b'href="/admin/products"' in response.data
    assert b'href="/admin/monitor"' in response.data
    assert b'href="/admin/logs"' in response.data
    assert b'action="/admin/logout"' in response.data

    assert b"Admin Login" not in response.data
