from pathlib import Path

from app import create_app


PROJECT_ROOT = Path(__file__).resolve().parents[1]


EXPECTED_PRODUCT_ICONS = {
    "Wireless Headphones": "\U0001F3A7",
    "USB-C Charger": "\U0001F50C",
    "Laptop Stand": "\U0001F4BB",
    "Wireless Mouse": "\U0001F5B1",
    "Mechanical Keyboard": "\u2328",
    "Portable SSD": "\U0001F4BE",
    "USB-C Hub": "\U0001F517",
    "HD Webcam": "\U0001F4F7",
    "Bluetooth Speaker": "\U0001F50A",
    "LED Desk Lamp": "\U0001F4A1",
}


def read_template(name):
    return (
        PROJECT_ROOT
        / "templates"
        / name
    ).read_text(encoding="utf-8-sig")


def read_stylesheet():
    return (
        PROJECT_ROOT
        / "static"
        / "style.css"
    ).read_text(encoding="utf-8-sig")


def test_default_products_have_distinct_icons():
    from product_visuals import get_product_icon

    actual_icons = {
        product_name: get_product_icon(
            product_name,
            "Unknown",
        )
        for product_name in EXPECTED_PRODUCT_ICONS
    }

    assert actual_icons == EXPECTED_PRODUCT_ICONS


def test_unknown_product_uses_category_fallback():
    from product_visuals import get_product_icon

    assert get_product_icon(
        "Studio Microphone",
        "Audio",
    ) == "\U0001F50A"

    assert get_product_icon(
        "External Drive",
        "Storage",
    ) == "\U0001F4BE"

    assert get_product_icon(
        "Docking Station",
        "Connectivity",
    ) == "\U0001F517"


def test_completely_unknown_product_uses_default_icon():
    from product_visuals import get_product_icon

    assert get_product_icon(
        "Mystery Product",
        "Unknown Category",
    ) == "\u2699"


def test_flask_registers_product_icon_template_helper():
    from product_visuals import get_product_icon

    app = create_app({"TESTING": True})

    assert (
        app.jinja_env.globals["product_icon"]
        is get_product_icon
    )


def test_homepage_contains_product_visual_area():
    template = read_template("index.html")

    assert 'class="product-visual"' in template
    assert 'class="product-icon"' in template

    assert (
        "product_icon("
        "product.name, product.category"
        ")"
        in template
    )


def test_product_detail_contains_large_visual_area():
    template = read_template(
        "product_detail.html"
    )

    assert (
        'class="product-detail-layout"'
        in template
    )
    assert (
        'class="product-detail-visual"'
        in template
    )
    assert (
        'class="product-detail-icon"'
        in template
    )

    assert "&larr; Back to Product List" in template
    assert "鈫?" not in template


def test_product_visual_styles_are_responsive():
    stylesheet = read_stylesheet()

    assert ".product-visual" in stylesheet
    assert ".product-icon" in stylesheet
    assert ".product-detail-layout" in stylesheet
    assert ".product-detail-visual" in stylesheet
    assert ".product-detail-icon" in stylesheet

    assert "grid-template-columns: minmax(260px, 0.8fr)" in (
        stylesheet
    )

    assert (
        ".product-detail-layout {\n"
        "        grid-template-columns: 1fr"
        in stylesheet
    )
