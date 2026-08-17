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

Run (inside the shared Docker image; see Execution notes below):

```bash
docker run --rm -v ${PWD}:/code -w /code k8-ai-ops:dev src/metrics/metrics_client.py
```

Expected result: printed metrics that match the values in Grafana.

## Execution notes (2026-08-17)

### What was actually done

- Built a shared Docker image `k8-ai-ops:dev` (Python 3.11-slim base) to run all
  project Python scripts (see `ops/docker/Dockerfile`). Host Python 3.12 + Locust
  2.44 hits a gevent `RecursionError` on Windows; containerising on Python 3.11
  sidesteps it and gives a consistent Linux runtime for the rest of the project
  (Faust/Kopf officially target 3.10/3.11). One image, ~615 MB, reused by every
  later Python service day. Full rationale in `tasks/AMENDMENTS.md`.
- Wrote `src/metrics/metrics_client.py` — `PodinfoMetricsClient` class + CLI. Six
  PromQL queries are locked in a `QUERIES` dict so every downstream consumer
  (Faust processor, River-ML models, decision engine) agrees on metric
  definitions.
- Wrote `locustfile.py` — `PodinfoUser` with three weighted tasks: `GET /` (5),
  `GET /api/info` (3), `POST /api/echo` (2). Wait time 1-3 s between requests.
- Wrote `src/metrics/capture_baseline.py` — orchestrator that spawns Locust as a
  subprocess and concurrently samples Prometheus every 10 s into
  `data/baseline_metrics.csv`. Locust's end-of-run stats are written to
  `logs/locust_baseline_stats.csv`.

### Baseline run results (10 users, 1/s spawn, 300 s, sample every 10 s)

**Locust — 1,475 requests, 0 failures:**

| Endpoint        | Reqs | Fail | Median (ms) | Avg (ms) | p99 (ms) | RPS   |
|-----------------|------|------|-------------|----------|----------|-------|
| GET /           | 739  | 0    | 7           | 12.8     | 140      | 2.27  |
| GET /api/info   | 451  | 0    | 7           | 13.3     | 160      | 1.39  |
| POST /api/echo  | 285  | 0    | 7           | 12.6     | 67       | 0.88  |
| Aggregated      | 1475 | 0    | 7           | 12.9     | 150      | 4.54  |

**Prometheus baseline (32 samples, ~5 min):**

- CPU: ~0.008-0.026 cores (steady-state ~0.01)
- Memory working set: ~104-110 MiB (stable, no leak)
- Request rate: ramps 0.7 -> ~5.2/s as Locust spawns, holds ~5/s at steady state
- Error rate (5xx): 0.0 throughout
- Replicas: spec 2, available 2 — no scaling noise contaminates the baseline

This CSV is the "healthy baseline" the River-ML models (Days 7-8) train against.

### Reproduction commands (host has the port-forwards, container does the work)

```bash
# 1. Start port-forwards on the host (two terminals, leave running):
kubectl -n monitoring port-forward svc/kube-prometheus-stack-prometheus 9090:9090
kubectl -n podinfo port-forward svc/podinfo 8070:9898

# 2. Smoke-test the metrics client (prints one snapshot):
docker run --rm -v ${PWD}:/code -w /code k8-ai-ops:dev src/metrics/metrics_client.py

# 3. Full baseline capture (~5.5 min):
docker run --rm -v ${PWD}:/code -w /code k8-ai-ops:dev \
    src/metrics/capture_baseline.py --duration 300 --users 10 --spawn 1 --interval 10
```

`PROMETHEUS_URL` (default `http://host.docker.internal:9090`) and `LOCUST_HOST`
(default `http://host.docker.internal:8070`) can be overridden via env vars when
running on a host Python instead of inside the container.
