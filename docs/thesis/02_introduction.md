# Chapter 2 — Introduction

> **Status:** Scaffolding. Filled after Day 14.

## 2.1 Problem statement

Kubernetes operators automate scaling, healing, and configuration management for workloads running in a cluster. The de-facto standard is the Horizontal Pod Autoscaler (HPA), which scales based on a single CPU-utilization threshold. This works for predictable, steady-state workloads but has well-documented limitations:

- **Slow reaction to load changes.** HPA's default sync period is 15 s and the stabilization window is 5 min. Spikes that resolve in 30 s are missed entirely.
- **Single signal.** CPU usage correlates poorly with end-user load for many modern workloads (asynchronous, batch, ML inference). HPA does not use request rate, latency, or error rate.
- **No formal safety guarantee.** HPA can scale to 0 replicas (if misconfigured), exceed node capacity, or oscillate. There is no machine-checked invariant.
- **No anomaly detection.** HPA does not detect or heal faulty pods. Self-healing requires a separate mechanism (Kubernetes `restartPolicy`, PodDisruptionBudget, or external chaos engineering).

KEDA addresses the signal problem by introducing event-driven triggers (e.g., Prometheus query, Kafka lag, cron), but it inherits HPA's lack of formal safety guarantees and adds no anomaly detection.

This project asks: *can an operator scale and heal using multiple learned signals (request rate, CPU%, error rate, latency, replica history), while remaining provably safe under a machine-checked invariant set?*

## 2.2 Contributions

1. **End-to-end pipeline.** Prometheus → Kafka → Faust (30-s windows) → River-ML decision engine → TLA+-verified Safety Shield → Kubernetes actuator, with full audit logs at every stage.
2. **Online learning.** Replica predictor and anomaly detector continue to learn during operator runtime; the system is not frozen on a static dataset.
3. **Formal safety verification.** All five safety invariants (`min_replicas`, `max_replicas`, `max_scale_step`, `heal_no_scale`, `bounded_rate`) verified by the TLC model checker on every reachable state.
4. **Quantitative comparison.** HPA / KEDA / AI evaluated head-to-head on three load scenarios with N=3 repetitions and statistical comparison.
5. **Reproducibility.** Bootstrap-from-scratch scripts and a single Dockerfile that captures every dependency.

## 2.3 Thesis outline

- **Chapter 3 — Literature Survey:** HPA, KEDA, online ML, TLA+ in distributed systems.
- **Chapter 4 — Existing System:** HPA and KEDA architectures, with concrete examples.
- **Chapter 5 — Proposed System:** The AI-driven operator architecture.
- **Chapter 6 — Implementation:** Per-day build log (Days 1–16).
- **Chapter 7 — Results:** Comparison table, ablation, p95 variability evidence.
- **Chapter 8 — Discussion:** Threats to validity, deviations from the original plan.
- **Chapter 9 — Conclusion:** Summary, limitations, future work.

## 2.4 Outline of remaining thesis chapters

[This section will be filled after Day 14 when all chapters exist.]