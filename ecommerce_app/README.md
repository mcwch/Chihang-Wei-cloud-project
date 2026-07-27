# Simple Ecommerce Flask Application

A full-stack ecommerce application built with Flask and MySQL. The project combines product and inventory management, session-based shopping, checkout and order processing, optional serverless order confirmation, multi-instance load balancing, administrator access control, application monitoring, and security audit logging.

## Key Features

### Storefront

- Dynamic product catalog backed by MySQL
- Product detail and inventory views
- Responsive navigation for desktop and mobile devices
- Product visual placeholders for catalog and detail views
- Session-based shopping cart
- Quantity updates, item removal, and cart clearing
- Stock-aware cart limits
- Simulated checkout with customer information validation
- Persistent orders and order items
- Automatic inventory reduction after successful checkout

### Order Management

- Administrator login and logout
- Protected order-management routes
- Order statistics grouped by status
- Filtering by Pending, Processing, Shipped, Completed, or Cancelled
- Detailed customer and order-item views
- Order-status updates
- Consistent responsive layouts across customer and administrator pages

### Reliability and Cloud Features

- Optional Cloudflare Worker integration for order confirmations
- Multiple named Flask application instances
- Reverse-proxy load balancer
- Round-robin request routing
- Background health checks
- Automatic removal and recovery of unhealthy instances
- Connection failover to another healthy backend
- Dynamic backend configuration through `targets.json`

### Monitoring and Security

- Database-aware `/health` endpoint
- Per-instance request and response-time metrics
- HTTP 403, 404, and 500 counters
- Failed administrator login tracking
- Application uptime reporting
- Security audit log for authentication, access, and order changes
- Environment-based secrets and database credentials
- Session-protected administrative routes

## Architecture

```text
Client Browser
      |
      v
Load Balancer :8000
      |
      +---------------------+
      |                     |
      v                     v
Flask Instance 1 :5000   Flask Instance 2 :5001
      |                     |
      +----------+----------+
                 |
                 v
             MySQL Database

Order Confirmation
      |
      v
Optional Cloudflare Worker
```

The load balancer checks each backend through `/health` every five seconds and forwards requests only to healthy instances. Requests are distributed with round-robin selection. If a connection fails before a backend responds, another healthy instance is attempted.

## Technology Stack

- **Backend:** Python, Flask
- **Database:** MySQL, Flask-SQLAlchemy, PyMySQL
- **Frontend:** Jinja2, HTML, CSS
- **Serverless:** Cloudflare Workers
- **Load Balancing:** Custom Flask reverse proxy
- **Configuration:** python-dotenv
- **Testing:** pytest
- **Containerization:** Docker

## Project Structure

```text
ecommerce_app/
├── app.py
├── config.py
├── models.py
├── seed.py
├── serverless.py
├── run_instance.py
├── load_balancer.py
├── targets.json
├── requirements.txt
├── Dockerfile
├── .env.example
├── cloudflare_worker/
│   ├── worker.js
│   └── README.md
├── static/
│   └── style.css
├── templates/
│   ├── index.html
│   ├── product_detail.html
│   ├── cart.html
│   ├── checkout.html
│   ├── order_success.html
│   ├── admin_login.html
│   ├── orders.html
│   ├── order_detail.html
│   ├── admin_monitor.html
│   ├── admin_logs.html
│   └── load_balancer_status.html
└── tests/
```

## Configuration

Copy `.env.example` to `.env` and replace the placeholder values.

```text
SECRET_KEY=replace-with-a-random-secret-key
ADMIN_PASSWORD=replace-with-a-private-admin-password
DB_HOST=localhost
DB_PORT=3306
DB_NAME=ecommerce_app
DB_USER=ecommerce_user
DB_PASSWORD=replace-with-your-database-password
DB_TEST_NAME=ecommerce_app_test
SERVERLESS_FUNCTION_URL=
```

### Important Settings

| Variable | Purpose |
|---|---|
| `SECRET_KEY` | Protects Flask sessions |
| `ADMIN_PASSWORD` | Grants access to protected administration pages |
| `DB_HOST` | MySQL host |
| `DB_PORT` | MySQL port |
| `DB_NAME` | Main application database |
| `DB_TEST_NAME` | Test database |
| `DB_USER` | MySQL user |
| `DB_PASSWORD` | MySQL password |
| `SERVERLESS_FUNCTION_URL` | Optional Cloudflare Worker endpoint |

All application instances behind the load balancer should use the same `SECRET_KEY` and `ADMIN_PASSWORD`.

The real `.env` file is excluded from Git and should never be committed.

## Local Setup

### 1. Create a virtual environment

```powershell
python -m venv .venv
```

### 2. Activate it

```powershell
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 4. Configure MySQL

Create the application and test databases, then update `.env` with credentials that can access both databases.

```text
ecommerce_app
ecommerce_app_test
```

The application uses the `Product`, `Order`, and `OrderItem` models defined in `models.py`.

### 5. Configure private settings

Create `.env` from `.env.example` and set at least:

```text
SECRET_KEY=your-private-session-secret
ADMIN_PASSWORD=your-private-admin-password
```

## Running the Application

### Standalone Mode

```powershell
.\.venv\Scripts\python.exe .\app.py
```

Open:

```text
http://127.0.0.1:3000
```

### Multi-Instance Mode

Open separate PowerShell terminals in the `ecommerce_app` directory.

Instance 1:

```powershell
.\.venv\Scripts\python.exe .\run_instance.py --name "Instance 1" --port 5000
```

Instance 2:

```powershell
.\.venv\Scripts\python.exe .\run_instance.py --name "Instance 2" --port 5001
```

Load balancer:

```powershell
.\.venv\Scripts\python.exe .\load_balancer.py
```

Open the application through:

```text
http://127.0.0.1:8000
```

Load-balancer status:

```text
http://127.0.0.1:8000/load-balancer-status
```

### Adding Another Instance

Start another backend:

```powershell
.\.venv\Scripts\python.exe .\run_instance.py --name "Instance 3" --port 5002
```

Then add it to `targets.json`:

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
    },
    {
      "name": "Instance 3",
      "url": "http://127.0.0.1:5002"
    }
  ]
}
```

The load balancer reloads the target configuration during health checks.

## Administrator Pages

```text
/admin/login
/orders
/admin/monitor
/admin/logs
```

The order list, order details, status updates, monitoring dashboard, and audit log require an authenticated administrator session.

## Health and Monitoring

### Health Endpoint

```text
/health
```

A healthy response contains:

```json
{
  "status": "healthy",
  "database": "connected",
  "instance": "Instance 1",
  "total_orders": 6
}
```

If the database check fails, the endpoint returns HTTP `503`.

### Monitoring Dashboard

The dashboard reports:

- Application instance name
- Database connection status
- Application uptime
- Total requests
- Average response time
- HTTP error counts
- Failed administrator logins
- Total orders
- Orders grouped by status

### Audit Log

The in-memory audit log stores the latest 100 events, including:

- Successful logins
- Failed logins
- Logout events
- Unauthorized access attempts
- Order-status changes

Each application instance keeps its own monitoring data and audit log.

## Serverless Integration

The optional Cloudflare Worker accepts a POST request containing:

```json
{
  "order_id": 42,
  "customer_name": "Michael"
}
```

It returns:

```json
{
  "message": "Cloudflare confirmed order #42 for Michael."
}
```

Set `SERVERLESS_FUNCTION_URL` to the deployed Worker URL to enable this integration. When the URL is missing or the function is unavailable, the application falls back to a local confirmation message.

## Testing

Run the complete automated test suite:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

The latest verified local run completed successfully:

```text
154 passed in 4.87s
```

The test suite covers:

- Configuration and database access
- Product and order models
- Seed data
- Product routes
- Product visual placeholders
- Responsive navigation and shared UI consistency
- Cart management
- Checkout and inventory updates
- Serverless requests and headers
- Cloudflare Worker behavior
- Named application instances
- Health checks
- Load-balancer routing and failover
- Administrator authentication
- Order-management access control
- Monitoring metrics
- Security audit logging

Detailed verification results are available in the [Testing and Reliability Report](docs/testing-report.md).

### Verified Multi-Instance Reliability

The multi-instance configuration was also verified through a live local test:

- Instance 1 ran on port `5000`
- Instance 2 ran on port `5001`
- The load balancer ran on port `8000`
- Six consecutive requests alternated between Instance 1 and Instance 2
- After Instance 1 stopped, four consecutive requests were served by Instance 2 with HTTP 200 responses
- The load balancer logged `event=became_unhealthy backend=Instance 1`
- After Instance 1 restarted, the load balancer logged `event=recovered backend=Instance 1`
- Subsequent requests alternated between both instances again

This verification demonstrates health-check-based traffic removal, continued availability through a healthy backend, automatic recovery detection, and restoration of round-robin routing.

## Docker

Build the image:

```powershell
docker build -t ecommerce-flask-app .
```

Run the container:

```powershell
docker run --env-file .env -p 3000:3000 ecommerce-flask-app
```

The container starts the standalone Flask application on port `3000`.

## Current Limitations

- Checkout is simulated and does not process real payments.
- Monitoring metrics and audit events are stored in memory.
- Monitoring and audit data reset when an instance restarts.
- Metrics and logs are not shared between application instances.
- The built-in Flask server and custom load balancer are intended for development and demonstration rather than production deployment.
- Database migrations and a production WSGI configuration are not included.
- Local URLs are accessible only while the related services are running.

## Repository

https://github.com/mcwch/Chihang-Wei-cloud-project
