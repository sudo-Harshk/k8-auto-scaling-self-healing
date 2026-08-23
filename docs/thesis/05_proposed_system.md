# Chapter 5 — Proposed System

> **Status:** Scaffolding. Filled after Day 14.

## 5.1 Architecture overview

```
                +-----------------+      +-----------------+
   podinfo ---> |  Prometheus     | ---> |  Kafka          |
   (or v2       |  (9090)         |      |  topic:         |
   workload)    +-----------------+      |  k8s-metrics    |
                                         +--------+--------+
                                                  |
                                                  v
                                         +--------+--------+
                                         |  Faust          |
                                         |  30-s windows   |
                                         +--------+--------+
                                                  |
                                                  v
                                         +--------+--------+
                                         |  Kafka topic:   |
                                         |  k8s-features   |
                                         +--------+--------+
                                                  |
                                                  v
                                         +--------+--------+
                                         |  Decision       |
                                         |  Engine         |
                                         |  (River ML)     |
                                         +--------+--------+
                                                  |
                                                  v
                                         +--------+--------+
                                         |  Safety         |
                                         |  Shield         |
                                         |  (TLA+ verified)|
                                         +--------+--------+
                                                  |
                                                  v
                                         +--------+--------+
                                         |  Kafka topic:   |
                                         |  k8s-decisions  |
                                         +--------+--------+
                                                  |
                                                  v
                                         +--------+--------+
                                         |  Operator       |
                                         |  (Kubernetes    |
                                         |   actuator)     |
                                         +--------+--------+
                                                  |
                                                  v
                                         podinfo Deployment
                                         (scale or heal)
```

(Full diagram with labeled arrows in `docs/architecture.png` or `README.md` section.)

## 5.2 Components

### 5.2.1 Metrics client (`src/metrics/`)

Polls Prometheus every 10 s for seven metrics:
- `cpu_cores` (Prometheus: `rate(container_cpu_usage_seconds_total[1m])`)
- `memory_bytes` (Prometheus: `container_memory_working_set_bytes`)
- `request_rate_per_s` (Prometheus: `rate(http_requests_total[1m])`)
- `error_rate_per_s` (Prometheus: `rate(http_requests_total{status=~"5.."}[1m])`)
- `current_replicas`, `available_replicas` (kube-state-metrics)
- `p95_latency_ms` (Prometheus: `histogram_quantile(0.95, …)`)

Published as JSON to Kafka topic `k8s-metrics`.

### 5.2.2 Stream processor (`src/streaming/`)

Faust worker consumes `k8s-metrics`, accumulates into 30-second windows, and emits the windowed aggregate to Kafka topic `k8s-features`. Each Faust window produces one record with `*_avg` suffixed field names.

### 5.2.3 Decision engine (`src/decision/`)

Combines:
- **Replica predictor** (River HoeffdingAdaptiveTreeRegressor wrapped in a StandardScaler pipeline) — predicts target_replicas from the 8-feature vector.
- **Anomaly detector** (River HalfSpaceTrees with `window_size=10`) — scores the same vector for anomaly likelihood.

Decision rule (single, deterministic):
1. If `anomaly_score > 2 × threshold` → `heal`
2. Else if `predicted_replicas != current_replicas` → `scale`
3. Else → `noop`

Each decision includes a leave-one-out perturbation-based explanation (top 2 features by predicted-replica change).

### 5.2.4 Safety Shield (`src/safety/`)

Python implementation of the five TLA+-verified invariants:
- `SafetyMinReplicas` — clamp `target_replicas >= min_replicas`
- `SafetyMaxReplicas` — clamp `target_replicas <= max_replicas`
- `max_scale_step` — shrink `|new - old| <= max_scale_step`
- `heal_no_scale` — heal preserves replicas
- `bounded_rate` — cooldown (60 s) between actions

Returns `Decision` (allowed, possibly clamped) or `RejectedDecision`.

### 5.2.5 Operator (`src/kopf_operator/`)

Consumes Kafka topic `k8s-decisions`, re-validates with SafetyShield (defense in depth), and applies via the official `kubernetes` client:
- `scale` → patch Deployment.spec.replicas
- `heal` → delete a pod (preferring `target_pod` from features, else highest-restart pod)
- `noop` → log only

### 5.2.6 Audit logs

Every validation produces a JSON line:
- `logs/decisions.log` — Decision Engine output
- `logs/safety_audit.log` — Safety Shield input/output/modifications
- `logs/operator_actions.log` — Operator applied actions

## 5.3 Formal specification (`specs/SafetyShield.tla`)

The safety layer is specified in TLA+ (`specs/SafetyShield.tla`). PlusCal algorithm with seven variables and eight actions. Five state invariants verified by TLC on every reachable state:

```
TypeOK
SafetyMinReplicas
SafetyMaxReplicas
SafetyScalingStep
SafetyHealNoScale
SafetyBoundedRate
```

TLC run (Day 10): 264,330 distinct states explored, 0 errors found, 3 s runtime, fp-collision probability 3.0E-11.

## 5.4 Why this design

(Filled after Day 14 — arguments for why each design choice was made: Kafka as the bus vs in-memory, River for online learning, TLA+ for formal safety, Kafka actuator vs Kopf CRD, etc.)