# Chapter 4 — Existing System

> **Status:** Scaffolding. Filled after Day 14.

## 4.1 Horizontal Pod Autoscaler (HPA)

### Architecture

HPA runs as a Kubernetes controller. Every 15 s (configurable), it queries the metrics API for the current resource utilization of each target Deployment, compares against the target, and computes the desired replica count. If the new count differs from the current, it patches the Deployment.

### Limitations

1. **Single signal.** HPA's only first-class signal is CPU or memory. Custom metrics require the metrics adapter pattern (e.g., Prometheus Adapter).
2. **No anomaly detection.** HPA does not observe error rate, latency, or any signal that would indicate a faulty pod.
3. **Stabilization delay.** Default 5 min stabilization window makes HPA slow to react to short spikes.
4. **No safety bounds.** HPA does not enforce a minimum replica count or a maximum step size unless the user configures them manually.

## 4.2 KEDA

### Architecture

KEDA wraps HPA. It introduces a `ScaledObject` CRD that maps external triggers (Prometheus query, Kafka lag, RabbitMQ queue depth, cron, etc.) to a custom metric. HPA then scales on that metric as if it were CPU.

### Improvements over HPA

- **Rich signal library.** 60+ scalers built in (Prometheus, Kafka, Redis, RabbitMQ, AWS SQS, GCP Pub/Sub, …).
- **Scaling to zero.** KEDA can scale a Deployment to 0 replicas when no triggers are active.

### Limitations (inherited from HPA)

- **No anomaly detection.**
- **No formal safety verification.** Trigger thresholds can be misconfigured (e.g., scale to 0 forever).
- **Single-signal per scaler.** Composing multiple triggers requires per-trigger ScaledObjects and aggregation logic outside the operator.

## 4.3 Self-healing in vanilla Kubernetes

- **Liveness probes** restart a pod when a check fails (e.g., HTTP `/healthz`).
- **PodDisruptionBudget** limits voluntary disruption but does not initiate healing.
- **RestartPolicy / backoffLimit** retries on failure.
- **No active healing** (e.g., delete a pod that is returning 500s despite passing health checks).

## 4.4 Formal verification in K8s operators

Notable uses of TLA+ in Kubernetes-related projects:

- **Kubernetes HPA v2 KEP** includes a TLA+ model (informally).
- **etcd** has been specified in TLA+ since 2014.
- **Paxos / Raft consensus** libraries often ship TLA+ specs as correctness arguments.

## 4.5 The gap this project addresses

Neither HPA nor KEDA combines:
1. Multi-signal decision making
2. Active anomaly-driven healing
3. Formally verified safety invariants
4. Online learning from production traffic

This project addresses all four. The thesis argument is that *each of these is necessary* and *together they produce a safer, more responsive operator than any one alone*.