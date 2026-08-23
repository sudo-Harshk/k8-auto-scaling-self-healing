# Demo Script — 5-Minute Walkthrough

> **Status:** Scaffolding. Filled after Day 14 evaluation runs (numbers are placeholders).

## 0:00 — Introduction (15 s)

> "Hi. This is the AI-driven Kubernetes operator for unified auto-scaling and auto-healing. The architecture has five components: Prometheus for metrics, Kafka as the bus, Faust for 30-second windowed aggregation, an online River-ML decision engine, a TLA+-verified safety shield, and a Kubernetes operator that applies the decisions. Every decision is gated by a formally verified invariant set."

## 0:15 — VM and cluster (30 s)

Show:
- VM up (4 vCPU, 16 GB RAM, Ubuntu 24.04)
- kind cluster with 1 control-plane node
- podinfo with 2 healthy replicas
- Prometheus + Grafana + Kafka running

## 0:45 — Pipeline bring-up (45 s)

Run `./scripts/run_pipeline.sh` in one terminal:
- Producer (Prometheus → Kafka)
- Faust worker (Kafka → Kafka)
- Decision Engine (Kafka → Kafka + Safety Shield)
- Operator (Kafka → cluster)

Show Kafka offsets climbing:
```
k8s-metrics:    N messages
k8s-features:    M messages
k8s-decisions:   K messages
```

## 1:30 — Locust spike test (60 s)

Run `locust -u 100 -r 20 -t 180s --headless` against podinfo.

Show:
- Grafana CPU spike
- Grafana request-rate spike
- AI operator scaling podinfo 2 → N replicas

Expected:
```
[t+00:30]  scale: 2 -> 4 (target_replicas=4, predictor says 4)
[t+00:30]  safety_pass (no mods needed)
[t+01:00]  steady at 4 replicas
[t+03:00]  scale: 4 -> 2 (load decreased, predictor says 2)
```

## 2:30 — Fault injection (60 s)

While Locust is running, inject a fault:
```
curl -X POST http://podinfo.podinfo:9898/fault_injection/enable
```

Show:
- error rate climbs (Grafana)
- decision engine emits heal action (logs/decisions.log)
- operator deletes the faulty pod (logs/operator_actions.log)
- Kubernetes creates a replacement pod

Expected:
```
[t+00:00]  fault injected on pod N
[t+00:30]  Faust window shows error_rate=1.5
[t+01:00]  decision: heal (anomaly_score=0.69 > heal_threshold)
[t+01:00]  operator: deleted pod N, replicas=2
[t+01:05]  Kubernetes: created replacement pod N+1
[t+01:30]  error_rate back to 0
```

## 3:30 — Comparison (60 s)

Show the comparison table from `data/evaluation/comparison_results.csv`:
- HPA vs KEDA vs AI scaling lag
- Detection latency (AI is the only one with anomaly-driven healing)
- Unsafe actions: 0 for AI (Safety Shield); unconstrained for HPA/KEDA

## 4:30 — Summary (30 s)

> "Key takeaways:
> 1. Online ML + formal verification is feasible — every decision is TLA+-verified before application.
> 2. The AI operator scales and heals. HPA does neither with anomaly detection. KEDA scales but does not heal.
> 3. The full pipeline reproduces from a fresh VM in 30 minutes via `scripts/bootstrap_vm.sh`.
>
> Future work: production deployment, multi-tenant policies, fairness extensions to the TLA+ spec."

## 5:00 — End

## Notes for the presenter

- Keep the script visible so the audience sees what command produces each visual.
- Pre-stage the Locust and curl commands in a separate terminal window.
- Have the Grafana dashboard open in another tab.
- The numbers will be filled in after Day 14 evaluation. Use placeholders if running this before Day 14.