from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
HOME_TEMPLATE = PROJECT_ROOT / "templates" / "index.html"
STYLESHEET = PROJECT_ROOT / "static" / "style.css"


def read_home_template():
    return HOME_TEMPLATE.read_text(
        encoding="utf-8-sig"
    )


def read_stylesheet():
    return STYLESHEET.read_text(
        encoding="utf-8-sig"
    )


def test_homepage_uses_modern_store_structure():
    template = read_home_template()

    assert 'class="hero hero-panel"' in template
    assert 'class="hero-content"' in template
    assert 'class="hero-offer"' in template
    assert 'class="hero-actions"' in template

    assert 'href="#featured-products"' in template
    assert "Shop Products" in template

    assert 'id="featured-products"' in template
    assert 'class="product-card-body"' in template
    assert 'class="product-card-footer"' in template
    assert 'class="stock-badge"' in template


def test_homepage_modern_store_styles_are_defined():
    stylesheet = read_stylesheet()

    assert ".hero-panel" in stylesheet
    assert ".hero-content" in stylesheet
    assert ".hero-offer" in stylesheet
    assert ".hero-actions" in stylesheet

    assert "linear-gradient" in stylesheet
    assert ".product-card-body" in stylesheet
    assert ".product-card-footer" in stylesheet
    assert ".stock-badge" in stylesheet

    assert "height: 100%" in stylesheet
    assert "margin-top: auto" in stylesheet
    assert "transform: translateY(-4px)" in stylesheet
