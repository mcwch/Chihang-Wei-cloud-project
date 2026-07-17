from decimal import Decimal

from app import create_app
from models import Product, db


def create_product(app, stock=10):
    with app.app_context():
        db.create_all()
        Product.query.delete()
        db.session.commit()

        product = Product(
            name="Wireless Mouse",
            description="A wireless mouse stored in MySQL.",
            price=Decimal("29.99"),
            stock=stock,
            category="Accessories",
            image_url=None,
        )

        db.session.add(product)
        db.session.commit()

        return product.id


def test_add_product_to_cart_stores_quantity_in_session():
    app = create_app({"TESTING": True})
    product_id = create_product(app)

    client = app.test_client()

    response = client.post(
        f"/cart/add/{product_id}",
        data={"quantity": "2"},
    )

    assert response.status_code == 302

    with client.session_transaction() as session:
        assert session["cart"][str(product_id)] == 2


def test_adding_same_product_increases_quantity():
    app = create_app({"TESTING": True})
    product_id = create_product(app)

    client = app.test_client()

    client.post(
        f"/cart/add/{product_id}",
        data={"quantity": "1"},
    )
    client.post(
        f"/cart/add/{product_id}",
        data={"quantity": "2"},
    )

    with client.session_transaction() as session:
        assert session["cart"][str(product_id)] == 3


def test_cart_page_displays_item_subtotal_and_total():
    app = create_app({"TESTING": True})
    product_id = create_product(app)

    client = app.test_client()

    client.post(
        f"/cart/add/{product_id}",
        data={"quantity": "2"},
    )

    response = client.get("/cart")

    assert response.status_code == 200
    assert b"Wireless Mouse" in response.data
    assert b"$29.99" in response.data
    assert b"$59.98" in response.data
