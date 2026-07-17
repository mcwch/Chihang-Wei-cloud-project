from sqlalchemy import text

from app import create_app
from models import db


def test_mysql_connection_uses_test_database():
    app = create_app({"TESTING": True})

    with app.app_context():
        database_name = db.session.execute(
            text("SELECT DATABASE()")
        ).scalar_one()

    assert database_name == "ecommerce_app_test"
