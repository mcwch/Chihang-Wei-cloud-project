# Cloudflare FaaS Migration Design

## Goal

Replace the DigitalOcean order-confirmation function with a Cloudflare Worker while keeping the application behavior unchanged.

## Architecture

Flask will send the same order_id and customer_name JSON fields. The Worker will return a top-level message field.

## Application Changes

- Replace DIGITALOCEAN_FUNCTION_URL with SERVERLESS_FUNCTION_URL.
- Keep serverless.py responsible for HTTP communication.
- Preserve the existing local fallback.
- Do not modify the database or order-management features.

## Testing

- Test the generic configuration.
- Test the Cloudflare response.
- Test the local fallback.
- Run the complete pytest suite.

## Success Criteria

- Checkout continues saving orders.
- The success page displays the Cloudflare confirmation.
- Existing features remain unchanged.
- All tests pass.
