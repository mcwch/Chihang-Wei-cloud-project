from decimal import Decimal

from app import create_app
from models import Product, db


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
