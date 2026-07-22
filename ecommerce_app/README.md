# Simple Ecommerce Flask App

A simple Flask ecommerce application with a product listing and inventory information.

## Features

* Product listing page
* Product prices
* Inventory stock quantities
* Summer sale banner

## Run Locally

```bash
source venv/bin/activate
python3 app.py
```

Open the application using Codio's Box URL SSL preview.

## Load Balancing and Dynamic Scaling

This application includes a Flask reverse-proxy load balancer that distributes traffic across multiple application instances.

### Architecture

- Load balancer: `http://127.0.0.1:8000`
- Instance 1: `http://127.0.0.1:5000`
- Instance 2: `http://127.0.0.1:5001`
- Optional Instance 3: `http://127.0.0.1:5002`
- Backend configuration: `targets.json`
- Status dashboard: `http://127.0.0.1:8000/load-balancer-status`

The load balancer uses round-robin routing across healthy instances. It checks each instance every five seconds through its `/health` endpoint.

### Install Dependencies

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### Run the Application Instances

Open separate PowerShell terminals in the `ecommerce_app` directory.

Instance 1:

```powershell
.\.venv\Scripts\python.exe .\run_instance.py --name "Instance 1" --port 5000
```

Instance 2:

```powershell
.\.venv\Scripts\python.exe .\run_instance.py --name "Instance 2" --port 5001
```

Start the load balancer:

```powershell
.\.venv\Scripts\python.exe .\load_balancer.py
```

Access the application through:

```text
http://127.0.0.1:8000
```

### Dynamic Scaling

A third instance can be started without restarting the load balancer:

```powershell
.\.venv\Scripts\python.exe .\run_instance.py --name "Instance 3" --port 5002
```

Add it to `targets.json`:

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

The load balancer reloads this configuration during health checks and automatically adds the new healthy instance to the round-robin rotation.

### Health Monitoring and Failover

The status dashboard displays:

- Backend instance names and URLs
- Healthy or unhealthy status
- Last health-check time
- Connection and configuration errors

When an instance becomes unavailable, it is automatically removed from normal request routing. When it recovers, it automatically rejoins the rotation.

If a connection fails while forwarding a request, the load balancer tries another healthy instance. It does not retry after receiving an HTTP response, which prevents completed POST requests from being repeated.

### Run Tests

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

The automated tests cover application health checks, instance identity, dynamic target configuration, round-robin routing, proxy behavior, status reporting, and connection failover.
