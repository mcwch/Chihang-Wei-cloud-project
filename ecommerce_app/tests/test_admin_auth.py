from app import create_app


def build_app():
    return create_app(
        {
            "TESTING": True,
            "ADMIN_PASSWORD": "test-admin-password",
        }
    )


def test_admin_login_page_is_available():
    app = build_app()
    client = app.test_client()

    response = client.get("/admin/login")

    assert response.status_code == 200
    assert b"Administrator Login" in response.data


def test_orders_redirects_to_login_when_admin_is_signed_out():
    app = build_app()
    client = app.test_client()

    response = client.get("/orders")

    assert response.status_code == 302
    assert response.headers["Location"].endswith(
        "/admin/login?next=/orders"
    )


def test_admin_login_rejects_incorrect_password():
    app = build_app()
    client = app.test_client()

    response = client.post(
        "/admin/login",
        data={"password": "wrong-password"},
    )

    assert response.status_code == 401
    assert b"Invalid administrator password" in response.data

    with client.session_transaction() as admin_session:
        assert admin_session.get("is_admin") is not True


def test_admin_login_accepts_correct_password():
    app = build_app()
    client = app.test_client()

    response = client.post(
        "/admin/login",
        data={"password": "test-admin-password"},
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/orders")

    with client.session_transaction() as admin_session:
        assert admin_session["is_admin"] is True


def test_admin_logout_clears_admin_session():
    app = build_app()
    client = app.test_client()

    with client.session_transaction() as admin_session:
        admin_session["is_admin"] = True

    response = client.post("/admin/logout")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/admin/login")

    with client.session_transaction() as admin_session:
        assert admin_session.get("is_admin") is None


def test_order_detail_redirects_to_login_when_admin_is_signed_out():
    app = build_app()
    client = app.test_client()

    response = client.get("/orders/123")

    assert response.status_code == 302
    assert response.headers["Location"].endswith(
        "/admin/login?next=/orders/123"
    )


def test_order_status_update_redirects_when_admin_is_signed_out():
    app = build_app()
    client = app.test_client()

    response = client.post(
        "/orders/123/status",
        data={"status": "Shipped"},
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith(
        "/admin/login?next=/orders/123/status"
    )
