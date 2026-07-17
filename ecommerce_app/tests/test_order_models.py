from sqlalchemy import inspect

from models import Order, OrderItem


def test_order_model_has_required_columns():
    columns = {
        column.name
        for column in inspect(Order).columns
    }

    assert columns == {
        "id",
        "customer_name",
        "email",
        "address",
        "total_price",
        "created_at",
    }


def test_order_item_model_has_required_columns():
    columns = {
        column.name
        for column in inspect(OrderItem).columns
    }

    assert columns == {
        "id",
        "order_id",
        "product_id",
        "quantity",
        "unit_price",
    }


def test_order_prices_use_fixed_decimal_types():
    order_total = inspect(Order).columns.total_price
    unit_price = inspect(OrderItem).columns.unit_price

    assert order_total.type.precision == 10
    assert order_total.type.scale == 2
    assert unit_price.type.precision == 10
    assert unit_price.type.scale == 2


def test_order_item_has_order_and_product_foreign_keys():
    order_foreign_keys = {
        foreign_key.target_fullname
        for foreign_key
        in inspect(OrderItem).columns.order_id.foreign_keys
    }

    product_foreign_keys = {
        foreign_key.target_fullname
        for foreign_key
        in inspect(OrderItem).columns.product_id.foreign_keys
    }

    assert order_foreign_keys == {"orders.id"}
    assert product_foreign_keys == {"products.id"}
