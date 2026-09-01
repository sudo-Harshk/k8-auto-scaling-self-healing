# SHIELD-AI — AI-Driven Kubernetes Operator for Safe Online Auto-Scaling and Auto-Healing

M.Tech project: a formally-safe autonomous Kubernetes controller that unifies AI-driven
auto-scaling and auto-healing behind a TLA+-verified Safety Shield.

## Thesis (locked)

> **Naive ML-based Kubernetes controllers are unsafe under burst load. SHIELD-AI combines
> online ML (River) with a formally-verified safety shield (TLA+) to retain ML
> adaptability while provably satisfying safety invariants that bare controllers violate.**

## Three contributions

1. **Hybrid ML + Formal Safety Controller** — a Kubernetes operator whose action space is
   the intersection of ML-driven decisions and a TLA+-verified invariant set.
2. **Empirically-validated failure mode of pure ML controllers** — Day-15 N=3 evidence
   showing AI without the shield gets stuck at 2 replicas with 100% error under burst load.
3. **Reproducible artifact** — N≥10 statistical comparison, containerized `make demo`,
   full TLA+ TLC trace, and a FIRM-style ML baseline.

See `tasks/THESIS.md` for the central thesis tracker, `docs/VIVA_GAUNTLET.md` for the
20-question viva prep, and `docs/GOLDEN_RUN.md` for the 12-step demo.

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
- **Operator:** Python (kafka-python consumer + kubernetes client; Kafka-driven actuator, NOT Kopf — see AMENDMENTS 2026-08-23)
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
docs/       Walkthroughs, thesis chapters, IEEE paper draft, demo script, PPT outline
scripts/    Reproducibility scripts (bootstrap, build, deploy, run, swap, run_comparison)
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
- [x] Day 6 - Feature Engineering & Dataset
- [x] Day 7 - Replica Prediction Model
- [x] Day 8 - Anomaly Detection Model
- [x] Day 9 - Decision Engine & SHAP Explainability
- [x] Day 10 - TLA+ Safety Shield Specification
- [x] Day 11 - Safety Shield Implementation
- [x] Day 12 - Kubernetes Operator (Kafka actuator)
- [x] Day 13 - End-to-End Integration & Chaos Testing
- [x] Day 14 - Evaluation, Dashboards & Final Documentation
- [x] Day 15 - Statistical Rigor, Liveness & Reproducibility
- [x] Day 16 - p95 Variability Rework, IEEE Paper Draft, Dashboard
- [x] Day 17 - Paper Strengthening for Viva Defense (Threat Model + Production Roadmap)
- [x] Day 18 - Close Research Gaps (workload-v2 AI pipeline + Day-13 E2E + N=3 v2 + 5 tests)

## Rescue plan (P0 → P5)

| Phase | Goal | Status |
|-------|------|--------|
| **P0** | Lock thesis sentence + paper skeleton + golden run outline | ✅ done |
| P1 | Fix autoscaling (real online learn, scale vs heal, retrain canonical) | pending |
| P2 | Stats-grade evaluation (FIRM baseline, N≥10, paired tests) | pending |
| P3 | Formal & artifact (TLA+ composition, containerized `make demo`) | pending |
| P4 | Paper & thesis write-up | pending |
| P5 | Strict viva gauntlet (20 questions) | pending |