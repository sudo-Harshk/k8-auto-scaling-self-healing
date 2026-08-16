# Day 3 — Metrics API & Baseline Load Test

## Task
Query Prometheus metrics programmatically and establish a baseline load profile for podinfo.

## Aim
Build the data source that the AI model and streaming pipeline will consume.

## Requirements

- Python 3.10+
- `prometheus-api-client`
- `requests`
- Locust
- Running Prometheus and podinfo from Days 1–2

## Steps

1. **Set up a Python project folder**
   - Create a folder (e.g., `src/metrics`).
   - Create a virtual environment and install dependencies.

2. **Write `metrics_client.py`**
   - Connect to Prometheus at `http://localhost:9090`.
   - Fetch metrics for the `podinfo` deployment:
     - CPU usage: `rate(container_cpu_usage_seconds_total{namespace="podinfo"}[1m])`
     - Memory usage: `container_memory_usage_bytes{namespace="podinfo"}`
     - Request rate: `rate(http_requests_total{namespace="podinfo"}[1m])` (podinfo exposes `/metrics`)
     - Error rate: `rate(http_requests_total{namespace="podinfo",status=~"5.."}[1m])`
     - Pod count: `kube_deployment_status_replicas_available{namespace="podinfo",deployment="podinfo"}`
   - Return metrics as a structured dictionary or DataFrame.

3. **Test the metrics client**
   - Run the script and print current metrics.
   - Verify values match what you see in Grafana.

4. **Write a basic Locust load test**
   - Create `locustfile.py` with tasks that hit the podinfo home page (`/`), `/api/info`, and `/echo` (POST with a small JSON body). These endpoints are sufficient to drive CPU, request-rate, and error-rate signals for the ML models.
   - Start Locust with `locust -f locustfile.py --host http://localhost:8070`.

5. **Run a baseline load test**
   - Run for 5 minutes with 10 users and spawn rate 1.
   - Watch Grafana dashboards during the test.

6. **Save sample metrics**
   - Capture metrics every 10 seconds during the load test.
   - Save to `data/baseline_metrics.csv` or `data/baseline_metrics.json`.

## Outcome

- A reusable Python metrics client is working.
- Locust load test is configured and runs against podinfo.
- A baseline metrics dataset is saved for model training.

## Verification

Run:

```bash
python src/metrics/metrics_client.py
```

Expected result: printed metrics that match the values in Grafana.
