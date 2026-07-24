from decimal import Decimal

from app import create_app
from models import Order, OrderItem, db


def build_app():
    return create_app(
        {
            "TESTING": True,
            "ADMIN_PASSWORD": "test-admin-password",
        }
    )


def reset_orders():
    OrderItem.query.delete()
    Order.query.delete()
    db.session.commit()


def create_order(app, customer_name, status):
    with app.app_context():
        db.create_all()

        order = Order(
            customer_name=customer_name,
            email=f"{customer_name.lower().replace(' ', '.')}@example.com",
            address="Toronto, Ontario",
            total_price=Decimal("49.99"),
            status=status,
        )

        db.session.add(order)
        db.session.commit()

        return order.id


def sign_in_admin(client):
    with client.session_transaction() as admin_session:
        admin_session["is_admin"] = True


def test_orders_dashboard_displays_status_statistics():
    app = build_app()

    with app.app_context():
        db.create_all()
        reset_orders()

    create_order(app, "Pending Customer", "Pending")
    create_order(app, "Processing Customer", "Processing")
    create_order(app, "Shipped Customer", "Shipped")
    create_order(app, "Completed Customer", "Completed")
    create_order(app, "Cancelled Customer", "Cancelled")

    client = app.test_client()
    sign_in_admin(client)

    response = client.get("/orders")

    assert response.status_code == 200

    normalized_html = " ".join(
        response.get_data(as_text=True).split()
    )

    assert "Total Orders: 5" in normalized_html
    assert "Pending: 1" in normalized_html
    assert "Processing: 1" in normalized_html
    assert "Shipped: 1" in normalized_html
    assert "Completed: 1" in normalized_html
    assert "Cancelled: 1" in normalized_html


def test_orders_dashboard_filters_orders_by_status():
    app = build_app()

    with app.app_context():
        db.create_all()
        reset_orders()

    create_order(app, "Pending Customer", "Pending")
    create_order(app, "Shipped Customer", "Shipped")

    client = app.test_client()
    sign_in_admin(client)

    response = client.get("/orders?status=Pending")

    assert response.status_code == 200
    assert b"Showing: Pending" in response.data
    assert b"Pending Customer" in response.data
    assert b"Shipped Customer" not in response.data


def test_order_status_can_be_changed_to_cancelled():
    app = build_app()

    with app.app_context():
        db.create_all()
        reset_orders()

    order_id = create_order(
        app,
        "Cancellation Customer",
        "Pending",
    )

    client = app.test_client()
    sign_in_admin(client)

    response = client.post(
        f"/orders/{order_id}/status",
        data={"status": "Cancelled"},
        follow_redirects=True,
    )

    assert response.status_code == 200

    with app.app_context():
        order = db.session.get(Order, order_id)
        assert order.status == "Cancelled"

    assert b"Cancelled" in response.data
