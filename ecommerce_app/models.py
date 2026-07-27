from datetime import datetime, timezone

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    stock = db.Column(db.Integer, nullable=False, default=0)
    category = db.Column(db.String(100), nullable=False)
    image_url = db.Column(db.String(500), nullable=True)

    is_active = db.Column(
        db.Boolean,
        nullable=False,
        default=True,
        server_default="1",
    )

    def __init__(self, **kwargs):
        kwargs.setdefault("is_active", True)
        super().__init__(**kwargs)


class Order(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(
        db.String(200),
        nullable=False,
    )
    email = db.Column(
        db.String(200),
        nullable=False,
    )
    address = db.Column(
        db.Text,
        nullable=False,
    )
    total_price = db.Column(
        db.Numeric(10, 2),
        nullable=False,
    )
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    status = db.Column(
        db.String(50),
        nullable=False,
        default="Pending",
    )

    items = db.relationship(
        "OrderItem",
        back_populates="order",
        cascade="all, delete-orphan",
    )


class OrderItem(db.Model):
    __tablename__ = "order_items"

    id = db.Column(db.Integer, primary_key=True)

    order_id = db.Column(
        db.Integer,
        db.ForeignKey("orders.id"),
        nullable=False,
    )

    product_id = db.Column(
        db.Integer,
        db.ForeignKey("products.id"),
        nullable=False,
    )

    quantity = db.Column(
        db.Integer,
        nullable=False,
    )

    unit_price = db.Column(
        db.Numeric(10, 2),
        nullable=False,
    )

    order = db.relationship(
        "Order",
        back_populates="items",
    )

    product = db.relationship(
        "Product",
    )
