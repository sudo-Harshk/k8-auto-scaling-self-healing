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
