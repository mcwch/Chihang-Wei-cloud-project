from decimal import Decimal

from app import create_app
from models import Order, OrderItem, db


def build_app():
    return create_app(
        {
            "TESTING": True,
            "ADMIN_PASSWORD": "test-admin-password",
            "INSTANCE_NAME": "Audit Test Instance",
        }
    )


def create_order(app):
    with app.app_context():
        db.create_all()
        OrderItem.query.delete()
        Order.query.delete()
        db.session.commit()

        order = Order(
            customer_name="Audit Customer",
            email="audit@example.com",
            address="Toronto, Ontario",
            total_price=Decimal("50.00"),
            status="Pending",
        )

        db.session.add(order)
        db.session.commit()

        return order.id


def sign_in_admin_session(client):
    with client.session_transaction() as admin_session:
        admin_session["is_admin"] = True


def normalize_html(response):
    return " ".join(
        response.get_data(as_text=True).split()
    )


def test_audit_log_page_requires_admin_login():
    app = build_app()
    client = app.test_client()

    response = client.get("/admin/logs")

    assert response.status_code == 302
    assert response.headers["Location"].endswith(
        "/admin/login?next=/admin/logs"
    )


def test_audit_log_records_login_events():
    app = build_app()
    client = app.test_client()

    client.post(
        "/admin/login",
        data={"password": "wrong-password"},
    )

    client.post(
        "/admin/login",
        data={"password": "test-admin-password"},
    )

    response = client.get("/admin/logs")
    html = normalize_html(response)

    assert response.status_code == 200
    assert "Security Audit Log" in html
    assert "Admin Login Failed" in html
    assert "Admin Login Successful" in html
    assert "Audit Test Instance" in html


def test_audit_log_records_logout():
    app = build_app()
    client = app.test_client()
    sign_in_admin_session(client)

    client.post("/admin/logout")

    sign_in_admin_session(client)
    response = client.get("/admin/logs")
    html = normalize_html(response)

    assert response.status_code == 200
    assert "Admin Logout" in html


def test_audit_log_records_order_status_change():
    app = build_app()
    order_id = create_order(app)

    client = app.test_client()
    sign_in_admin_session(client)

    client.post(
        f"/orders/{order_id}/status",
        data={"status": "Shipped"},
    )

    response = client.get("/admin/logs")
    html = normalize_html(response)

    assert response.status_code == 200
    assert "Order Status Changed" in html
    assert f"Order #{order_id}" in html
    assert "Pending" in html
    assert "Shipped" in html


def test_audit_log_keeps_at_most_100_entries():
    app = build_app()

    audit_log = app.extensions["audit_log"]

    for index in range(120):
        audit_log.append(
            {
                "timestamp": str(index),
                "event_type": "Test Event",
                "description": f"Event {index}",
                "instance": "Audit Test Instance",
            }
        )

    assert len(audit_log) == 100
    assert audit_log[0]["description"] == "Event 20"
