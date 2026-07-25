from decimal import Decimal

from app import create_app
from models import Product


def sign_in_admin(client):
    with client.session_transaction() as admin_session:
        admin_session["is_admin"] = True


def make_product():
    return Product(
        name="Archive Test Keyboard",
        description="A product used to test catalogue management.",
        price=Decimal("69.99"),
        stock=7,
        category="Accessories",
        image_url=None,
    )


def test_product_defaults_to_active():
    product = make_product()

    assert getattr(product, "is_active", None) is True


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
