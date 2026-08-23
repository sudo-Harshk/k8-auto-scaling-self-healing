# Chapter 6 — Implementation

> **Status:** Scaffolding. Filled after Day 14.

This chapter walks through the 16-day build, with one section per day. Each section links to the relevant code, manifests, and runnable verification command.

## 6.1 Day 1 — Cluster & Workload Deployment

- kind cluster with `kindest/node:v1.30.0` pinned (cgroup v1/v2 compat)
- podinfo (stefanprodan/podinfo v6.14.1) chosen over Sock Shop (lower memory footprint, CNCF benchmark, built-in `/fault_injection/enable`)
- Single-node kind cluster (Docker Desktop RAM cap)
- See `tasks/day-01-cluster-and-workload.md` + `ops/manifests/podinfo.yaml`

## 6.2 Day 2 — Monitoring Stack

- Helm chart `prometheus-community/kube-prometheus-stack` with slim values
- Alertmanager disabled (~150 MB saved)
- Grafana probe headroom tuning (initialDelaySeconds=300)
- See `tasks/day-02-monitoring-stack.md` + `ops/manifests/monitoring-values.yaml`

## 6.3 Day 3 — Metrics Client & Locust Baseline

- Shared Docker image `k8-ai-ops:dev` (`python:3.11-slim` base)
- `src/metrics/metrics_client.py` with 6 PromQL queries
- `locustfile.py` with three weighted tasks
- Azure VM baseline: 1,478 reqs, 0 failures, 4.94 RPS
- See `tasks/day-03-metrics-api-and-load-test.md`

## 6.4 Day 4 — Kafka Pipeline

- Official `apache/kafka:3.9.1` (Bitnami moved paid)
- Two listeners: PLAINTEXT (in-cluster) and EXTERNAL (host-side port-forward)
- `src/kafka/producer.py` + `consumer.py`
- See `tasks/day-04-kafka-pipeline.md` + `ops/manifests/kafka.yaml`

## 6.5 Day 5 — Faust Stream Processor

- `faust-streaming==0.11.3` (mode.utils.typing fix from 0.10.11)
- `aiokafka==0.10.0` pinned (MetadataRequest_v1 protocol)
- 30-s manual `floor(epoch/30)` windows
- See `tasks/day-05-faust-stream-processor.md`

## 6.6 Day 6 — Feature Engineering

- Two-script architecture: `feature_builder.py` (per-scenario JSONL) + `build_dataset.py` (merge + label + target_replicas)
- Podinfo pod limits (100m CPU / 128 Mi memory per replica)
- p95 latency added (Day 6 — additive to Day 3's 6 fields)
- 55-row dataset across 4 scenarios (baseline / spike / steady_high / idle)
- See `tasks/day-06-feature-engineering.md`

## 6.7 Day 7 — Replica Prediction Model

- River HoeffdingAdaptiveTreeRegressor + StandardScaler pipeline
- Final MAE 0.2364 (target < 1.0)
- Smoke test: spike→4, baseline→1, idle→1, overload→6
- See `tasks/day-07-replica-prediction-model.md`

## 6.8 Day 8 — Anomaly Detection

- River HalfSpaceTrees with `window_size=10` (not default 250)
- 33 normal rows for training, 22 abnormal for testing
- 6.7× mean separation, 55% detection rate
- See `tasks/day-08-anomaly-detection-model.md`

## 6.9 Day 9 — Decision Engine

- Combined Day-7 predictor + Day-8 detector
- Single rule (scale if predictor says, else heal if anomaly, else noop)
- Perturbation-based feature importance (not SHAP — River incompatibility)
- See `tasks/day-09-decision-engine-and-shap.md`

## 6.10 Day 10 — TLA+ Safety Shield Specification

- 217-line TLA+ spec, PlusCal algorithm with 7 variables and 8 actions
- 5 invariants verified by TLC: 264,330 distinct states, 0 errors, 3 s
- See `tasks/day-10-tla-safety-shield-spec.md` + `specs/SafetyShield.tla`

## 6.11 Day 11 — Safety Shield Implementation

- Python `SafetyShield` class loading `specs/safety_policy.yaml`
- 16 unit tests, all 5 invariants anti-drift-tested (intentional violations caught)
- See `tasks/day-11-safety-shield-implementation.md`

## 6.12 Day 12 — Kubernetes Operator (Kafka actuator)

- `src/kopf_operator/actuator.py`: Kafka consumer + `kubernetes` client
- Re-validates every decision with SafetyShield before applying
- Smoke test verified scale 2→4, heal (pod deleted), noop
- See `tasks/day-12-kopf-operator.md`

## 6.13 Day 13 — End-to-End Integration & Chaos Testing

- Full pipeline ran live on VM: producer → Kafka → Faust → engine → Shield → operator → cluster
- Auto-scaling verified: AI scaled 2→1 under low traffic
- Auto-healing verified: fault injected → anomaly_score=0.69 → operator deleted faulty pod
- 3 critical bugs found and fixed (operator sort-key, decision engine field-name mismatch, heal-saturation on baseline)
- 9 evidence files in `data/evaluation/`
- See `tasks/day-13-end-to-end-integration-and-chaos.md`

## 6.14 Day 14 — Evaluation, Comparison Harness & Thesis Draft

[To be filled after Day 14 execution.]

## 6.15 Day 15 — Statistical Rigor, Liveness & Reproducibility

[To be filled after Day 15 execution.]

## 6.16 Day 16 — p95 Variability Rework, IEEE Paper Draft & Dashboard

[To be filled after Day 16 execution.]

## 6.17 Code structure summary

(Filled after Day 14 — total LOC, modules, dependencies, etc.)