from decimal import Decimal

import serverless

from flask import (
    Flask,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from config import Config
from models import Order, OrderItem, Product, db


def get_cart_summary():
    cart = session.get("cart", {})

    if not cart:
        return [], Decimal("0.00")

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

    for product_id, stored_quantity in cart.items():
        product = products_by_id.get(int(product_id))

        if product is None:
            continue

        quantity = int(stored_quantity)
        subtotal = product.price * quantity
        cart_total += subtotal

        cart_items.append(
            {
                "product": product,
                "quantity": quantity,
                "subtotal": subtotal,
            }
        )

    return cart_items, cart_total


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

        cart[product_key] = min(
            new_quantity,
            product.stock,
        )

        session["cart"] = cart
        session.modified = True

        return redirect(url_for("view_cart"))

    @app.route("/cart")
    def view_cart():
        cart_items, cart_total = get_cart_summary()

        return render_template(
            "cart.html",
            cart_items=cart_items,
            cart_total=cart_total,
        )

    @app.post("/cart/update/<int:product_id>")
    def update_cart(product_id):
        product = db.get_or_404(Product, product_id)

        try:
            quantity = int(request.form.get("quantity", 1))
        except (TypeError, ValueError):
            quantity = 1

        cart = session.get("cart", {})
        product_key = str(product.id)

        if quantity <= 0 or product.stock <= 0:
            cart.pop(product_key, None)
        else:
            cart[product_key] = min(
                quantity,
                product.stock,
            )

        session["cart"] = cart
        session.modified = True

        return redirect(url_for("view_cart"))

    @app.post("/cart/remove/<int:product_id>")
    def remove_from_cart(product_id):
        cart = session.get("cart", {})
        cart.pop(str(product_id), None)

        session["cart"] = cart
        session.modified = True

        return redirect(url_for("view_cart"))

    @app.post("/cart/clear")
    def clear_cart():
        session["cart"] = {}
        session.modified = True

        return redirect(url_for("view_cart"))

    @app.route("/checkout", methods=["GET", "POST"])
    def checkout():
        cart_items, cart_total = get_cart_summary()

        if not cart_items:
            return redirect(url_for("view_cart"))

        error_message = None

        if request.method == "POST":
            customer_name = request.form.get(
                "customer_name",
                "",
            ).strip()

            email = request.form.get(
                "email",
                "",
            ).strip()

            address = request.form.get(
                "address",
                "",
            ).strip()

            if not customer_name or not email or not address:
                error_message = (
                    "Please complete all required fields."
                )

                return (
                    render_template(
                        "checkout.html",
                        cart_items=cart_items,
                        cart_total=cart_total,
                        error_message=error_message,
                    ),
                    400,
                )

            for item in cart_items:
                if item["quantity"] > item["product"].stock:
                    error_message = (
                        f"Insufficient stock for "
                        f"{item['product'].name}."
                    )

                    return (
                        render_template(
                            "checkout.html",
                            cart_items=cart_items,
                            cart_total=cart_total,
                            error_message=error_message,
                        ),
                        400,
                    )

            try:
                order = Order(
                    customer_name=customer_name,
                    email=email,
                    address=address,
                    total_price=cart_total,
                )

                db.session.add(order)
                db.session.flush()

                for item in cart_items:
                    product = item["product"]
                    quantity = item["quantity"]

                    order_item = OrderItem(
                        order_id=order.id,
                        product_id=product.id,
                        quantity=quantity,
                        unit_price=product.price,
                    )

                    product.stock -= quantity
                    db.session.add(order_item)

                db.session.commit()

            except Exception:
                db.session.rollback()
                raise

            session["cart"] = {}
            session.modified = True

            return redirect(
                url_for(
                    "order_success",
                    order_id=order.id,
                )
            )

        return render_template(
            "checkout.html",
            cart_items=cart_items,
            cart_total=cart_total,
            error_message=error_message,
        )

    @app.route("/orders")
    def orders():
        all_orders = Order.query.order_by(
            Order.created_at.desc()
        ).all()

        return render_template(
            "orders.html",
            orders=all_orders,
        )

    @app.route("/orders/<int:order_id>")
    def order_detail(order_id):
        order = db.get_or_404(Order, order_id)

        return render_template(
            "order_detail.html",
            order=order,
        )

    @app.post("/orders/<int:order_id>/status")
    def update_order_status(order_id):
        order = db.get_or_404(Order, order_id)

        allowed_statuses = {
            "Pending",
            "Processing",
            "Shipped",
            "Completed",
        }

        new_status = request.form.get(
            "status",
            "",
        ).strip()

        if new_status in allowed_statuses:
            order.status = new_status
            db.session.commit()

        return redirect(
            url_for(
                "order_detail",
                order_id=order.id,
            )
        )

    @app.route("/order-success/<int:order_id>")
    def order_success(order_id):
        order = db.get_or_404(Order, order_id)

        confirmation_message = (
            f"Order #{order.id} has been received."
        )

        function_url = app.config.get(
            "DIGITALOCEAN_FUNCTION_URL",
            "",
        ).strip()

        if function_url:
            confirmation_message = (
                serverless.get_order_confirmation(
                    function_url=function_url,
                    order_id=order.id,
                    customer_name=order.customer_name,
                )
            )

        return render_template(
            "order_success.html",
            order=order,
            confirmation_message=confirmation_message,
        )

    return app


app = create_app()


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=3000,
        debug=True,
    )
