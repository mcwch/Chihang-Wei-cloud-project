from decimal import Decimal

from app import create_app
from models import Order, OrderItem, Product, db


def reset_database():
    OrderItem.query.delete()
    Order.query.delete()
    Product.query.delete()
    db.session.commit()


def create_product(app, stock=10):
    with app.app_context():
        db.create_all()
        reset_database()

        product = Product(
            name="Smart Desk Lamp",
            description="An adjustable desk lamp stored in MySQL.",
            price=Decimal("34.99"),
            stock=stock,
            category="Home Office",
            image_url=None,
        )

        db.session.add(product)
        db.session.commit()

        return product.id


def add_product_to_cart(client, product_id, quantity):
    with client.session_transaction() as session:
        session["cart"] = {
            str(product_id): quantity,
        }


def test_checkout_page_displays_order_summary():
    app = create_app({"TESTING": True})
    product_id = create_product(app)
    client = app.test_client()

    add_product_to_cart(client, product_id, 2)

    response = client.get("/checkout")

    assert response.status_code == 200
    assert b"Checkout" in response.data
    assert b"Smart Desk Lamp" in response.data
    assert b"$69.98" in response.data
    assert b"Customer Name" in response.data


def test_empty_cart_redirects_from_checkout():
    app = create_app({"TESTING": True})
    client = app.test_client()

    response = client.get("/checkout")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/cart")


def test_checkout_creates_order_and_reduces_stock():
    app = create_app({"TESTING": True})
    product_id = create_product(app, stock=10)
    client = app.test_client()

    add_product_to_cart(client, product_id, 2)

    response = client.post(
        "/checkout",
        data={
            "customer_name": "Michael Wei",
            "email": "michael@example.com",
            "address": "123 Cloud Street, Toronto",
        },
    )

    assert response.status_code == 302
    assert "/order-success/" in response.headers["Location"]

    with app.app_context():
        order = Order.query.one()
        order_item = OrderItem.query.one()
        product = db.session.get(Product, product_id)

        assert order.customer_name == "Michael Wei"
        assert order.email == "michael@example.com"
        assert str(order.total_price) == "69.98"

        assert order_item.order_id == order.id
        assert order_item.product_id == product_id
        assert order_item.quantity == 2
        assert str(order_item.unit_price) == "34.99"

        assert product.stock == 8

    with client.session_transaction() as session:
        assert session["cart"] == {}


def test_checkout_requires_customer_information():
    app = create_app({"TESTING": True})
    product_id = create_product(app)
    client = app.test_client()

    add_product_to_cart(client, product_id, 1)

    response = client.post(
        "/checkout",
        data={
            "customer_name": "",
            "email": "",
            "address": "",
        },
    )

    assert response.status_code == 400
    assert b"Please complete all required fields." in response.data

    with app.app_context():
        assert Order.query.count() == 0
        assert OrderItem.query.count() == 0
