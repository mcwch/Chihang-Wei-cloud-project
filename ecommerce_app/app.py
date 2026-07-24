from decimal import Decimal
from functools import wraps
from hmac import compare_digest
from threading import Lock
from time import perf_counter

import serverless

from sqlalchemy import text

from flask import (
    Flask,
    g,
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

    app.config.setdefault(
        "INSTANCE_NAME",
        "Standalone Instance",
    )

    if (
        app.config.get("TESTING")
        and "SQLALCHEMY_DATABASE_URI" not in test_config
    ):
        app.config["SQLALCHEMY_DATABASE_URI"] = (
            app.config["SQLALCHEMY_TEST_DATABASE_URI"]
        )

    db.init_app(app)

    monitoring_state = {
        "started_at": perf_counter(),
        "total_requests": 0,
        "successful_responses": 0,
        "responses_403": 0,
        "responses_404": 0,
        "responses_500": 0,
        "failed_admin_logins": 0,
        "total_response_time_ms": 0.0,
    }

    monitoring_lock = Lock()

    app.extensions["monitoring_state"] = monitoring_state
    app.extensions["monitoring_lock"] = monitoring_lock

    @app.before_request
    def start_request_timer():
        g.request_started_at = perf_counter()

    @app.after_request
    def record_request_metrics(response):
        started_at = getattr(
            g,
            "request_started_at",
            perf_counter(),
        )

        response_time_ms = (
            perf_counter() - started_at
        ) * 1000

        with monitoring_lock:
            monitoring_state["total_requests"] += 1
            monitoring_state[
                "total_response_time_ms"
            ] += response_time_ms

            if 200 <= response.status_code < 400:
                monitoring_state[
                    "successful_responses"
                ] += 1

            if response.status_code == 403:
                monitoring_state["responses_403"] += 1
            elif response.status_code == 404:
                monitoring_state["responses_404"] += 1
            elif response.status_code >= 500:
                monitoring_state["responses_500"] += 1

        return response

    def admin_required(view_function):
        @wraps(view_function)
        def wrapped_view(*args, **kwargs):
            if session.get("is_admin") is not True:
                return redirect(
                    url_for(
                        "admin_login",
                        next=request.path,
                    )
                )

            return view_function(*args, **kwargs)

        return wrapped_view

    @app.route(
        "/admin/login",
        methods=["GET", "POST"],
    )
    def admin_login():
        error_message = None

        next_url = request.values.get(
            "next",
            "",
        ).strip()

        if request.method == "POST":
            submitted_password = request.form.get(
                "password",
                "",
            )

            configured_password = app.config.get(
                "ADMIN_PASSWORD",
                "",
            )

            password_is_valid = (
                bool(configured_password)
                and compare_digest(
                    submitted_password,
                    configured_password,
                )
            )

            if password_is_valid:
                session["is_admin"] = True
                session.modified = True

                if (
                    next_url.startswith("/")
                    and not next_url.startswith("//")
                ):
                    return redirect(next_url)

                return redirect(url_for("orders"))

            with monitoring_lock:
                monitoring_state[
                    "failed_admin_logins"
                ] += 1

            error_message = (
                "Invalid administrator password."
            )

            return (
                render_template(
                    "admin_login.html",
                    error_message=error_message,
                    next_url=next_url,
                ),
                401,
            )

        return render_template(
            "admin_login.html",
            error_message=error_message,
            next_url=next_url,
        )

    @app.post("/admin/logout")
    def admin_logout():
        session.pop("is_admin", None)
        session.modified = True

        return redirect(url_for("admin_login"))

    @app.get("/health")
    def health():
        try:
            db.session.execute(text("SELECT 1"))
            total_orders = Order.query.count()

        except Exception:
            db.session.rollback()

            return (
                {
                    "status": "unhealthy",
                    "database": "disconnected",
                    "instance": app.config["INSTANCE_NAME"],
                },
                503,
            )

        return {
            "status": "healthy",
            "database": "connected",
            "instance": app.config["INSTANCE_NAME"],
            "total_orders": total_orders,
        }

    @app.get("/admin/monitor")
    @admin_required
    def admin_monitor():
        allowed_statuses = (
            "Pending",
            "Processing",
            "Shipped",
            "Completed",
            "Cancelled",
        )

        try:
            db.session.execute(text("SELECT 1"))
            database_status = "Connected"

            all_orders = Order.query.all()

            order_statistics = {
                "total": len(all_orders),
            }

            for status in allowed_statuses:
                order_statistics[status] = sum(
                    order.status == status
                    for order in all_orders
                )

        except Exception:
            db.session.rollback()
            database_status = "Disconnected"

            order_statistics = {
                "total": 0,
            }

            for status in allowed_statuses:
                order_statistics[status] = 0

        with monitoring_lock:
            monitoring_snapshot = dict(
                monitoring_state
            )

        total_requests = monitoring_snapshot[
            "total_requests"
        ]

        if total_requests:
            average_response_time_ms = (
                monitoring_snapshot[
                    "total_response_time_ms"
                ]
                / total_requests
            )
        else:
            average_response_time_ms = 0.0

        uptime_seconds = (
            perf_counter()
            - monitoring_snapshot["started_at"]
        )

        return render_template(
            "admin_monitor.html",
            database_status=database_status,
            monitoring=monitoring_snapshot,
            average_response_time_ms=(
                average_response_time_ms
            ),
            uptime_seconds=uptime_seconds,
            order_statistics=order_statistics,
        )

    @app.after_request
    def add_instance_header(response):
        response.headers["X-App-Instance"] = (
            app.config["INSTANCE_NAME"]
        )
        return response

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
    @admin_required
    def orders():
        allowed_statuses = (
            "Pending",
            "Processing",
            "Shipped",
            "Completed",
            "Cancelled",
        )

        all_orders = Order.query.order_by(
            Order.created_at.desc()
        ).all()

        order_statistics = {
            "total": len(all_orders),
        }

        for status in allowed_statuses:
            order_statistics[status] = sum(
                order.status == status
                for order in all_orders
            )

        requested_status = request.args.get(
            "status",
            "",
        ).strip()

        if requested_status in allowed_statuses:
            displayed_orders = [
                order
                for order in all_orders
                if order.status == requested_status
            ]
            active_filter = requested_status
        else:
            displayed_orders = all_orders
            active_filter = None

        return render_template(
            "orders.html",
            orders=displayed_orders,
            order_statistics=order_statistics,
            allowed_statuses=allowed_statuses,
            active_filter=active_filter,
        )

    @app.route("/orders/<int:order_id>")
    @admin_required
    def order_detail(order_id):
        order = db.get_or_404(Order, order_id)

        return render_template(
            "order_detail.html",
            order=order,
        )

    @app.post("/orders/<int:order_id>/status")
    @admin_required
    def update_order_status(order_id):
        order = db.get_or_404(Order, order_id)

        allowed_statuses = {
            "Pending",
            "Processing",
            "Shipped",
            "Completed",
            "Cancelled",
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
            "SERVERLESS_FUNCTION_URL",
            "",
        ).strip()

        if function_url:
            try:
                confirmation_message = (
                    serverless.get_order_confirmation(
                        function_url=function_url,
                        order_id=order.id,
                        customer_name=order.customer_name,
                    )
                )
            except OSError:
                pass

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
