from flask import Flask, render_template

from config import Config
from models import Product, db


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_object(Config)

    test_config = test_config or {}
    app.config.update(test_config)

    if (
        app.config.get("TESTING")
        and "SQLALCHEMY_DATABASE_URI" not in test_config
    ):
        app.config["SQLALCHEMY_DATABASE_URI"] = (
            app.config["SQLALCHEMY_TEST_DATABASE_URI"]
        )

    db.init_app(app)

    @app.route("/")
    def home():
        products = Product.query.order_by(Product.id).all()

        return render_template(
            "index.html",
            products=products,
        )

    @app.route("/product/<int:product_id>")
    def product_detail(product_id):
        product = db.get_or_404(Product, product_id)

        return render_template(
            "product_detail.html",
            product=product,
        )

    return app


app = create_app()


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=3000,
        debug=True,
    )
