export default {
  async fetch(request) {
    if (request.method !== "POST") {
      return Response.json(
        { error: "Method not allowed" },
        { status: 405 },
      );
    }

    let body;

    try {
      body = await request.json();
    } catch {
      return Response.json(
        { error: "Invalid JSON" },
        { status: 400 },
      );
    }

    const orderId =
      body.order_id ?? "unknown";
    const customerName =
      body.customer_name ?? "Customer";

    return Response.json({
      message:
        `Cloudflare confirmed order #${orderId} ` +
        `for ${customerName}.`,
    });
  },
};
