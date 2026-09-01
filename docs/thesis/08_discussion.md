# Chapter 8 — Discussion

## 8.1 Architecture choices revisited

### 8.1.1 Kafka vs in-memory bus

**Chosen:** Kafka (KRaft mode, durable, replayable). **Cost:** ~10 ms per hop latency, two extra processes to operate. **Benefit:** durability (no metrics lost if the engine crashes), audit trail (every decision is on a Kafka topic), replay capability for the offline evaluation harness (`scripts/replay_shield.py`).

The trade-off is justified: the thesis makes a safety claim, and a safety claim requires an auditable decision record. Without Kafka we could not reproduce the Day-15 evidence or run the offline replay.

### 8.1.2 River Hoeffding Adaptive Tree Regressor vs offline ML

**Chosen:** River HTR (online, single-pass, O(memory)). **Rejected:** scikit-learn Random Forest (offline; would require retraining on every concept drift), PyTorch neural net (GPU unavailable on a single-node kind cluster), RL (out of scope).

River's HTR is the simplest model that satisfies multi-signal fusion, online learning, and explainability (leave-one-out perturbation). The P1 fix demonstrates the cost of getting online learning wrong: a frozen model + heal-first ordering produced the worst result of the three controllers in the Day-15 evaluation.

### 8.1.3 TLA+ vs runtime assertions only

**Chosen:** TLA+ (exhaustive model checking by TLC). **Rejected:** unit tests alone (cannot cover every reachable state), property-based testing (better than unit tests but not exhaustive), runtime guards only (catches bugs but does not prove absence).

The shield's invariants are checked on every reachable state of the spec — not on a sample. This is the difference between "tested" and "verified". The composition spec `ML_Composition.tla` extends this guarantee to the closed-loop ML+Shield system.

### 8.1.4 Kafka actuator vs Custom Resource watches

**Chosen:** Kafka consumer + `kubernetes` client. **Rejected:** Kopf CRD handler.

Rationale (per AMENDMENTS 2026-08-23): simpler test surface (one process, no CRD lifecycle), no Kopf requeue logic to debug, decoupled from K8s CRD registry (works against any K8s endpoint), and easier to formally model — the operator's input is a Kafka topic; the formal spec doesn't need to model CRD reconciliation.

## 8.2 Deviations from the original 14-day plan

A full list lives in `tasks/AMENDMENTS.md`. Summary:

| Day | Original plan | Actual implementation | Reason |
|-----|---------------|----------------------|--------|
| 1  | Sock Shop workload | podinfo v6.14.1 | RAM ceiling; better CNCF fit; built-in fault injection |
| 3  | Host venv | Shared Docker image | Locust+gevent+3.12 incompatibility |
| 5  | Faust 0.10.x | Faust 0.11.3 | `mode.utils.typing` compat with 3.11 |
| 9  | SHAP library | Perturbation-based FI | SHAP's TreeExplainer doesn't support River |
| 10 | TLA+ Toolbox GUI | CLI (java + tla2tools.jar) on VM | Reproducibility; no GUI needed |
| 12 | Kopf operator | kafka-python + kubernetes client | Trigger is Kafka, not K8s resource watches |
| 13 | "Train on full pipeline from Day 1" | Three critical bugs found + fixed | Online mode never tested before |
| 14 | Single-run M.Tech evaluation | 3-day cycle (Days 14–16) with N=3 runs, liveness, p95 rework, IEEE paper | Closer to publication-ready |
| 15 | (new) | Liveness property + statistical rigor | Reviewer feedback from Day-14 dry run |
| 17 | (new) | P0+P1 lock-in, FIRM baseline, ML+Shield composition spec | Thesis must defend one claim; composition spec is strongest single artifact |

## 8.3 Bugs found during E2E (Day 13 retrospective)

Three bugs that were not caught earlier because:

1. **Operator sort-key tuple-negation** (`src/kopf_operator/actuator.py:139`) — only triggered when 2+ pods existed with different restart counts; smoke test had homogeneous pods.
2. **Decision engine field-name mismatch** — Faust emits `cpu_cores_avg`, decision engine looked for `cpu_percent`. Online mode never run before; offline mode passed because CSV column names matched.
3. **Heal-saturation on baseline traffic** — every 30-s window crossed the anomaly threshold. Runtime-only behavior.

This is a real lesson: **online modes of components must be tested online before E2E evaluation**, not just smoke-tested offline.

The P1 algorithm fix closed three additional bugs that emerged on Day 17:

4. **Decision-engine ordering (heal-first vs load-first)** — healed before scaling under burst load; the load-first ordering is now enforced.
5. **No-op learn loop missing** — `_run_online` never called `.learn_one()`; the Day-15 frozen-model bug. Fixed by adding `engine.learn()` after every noop.
6. **Parser bug in `build_dataset_v2.py`** — Locust's `Requests/s` field is a lifetime average, returning 0 at the start of a test; replaced with `Total Request Count` delta for per-second rate.

## 8.4 What we would do differently

1. **Build a workload generator early.** Day-16's p95 rework was forced by podinfo's triviality. A DB-backed workload from Day 1 would have saved the rework (workload-v2 was added on Day 17).
2. **Define evaluation metrics on Day 1.** We didn't capture "scaling lag" until Day 14. Adding Prometheus recording rules for evaluation metrics from Day 1 would have made Day 14 trivial.
3. **Test online modes online, smoke-test offline modes offline.** Day 9's offline test gave false confidence; Day 13's online test caught the field-name mismatch.
4. **Run Day 6's feature builder against the live Faust stream earlier.** The field-name mismatch would have been caught on Day 5, not Day 13.
5. **Write the TLA+ composition spec on Day 11.** The composition theorem is the strongest paper claim; we wrote it on Day 17 because we didn't realise we needed the ML-as-thin-abstraction framing until then. Earlier would have saved a week.

## 8.5 Open questions

- **Concept drift in production.** The online learn loop is in place; we have not yet measured how fast the replica predictor's MAE degrades over a multi-day run. A drift detector (e.g., ADWIN on the residual error) would be a natural extension.
- **Multi-tenant fairness.** The shield's invariants are per-Deployment. Cross-Deployment fairness (avoiding noisy-neighbour effects on the same node) is not modelled. A multi-tenant extension to the TLA+ spec would add `NodeAllocations` and a fairness invariant.
- **Cold start.** The replica predictor's first prediction (before any online learning) is unreliable. The shield's clamp protects the cluster from over-large cold-start steps, but does not protect against systematically wrong cold-start *direction* (e.g., predicting scale-down when the cluster is overloaded). A cold-start heuristic fallback is a natural extension.

## 8.6 Why this project is publishable

1. **Architecture novelty.** Hybrid ML+formal-safety controller for Kubernetes is not present in the literature as of 2026. HPA and KEDA are pure reactive controllers; FIRM is a static threshold controller; safe-RL shielding has been applied to robotics but not to K8s operators.
2. **Formal verification depth.** Two TLA+ specs (`SafetyShield.tla` and `ML_Composition.tla`) provide machine-checked correctness arguments at two levels of abstraction: the shield alone, and the ML+Shield composition. The composition theorem proves the shield is necessary and sufficient.
3. **Reproducibility.** 53 unit tests, 9 Python services, single-command bootstrap via `make demo`, TLA+ specs runnable on commodity hardware.
4. **Empirical evaluation.** Head-to-head comparison against HPA, KEDA, and FIRM on three workload scenarios. Day-15 evidence is honest about the failure mode of ML-only controllers and motivates the shield.
5. **Practical impact.** A live cluster demonstrator with workload-v2, end-to-end pipeline, audit logs, and a Kafka actuator that can be deployed against any K8s cluster (not just kind).
