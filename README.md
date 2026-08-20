# AI-Driven Kubernetes Operator for Unified Online Auto-Scaling and Auto-Healing

M.Tech project: a formally-safe autonomous Kubernetes controller that unifies AI-driven
auto-scaling and auto-healing behind a TLA+-verified Safety Shield.

## Pipeline

```
Prometheus -> Kafka producer -> Faust (30s windows) -> k8s-features
  -> Decision Engine (River-ML regressor + HalfSpaceTrees anomaly + SHAP)
  -> Safety Shield (TLA+ policy gate: approved / rejected / modified)
  -> k8s-decisions -> Kopf Operator -> patches Deployment.replicas / deletes pods
```

Three Kafka topics thread it together: `k8s-metrics` -> `k8s-features` -> `k8s-decisions`.

## Stack

- **Infra:** Azure VM, kind, Docker CE, Helm 3, kubectl
- **Benchmark:** stefanprodan/podinfo v6.14.1 (lightweight Go microservice, built-in Prometheus `/metrics` + `/fault_injection/enable`)
- **Streaming:** Kafka (apache/kafka:3.9.1 KRaft, no Zookeeper), Faust (faust-streaming 0.11.3)
- **Operator:** Kopf (Python) + kubernetes client
- **ML:** River-ML (online), SHAP
- **Safety:** TLA+ / PlusCal + TLC
- **Chaos:** LitmusChaos
- **Load:** Locust
- **Monitoring:** Prometheus / Grafana / kube-state-metrics

## Infrastructure

Canonical environment (Days 4-14): Azure `Standard_D4as_v5` (4 vCPU AMD EPYC x86-64,
16 GB RAM, 64 GB Standard SSD), Ubuntu 24.04 LTS, cgroup v2, Central India.
kind v1.30.0 single-node cluster; Python services run in the shared `k8-ai-ops:dev`
image. Access is SSH-key-only (port 22); Grafana/Prometheus are reached via
`ssh -L` tunnels. VM auto-shuts-down daily at 23:00 IST. The Windows laptop setup
(Days 1-3) remains as a demo fallback. See `tasks/AMENDMENTS.md` (2026-08-18).

Daily ops (~1 min bring-up after the VM starts):

```bash
ssh k8-vm                                   # Azure VM alias (laptop ~/.ssh/config)
docker start k8-ai-control-plane            # only if the kind node container stopped
kubectl -n monitoring port-forward svc/kube-prometheus-stack-prometheus 9090:9090 &
kubectl -n kafka port-forward svc/kafka 9094:9094 &
# Grafana on the laptop: ssh -L 3000:localhost:3000 k8-vm  with
#   kubectl -n monitoring port-forward svc/kube-prometheus-stack-grafana 3000:80 on the VM
```

## Layout

```
src/        Python services (metrics, streaming, features, models, decision, safety, operator)
ops/        Infrastructure (kind config, k8s manifests, shared docker image)
config/     Safety policy (derived from TLA+ spec)
specs/      TLA+ specification + TLC config
data/       Captured metrics (baselines committed as evidence; live runs gitignored)
logs/       Decision / audit logs (summary stats committed; raw run output gitignored)
tasks/      Day-by-day build plan (source of truth)
```

## Build plan

See `tasks/README.md` for the 14-day plan. Days 1-14 are implemented in order;
each day is committed and tagged.

## Status

- [x] Day 1 - Cluster & Workload Deployment
- [x] Day 2 - Monitoring Stack
- [x] Day 3 - Metrics API & Baseline Load Test
- [x] Day 4 - Kafka Streaming Pipeline
- [x] Day 5 - Faust Stream Processor
- [ ] Day 6 - Feature Engineering & Dataset
- [ ] Day 7 - Replica Prediction Model
- [ ] Day 8 - Anomaly Detection Model
- [ ] Day 9 - Decision Engine & SHAP Explainability
- [ ] Day 10 - TLA+ Safety Shield Specification
- [ ] Day 11 - Safety Shield Implementation
- [ ] Day 12 - Kubernetes Operator with Kopf
- [ ] Day 13 - End-to-End Integration & Chaos Testing
- [ ] Day 14 - Evaluation, Dashboards & Final Documentation