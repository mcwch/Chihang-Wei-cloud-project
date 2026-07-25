from decimal import Decimal

import pytest

from app import create_app
from models import Product, db


def sign_in_admin(client):
    with client.session_transaction() as admin_session:
        admin_session["is_admin"] = True


def delete_product_by_name(app, product_name):
    with app.app_context():
        Product.query.filter_by(name=product_name).delete()
        db.session.commit()


def make_product():
    return Product(
        name="Archive Test Keyboard",
        description="A product used to test catalogue management.",
        price=Decimal("69.99"),
        stock=7,
        category="Accessories",
        image_url=None,
    )


def valid_product_form(product_name):
    return {
        "name": product_name,
        "description": (
            "A compact accessory created through the admin form."
        ),
        "price": "49.99",
        "stock": "15",
        "category": "Accessories",
    }


def test_product_defaults_to_active():
    product = make_product()

    assert product.is_active is True


def test_product_management_requires_admin_login():
    app = create_app({"TESTING": True})
    client = app.test_client()

    response = client.get("/admin/products")

    assert response.status_code == 302
    assert response.headers["Location"].endswith(
        "/admin/login?next=/admin/products"
    )


def test_admin_can_open_product_management_page():
    app = create_app({"TESTING": True})
    client = app.test_client()
    sign_in_admin(client)

    response = client.get("/admin/products")

    assert response.status_code == 200
    assert b"Product Management" in response.data
    assert b"Add Product" in response.data


def test_add_product_page_requires_admin_login():
    app = create_app({"TESTING": True})
    client = app.test_client()

    response = client.get("/admin/products/new")

    assert response.status_code == 302
    assert response.headers["Location"].endswith(
        "/admin/login?next=/admin/products/new"
    )


def test_admin_can_open_add_product_form():
    app = create_app({"TESTING": True})
    client = app.test_client()
    sign_in_admin(client)

    response = client.get("/admin/products/new")

    assert response.status_code == 200
    assert b"Add Product" in response.data
    assert b'name="name"' in response.data
    assert b'name="description"' in response.data
    assert b'name="price"' in response.data
    assert b'name="stock"' in response.data
    assert b'name="category"' in response.data


def test_admin_can_create_product_and_audit_event():
    product_name = "Travel Power Adapter"

    app = create_app({"TESTING": True})
    delete_product_by_name(app, product_name)

    client = app.test_client()
    sign_in_admin(client)

    response = client.post(
        "/admin/products/new",
        data=valid_product_form(product_name),
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith(
        "/admin/products"
    )

    with app.app_context():
        product = Product.query.filter_by(
            name=product_name
        ).one()

        assert product.description == (
            "A compact accessory created through the admin form."
        )
        assert product.price == Decimal("49.99")
        assert product.stock == 15
        assert product.category == "Accessories"
        assert product.is_active is True

    audit_entries = list(app.extensions["audit_log"])

    assert any(
        entry["event_type"] == "Product Created"
        and product_name in entry["description"]
        for entry in audit_entries
    )


def test_add_product_rejects_blank_name():
    app = create_app({"TESTING": True})
    client = app.test_client()
    sign_in_admin(client)

    form_data = valid_product_form(" ")
    response = client.post(
        "/admin/products/new",
        data=form_data,
    )

    assert response.status_code == 400
    assert b"Product name is required." in response.data


def test_add_product_rejects_duplicate_name():
    product_name = "Duplicate Product Test"

    app = create_app({"TESTING": True})
    delete_product_by_name(app, product_name)

    with app.app_context():
        db.session.add(
            Product(
                name=product_name,
                description="Existing product.",
                price=Decimal("20.00"),
                stock=5,
                category="Test",
                image_url=None,
            )
        )
        db.session.commit()

    client = app.test_client()
    sign_in_admin(client)

    response = client.post(
        "/admin/products/new",
        data=valid_product_form(product_name),
    )

    assert response.status_code == 400
    assert b"A product with this name already exists." in response.data

    with app.app_context():
        assert (
            Product.query.filter_by(name=product_name).count()
            == 1
        )


@pytest.mark.parametrize(
    "price",
    ["not-a-price", "-1.00"],
)
def test_add_product_rejects_invalid_price(price):
    app = create_app({"TESTING": True})
    client = app.test_client()
    sign_in_admin(client)

    form_data = valid_product_form(
        f"Invalid Price Product {price}"
    )
    form_data["price"] = price

    response = client.post(
        "/admin/products/new",
        data=form_data,
    )

    assert response.status_code == 400
    assert (
        b"Please enter a valid non-negative price."
        in response.data
    )


@pytest.mark.parametrize(
    "stock",
    ["not-a-number", "-1"],
)
def test_add_product_rejects_invalid_stock(stock):
    app = create_app({"TESTING": True})
    client = app.test_client()
    sign_in_admin(client)

    form_data = valid_product_form(
        f"Invalid Stock Product {stock}"
    )
    form_data["stock"] = stock

    response = client.post(
        "/admin/products/new",
        data=form_data,
    )

    assert response.status_code == 400
    assert (
        b"Please enter a valid non-negative stock quantity."
        in response.data
    )
