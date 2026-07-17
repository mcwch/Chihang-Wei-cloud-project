from sqlalchemy import inspect

from models import Product


def test_product_model_has_required_columns():
    columns = {
        column.name
        for column in inspect(Product).columns
    }

    assert columns == {
        "id",
        "name",
        "description",
        "price",
        "stock",
        "category",
        "image_url",
    }


def test_product_price_uses_fixed_decimal_type():
    price_column = inspect(Product).columns.price

    assert price_column.type.precision == 10
    assert price_column.type.scale == 2
