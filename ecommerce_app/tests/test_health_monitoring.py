from decimal import Decimal

from app import create_app
from models import Order, OrderItem, db


def build_app():
    return create_app(
        {
            "TESTING": True,
            "INSTANCE_NAME": "Health Test Instance",
        }
    )


def reset_orders():
    OrderItem.query.delete()
    Order.query.delete()
    db.session.commit()


def test_health_reports_database_and_order_count():
    app = build_app()

    with app.app_context():
        db.create_all()
        reset_orders()

        order = Order(
            customer_name="Health Customer",
            email="health@example.com",
            address="Toronto, Ontario",
            total_price=Decimal("25.00"),
            status="Pending",
        )

        db.session.add(order)
        db.session.commit()

    client = app.test_client()
    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json() == {
        "status": "healthy",
        "database": "connected",
        "instance": "Health Test Instance",
        "total_orders": 1,
    }


def test_health_returns_503_when_database_check_fails(
    monkeypatch,
):
    app = build_app()

    def fail_database_query(*args, **kwargs):
        raise RuntimeError(
            "Sensitive database error must stay private."
        )

    with app.app_context():
        monkeypatch.setattr(
            db.session,
            "execute",
            fail_database_query,
        )

        client = app.test_client()
        response = client.get("/health")

    assert response.status_code == 503

    payload = response.get_json()

    assert payload == {
        "status": "unhealthy",
        "database": "disconnected",
        "instance": "Health Test Instance",
    }

    assert "Sensitive database error" not in (
        response.get_data(as_text=True)
    )
