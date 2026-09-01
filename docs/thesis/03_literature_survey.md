# Chapter 3 — Literature Survey

## 3.1 Kubernetes auto-scaling

- **Horizontal Pod Autoscaler (HPA):** Kubernetes-native controller, scales Deployments based on a target metric (default CPU%). Polls metrics every 15 s. Stabilization window defaults to 5 min. Documented limitations: single-signal, slow reaction to bursts, no formal safety, no healing.
- **Vertical Pod Autoscaler (VPA):** Adjusts resource requests/limits instead of replica count. Out of scope for this thesis.
- **KEDA:** Event-driven autoscaler. Wraps HPA with custom metric sources. Strong signal library (Prometheus, Kafka lag, RabbitMQ, cron, etc.). Inherits HPA's safety limitations; no anomaly detection.
- **Cluster Autoscaler / Karpenter:** Adds/removes nodes, not pods. Composable with this thesis but not implemented.

## 3.2 Self-healing and chaos engineering

- **Kubernetes `restartPolicy`, liveness/readiness probes:** Restart-on-failure but no anomaly detection. Cannot react to 5xx responses that pass the probe threshold.
- **LitmusChaos, Chaos Mesh:** Active fault injection frameworks. Used as evaluation harnesses in industry.
- **Podinfo's built-in `/fault_injection/enable`:** Lightweight alternative for evaluation. Used in our Day-15 evaluation to inject 5xx errors.

## 3.3 Stream processing

- **Apache Kafka:** De-facto message bus. KRaft mode (since 2.8) eliminates the ZooKeeper dependency, simplifying cluster setup. Used here as the durable buffer between metric producer and stream processor.
- **Faust (Python):** Stream processing library built on Kafka and asyncio. Used here for 30-second windowed aggregation; integrates with River-ML on the same event loop.

## 3.4 Online machine learning

- **River (formerly scikit-multiflow):** Online ML library for Python [Montiel et al., 2021]. Implements Hoeffding Adaptive Tree Regressors (HTR), Half-Space Trees for anomaly detection, and linear regressors. Single-pass, O(memory) per update, suitable for the Faust 30-s window cadence.
- **Hoeffding trees [Hulten et al., 2001]:** Decision trees that adapt their split criteria online based on Hoeffding-bound confidence intervals. We use the regression variant for the replica predictor.
- **Half-Space Trees [Tan et al., 2011]:** Unsupervised anomaly detection; scores each window by mass of points falling outside learned half-spaces. Used here for the anomaly detector.
- **SHAP / KernelExplainer:** Model-agnostic explanations. Not used because SHAP on a Hoeffding tree is non-trivial and the leave-one-out perturbation (Decision.explanation) satisfies the explainability requirement for the viva.

## 3.5 Formal verification in distributed systems

- **TLA+ [Lamport, 1994]:** Leslie Lamport's specification language for concurrent / distributed systems. State-machine semantics with explicit temporal operators.
- **PlusCal:** Algorithm pseudocode that translates to TLA+. Used in `specs/SafetyShield.tla` for clarity.
- **TLC:** The model checker that exhaustively explores state spaces up to a configurable bound.
- **Industrial use:** Amazon (DynamoDB, S3), Microsoft (Cosmos DB), and Kubernetes operators (e.g., the KEP for HPA v2 included a TLA+ model). This thesis adds to the body of work applying TLA+ to operator-level safety.

## 3.6 Safe-RL and runtime shielding

- **Alshiekh et al. [AAAI 2018]:** Proposed runtime shielding for RL agents via LTL specifications. A "shield" intercepts every action proposed by the RL policy and replaces it with a safe alternative if the proposed action would violate a temporal-logic property. Our work applies the same idea to online-learning controllers (a different oracle family), with a closed-form TLA+ specification rather than LTL shield synthesis.
- **Li et al. [IJRR 2019]:** Surveyed safe-RL approaches; concludes that shielding is among the most practical for industrial systems where exhaustive policy verification is infeasible.

## 3.7 Threshold-based autoscalers

- **FIRM (Lim et al., 2020):** Threshold-based autoscaler using multiple resource signals (CPU, memory, request rate, latency). Hand-tuned thresholds per signal with a max-replica aggregation. Our `src/baselines/firm_controller.py` reproduces this design as the strongest non-ML baseline because it uses the same 8 features as our AI controller.

## 3.8 Related operator projects

- **KEDA:** Mentioned above. Closest commercial-grade competitor to this thesis.
- **Goldpinger:** Shopify's HPA visualizer (different scope — observability, not control).
- **RobustScaler:** Academic project on robust scaling under uncertainty (referenced, not implemented).
- **Kubernetes Event-Driven Autoscaling (KEDA) + cluster autoscaler** in production: documented in [KEDA, 2023].

## 3.9 Summary table

| Project | Auto-scaling signal | Auto-healing | Formal safety | Online learning |
|---------|---------------------|--------------|---------------|-----------------|
| HPA | CPU/memory only | ❌ | ❌ | ❌ |
| KEDA | Multi (Prometheus, Kafka, …) | ❌ | ❌ | ❌ |
| LitmusChaos + HPA | (inherits HPA) | ✅ | ❌ | ❌ |
| FIRM-style threshold | Multi (4 signals) | ❌ | ❌ (no formal proof) | ❌ |
| **SHIELD-AI (this thesis)** | Multi (8 features) | ✅ | ✅ TLA+ (6 invariants) | ✅ River HTR + HST |

## 3.10 Position of this thesis

SHIELD-AI sits at the intersection of three lines of work: (a) Kubernetes autoscaling (HPA, KEDA, VPA), (b) online learning for control (River, Hoeffding trees), and (c) formal verification of safety (TLA+, runtime shielding). The unique contribution is the closed-form composition theorem in `specs/ML_Composition.tla`: regardless of what the ML oracle outputs, the Safety Shield's invariants hold. This is the strongest single claim we make.
