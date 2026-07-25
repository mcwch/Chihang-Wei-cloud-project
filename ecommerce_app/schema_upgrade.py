from sqlalchemy import inspect, text

from models import db


def upgrade_product_schema():
    inspector = inspect(db.engine)
    table_names = inspector.get_table_names()

    if "products" not in table_names:
        db.create_all()
        return "Created database tables."

    column_names = {
        column["name"]
        for column in inspector.get_columns("products")
    }

    if "is_active" in column_names:
        return "products.is_active already exists."

    db.session.execute(
        text(
            "ALTER TABLE products "
            "ADD COLUMN is_active BOOLEAN "
            "NOT NULL DEFAULT 1"
        )
    )
    db.session.commit()

    return "Added products.is_active."
