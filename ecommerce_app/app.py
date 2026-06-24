from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Simple Ecommerce Store</title>
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

            .product {
                background-color: white;
                padding: 15px;
                margin: 10px 0;
                border-radius: 5px;
            }
        </style>
    </head>
    <body>
        <h1>Simple Ecommerce Store</h1>

        <div class="banner">
            Summer Sale: 20% off selected items!
        </div>

        <h2>Available Products</h2>

        <div class="product">
            <strong>Wireless Headphones</strong><br>
            Price: $59.99<br>
            In Stock: 12
        </div>

        <div class="product">
            <strong>USB-C Charger</strong><br>
            Price: $19.99<br>
            In Stock: 25
        </div>

        <div class="product">
            <strong>Laptop Stand</strong><br>
            Price: $39.99<br>
            In Stock: 8
        </div>
    </body>
    </html>
    """

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000, debug=True)