from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


CUSTOMER_TEMPLATES = [
    "cart.html",
    "checkout.html",
    "order_success.html",
    "product_detail.html",
]


ADMIN_TEMPLATES = [
    "admin_login.html",
    "admin_products.html",
    "admin_product_form.html",
    "orders.html",
    "order_detail.html",
    "admin_monitor.html",
    "admin_logs.html",
]


def read_project_file(relative_path):
    return (
        PROJECT_ROOT
        / relative_path
    ).read_text(encoding="utf-8-sig")


def test_customer_pages_use_shared_page_shell():
    for template_name in CUSTOMER_TEMPLATES:
        template = read_project_file(
            f"templates/{template_name}"
        )

        assert "page-shell" in template


def test_admin_pages_use_shared_page_shell():
    for template_name in ADMIN_TEMPLATES:
        template = read_project_file(
            f"templates/{template_name}"
        )

        assert "page-shell" in template


def test_main_forms_use_shared_form_card():
    admin_login = read_project_file(
        "templates/admin_login.html"
    )
    product_form = read_project_file(
        "templates/admin_product_form.html"
    )
    checkout = read_project_file(
        "templates/checkout.html"
    )

    assert "form-card" in admin_login
    assert "form-card" in product_form
    assert "form-card" in checkout


def test_major_content_sections_use_shared_cards():
    expected_templates = [
        "templates/cart.html",
        "templates/checkout.html",
        "templates/order_success.html",
        "templates/order_detail.html",
        "templates/admin_monitor.html",
        "templates/admin_logs.html",
    ]

    for relative_path in expected_templates:
        template = read_project_file(relative_path)

        assert "content-card" in template


def test_empty_states_use_consistent_markup():
    orders = read_project_file(
        "templates/orders.html"
    )
    logs = read_project_file(
        "templates/admin_logs.html"
    )

    assert 'class="empty-state"' in orders
    assert 'class="empty-state"' in logs


def test_checkout_and_success_markup_has_no_corruption():
    checkout = read_project_file(
        "templates/checkout.html"
    )
    success = read_project_file(
        "templates/order_success.html"
    )

    assert "&larr; Back to Shopping Cart" in checkout
    assert "?Back to Shopping Cart" not in checkout

    assert "&#10003;" in success
    assert "?/div>" not in success


def test_shared_ui_css_defines_consistent_components():
    stylesheet = read_project_file(
        "static/style.css"
    )

    expected_selectors = [
        ".page-shell",
        ".content-card",
        ".form-card",
        ".status-message",
        ".page-header-actions",
    ]

    for selector in expected_selectors:
        assert selector in stylesheet

    assert "overflow-wrap: anywhere;" in stylesheet
    assert "@media (max-width: 760px)" in stylesheet


def test_load_balancer_page_uses_shared_visual_tokens():
    template = read_project_file(
        "templates/load_balancer_status.html"
    )

    assert 'class="page-shell"' in template
    assert 'class="page-header"' in template
    assert "content-card" in template
    assert "status-message" in template
    assert "overflow-wrap: anywhere;" in template
