from decimal import Decimal

from models import Product, db


DEFAULT_PRODUCTS = [
    {
        "name": "Wireless Headphones",
        "description": (
            "Comfortable wireless headphones for music, "
            "video calls, and everyday listening."
        ),
        "price": Decimal("59.99"),
        "stock": 12,
        "category": "Audio",
        "image_url": None,
    },
    {
        "name": "USB-C Charger",
        "description": (
            "A compact fast charger for phones, tablets, "
            "and other USB-C devices."
        ),
        "price": Decimal("19.99"),
        "stock": 25,
        "category": "Power",
        "image_url": None,
    },
    {
        "name": "Laptop Stand",
        "description": (
            "An adjustable laptop stand designed for a "
            "more comfortable and organised workspace."
        ),
        "price": Decimal("39.99"),
        "stock": 8,
        "category": "Workspace",
        "image_url": None,
    },
    {
        "name": "Wireless Mouse",
        "description": (
            "A lightweight wireless mouse with smooth tracking "
            "for work, study, and travel."
        ),
        "price": Decimal("29.99"),
        "stock": 18,
        "category": "Accessories",
        "image_url": None,
    },
    {
        "name": "Mechanical Keyboard",
        "description": (
            "A responsive mechanical keyboard with a compact "
            "layout and comfortable key switches."
        ),
        "price": Decimal("79.99"),
        "stock": 10,
        "category": "Accessories",
        "image_url": None,
    },
    {
        "name": "Portable SSD",
        "description": (
            "Fast and portable solid-state storage for files, "
            "backups, photos, and projects."
        ),
        "price": Decimal("89.99"),
        "stock": 9,
        "category": "Storage",
        "image_url": None,
    },
    {
        "name": "USB-C Hub",
        "description": (
            "A multi-port USB-C hub for connecting displays, "
            "storage devices, and other accessories."
        ),
        "price": Decimal("34.99"),
        "stock": 16,
        "category": "Connectivity",
        "image_url": None,
    },
    {
        "name": "HD Webcam",
        "description": (
            "A clear HD webcam with a built-in microphone "
            "for meetings, classes, and video calls."
        ),
        "price": Decimal("49.99"),
        "stock": 11,
        "category": "Video",
        "image_url": None,
    },
    {
        "name": "Bluetooth Speaker",
        "description": (
            "A compact Bluetooth speaker that delivers clear "
            "sound at home or while travelling."
        ),
        "price": Decimal("44.99"),
        "stock": 14,
        "category": "Audio",
        "image_url": None,
    },
    {
        "name": "LED Desk Lamp",
        "description": (
            "An adjustable LED desk lamp with multiple brightness "
            "settings for work and reading."
        ),
        "price": Decimal("27.99"),
        "stock": 13,
        "category": "Workspace",
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


def main(app_factory=None):
    if app_factory is None:
        from app import create_app

        app_factory = create_app

    app = app_factory()

    with app.app_context():
        db.create_all()
        created_count = seed_products()

    print(
        f"Created {created_count} missing products."
    )

    return created_count


if __name__ == "__main__":
    main()
