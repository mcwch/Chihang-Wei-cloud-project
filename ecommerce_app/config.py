import os
from urllib.parse import quote_plus

from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv(
        "SECRET_KEY",
        "development-secret-key",
    )

    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "3306")
    DB_NAME = os.getenv("DB_NAME", "ecommerce_app")
    DB_TEST_NAME = os.getenv(
        "DB_TEST_NAME",
        "ecommerce_app_test",
    )
    DB_USER = os.getenv("DB_USER", "ecommerce_user")
    DB_PASSWORD = quote_plus(
        os.getenv("DB_PASSWORD", "")
    )

    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}"
        f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )

    SQLALCHEMY_TEST_DATABASE_URI = (
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}"
        f"@{DB_HOST}:{DB_PORT}/{DB_TEST_NAME}"
    )

    SERVERLESS_FUNCTION_URL = os.getenv(
        "SERVERLESS_FUNCTION_URL",
        "",
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False
