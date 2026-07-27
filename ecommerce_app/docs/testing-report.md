# NovaGear Testing and Reliability Report

## Overview

This report documents the final automated and manual verification performed for the NovaGear Flask ecommerce application. Testing focused on storefront behavior, administrator workflows, responsive interface consistency, monitoring, security controls, multi-instance routing, backend failure handling, and automatic recovery.

## Test Environment

The final verification was performed locally with:

- Python virtual environment
- Flask application
- MySQL database
- Flask-SQLAlchemy and PyMySQL
- Custom Flask reverse-proxy load balancer
- Two independently running application instances
- PowerShell for service and HTTP verification
- pytest for automated testing

The multi-instance environment used:

| Component | Address |
| --- | --- |
| Instance 1 | `http://127.0.0.1:5000` |
| Instance 2 | `http://127.0.0.1:5001` |
| Load Balancer | `http://127.0.0.1:8000` |

## Automated Test Results

The complete automated test suite was executed with:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Final result:

```text
154 passed in 4.87s
```

No automated tests failed.

## Automated Test Coverage

The test suite verifies:

- Configuration and environment handling
- Database access
- Product and order models
- Product seed data
- Product catalog and detail routes
- Product visual placeholders
- Responsive navigation
- Shared customer and administrator UI components
- Shopping-cart operations
- Quantity and inventory limits
- Checkout validation
- Order and order-item persistence
- Inventory reduction
- Serverless requests and headers
- Cloudflare Worker behavior
- Named application instances
- Instance identity headers
- Database-aware health checks
- Round-robin backend selection
- Load-balancer request forwarding
- Connection failover behavior
- Load-balancer status rendering
- Load-balancer event logging
- Administrator authentication
- Protected administrative routes
- Product-management operations
- Order filtering and status updates
- Monitoring metrics
- Persistent application logs
- Security audit logging

## User-Interface Verification

Customer and administrator pages were manually reviewed after the shared layout update.

The review confirmed:

- Consistent page spacing and card presentation
- Responsive desktop and mobile navigation
- Responsive product catalog and detail views
- Correct cart and checkout layouts
- Correct checkout navigation symbol
- Correct order-success confirmation symbol
- Responsive administrator forms and tables
- Readable monitoring and log pages
- No unintended full-page horizontal scrolling
- Continued operation of customer and administrator controls

## Multi-Instance Routing Verification

Both Flask application instances were started independently and connected to the same MySQL database.

Health responses confirmed that both instances were healthy and connected to the database.

Six consecutive requests sent through the load balancer were handled in this order:

```text
Instance 1
Instance 2
Instance 1
Instance 2
Instance 1
Instance 2
```

The `X-App-Instance` response header matched the instance reported in each response body. This confirmed that requests were being handled by separate backend processes through round-robin routing.

## Failure and Availability Verification

Instance 1 was stopped while Instance 2 and the load balancer remained active.

After the failure:

- Port `5000` was no longer listening
- Port `5001` remained available
- Port `8000` remained available
- Four consecutive requests returned HTTP 200
- All four requests were handled by Instance 2
- No tested request returned HTTP 502 or HTTP 503

The load-balancer log recorded:

```text
event=became_unhealthy backend=Instance 1
```

This confirmed that the background health monitor detected the unavailable backend and removed it from the healthy routing pool.

## Automatic Recovery Verification

Instance 1 was restarted without restarting the load balancer.

Its health endpoint again reported:

```text
instance: Instance 1
status: healthy
database: connected
```

The load-balancer log recorded:

```text
event=recovered backend=Instance 1
```

Four additional requests were handled in this order:

```text
Instance 2
Instance 1
Instance 2
Instance 1
```

This confirmed that the recovered instance was automatically returned to the healthy backend pool and resumed round-robin request processing.

## Connection Failover Scope

The automated test suite verifies that the load balancer attempts another healthy backend when a connection fails before a backend response is received.

The live manual test primarily verified health-check-based backend removal, continued availability through Instance 2, automatic recovery detection, and restoration of round-robin routing.

## Current Limitations

- The environment uses Flask development servers rather than production WSGI servers.
- The custom load balancer is intended for local development and demonstration.
- Checkout does not process real payments.
- Some monitoring metrics and audit events are stored in memory.
- Metrics are maintained separately by each application instance.
- The environment runs locally rather than on separate cloud virtual machines.
- Database migrations and production deployment automation are not included.

## Conclusion

The final verification found no automated test failures or browser-level regressions. NovaGear demonstrated ecommerce workflows, responsive customer and administrator interfaces, monitoring and security features, two-instance round-robin routing, health-check-driven failure handling, continued service through a healthy backend, and automatic restoration of a recovered instance.
