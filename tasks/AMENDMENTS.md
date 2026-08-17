# AMENDMENTS — deviations from the original 14-day plan

This file records every substantive change made to `tasks/day-*.md` during the build, with
timestamp and rationale. The original day docs are edited **in place**; this file is the
human-readable changelog so the thesis and reviewers can trace what was changed and why.

All times IST.

---

## 2026-08-17 — Python runs inside shared Docker image, not host venv (Day 3)

**What changed**
- Built a shared Docker image `k8-ai-ops:dev` (python:3.11-slim base) at
  `ops/docker/Dockerfile` holding the Python dependencies for the project
  (Days 3, 4, 5, 7, 9, 12). All Python scripts are run via
  `docker run --rm -v ${PWD}:/code -w /code k8-ai-ops:dev ...` instead of a host
  virtual environment.
- `ops/docker/requirements.txt` is pinned to Day-3 deps only
  (prometheus-api-client 0.5.5, requests 2.32.3, locust 2.31.1, pandas 2.2.3,
  numpy 1.26.4). Future days append their own deps as those components come online.

**Why**
Locust 2.44 + gevent on **Python 3.12 Windows** raises `RecursionError` from the
SSL monkey-patch (`ssl._ssl._sslocert_verify`), so the host's preinstalled Python
runtime cannot run Locust. Python 3.11 (slim Debian) inside Docker sidesteps this
entirely and gives a consistent Linux runtime for the rest of the project
(Faust and Kopf officially target 3.10/3.11). One image (~615 MB) is reused by
every later Python service day, so the cost is paid once.

**Side effect**
First-run image build takes ~3-5 min; subsequent script runs reuse the cached
image. Containerised scripts reach host port-forwards via `host.docker.internal`
(the `PROMETHEUS_URL` and `LOCUST_HOST` defaults baked into the code use it).

---

## 2026-08-17 — Locust endpoint fix: /echo -> /api/echo, 2xx accepted (Day 3)

**What changed**
- `locustfile.py` posts to `/api/echo` (not `/echo`).
- Failure check accepts any 2xx (not `== 200`).

**Why**
podinfo's `/echo` is a **WebSocket** endpoint — plain HTTP POSTs are rejected
with 4xx. The HTTP echo API is `/api/echo`, which returns **202 Accepted**
(not 200) with the posted JSON echoed in the body. The first baseline run flagged
100 % of POSTs as failures (314/314) until this was fixed. After the fix: 285
requests, **0 failures**.

**Side effect**
The baseline error-rate metric (`rate(http_requests_total{status=~"5.."}[1m])`)
stayed at 0.0 throughout both runs — the original 4xx failures were correctly
excluded from the 5xx error-rate signal. The metrics pipeline was already sound;
only the Locust request definition was wrong.

---

## 2026-08-16 — Slim monitoring stack (Day 2)

**What changed**
- Used `prometheus-community/kube-prometheus-stack` chart (v88.3.0) with a slim
  `ops/manifests/monitoring-values.yaml` that:
  - Disables **Alertmanager** (we feed an AI pipeline, not human alerts -> ~150 MB saved).
  - Sets memory/CPU limits sized for the 3.6 GB Docker Desktop WSL2 VM.
  - Sets Prometheus retention to 2h, no PVC (emptyDir).
  - Sets Grafana admin password to `admin` (explicit, known).
  - Disables the chart's default alerting/recording Rule groups (less CPU churn).
- Added `ops/manifests/podinfo-service-monitor.yaml` (a `ServiceMonitor` CRD with
  the `release: kube-prometheus-stack` label so Prometheus Operator picks it up)
  that scrapes podinfo's `/metrics` every 15s.

**Why**
- Alertmanager is dead weight for this project (no humans to alert).
- Default chart resources are sized for real clusters and would OOM our VM.
- podinfo's Service needs a `ServiceMonitor` (not legacy annotation scraping)
  because the Prometheus Operator only honors ServiceMonitors/PodMonitors.

**Grafana first-boot needed two fixes** (took iteration during Day 2):
1. **Liveness probe was too aggressive** for Grafana 13.1.3, which spends ~3-4 min
   on FIRST boot installing its "Grafana Apps" resource manager (alerting, playlists,
   advisor, etc.) before HTTP binds port 3000. Default chart probe
   (`initialDelaySeconds=60, failureThreshold=10`) killed the container at ~160s.
   Fix: bumped `grafana.livenessProbe.initialDelaySeconds` to 300 and
   `failureThreshold` to 30 (~8 min total tolerance).
2. **128 Mi memory limit was too tight** for the same init phase - the Go runtime's
   `GOMEMLIMIT` was bound to the pod limit, and the first-run heap spike was OOMKilled
   (exit 137). Fix: bumped Grafana `resources.limits.memory` to 256 Mi (request 128 Mi).

After both fixes Grafana came up `3/3 Running, 0 restarts`. Subsequent boots are much
faster (migrations cached), so the probe headroom has plenty of margin.

**Known Down targets (expected, not a problem)**
Four control-plane scrape targets in the Prometheus `/targets` page report `DOWN`:
- `https://172.18.0.2:10257/metrics` (kube-controller-manager)
- `http://172.18.0.2:2381/metrics` (etcd)
- `http://172.18.0.2:10249/metrics` (kube-proxy)
- `https://172.18.0.2:10259/metrics` (kube-scheduler)

Root cause: kind runs these components with `--bind-address=127.0.0.1`, so they are
only reachable from inside the kind node container, not from the pod network.
**No impact on the AI pipeline**: the metrics we actually need are scraped from
cAdvisor (`container_cpu_usage_seconds_total`), kube-state-metrics
(`kube_deployment_status_replicas_available`), node-exporter, and podinfo's own
`/metrics` - all of which are `UP`.

---

## 2026-08-16 — Workload swap: Sock Shop -> podinfo (Day 1)

**What changed**
- Replaced Weaveworks **Sock Shop** with **stefanprodan/podinfo v6.14.1** as the workload that
  the operator auto-scales and auto-heals.
- Namespace changed from `sock-shop` to `podinfo`.
- Edited in place: `README.md` (root), `tasks/README.md`, `tasks/day-01`,
  `tasks/day-02`, `tasks/day-03`, `tasks/day-06`, `tasks/day-13`.
  (`ops/manifests/sock-shop-*.yaml` deleted; new `ops/manifests/podinfo.yaml` added).

**Why**
1. **RAM ceiling.** Docker Desktop's WSL2 VM is capped at ~3.6 GB on this host. The slim
   5-service Sock Shop subset (front-end + catalogue + catalogue-db + carts + carts-db) was
   already using ~1.1 GB on Day 1 with thin headroom for Prometheus + Kafka (Days 2 & 4).
   podinfo runs at ~30 MB image / ~30 MB RAM for 2 replicas — frees ~1 GB of VM RAM.
2. **Broken UI.** The slim Sock Shop subset renders a **white page** because the front-end
   (Node.js) ships product data as client-side JSON and its hydration depends on services we
   had dropped (user/session/queue-master), so the page errors out instead of painting.
3. **Catalogue-db image dead-ends on this kernel.** The
   `weaveworksdemos/catalogue-db:0.3.0` image (mysql:5.7 from 2016) gets VM-OOMKilled at
   `mysqld --verbose --help` inside the kind node on this WSL2 cgroup-v1 kernel. We worked
   around it once via a modern `mysql:8.0` + extracted seed, but the whole stack is fragile.
4. **Better fit for the thesis.** podinfo is a 6k-star, Apache-2.0, **actively-maintained**
   Go microservice used by CNCF Flux and Flagger for autoscaling and progressive-delivery
   e2e tests and workshops. Citing it is more credible than citing an abandoned 2017 demo.
5. **Built-in fault injection.** podinfo's `POST /fault_injection/enable` makes a single
   replica return HTTP 500 on application endpoints while keeping probes healthy — a clean
   error-rate spike for the anomaly detector (Day 8) and a RAM-light alternative to
   LitmusChaos for the Day 13 auto-heal demo.

**Thesis framing**
*"We evaluate the operator against podinfo, a CNCF-adopted Go microservice benchmark
designed for Kubernetes autoscaling and progressive-delivery workshops (Flux, Flagger)."*

**Impact on later days**
- Day 3 Locust profile changes from browse/cart/orders to hitting `/`, `/api/info`, and `/echo`.
- Day 6 load scenarios unchanged (Baseline / Spike / Steady-high / Idle) but against podinfo.
- Day 13 chaos: now offers two equivalent fault paths (LitmusChaos pod-delete OR podinfo
  built-in fault injection). Either or both can be demonstrated.
- Day 14 evaluation: no change (same HPA-vs-AI-operator comparison, same SLOs).

---

## 2026-08-16 — kind node image pinned to v1.30.0 (Day 1)

**What changed**
`ops/kind/kind-cluster.yaml` pins `kindest/node:v1.30.0` instead of the kind default.

**Why**
The kind default (`kindest/node:v1.36.1`) kubelet **refuses to run on cgroup v1**:
```
kubelet: "kubelet is configured to not run on a host using cgroup v1"
```
The Docker Desktop WSL2 kernel boots in **cgroup v1** (hybrid mode), so the v1.36 kubelet
crash-loops, the API server never comes up, and `kind create cluster` fails during
`wait-control-plane`. v1.30.0 still accepts cgroup v1 and also matches the user's kubectl
client version (`v1.30.0`) — a clean compatibility win.

**Side effect**
[Long-term fix] If the host ever moves to cgroup v2 (newer WSL2 kernel via
`wsl --update`), we can unpin to use the kind default again.

---

## 2026-08-16 — Single-node kind cluster (not 3 nodes)

**What changed**
The cluster runs one control-plane node only (instead of the original 1 control-plane +
2 workers the spec called for). All workloads (podinfo + monitoring + Kafka + Python services)
schedule on that single node.

**Why**
Docker Desktop's WSL2 VM is capped at ~3.6 GB RAM; a 3-node kind cluster failed during
bootstrapping immediately (API server timed out waiting for resources). A single node
schedules everything because kind does not apply a `NoSchedule` taint to control-plane nodes
by default.

**Side effect**
No multi-node scheduling realism in the demo. Acceptable: this project studies scaling/healing
behaviour, not bin-packing. If we ever need it, adding a worker node is one line in
`kind-cluster.yaml`.

---