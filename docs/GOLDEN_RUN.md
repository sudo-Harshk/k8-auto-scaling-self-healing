# Golden Run — 12-Step Deterministic Demo

> **Purpose:** one repeatable sequence a reviewer can run on a fresh machine
> and reproduce every claim in the paper. This is the artifact submitted to
> IEEE.

## Prereqs

- Docker CE (or Podman + kind-compatible)
- `kind`, `kubectl`, `helm`, `docker compose`
- 8 GB RAM minimum
- Network access (pulls Kafka, Prometheus, podinfo images)

## The 12 steps

| # | Action | Command | Verifies |
|---|--------|---------|----------|
| 1 | Create kind cluster | `make kind-up` | Single-node K8s cluster `k8-ai` |
| 2 | Build shared image | `make build-image` | `k8-ai-ops:dev` Python 3.11-slim |
| 3 | Deploy Kafka | `make deploy-kafka` | KRaft cluster, topics `k8s-metrics`, `k8s-features`, `k8s-decisions` |
| 4 | Deploy Prometheus + Grafana | `make deploy-prometheus` | ServiceMonitor for podinfo + workload-v2 |
| 5 | Deploy workload (podinfo) | `make deploy-workload` | 2 healthy replicas, `/metrics` endpoint |
| 6 | Start pipeline | `make pipeline-up` | Producer + Faust + Decision + Operator all running |
| 7 | Baseline traffic (5 min) | `make load-baseline` | p95 stable, decisions = `noop` |
| 8 | Burst (5 min, 100 RPS ramp) | `make load-burst` | decisions = `scale` 2 → 6 (verified via `kubectl get deploy`) |
| 9 | Ramp down | `make load-rampdown` | decisions = `scale` 6 → 2 |
| 10 | Pod failure | `make inject-fault` | decision = `heal` (anomaly_score > 2x threshold), operator deletes pod, K8s recreates |
| 11 | Rejected unsafe action | `make inject-unsafe` | Decision engine emits `replicas=20` (via test hook), Shield rejects with audit log line |
| 12 | Export graphs | `make export-graphs` | Latency/replicas/decisions PNG + CSV in `results_N10/` |

## Quick path

```bash
make demo        # runs all 12 steps end-to-end (~30 min)
make eval        # runs N=10 harness (~3 hours)
make tla         # runs TLC model-checker
make paper       # builds docs/paper/main.pdf
make thesis      # builds thesis chapters into a single PDF
```

## What each step proves (for the viva)

1. **kind-up** — system is self-contained, no Azure dependency.
2. **build-image** — same Python 3.11 env as production, no host pollution.
3. **deploy-kafka** — bus is real Kafka, not in-memory mock.
4. **deploy-prometheus** — metrics are real Prometheus, not synthetic.
5. **deploy-workload** — workload is real microservice, not toy.
6. **pipeline-up** — all four processes actually run.
7. **load-baseline** — system does nothing when nothing is needed.
8. **load-burst** — **autoscaling works** (the P1 fix).
9. **load-rampdown** — autoscaling is not a one-way ratchet.
10. **inject-fault** — **self-healing works**.
11. **inject-unsafe** — **safety shield blocks unsafe ML output** (the strongest contribution).
12. **export-graphs** — paper figures are reproducible, not hand-drawn.

## Failure mode handling

- If any step fails, `make demo` halts and prints the failing log.
- `make reset` cleans up to a known state (deletes cluster, images, volumes).
- All run output is captured to `logs/demo_<timestamp>/` for postmortem.
