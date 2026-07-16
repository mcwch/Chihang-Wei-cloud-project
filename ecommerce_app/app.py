from flask import Flask, abort

app = Flask(__name__)

products = [
    {
        "id": 1,
        "name": "Wireless Headphones",
        "price": "$59.99",
        "stock": 12,
        "description": "Comfortable wireless headphones for music, video calls, and daily use."
    },
    {
        "id": 2,
        "name": "USB-C Charger",
        "price": "$19.99",
        "stock": 25,
        "description": "A compact USB-C charger for phones, tablets, and other devices."
    },
    {
        "id": 3,
        "name": "Laptop Stand",
        "price": "$39.99",
        "stock": 8,
        "description": "An adjustable laptop stand that helps improve desk setup and comfort."
    }
]

def page_style():
    return """
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 40px;
            background-color: #f5f5f5;
        }

        h1 {
            color: #333333;
        }

        .banner {
            background-color: #dff0d8;
            padding: 15px;
            margin-bottom: 20px;
            border-radius: 5px;
        }

        .product, .detail {
            background-color: white;
            padding: 15px;
            margin: 10px 0;
            border-radius: 5px;
        }

        a {
            color: #0066cc;
            text-decoration: none;
        }
    </style>
    """

@app.route("/")
def home():
    product_html = ""

    for product in products:
        product_html += f"""
        <div class="product">
            <strong>{product["name"]}</strong><br>
            Price: {product["price"]}<br>
            In Stock: {product["stock"]}<br>
            <a href="/product/{product["id"]}">View Details</a>
        </div>
        """

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Simple Ecommerce Store</title>
        {page_style()}
    </head>
    <body>
        <h1>Simple Ecommerce Store</h1>

        <div class="banner">
            Summer Sale: 20% off selected items!
        </div>

        <h2>Available Products</h2>
        {product_html}
    </body>
    </html>
    """

@app.route("/product/<int:product_id>")
def product_detail(product_id):
    selected_product = None

    for product in products:
        if product["id"] == product_id:
            selected_product = product
            break

    if selected_product is None:
        abort(404)

    if selected_product["stock"] > 0:
        inventory_status = "Available"
    else:
        inventory_status = "Out of stock"

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{selected_product["name"]}</title>
        {page_style()}
    </head>
    <body>
        <h1>{selected_product["name"]}</h1>

        <div class="detail">
            <p><strong>Price:</strong> {selected_product["price"]}</p>
            <p><strong>Stock Quantity:</strong> {selected_product["stock"]}</p>
            <p><strong>Inventory Status:</strong> {inventory_status}</p>
            <p><strong>Description:</strong> {selected_product["description"]}</p>
        </div>

        <p><a href="/">Back to Product List</a></p>
    </body>
    </html>
    """

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000, debug=True)
