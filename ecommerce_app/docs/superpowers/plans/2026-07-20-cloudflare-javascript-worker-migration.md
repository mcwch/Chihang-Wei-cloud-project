# Cloudflare JavaScript Worker Migration Plan

> **For agentic workers:** Execute this plan task-by-task using a test-first workflow.

**Goal:** Replace the DigitalOcean order-confirmation endpoint with a Cloudflare JavaScript Worker while preserving the existing checkout and order-management behavior.

**Architecture:** Flask continues to call `serverless.py` with the same JSON request and expects the same top-level `message` response. Only the configuration name and deployed endpoint change. The Worker is deployed from the Cloudflare dashboard and its source is also stored in this repository.

**Tech Stack:** Flask, pytest, JavaScript, Cloudflare Workers.

## Global Constraints

- Use `SERVERLESS_FUNCTION_URL`.
- Keep request fields `order_id` and `customer_name`.
- Keep response format `{"message": "..."}`.
- Preserve the local fallback.
- Do not change database models or order-management pages.
- Do not commit `.env`.

---

### Task 1: Rename the serverless configuration

**Files:**
- Create: `tests/test_config.py`
- Modify: `tests/test_routes.py`
- Modify: `config.py`
- Modify: `app.py`
- Modify: `.env.example`

1. Add a failing test that expects `Config.SERVERLESS_FUNCTION_URL` and rejects the old DigitalOcean-specific setting.
2. Replace `DIGITALOCEAN_FUNCTION_URL` with `SERVERLESS_FUNCTION_URL` in tests.
3. Run the affected tests and confirm failure.
4. Rename the setting in production files.
5. Run the affected tests and then the full suite.
6. Commit with `Use generic serverless function configuration`.

### Task 2: Add the Cloudflare Worker source

**Files:**
- Create: `cloudflare_worker/worker.js`
- Create: `cloudflare_worker/README.md`

The Worker source will:

```javascript
export default {
  async fetch(request) {
    if (request.method !== "POST") {
      return Response.json(
        { error: "Method not allowed" },
        { status: 405 }
      );
    }

    let body;

    try {
      body = await request.json();
    } catch {
      return Response.json(
        { error: "Invalid JSON" },
        { status: 400 }
      );
    }

    const orderId = body.order_id ?? "unknown";
    const customerName =
      body.customer_name ?? "Customer";

    return Response.json({
      message:
        `Cloudflare confirmed order #${orderId} ` +
        `for ${customerName}.`,
    });
  },
};
```

The README will document the expected request and response. Commit with `Add Cloudflare order confirmation worker`.

### Task 3: Deploy through the Cloudflare dashboard

1. Create a Worker named `ecommerce-order-confirmation`.
2. Replace the default source with `cloudflare_worker/worker.js`.
3. Deploy the Worker.
4. Copy the generated `workers.dev` URL.
5. Send a POST request containing order ID 42 and customer name Michael.
6. Confirm the response message is `Cloudflare confirmed order #42 for Michael.`

### Task 4: Connect Flask to Cloudflare

**Local-only file:**
- Modify: `.env`

1. Remove existing `DIGITALOCEAN_FUNCTION_URL` and `SERVERLESS_FUNCTION_URL` lines.
2. Add one `SERVERLESS_FUNCTION_URL=<workers.dev URL>` line.
3. Verify Flask loads the Worker URL.
4. Run the full pytest suite.
5. Start Flask and complete one checkout.
6. Confirm the success page displays the Cloudflare confirmation.

### Task 5: Final verification and integration

1. Confirm `.env` is ignored by Git.
2. Run the full pytest suite.
3. Review `git status` and recent commits.
4. Push `feature/cloudflare-faas-migration`.
5. Merge into `main` only after the real checkout succeeds.
6. Delete the DigitalOcean Function only after Cloudflare is verified.
