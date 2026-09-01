# Chapter 2 — Introduction

## 2.1 Problem statement

Kubernetes operators automate scaling, healing, and configuration management for workloads running in a cluster. The de-facto standard is the Horizontal Pod Autoscaler (HPA), which scales based on a single CPU-utilization threshold. This works for predictable, steady-state workloads but has well-documented limitations:

- **Slow reaction to load changes.** HPA's default sync period is 15 s and the stabilization window is 5 min. Spikes that resolve in 30 s are missed entirely.
- **Single signal.** CPU usage correlates poorly with end-user load for many modern workloads (asynchronous, batch, ML inference). HPA does not use request rate, latency, or error rate.
- **No formal safety guarantee.** HPA can scale to 0 replicas (if misconfigured), exceed node capacity, or oscillate. There is no machine-checked invariant.
- **No anomaly detection.** HPA does not detect or heal faulty pods. Self-healing requires a separate mechanism (Kubernetes `restartPolicy`, `PodDisruptionBudget`, or external chaos engineering).

KEDA addresses the signal problem by introducing event-driven triggers (e.g., Prometheus query, Kafka lag, cron), but it inherits HPA's lack of formal safety guarantees and adds no anomaly detection.

This thesis asks: *can an operator scale and heal using multiple learned signals (request rate, CPU%, error rate, latency, replica history) while remaining provably safe under a machine-checked invariant set?*

## 2.2 The motivating failure: Day-15

Before settling on the SHIELD-AI architecture we built and evaluated a "Day-15 prototype" that combined the same Prometheus → Kafka → Faust pipeline with a River-ML decision engine *without* a formal safety shield. The N=3 evaluation exposed a hard failure mode:

| Operator | Scaling lag (s) | Total scale actions | Heal actions | Error rate (%) | Replicas (start → end) |
|----------|----------------|---------------------|--------------|----------------|-------------------------|
| HPA      | 15 (poll interval) | 8 (2→10→6) | 0 | 0.0 | 2 → 6 |
| KEDA     | 5  (poll interval) | 6 (2→10→2) | 0 | 0.0 | 2 → 2 |
| **AI (Day-15, no shield)** | 90 (cooldown + 30-s window) | 0 | 1 | **69.2** | **2 → 2** |

The ML-only operator was **worse than HPA under burst load**: it emitted a single heal action and never scaled. Two distinct algorithmic defects caused the regression:

1. **Ordering bug.** The decision engine checked `heal` before `scale`. Under burst load the anomaly detector flagged high p95 latency as anomalous and the engine emitted `heal` actions (no replica change) instead of `scale`.
2. **No online learning.** Despite the architecture claiming online learning since Day 7, the live Kafka consumer never called `ReplicaPredictor.learn_one()`. The production model was frozen at whatever the Day-7 offline training produced and never adapted to live traffic.

These two defects combined to make the ML-only controller *worse* than HPA under burst load. SHIELD-AI closes both: a load-first decision order (see §5.3) and a real online-learning loop that updates both models from every stable window. But fixing the algorithm is not enough: even a correct ML controller can propose unsafe actions in edge cases. Hence the Safety Shield (§5.4).

## 2.3 Contributions

1. **End-to-end pipeline.** Prometheus → Kafka → Faust (30-s windows) → River-ML decision engine → TLA+-verified Safety Shield → Kubernetes actuator, with full audit logs at every stage.
2. **Online learning.** Replica predictor and anomaly detector continue to learn during operator runtime; the system is not frozen on a static dataset. The P1 algorithm fix closes the Day-15 frozen-model gap.
3. **Hybrid ML + formal safety.** A TLA+-verified Safety Shield gates every ML proposal before it reaches Kubernetes, model-checked exhaustively over 273,702 reachable states.
4. **ML+Shield composition theorem.** A second TLA+ spec (`specs/ML_Composition.tla`) models the ML oracle as a thin non-deterministic abstraction and proves the shield is *necessary* (an ML-only counterexample demonstrates the violation) and *sufficient* (the shield path satisfies all invariants on every reachable state).
5. **Quantitative comparison.** HPA / KEDA / AI evaluated head-to-head on three load scenarios with paired statistical tests; FIRM-style threshold controller added as a learned-model baseline.
6. **Reproducibility.** 53 unit tests, 9 Python services, 12-step `make demo` golden run captured in `docs/GOLDEN_RUN.md`.

## 2.4 Thesis outline

- **Chapter 3 — Literature Survey:** HPA, KEDA, online ML (River), TLA+ in distributed systems, safe-RL shielding.
- **Chapter 4 — Existing System:** HPA and KEDA architectures, with concrete limitations demonstrated by the Day-15 evaluation.
- **Chapter 5 — Proposed System:** The SHIELD-AI architecture; the ML oracle; the Safety Shield.
- **Chapter 6 — Implementation:** Per-day build log (Days 1–18).
- **Chapter 7 — Results:** Comparison table, FIRM-style baseline, per-scenario shield clamping, threats to validity.
- **Chapter 8 — Discussion:** Why River HTR (vs. neural net / RL), why TLA+ (vs. unit tests), why shield before operator.
- **Chapter 9 — Conclusion:** Summary, limitations, future work (production deployment, multi-tenant fairness).

## 2.5 Non-goals (to keep scope honest)

- No production deployment or multi-tenant fairness policy.
- No Kubernetes operator framework rewrite (Kopf is explicitly out per AMENDMENTS 2026-08-23).
- No LLM-based policy generation.
- No multi-cluster federation.
- No service mesh integration.

These omissions are documented as threats-to-validity (§8), not bugs.
