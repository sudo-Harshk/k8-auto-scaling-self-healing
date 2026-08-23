# Chapter 3 — Literature Survey

> **Status:** Scaffolding. Filled after Day 14.

## 3.1 Kubernetes auto-scaling

- **Horizontal Pod Autoscaler (HPA):** Kubernetes-native controller, scales Deployments based on a target metric (default CPU%). Polls metrics every 15 s. Stabilization window defaults to 5 min.
- **Vertical Pod Autoscaler (VPA):** Adjusts resource requests/limits instead of replica count. Out of scope for this project.
- **KEDA:** Event-driven autoscaler. Wraps HPA with custom metric sources. Strong signal library (Prometheus, Kafka lag, RabbitMQ, cron, etc.).
- **Cluster Autoscaler / Karpenter:** Adds/removes nodes, not pods. Composable with this project.

## 3.2 Self-healing and chaos engineering

- **Kubernetes restartPolicy, liveness/readiness probes:** Restart-on-failure but no anomaly detection.
- **LitmusChaos, Chaos Mesh:** Active fault injection. Used in evaluation harnesses.
- **Podinfo's built-in `/fault_injection/enable`:** Lightweight alternative for evaluation.

## 3.3 Stream processing

- **Apache Kafka:** De-facto message bus. KRaft mode (since 2.8) eliminates ZooKeeper dependency.
- **Faust (Python):** Stream processing library built on Kafka and asyncio. Used here for 30-second windowed aggregation.

## 3.4 Online machine learning

- **River (formerly scikit-multiflow):** Online ML library for Python. Implements Hoeffding trees, half-space trees, linear regressors. Used here for both the replica predictor and anomaly detector.
- **SHAP / KernelExplainer:** Model-agnostic explanations. Not directly used because of River incompatibility; substituted with leave-one-out perturbation (documented in AMENDMENTS).

## 3.5 Formal verification in distributed systems

- **TLA+:** Leslie Lamport's specification language for concurrent / distributed systems.
- **PlusCal:** Algorithm pseudocode that translates to TLA+.
- **TLC:** The model checker that exhaustively explores state spaces.
- **Industrial use:** Amazon (DynamoDB, S3), Microsoft (Cosmos DB), and Kubernetes operators (e.g., the KEP for HPA v2 included a TLA+ model).

## 3.6 Related operator projects

- **KEDA:** Mentioned above. Closest commercial-grade competitor to this project.
- **Goldpinger:** Shopify's HPA visualizer (different scope).
- **RobustScaler:** Academic project on robust scaling under uncertainty (referenced, not implemented).

## 3.7 Summary of related work

| Project | Auto-scaling signal | Auto-healing | Formal safety | Online learning |
|---------|---------------------|--------------|---------------|-----------------|
| HPA | CPU/memory only | ❌ | ❌ | ❌ |
| KEDA | Multi (Prometheus, Kafka, …) | ❌ | ❌ | ❌ |
| LitmusChaos + HPA | (inherits HPA) | ✅ | ❌ | ❌ |
| **This project** | Multi (request_rate, error_rate, latency, …) | ✅ | ✅ TLA+ | ✅ River |

[Filled in fully after Day 14.]