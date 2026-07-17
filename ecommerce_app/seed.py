from decimal import Decimal

from models import Product, db


DEFAULT_PRODUCTS = [
    {
        "name": "Wireless Headphones",
        "description": (
            "Comfortable wireless headphones for music, "
            "video calls, and daily use."
        ),
        "price": Decimal("59.99"),
        "stock": 12,
        "category": "Audio",
        "image_url": None,
    },
    {
        "name": "USB-C Charger",
        "description": (
            "A compact USB-C charger for phones, tablets, "
            "and other devices."
        ),
        "price": Decimal("19.99"),
        "stock": 25,
        "category": "Accessories",
        "image_url": None,
    },
    {
        "name": "Laptop Stand",
        "description": (
            "An adjustable laptop stand that helps improve "
            "desk setup and comfort."
        ),
        "price": Decimal("39.99"),
        "stock": 8,
        "category": "Accessories",
        "image_url": None,
    },
]


def seed_products():
    created_count = 0

    for product_data in DEFAULT_PRODUCTS:
        existing_product = Product.query.filter_by(
            name=product_data["name"]
        ).first()

        if existing_product is None:
            db.session.add(Product(**product_data))
            created_count += 1

    db.session.commit()
    return created_count
