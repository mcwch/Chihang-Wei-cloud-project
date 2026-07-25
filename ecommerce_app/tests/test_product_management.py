from decimal import Decimal

import pytest

from app import create_app
from models import Product, db


def sign_in_admin(client):
    with client.session_transaction() as admin_session:
        admin_session["is_admin"] = True


def delete_product_by_name(app, product_name):
    with app.app_context():
        Product.query.filter_by(name=product_name).delete()
        db.session.commit()


def make_product():
    return Product(
        name="Archive Test Keyboard",
        description="A product used to test catalogue management.",
        price=Decimal("69.99"),
        stock=7,
        category="Accessories",
        image_url=None,
    )


def valid_product_form(product_name):
    return {
        "name": product_name,
        "description": (
            "A compact accessory created through the admin form."
        ),
        "price": "49.99",
        "stock": "15",
        "category": "Accessories",
    }


def test_product_defaults_to_active():
    product = make_product()

    assert product.is_active is True


def test_product_management_requires_admin_login():
    app = create_app({"TESTING": True})
    client = app.test_client()

    response = client.get("/admin/products")

    assert response.status_code == 302
    assert response.headers["Location"].endswith(
        "/admin/login?next=/admin/products"
    )


def test_admin_can_open_product_management_page():
    app = create_app({"TESTING": True})
    client = app.test_client()
    sign_in_admin(client)

    response = client.get("/admin/products")

    assert response.status_code == 200
    assert b"Product Management" in response.data
    assert b"Add Product" in response.data


def test_add_product_page_requires_admin_login():
    app = create_app({"TESTING": True})
    client = app.test_client()

    response = client.get("/admin/products/new")

    assert response.status_code == 302
    assert response.headers["Location"].endswith(
        "/admin/login?next=/admin/products/new"
    )


def test_admin_can_open_add_product_form():
    app = create_app({"TESTING": True})
    client = app.test_client()
    sign_in_admin(client)

    response = client.get("/admin/products/new")

    assert response.status_code == 200
    assert b"Add Product" in response.data
    assert b'name="name"' in response.data
    assert b'name="description"' in response.data
    assert b'name="price"' in response.data
    assert b'name="stock"' in response.data
    assert b'name="category"' in response.data


def test_admin_can_create_product_and_audit_event():
    product_name = "Travel Power Adapter"

    app = create_app({"TESTING": True})
    delete_product_by_name(app, product_name)

    client = app.test_client()
    sign_in_admin(client)

    response = client.post(
        "/admin/products/new",
        data=valid_product_form(product_name),
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith(
        "/admin/products"
    )

    with app.app_context():
        product = Product.query.filter_by(
            name=product_name
        ).one()

        assert product.description == (
            "A compact accessory created through the admin form."
        )
        assert product.price == Decimal("49.99")
        assert product.stock == 15
        assert product.category == "Accessories"
        assert product.is_active is True

    audit_entries = list(app.extensions["audit_log"])

    assert any(
        entry["event_type"] == "Product Created"
        and product_name in entry["description"]
        for entry in audit_entries
    )


def test_add_product_rejects_blank_name():
    app = create_app({"TESTING": True})
    client = app.test_client()
    sign_in_admin(client)

    form_data = valid_product_form(" ")
    response = client.post(
        "/admin/products/new",
        data=form_data,
    )

    assert response.status_code == 400
    assert b"Product name is required." in response.data


def test_add_product_rejects_duplicate_name():
    product_name = "Duplicate Product Test"

    app = create_app({"TESTING": True})
    delete_product_by_name(app, product_name)

    with app.app_context():
        db.session.add(
            Product(
                name=product_name,
                description="Existing product.",
                price=Decimal("20.00"),
                stock=5,
                category="Test",
                image_url=None,
            )
        )
        db.session.commit()

    client = app.test_client()
    sign_in_admin(client)

    response = client.post(
        "/admin/products/new",
        data=valid_product_form(product_name),
    )

    assert response.status_code == 400
    assert b"A product with this name already exists." in response.data

    with app.app_context():
        assert (
            Product.query.filter_by(name=product_name).count()
            == 1
        )


@pytest.mark.parametrize(
    "price",
    ["not-a-price", "-1.00"],
)
def test_add_product_rejects_invalid_price(price):
    app = create_app({"TESTING": True})
    client = app.test_client()
    sign_in_admin(client)

    form_data = valid_product_form(
        f"Invalid Price Product {price}"
    )
    form_data["price"] = price

    response = client.post(
        "/admin/products/new",
        data=form_data,
    )

    assert response.status_code == 400
    assert (
        b"Please enter a valid non-negative price."
        in response.data
    )


@pytest.mark.parametrize(
    "stock",
    ["not-a-number", "-1"],
)
def test_add_product_rejects_invalid_stock(stock):
    app = create_app({"TESTING": True})
    client = app.test_client()
    sign_in_admin(client)

    form_data = valid_product_form(
        f"Invalid Stock Product {stock}"
    )
    form_data["stock"] = stock

    response = client.post(
        "/admin/products/new",
        data=form_data,
    )

    assert response.status_code == 400
    assert (
        b"Please enter a valid non-negative stock quantity."
        in response.data
    )


def create_managed_product(app, product_name):
    delete_product_by_name(app, product_name)

    with app.app_context():
        product = Product(
            name=product_name,
            description="Original product description.",
            price=Decimal("35.00"),
            stock=6,
            category="Original Category",
            image_url=None,
        )

        db.session.add(product)
        db.session.commit()

        return product.id


def test_edit_product_page_requires_admin_login():
    product_name = "Protected Edit Product"
    app = create_app({"TESTING": True})
    product_id = create_managed_product(app, product_name)

    client = app.test_client()
    response = client.get(
        f"/admin/products/{product_id}/edit"
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith(
        f"/admin/login?next=/admin/products/{product_id}/edit"
    )


def test_admin_can_open_edit_product_form():
    product_name = "Editable Product"
    app = create_app({"TESTING": True})
    product_id = create_managed_product(app, product_name)

    client = app.test_client()
    sign_in_admin(client)

    response = client.get(
        f"/admin/products/{product_id}/edit"
    )

    assert response.status_code == 200
    assert b"Edit Product" in response.data
    assert product_name.encode() in response.data
    assert b"Original product description." in response.data
    assert b'value="35.00"' in response.data
    assert b'value="6"' in response.data
    assert b'value="Original Category"' in response.data


def test_admin_can_update_product_and_audit_event():
    original_name = "Product Before Update"
    updated_name = "Product After Update"

    app = create_app({"TESTING": True})
    delete_product_by_name(app, updated_name)
    product_id = create_managed_product(app, original_name)

    client = app.test_client()
    sign_in_admin(client)

    response = client.post(
        f"/admin/products/{product_id}/edit",
        data={
            "name": updated_name,
            "description": "Updated product description.",
            "price": "42.50",
            "stock": "19",
            "category": "Updated Category",
        },
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith(
        "/admin/products"
    )

    with app.app_context():
        product = db.session.get(Product, product_id)

        assert product.name == updated_name
        assert product.description == (
            "Updated product description."
        )
        assert product.price == Decimal("42.50")
        assert product.stock == 19
        assert product.category == "Updated Category"

    audit_entries = list(app.extensions["audit_log"])

    assert any(
        entry["event_type"] == "Product Updated"
        and updated_name in entry["description"]
        for entry in audit_entries
    )


def test_edit_product_allows_existing_name_for_same_product():
    product_name = "Same Name Product"

    app = create_app({"TESTING": True})
    product_id = create_managed_product(app, product_name)

    client = app.test_client()
    sign_in_admin(client)

    response = client.post(
        f"/admin/products/{product_id}/edit",
        data={
            "name": product_name,
            "description": "Changed while keeping the same name.",
            "price": "36.00",
            "stock": "8",
            "category": "Accessories",
        },
    )

    assert response.status_code == 302

    with app.app_context():
        product = db.session.get(Product, product_id)
        assert product.description == (
            "Changed while keeping the same name."
        )


def test_edit_product_rejects_another_products_name():
    first_name = "First Managed Product"
    second_name = "Second Managed Product"

    app = create_app({"TESTING": True})
    first_id = create_managed_product(app, first_name)
    create_managed_product(app, second_name)

    client = app.test_client()
    sign_in_admin(client)

    response = client.post(
        f"/admin/products/{first_id}/edit",
        data={
            "name": second_name,
            "description": "Attempted duplicate.",
            "price": "40.00",
            "stock": "5",
            "category": "Accessories",
        },
    )

    assert response.status_code == 400
    assert (
        b"A product with this name already exists."
        in response.data
    )

    with app.app_context():
        first_product = db.session.get(Product, first_id)
        assert first_product.name == first_name


def set_product_active_status(app, product_id, is_active):
    with app.app_context():
        product = db.session.get(Product, product_id)
        product.is_active = is_active
        db.session.commit()


def test_archive_product_requires_admin_login():
    product_name = "Protected Archive Product"

    app = create_app({"TESTING": True})
    product_id = create_managed_product(app, product_name)

    client = app.test_client()

    response = client.post(
        f"/admin/products/{product_id}/archive"
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith(
        f"/admin/login?next=/admin/products/{product_id}/archive"
    )


def test_admin_can_archive_product_and_audit_event():
    product_name = "Product To Archive"

    app = create_app({"TESTING": True})
    product_id = create_managed_product(app, product_name)

    client = app.test_client()
    sign_in_admin(client)

    response = client.post(
        f"/admin/products/{product_id}/archive"
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith(
        "/admin/products"
    )

    with app.app_context():
        product = db.session.get(Product, product_id)
        assert product.is_active is False

    audit_entries = list(app.extensions["audit_log"])

    assert any(
        entry["event_type"] == "Product Archived"
        and product_name in entry["description"]
        for entry in audit_entries
    )


def test_archived_product_is_hidden_from_homepage():
    product_name = "Hidden Archived Product"

    app = create_app({"TESTING": True})
    product_id = create_managed_product(app, product_name)
    set_product_active_status(app, product_id, False)

    client = app.test_client()
    response = client.get("/")

    assert response.status_code == 200
    assert product_name.encode() not in response.data


def test_archived_product_detail_returns_404():
    product_name = "Archived Detail Product"

    app = create_app({"TESTING": True})
    product_id = create_managed_product(app, product_name)
    set_product_active_status(app, product_id, False)

    client = app.test_client()

    response = client.get(f"/product/{product_id}")

    assert response.status_code == 404


def test_archived_product_cannot_be_added_to_cart():
    product_name = "Archived Cart Product"

    app = create_app({"TESTING": True})
    product_id = create_managed_product(app, product_name)
    set_product_active_status(app, product_id, False)

    client = app.test_client()

    response = client.post(
        f"/cart/add/{product_id}",
        data={"quantity": "1"},
    )

    assert response.status_code == 404

    with client.session_transaction() as customer_session:
        cart = customer_session.get("cart", {})
        assert str(product_id) not in cart


def test_admin_can_restore_product_and_audit_event():
    product_name = "Product To Restore"

    app = create_app({"TESTING": True})
    product_id = create_managed_product(app, product_name)
    set_product_active_status(app, product_id, False)

    client = app.test_client()
    sign_in_admin(client)

    response = client.post(
        f"/admin/products/{product_id}/restore"
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith(
        "/admin/products"
    )

    with app.app_context():
        product = db.session.get(Product, product_id)
        assert product.is_active is True

    audit_entries = list(app.extensions["audit_log"])

    assert any(
        entry["event_type"] == "Product Restored"
        and product_name in entry["description"]
        for entry in audit_entries
    )


def test_admin_product_page_shows_archive_and_restore_actions():
    active_name = "Active Action Product"
    archived_name = "Archived Action Product"

    app = create_app({"TESTING": True})

    active_id = create_managed_product(app, active_name)
    archived_id = create_managed_product(app, archived_name)

    set_product_active_status(app, archived_id, False)

    client = app.test_client()
    sign_in_admin(client)

    response = client.get("/admin/products")
    html = response.get_data(as_text=True)

    assert response.status_code == 200

    assert (
        f'action="/admin/products/{active_id}/archive"'
        in html
    )
    assert (
        f'action="/admin/products/{archived_id}/restore"'
        in html
    )

    assert "Archive" in html
    assert "Restore" in html
