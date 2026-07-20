import json
from urllib import request


def get_order_confirmation(
    function_url,
    order_id,
    customer_name,
):
    payload = json.dumps(
        {
            "order_id": order_id,
            "customer_name": customer_name,
        }
    ).encode("utf-8")

    http_request = request.Request(
        function_url,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "EcommerceApp/1.0",
        },
        method="POST",
    )

    with request.urlopen(
        http_request,
        timeout=5,
    ) as response:
        response_data = json.loads(
            response.read().decode("utf-8")
        )

    return response_data["message"]
