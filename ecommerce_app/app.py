from decimal import Decimal

from flask import (
    Flask,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

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

    @app.post("/cart/add/<int:product_id>")
    def add_to_cart(product_id):
        product = db.get_or_404(Product, product_id)

        try:
            quantity = int(request.form.get("quantity", 1))
        except (TypeError, ValueError):
            quantity = 1

        quantity = max(quantity, 1)

        cart = session.get("cart", {})
        product_key = str(product.id)

        current_quantity = int(cart.get(product_key, 0))
        new_quantity = current_quantity + quantity

        # Prevent the cart quantity from exceeding inventory.
        cart[product_key] = min(new_quantity, product.stock)

        session["cart"] = cart
        session.modified = True

        return redirect(url_for("view_cart"))

    @app.route("/cart")
    def view_cart():
        cart = session.get("cart", {})

        if not cart:
            return render_template(
                "cart.html",
                cart_items=[],
                cart_total=Decimal("0.00"),
            )

        product_ids = [
            int(product_id)
            for product_id in cart
        ]

        products = Product.query.filter(
            Product.id.in_(product_ids)
        ).all()

        products_by_id = {
            product.id: product
            for product in products
        }

        cart_items = []
        cart_total = Decimal("0.00")

        for product_id, quantity in cart.items():
            product = products_by_id.get(int(product_id))

            if product is None:
                continue

            subtotal = product.price * quantity
            cart_total += subtotal

            cart_items.append(
                {
                    "product": product,
                    "quantity": quantity,
                    "subtotal": subtotal,
                }
            )

        return render_template(
            "cart.html",
            cart_items=cart_items,
            cart_total=cart_total,
        )

    return app


app = create_app()


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=3000,
        debug=True,
    )
