from decimal import Decimal

from app import create_app
from models import Order, OrderItem, Product, db


def create_database_product(app):
    with app.app_context():
        db.create_all()
        Product.query.delete()
        db.session.commit()

        product = Product(
            name="Database Keyboard",
            description="A mechanical keyboard stored in MySQL.",
            price=Decimal("89.99"),
            stock=6,
            category="Accessories",
            image_url=None,
        )

        db.session.add(product)
        db.session.commit()

        return product.id


def test_home_page_displays_products_from_mysql():
    app = create_app({"TESTING": True})
    create_database_product(app)

    client = app.test_client()
    response = client.get("/")

    assert response.status_code == 200
    assert b"Database Keyboard" in response.data
    assert b"$89.99" in response.data
    assert b"In Stock: 6" in response.data


def test_product_detail_displays_product_from_mysql():
    app = create_app({"TESTING": True})
    product_id = create_database_product(app)

    client = app.test_client()
    response = client.get(f"/product/{product_id}")

    assert response.status_code == 200
    assert b"Database Keyboard" in response.data
    assert b"A mechanical keyboard stored in MySQL." in response.data
    assert b"$89.99" in response.data


def test_missing_product_returns_404():
    app = create_app({"TESTING": True})

    client = app.test_client()
    response = client.get("/product/999999")

    assert response.status_code == 404


def create_database_order(app):
    with app.app_context():
        db.create_all()

        OrderItem.query.delete()
        Order.query.delete()
        db.session.commit()

        order = Order(
            customer_name="Michael",
            email="michael@example.com",
            address="Toronto, Ontario",
            total_price=Decimal("89.99"),
            status="Pending",
        )

        db.session.add(order)
        db.session.commit()

        return order.id


def test_orders_page_displays_order_information():
    app = create_app({"TESTING": True})
    order_id = create_database_order(app)

    client = app.test_client()
    response = client.get("/orders")

    assert response.status_code == 200
    assert f"Order #{order_id}".encode() in response.data
    assert b"Michael" in response.data
    assert b"$89.99" in response.data
    assert b"Pending" in response.data


def create_order_with_item(app):
    with app.app_context():
        db.create_all()

        OrderItem.query.delete()
        Order.query.delete()
        Product.query.delete()
        db.session.commit()

        product = Product(
            name="Cloud Mouse",
            description="A wireless mouse.",
            price=Decimal("39.99"),
            stock=5,
            category="Accessories",
            image_url=None,
        )

        db.session.add(product)
        db.session.flush()

        order = Order(
            customer_name="Michael",
            email="michael@example.com",
            address="Toronto, Ontario",
            total_price=Decimal("79.98"),
            status="Pending",
        )

        db.session.add(order)
        db.session.flush()

        item = OrderItem(
            order_id=order.id,
            product_id=product.id,
            quantity=2,
            unit_price=Decimal("39.99"),
        )

        db.session.add(item)
        db.session.commit()

        return order.id


def test_order_detail_page_displays_customer_and_items():
    app = create_app({"TESTING": True})
    order_id = create_order_with_item(app)

    client = app.test_client()
    response = client.get(f"/orders/{order_id}")

    with app.app_context():
        OrderItem.query.delete()
        Order.query.delete()
        Product.query.delete()
        db.session.commit()

    assert response.status_code == 200
    assert f"Order #{order_id}".encode() in response.data
    assert b"Michael" in response.data
    assert b"michael@example.com" in response.data
    assert b"Toronto, Ontario" in response.data
    assert b"Cloud Mouse" in response.data
    assert b"Quantity: 2" in response.data
    assert b"$39.99" in response.data


def test_update_order_status():
    app = create_app({"TESTING": True})
    order_id = create_database_order(app)

    client = app.test_client()
    response = client.post(
        f"/orders/{order_id}/status",
        data={"status": "Shipped"},
        follow_redirects=True,
    )

    assert response.status_code == 200

    with app.app_context():
        order = db.session.get(Order, order_id)
        assert order.status == "Shipped"

        Order.query.delete()
        db.session.commit()

    assert b"Shipped" in response.data


def test_orders_page_links_to_order_detail():
    app = create_app({"TESTING": True})
    order_id = create_database_order(app)

    client = app.test_client()
    response = client.get("/orders")

    assert response.status_code == 200
    assert f'/orders/{order_id}'.encode() in response.data

    with app.app_context():
        Order.query.delete()
        db.session.commit()


def test_navigation_contains_orders_link():
    app = create_app({"TESTING": True})
    client = app.test_client()

    response = client.get("/")

    assert response.status_code == 200
    assert b"Orders" in response.data
    assert b'href="/orders"' in response.data


def test_order_success_uses_local_confirmation_without_function_url():
    app = create_app({
        "TESTING": True,
        "DIGITALOCEAN_FUNCTION_URL": "",
    })
    order_id = create_database_order(app)

    client = app.test_client()
    response = client.get(f"/order-success/{order_id}")

    assert response.status_code == 200
    assert (
        f"Order #{order_id} has been received.".encode()
        in response.data
    )

    with app.app_context():
        Order.query.delete()
        db.session.commit()
