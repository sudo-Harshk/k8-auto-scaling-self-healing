# Chapter 4 — Existing System

## 4.1 Horizontal Pod Autoscaler (HPA)

### 4.1.1 Architecture

HPA runs as a Kubernetes controller (part of `kube-controller-manager`). Every 15 s (configurable via `--horizontal-pod-autoscaler-sync-period`), it queries the metrics API for the current resource utilization of each target Deployment, computes the desired replica count, and patches the Deployment's `spec.replicas`.

```
+-------------------+      +----------------+      +------------------+
| Metrics API       |  --> | HPA Controller |  --> | Deployment       |
| (CPU, memory,     |      | desired_replicas|     | spec.replicas    |
|  custom metrics)  |      | = ceil(cur *    |     | updated          |
+-------------------+      |   target / cur)|      +------------------+
                           +----------------+
```

### 4.1.2 Concrete limitations

1. **Single signal.** HPA's only first-class signals are CPU and memory. Custom metrics require the metrics adapter pattern (e.g., Prometheus Adapter or KEDA). For workloads where request rate or latency drives the user-perceived load, CPU is a poor proxy.
2. **No anomaly detection.** HPA does not observe error rate, latency, or any signal that would indicate a faulty pod returning 5xx responses. A faulty pod that passes its liveness probe but returns 500s will continue to receive traffic.
3. **Stabilization delay.** Default 5-min stabilization window makes HPA slow to react to short spikes. A 30-s burst followed by a return to baseline is invisible to HPA.
4. **No safety bounds.** HPA does not enforce a minimum replica count or a maximum step size unless the user configures them manually. A misconfigured `minReplicas: 0` will happily scale the Deployment to zero.

### 4.1.3 Empirical evidence from the Day-15 evaluation

In the Day-15 N=3 evaluation (see §7 for full details), HPA scaled from 2 to 10 replicas with a 15-s scaling lag (the HPA sync period). It missed the recovery window during the spike scenario because the spike resolved within the 5-min stabilization window. Error rate: 0% — HPA correctly scaled before the workload experienced 5xx.

## 4.2 KEDA

### 4.2.1 Architecture

KEDA wraps HPA. It introduces a `ScaledObject` CRD that maps external triggers (Prometheus query, Kafka lag, RabbitMQ queue depth, cron, …) to a custom metric. HPA then scales on that metric as if it were CPU.

```
+-----------------+      +-----------+      +---------+      +--------------+
| External        |  --> | KEDA      |  --> | custom  |  --> | HPA          |
| trigger         |      | scaler    |      | metric  |      | (unchanged)  |
| (Prometheus,    |      |           |      | server  |      |              |
|  Kafka, …)      |      +-----------+      +---------+      +--------------+
```

### 4.2.2 Improvements over HPA

- **Rich signal library.** 60+ scalers built in (Prometheus, Kafka, Redis, RabbitMQ, AWS SQS, GCP Pub/Sub, …).
- **Scaling to zero.** KEDA can scale a Deployment to 0 replicas when no triggers are active (useful for batch jobs).
- **Per-trigger configuration.** Different scalers can be composed with separate `ScaledObject` resources.

### 4.2.3 Limitations (inherited from HPA)

- **No anomaly detection.** KEDA observes the trigger metric but not the error rate, latency, or pod-level signals.
- **No formal safety verification.** Trigger thresholds can be misconfigured (e.g., scale to 0 forever; scale to MAX_REPLICAS without bound).
- **Single-signal per scaler.** Composing multiple triggers requires per-trigger ScaledObjects and aggregation logic outside the operator.

### 4.2.4 Empirical evidence from the Day-15 evaluation

KEDA scaled from 2 to 10 with a 5-s scaling lag (its custom metric is polled more frequently). Error rate: 0%. KEDA matched HPA on correctness but had a smaller scaling lag.

## 4.3 Self-healing in vanilla Kubernetes

- **Liveness probes** restart a pod when a check fails (e.g., HTTP `/healthz`).
- **PodDisruptionBudget** limits voluntary disruption but does not initiate healing.
- **RestartPolicy / backoffLimit** retries on failure.
- **No active healing** (e.g., delete a pod that is returning 500s despite passing health checks).

This means a faulty pod that:
- starts up successfully (liveness passes),
- but returns 500s on 100% of requests,
- and never returns a non-2xx HTTP status that the probe interprets as failure,

…will continue to receive traffic indefinitely, lowering the success rate of the Deployment while HPA / KEDA scale *around* it rather than removing the bad pod.

## 4.4 Formal verification in K8s operators

Notable uses of TLA+ in Kubernetes-related projects:

- **Kubernetes HPA v2 KEP** includes a TLA+ model (informally) describing the controller loop.
- **etcd** has been specified in TLA+ since 2014 (consensus correctness).
- **Paxos / Raft consensus** libraries often ship TLA+ specs as correctness arguments.

However, none of these specs cover a *machine-learning* controller — the controller output is treated as a deterministic function of the metrics. SHIELD-AI's `specs/ML_Composition.tla` is novel in that it models the ML oracle as a thin non-deterministic abstraction and proves the safety of the composed system despite this uncertainty.

## 4.5 The gap this thesis addresses

Neither HPA nor KEDA combines:
1. **Multi-signal decision making** — multiple Prometheus + K8s features into a single decision.
2. **Active anomaly-driven healing** — detecting a faulty pod that passes health probes.
3. **Formally verified safety invariants** — machine-checked proof that the operator cannot reach an unsafe state.
4. **Online learning from production traffic** — the model continues to adapt to non-stationary load.

This thesis addresses all four. The argument is that *each of these is necessary* and *together they produce a safer, more responsive operator than any one alone*. SHIELD-AI's contribution (3) is the closed-form TLA+ specification of the ML+Shield composition — a guarantee that holds regardless of what the ML oracle outputs.
