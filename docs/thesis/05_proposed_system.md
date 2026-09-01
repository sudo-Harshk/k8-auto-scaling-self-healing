# Chapter 5 — Proposed System

## 5.1 Locked thesis sentence

> *"Naive ML-based Kubernetes controllers are unsafe under burst load. SHIELD-AI combines online ML (River) with a formally-verified safety shield (TLA+) to retain ML adaptability while provably satisfying safety invariants that bare controllers violate."*

Every component below traces back to this sentence.

## 5.2 Architecture overview

```
                +-----------------+      +-----------------+
   workload ---->|  Prometheus     | ---> |  Kafka topic    |
   (podinfo,     |  (9090)         |      |  k8s-metrics    |
    workload-v2) +-----------------+      +--------+--------+
                                                   |
                                                   v
                                          +--------+--------+
                                          |  Faust          |
                                          |  30-s windows   |
                                          |  (asyncio)      |
                                          +--------+--------+
                                                   |
                                                   v
                                          +--------+--------+
                                          |  Kafka topic    |
                                          |  k8s-features   |
                                          +--------+--------+
                                                   |
                                                   v
                                          +--------+--------+
                                          |  Decision       |
                                          |  Engine         |
                                          |  (River ML)     |
                                          |  + online learn |
                                          +--------+--------+
                                                   |
                                                   v
                                          +--------+--------+
                                          |  Safety Shield  |
                                          |  (TLA+ verified)|
                                          |  + diagnostics  |
                                          +--------+--------+
                                                   |
                                                   v
                                          +--------+--------+
                                          |  Kafka topic    |
                                          |  k8s-decisions  |
                                          +--------+--------+
                                                   |
                                                   v
                                          +--------+--------+
                                          |  Operator       |
                                          |  (K8s actuator) |
                                          |  - re-validate  |
                                          |  - apply        |
                                          +--------+--------+
                                                   |
                                                   v
                                          workload Deployment
                                          (scale or heal)
```

## 5.3 Components

### 5.3.1 Metrics client (`src/metrics/metrics_client.py`)

Polls Prometheus every 10 s for eight metrics and pulls Kubernetes deployment state:

- `cpu_percent` (Prometheus: `rate(container_cpu_usage_seconds_total[1m]) * 100`)
- `memory_percent` (Prometheus: `container_memory_working_set_bytes / limit`)
- `request_rate_per_s` (Prometheus: `rate(http_requests_total[1m])`)
- `p95_latency_ms` (Prometheus: `histogram_quantile(0.95, …)`)
- `error_rate_per_s` (Prometheus: `rate(http_requests_total{status=~"5.."}[1m])`)
- `current_replicas`, `available_replicas`, `target_replicas` (kube-state-metrics)

Published as JSON to Kafka topic `k8s-metrics`.

### 5.3.2 Stream processor (`src/streaming/stream_processor.py`)

Faust worker consumes `k8s-metrics`, accumulates into 30-second windows, and emits the windowed aggregate to Kafka topic `k8s-features`. Each Faust window produces one record with `*_avg` suffixed field names (e.g., `cpu_percent_avg`).

### 5.3.3 Decision engine (`src/decision/decision_engine.py`)

Combines:
- **Replica predictor** (River HoeffdingAdaptiveTreeRegressor wrapped in a StandardScaler pipeline) — predicts `target_replicas` from the 8-feature vector.
- **Anomaly detector** (River HalfSpaceTrees with `window_size=10`) — scores the same vector for anomaly likelihood.

**Decision rule (load-first ordering — P1 fix):**

1. If `predicted_replicas != current_replicas` → `scale`  *(load is dominant)*
2. Else if `anomaly_score > 2 × threshold` → `heal`
3. Else → `noop`

The pre-fix ordering checked `heal` first; under burst load this caused heal actions to shadow scale actions and the operator got stuck at 2 replicas (Day-15 motivating failure). The load-first ordering ensures that scale decisions fire whenever the predictor disagrees with the current state.

**Online learn loop (P1 fix):**

After every `noop` decision the engine calls `engine.learn(features, current_replicas)`. This is the missing feedback loop that caused the Day-15 frozen-model bug. Replica learns `(features, target_replicas)` via `River.compose.Pipeline.learn_one`; anomaly learns `features` (a noop means the window was a normal pattern).

**Decision explanation:**

Each decision includes a leave-one-out perturbation-based explanation (top 2 features by predicted-replica change) — see `Decision.explanation` in `src/decision/decision_engine.py`. Used in the viva when asked "why did the controller scale here?".

### 5.3.4 Safety Shield (`src/safety/safety_shield.py`)

Python implementation of the TLA+-verified invariants:

- `SafetyMinReplicas` — clamp `target_replicas >= min_replicas` (default 1)
- `SafetyMaxReplicas` — clamp `target_replicas <= max_replicas` (default 10)
- `max_scale_step` — shrink `|new - old| <= max_scale_step` (default 2)
- `heal_no_scale` — heal preserves replicas
- `bounded_rate` — cooldown (60 s) between actions

Returns `Decision` (allowed, possibly clamped) or `RejectedDecision`. Emits a per-call diagnostic tuple `(action, target_before, target_after, status)` to `logs/safety_audit.log`.

### 5.3.5 Operator (`src/kopf_operator/actuator.py`)

Consumes Kafka topic `k8s-decisions`, re-validates with `SafetyShield` (defense in depth), and applies via the official `kubernetes` client:

- `scale` → patch `Deployment.spec.replicas`
- `heal` → delete a pod (preferring `target_pod` from features, else highest-restart pod)
- `noop` → log only

Per AMENDMENTS 2026-08-23, the operator is implemented as a Kafka consumer, *not* a Kopf CRD handler. Rationale: simpler test surface; one less framework to learn; one less moving part in the formal model.

### 5.3.6 Audit logs

Every component produces a JSON line:

- `logs/metrics.log` — raw Prometheus snapshots
- `logs/features.log` — Faust 30-s windowed aggregates
- `logs/decisions.log` — Decision Engine output (ML-only path)
- `logs/safety_audit.log` — Safety Shield input/output/modifications
- `logs/operator_actions.log` — Operator applied actions

These logs are the empirical record for the thesis evaluation (§7).

## 5.4 Formal specification

### 5.4.1 Single-shield spec (`specs/SafetyShield.tla`)

The basic safety layer is specified in TLA+. PlusCal algorithm with eight variables and eight actions. Five state invariants and one liveness property verified by TLC on every reachable state:

```
TypeOK
SafetyMinReplicas       — replicas >= 1
SafetyMaxReplicas       — replicas <= MAX_REPLICAS (10)
SafetyScalingStep       — |delta| <= 2 on every Apply step
SafetyHealNoScale       — heal preserves replicas
SafetyBoundedRate       — cooldown elapsed OR no action pending

LivenessEventuallyScaleUp — sustained demand eventually triggers Apply
```

TLC run (Day 10 + Day 15 update): ~30 K distinct states explored, 0 errors found, <60 s runtime.

### 5.4.2 ML+Shield composition spec (`specs/ML_Composition.tla`)

This is the central paper claim. Unlike `SafetyShield.tla` (which assumes the predictor stays within bounded steps), this spec models the ML oracle as a thin non-deterministic abstraction that can emit ANY integer target replica count, including out-of-bounds and over-large-step outputs.

The spec runs TWO parallel paths:

- **SHIELD path (production)** — applies `shield_clamp(ML_output)` to cluster
- **ML_Only path (the bug)** — applies ML output directly with no shield

TLC checks:
1. **All six shield invariants hold on every reachable state of the joint spec** — the shield path is provably safe.
2. **The ML_Only path CAN violate** `MlSafetyMaxReplicas` — proven by the TLC-generated 3-step counterexample (propose target=11, apply directly, replicas=11). This proves the shield is necessary, not redundant.

The composition theorem: *the safety of the closed-loop system reduces to the safety of the shield, regardless of ML oracle behavior.*

## 5.5 Why this design

### 5.5.1 Kafka as the bus

**Why Kafka, not in-memory?** Kafka gives us durable buffering — if the decision engine crashes, no metrics are lost. It also gives us a replayable audit trail (every decision is on a Kafka topic). Cost: latency (~10 ms per hop). Trade-off accepted.

### 5.5.2 River Hoeffding Adaptive Tree Regressor

**Why not a neural net?** A neural net would require GPU, minibatch infrastructure, and a longer training horizon to converge — none of which are available on a single-node kind cluster. A Hoeffding tree is one-pass, O(memory), and explainable (leave-one-out perturbation works cleanly).

**Why not RL (PPO on replica count)?** RL would require a reward-shaped simulation environment and is out of M.Tech scope. River's HTR is the simplest model that satisfies multi-signal fusion + online learning + explainability.

### 5.5.3 TLA+ for safety

**Why not unit tests?** Unit tests can verify that the code passes test cases; they cannot verify that the code is correct for every possible input. TLA+ exhaustively explores every reachable state — that is the difference between "tested" and "verified".

**Why PlusCal?** PlusCal's algorithmic syntax is easier to read than raw TLA+. The translation to TLA+ is mechanical and TLC accepts both.

### 5.5.4 Kafka actuator, not Kopf CRD handler

**Why Kafka consumer, not Kopf?** Per AMENDMENTS 2026-08-23, the operator is a Kafka consumer:
- Simpler test surface (one process to test, not two).
- No Kopf lifecycle to manage (no requeue, no watcher, no CRD).
- Decouples the operator from the cluster's CRD registry (works against any K8s endpoint).
- Easier to formally model: the operator's input is a Kafka topic; the formal spec doesn't need to model CRD reconciliation.
