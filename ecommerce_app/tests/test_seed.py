from app import create_app
from models import Product, db
from seed import seed_products


def reset_products():
    Product.query.delete()
    db.session.commit()


def test_seed_products_adds_default_catalog():
    app = create_app({"TESTING": True})

    with app.app_context():
        db.create_all()
        reset_products()

        seed_products()

        products = Product.query.order_by(Product.id).all()

        assert [product.name for product in products] == [
            "Wireless Headphones",
            "USB-C Charger",
            "Laptop Stand",
        ]
        assert [str(product.price) for product in products] == [
            "59.99",
            "19.99",
            "39.99",
        ]
        assert [product.stock for product in products] == [12, 25, 8]


def test_seed_products_does_not_create_duplicates():
    app = create_app({"TESTING": True})

    with app.app_context():
        db.create_all()
        reset_products()

        seed_products()
        seed_products()

        assert Product.query.count() == 3
