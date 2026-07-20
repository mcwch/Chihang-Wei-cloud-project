# Cloudflare Order Confirmation Worker

This Worker receives order information from the Flask ecommerce application and returns a confirmation message.

## Request

POST JSON fields:

- order_id
- customer_name

Example:

```json
{
  "order_id": 42,
  "customer_name": "Michael"
}
```

## Response

```json
{
  "message": "Cloudflare confirmed order #42 for Michael."
}
```
