from app import create_app


def test_customer_homepage_uses_novagear_branding():
    app = create_app({"TESTING": True})
    client = app.test_client()

    response = client.get("/")
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "NovaGear" in html
    assert "Upgrade Your Everyday Tech" in html
    assert (
        "Smart accessories for work, travel, and everyday life."
        in html
    )

    assert "Simple Ecommerce Store" not in html
    assert "Cloud Computing Course Project" not in html
    assert "Module 6 Ecommerce Project" not in html
    assert (
        "stored and retrieved dynamically from a MySQL database"
        not in html
    )
