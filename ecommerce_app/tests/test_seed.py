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

        created_count = seed_products()

        products = Product.query.order_by(Product.id).all()

        assert created_count == 10

        assert [product.name for product in products] == [
            "Wireless Headphones",
            "USB-C Charger",
            "Laptop Stand",
            "Wireless Mouse",
            "Mechanical Keyboard",
            "Portable SSD",
            "USB-C Hub",
            "HD Webcam",
            "Bluetooth Speaker",
            "LED Desk Lamp",
        ]

        assert [str(product.price) for product in products] == [
            "59.99",
            "19.99",
            "39.99",
            "29.99",
            "79.99",
            "89.99",
            "34.99",
            "49.99",
            "44.99",
            "27.99",
        ]

        assert [product.stock for product in products] == [
            12,
            25,
            8,
            18,
            10,
            9,
            16,
            11,
            14,
            13,
        ]


def test_seed_products_does_not_create_duplicates():
    app = create_app({"TESTING": True})

    with app.app_context():
        db.create_all()
        reset_products()

        first_created_count = seed_products()
        second_created_count = seed_products()

        assert first_created_count == 10
        assert second_created_count == 0
        assert Product.query.count() == 10
