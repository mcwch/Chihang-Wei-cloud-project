from decimal import Decimal

from app import create_app
from models import Product, db


def create_product(app, stock=10):
    with app.app_context():
        db.create_all()
        Product.query.delete()
        db.session.commit()

        product = Product(
            name="Portable Speaker",
            description="A portable speaker stored in MySQL.",
            price=Decimal("49.99"),
            stock=stock,
            category="Audio",
            image_url=None,
        )

        db.session.add(product)
        db.session.commit()

        return product.id


def add_cart_item(client, product_id, quantity=1):
    with client.session_transaction() as session:
        session["cart"] = {
            str(product_id): quantity,
        }


def test_update_cart_changes_quantity():
    app = create_app({"TESTING": True})
    product_id = create_product(app, stock=10)
    client = app.test_client()

    add_cart_item(client, product_id, quantity=1)

    response = client.post(
        f"/cart/update/{product_id}",
        data={"quantity": "4"},
    )

    assert response.status_code == 302

    with client.session_transaction() as session:
        assert session["cart"][str(product_id)] == 4


def test_update_cart_does_not_exceed_stock():
    app = create_app({"TESTING": True})
    product_id = create_product(app, stock=5)
    client = app.test_client()

    add_cart_item(client, product_id, quantity=1)

    client.post(
        f"/cart/update/{product_id}",
        data={"quantity": "20"},
    )

    with client.session_transaction() as session:
        assert session["cart"][str(product_id)] == 5


def test_update_cart_with_zero_removes_product():
    app = create_app({"TESTING": True})
    product_id = create_product(app)
    client = app.test_client()

    add_cart_item(client, product_id, quantity=2)

    client.post(
        f"/cart/update/{product_id}",
        data={"quantity": "0"},
    )

    with client.session_transaction() as session:
        assert str(product_id) not in session["cart"]


def test_remove_product_from_cart():
    app = create_app({"TESTING": True})
    product_id = create_product(app)
    client = app.test_client()

    add_cart_item(client, product_id, quantity=2)

    response = client.post(
        f"/cart/remove/{product_id}"
    )

    assert response.status_code == 302

    with client.session_transaction() as session:
        assert str(product_id) not in session["cart"]


def test_clear_cart_removes_all_items():
    app = create_app({"TESTING": True})
    product_id = create_product(app)
    client = app.test_client()

    add_cart_item(client, product_id, quantity=3)

    response = client.post("/cart/clear")

    assert response.status_code == 302

    with client.session_transaction() as session:
        assert session["cart"] == {}


def test_cart_page_displays_management_controls():
    app = create_app({"TESTING": True})
    product_id = create_product(app)
    client = app.test_client()

    add_cart_item(client, product_id, quantity=2)

    response = client.get("/cart")

    assert response.status_code == 200
    assert b"Update" in response.data
    assert b"Remove" in response.data
    assert b"Clear Cart" in response.data
    assert b"Proceed to Checkout" in response.data
