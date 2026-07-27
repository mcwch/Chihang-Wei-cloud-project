from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def read_project_file(relative_path):
    return (
        PROJECT_ROOT
        / relative_path
    ).read_text(encoding="utf-8-sig")


def test_base_template_uses_accessible_site_navigation():
    template = read_project_file(
        "templates/base.html"
    )

    assert 'class="site-nav"' in template
    assert (
        'aria-label="Primary navigation"'
        in template
    )
    assert 'class="nav-link"' in template
    assert (
        'class="nav-link nav-button"'
        in template
    )


def test_navigation_styles_include_mobile_touch_layout():
    stylesheet = read_project_file(
        "static/style.css"
    )

    assert ".site-nav" in stylesheet
    assert ".nav-link" in stylesheet
    assert "min-height: 44px;" in stylesheet

    assert "@media (max-width: 760px)" in stylesheet
    assert (
        "grid-template-columns: "
        "repeat(2, minmax(0, 1fr));"
        in stylesheet
    )
    assert "width: 100%;" in stylesheet
