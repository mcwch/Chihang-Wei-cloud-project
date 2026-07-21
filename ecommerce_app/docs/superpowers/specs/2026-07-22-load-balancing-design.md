# Load Balancing and Dynamic Scaling Design

**Date:** 2026-07-22  
**Project:** Chihang-Wei Cloud Project  
**Scope:** Course Project Part 8 – Simulating Load Balancer and Scaling with Flask Applications

## 1. Objective

Upgrade the existing Flask ecommerce application from a single-instance application into a locally simulated multi-instance architecture that demonstrates load balancing, dynamic scale-out, health monitoring, failover, and recovery.

The existing standalone application must remain available through:

```powershell
python app.py
```

This continues to run the ecommerce application on port 3000.

The new multi-instance architecture will run multiple instances of the same ecommerce application behind a round-robin reverse-proxy load balancer.

## 2. Existing Project Baseline

The current application already includes:

- A Flask application factory through `create_app()`
- Product catalog and product detail routes
- Session-based shopping cart
- Checkout and order creation
- Order list, order detail, and order success pages
- Shared MySQL configuration
- A shared Flask `SECRET_KEY`
- Cloudflare Worker integration for order confirmation
- 37 passing automated tests

The load-balancing work will extend this design without duplicating the ecommerce application or replacing the existing startup method.

## 3. Architecture

### Existing standalone mode

```text
python app.py
└── Ecommerce Application → Port 3000
```

### Multi-instance mode

```text
Browser
   ↓
Round-Robin Load Balancer → Port 8000
   ├── Instance 1 → Port 5000
   ├── Instance 2 → Port 5001
   └── Instance 3 → Port 5002
              ↓
        Shared MySQL Database
              ↓
        Cloudflare Worker
```

All instances use the same application code, database, templates, static files, session secret, and Cloudflare Worker configuration.

## 4. Planned Files

```text
ecommerce_app/
├── app.py
├── run_instance.py
├── load_balancer.py
├── targets.json
├── config.py
├── models.py
├── templates/
│   ├── base.html
│   └── load_balancer_status.html
├── static/
├── tests/
│   └── test_load_balancer.py
└── docs/
    └── superpowers/
        └── specs/
            └── 2026-07-22-load-balancing-design.md
```

## 5. Application Instance Startup

A single reusable script, `run_instance.py`, will start any ecommerce application instance.

Example commands:

```powershell
python run_instance.py --name "Instance 1" --port 5000
python run_instance.py --name "Instance 2" --port 5001
python run_instance.py --name "Instance 3" --port 5002
```

The script will:

1. Parse the instance name and port.
2. Call the existing `create_app()` factory.
3. Set `INSTANCE_NAME` in the Flask configuration.
4. Start the application on the requested port.

No ecommerce business logic will be copied into the startup script.

## 6. Backend Instance Features

The existing Flask application will receive three small additions.

### 6.1 Health endpoint

Each instance will expose:

```text
GET /health
```

Example response:

```json
{
  "status": "healthy",
  "instance": "Instance 1"
}
```

### 6.2 Instance response header

Every backend response will include:

```text
X-App-Instance: Instance 1
```

This allows command-line verification with tools such as `curl`.

### 6.3 Instance name in the page footer

The shared base template will display:

```text
Served by Instance 1
```

The standalone application running on port 3000 will display a default name such as:

```text
Served by Standalone Instance
```

## 7. Target Configuration

The load balancer will read backend targets from `targets.json`.

Initial configuration:

```json
{
  "targets": [
    {
      "name": "Instance 1",
      "url": "http://127.0.0.1:5000"
    },
    {
      "name": "Instance 2",
      "url": "http://127.0.0.1:5001"
    }
  ]
}
```

To simulate scale-out, Instance 3 will be started and then added to the file:

```json
{
  "name": "Instance 3",
  "url": "http://127.0.0.1:5002"
}
```

The load balancer will detect the configuration change without restarting.

If `targets.json` becomes temporarily invalid, the load balancer will continue using the last successfully loaded target list. The status page will show the configuration error until the file is corrected.

## 8. Background Health Monitoring

The load balancer will run a background health-check thread.

Every five seconds, it will request:

```text
GET <target-url>/health
```

The load balancer will maintain:

- Configured targets
- Healthy targets
- Unhealthy targets
- Last health-check time
- Last error for each target
- Current configuration error, if any

Shared health state will be protected by a thread lock.

A failed target will be removed from normal request distribution. When it becomes healthy again, it will automatically rejoin the pool.

## 9. Round-Robin Reverse Proxy

The load balancer will run on port 8000 and choose only from healthy targets.

Before scale-out:

```text
Request 1 → Instance 1
Request 2 → Instance 2
Request 3 → Instance 1
Request 4 → Instance 2
```

After Instance 3 joins:

```text
Request 1 → Instance 1
Request 2 → Instance 2
Request 3 → Instance 3
Request 4 → Instance 1
```

The proxy must support the entire ecommerce application, not only the home page.

It will forward:

- URL paths
- Query parameters
- GET, POST, and other supported methods
- Request body and form data
- Browser cookies
- Relevant request headers

It will return:

- Backend response content
- Backend HTTP status code
- Relevant response headers
- `Set-Cookie`
- `X-App-Instance`

The following application routes must continue working through port 8000:

```text
/
/product/<id>
/cart
/checkout
/orders
/orders/<id>
/order-success/<id>
/static/style.css
```

## 10. Retry and Failure Behavior

### Configuration failure

If `targets.json` cannot be parsed, use the last valid target list and expose the error on the status page.

### Unhealthy backend

Do not send new requests to an instance currently marked unhealthy.

### Connection failure during proxying

If a connection fails before a backend response is received, the load balancer may try the next healthy target.

### Backend HTTP error response

If the backend returns an HTTP error response, return that response to the client. Do not automatically replay the request against another backend.

This is important for checkout and order creation because blindly retrying a POST request could create duplicate orders.

### No healthy instances

Return:

```text
503 Service Unavailable
```

### All proxy attempts fail

Return:

```text
502 Bad Gateway
```

## 11. Load Balancer Status Page

The load balancer will provide:

```text
GET /load-balancer-status
```

This route is handled directly by the load balancer and is never forwarded.

The page will display:

- Target name
- Target URL
- Healthy or Unhealthy status
- Most recent error
- Last health-check time
- Configuration error
- Number of configured targets
- Number of healthy targets

This page will provide visual evidence for dynamic scale-out, failure detection, and recovery.

## 12. Session and Shared Data

All instances will use the same:

- MySQL database
- `SECRET_KEY`
- Product data
- Order data
- Cloudflare Worker configuration

The load balancer must preserve cookies and `Set-Cookie` headers so the Flask session-based shopping cart continues working when consecutive requests are handled by different instances.

## 13. Dependency Update

The project will add the `requests` library to `requirements.txt` because the load balancer and health monitor need to communicate with backend Flask instances.

## 14. Testing Plan

All existing tests must continue to pass.

New tests will cover:

- Health endpoint response
- Instance name response header
- Instance name availability in templates
- Valid target configuration loading
- Invalid configuration fallback
- Dynamic target configuration updates
- Round-robin request distribution
- Unhealthy target exclusion
- Recovered target rejoining
- No healthy targets returning 503
- Proxy failure returning 502
- Query parameter forwarding
- POST body forwarding
- Cookie forwarding
- `Set-Cookie` forwarding
- Status page target display

Minimum completion condition:

```text
Existing 37 tests pass
+
All new load-balancing tests pass
```

## 15. Demonstration Procedure

1. Start Instance 1 on port 5000.
2. Start Instance 2 on port 5001.
3. Start the load balancer on port 8000.
4. Open the ecommerce application through port 8000.
5. Refresh repeatedly and observe Instance 1 and Instance 2 alternating.
6. Open `/load-balancer-status` and confirm that both instances are healthy.
7. Start Instance 3 on port 5002.
8. Add Instance 3 to `targets.json`.
9. Do not restart the load balancer.
10. Wait for the background health check to detect Instance 3.
11. Refresh the application and observe all three instances participating.
12. Stop Instance 2.
13. Confirm that the status page marks Instance 2 unhealthy.
14. Confirm that the ecommerce application continues through Instances 1 and 3.
15. Restart Instance 2.
16. Confirm that it becomes healthy and rejoins automatically.
17. Verify that cart, checkout, order, and Cloudflare confirmation features still work through port 8000.

## 16. Submission Evidence

The final Course Project Part 8 submission will include:

- GitHub repository URL
- Source code for the instances and load balancer
- Updated README instructions
- Terminal screenshots showing:
  - Instance 1
  - Instance 2
  - Instance 3
  - Load balancer
- Browser screenshot of the ecommerce application through port 8000
- Browser screenshot of `/load-balancer-status`
- Evidence of two-instance round robin
- Evidence of three-instance dynamic scale-out
- Evidence of unhealthy target removal and recovery
- Final automated test result

## 17. Scope Boundary

This project implements real application-level load balancing among multiple local Flask processes.

It simulates infrastructure-level auto-scaling because:

- All instances run on the same local machine.
- Instance 3 is started manually.
- The target registry is a local JSON file.
- Scaling is not triggered by CPU or cloud metrics.

The design intentionally does not include AWS Auto Scaling, Kubernetes, container orchestration, or multi-host deployment because those are outside the assignment requirements.
