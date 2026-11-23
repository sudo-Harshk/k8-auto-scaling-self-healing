# Day 2 — Monitoring Stack

## Task
Install Prometheus, Grafana, kube-state-metrics, and Node exporter for cluster and application observability.

## Aim
Capture real-time cluster and application metrics that will feed the AI pipeline.

## Requirements

- Helm 3
- Access to the kind cluster from Day 1
- Prometheus community Helm repo

## Steps

1. **Add Prometheus community Helm repository**
   - Add repo and update it.

2. **Install kube-prometheus-stack**
   - Install into a `monitoring` namespace.
   - This bundle's slim config (per `ops/manifests/monitoring-values.yaml`) keeps Prometheus, Grafana, kube-state-metrics, and Node exporter. **Alertmanager is disabled** (we feed an AI pipeline, not human alerts -> saves ~150 MB RAM).

3. **Wait for all monitoring pods to be Ready**
   - Check pods in the `monitoring` namespace.

4. **Expose Grafana and Prometheus**
   - Use `kubectl port-forward` for Grafana (port 3000) and Prometheus (port 9090).

5. **Verify Prometheus targets**
   - Open Prometheus UI at `http://localhost:9090/targets`.
   - Confirm that Kubernetes API, nodes, kubelet, and service endpoints are up.

6. **Import Kubernetes dashboards in Grafana**
   - Log in to Grafana with `admin` / `admin` (set explicitly in our Helm values).
   - Import a Kubernetes cluster dashboard or use built-in dashboards.
   - Confirm podinfo pod metrics are visible.

## Outcome

- Prometheus is scraping cluster and pod metrics.
- Grafana dashboards display CPU, memory, and pod count.
- You can query Prometheus metrics manually from the UI.

## Verification Commands

```bash
helm list -n monitoring
kubectl get pods -n monitoring
kubectl port-forward -n monitoring svc/kube-prometheus-stack-prometheus 9090:9090
kubectl port-forward -n monitoring svc/kube-prometheus-stack-grafana 3000:80
```

Expected result: Prometheus `/targets` shows 14+ `UP` states (both podinfo
`9898/metrics` scrapes are UP, plus kubelet, cAdvisor, kube-state-metrics, node-exporter).
A few `DOWN` targets (etcd, kube-scheduler, kube-controller-manager, kube-proxy) are
expected on kind: those control-plane components bind to localhost inside the kind
node, so pods cannot reach them. They do not affect the AI pipeline. Grafana shows
live graphs.

---

## Execution Notes (2026-08-16)

### Stack
- Helm chart `prometheus-community/kube-prometheus-stack` v88.3.0 with slim
  values (`ops/manifests/monitoring-values.yaml`):
  - **Alertmanager disabled** — dead weight for an AI pipeline; saves ~150 MB RAM.
  - Prometheus retention **2h, no PVC** (emptyDir) — fits the 16 GiB VM.
  - Grafana admin password set to `admin` explicitly.
  - Default alerting/recording rule groups disabled (less CPU churn).
- `ops/manifests/podinfo-service-monitor.yaml` — a `ServiceMonitor` CRD
  with the `release: kube-prometheus-stack` label so the Prometheus Operator
  picks it up. Scrapes podinfo's `/metrics` every 15 s.

### Grafana first-boot fixes (took iteration)
1. **Liveness probe too aggressive** for Grafana 13.1.3 — first boot
   takes 3-4 min installing "Grafana Apps" before binding port 3000.
   Default chart probe (`initialDelaySeconds=60, failureThreshold=10`)
   killed the container at ~160 s. Fix: `initialDelaySeconds: 300`,
   `failureThreshold: 30` (~8 min tolerance).
2. **128 Mi memory limit too tight** for the same init phase — Go's
   `GOMEMLIMIT` is bound to the pod limit and the first-run heap spike
   was OOMKilled (exit 137). Fix: bumped Grafana memory limit to 256 Mi
   (request 128 Mi).
   After both fixes Grafana came up `3/3 Running, 0 restarts`. Subsequent
   boots are much faster (migrations cached).

### Known `DOWN` targets (expected, not a problem)
Four control-plane scrape targets in the Prometheus `/targets` page report
`DOWN`:
- `https://172.18.0.2:10257/metrics` (kube-controller-manager)
- `http://172.18.0.2:2381/metrics` (etcd)
- `http://172.18.0.2:10249/metrics` (kube-proxy)
- `https://172.18.0.2:10259/metrics` (kube-scheduler)

**Root cause:** kind runs these components with `--bind-address=127.0.0.1`,
so they are only reachable from inside the kind node container, not from
the pod network. **No impact on the AI pipeline:** the metrics we actually
need are scraped from cAdvisor, kube-state-metrics, node-exporter, and
podinfo's `/metrics` — all `UP`.

### Live state at audit (2026-08-21)
```
kube-prometheus-stack-grafana-8574f6565-9zsv7               3/3 Running
kube-prometheus-stack-kube-state-metrics-7766cf68b6-tx8v8   1/1 Running
kube-prometheus-stack-operator-67dbf99d79-5xvzs             1/1 Running
kube-prometheus-stack-prometheus-node-exporter-c7z8r        1/1 Running
```
All four core monitoring pods `Running` on the VM cluster.
