# Comparison Summary (Day 14)

## Headline numbers

| Operator | Scaling lag (s) | Scale actions | Heal actions | Error rate (%) | Replicas (start → end) |
|----------|----------------|---------------|--------------|----------------|-------------------------|
| HPA | 15 | 8 | 0 | 0.0 | 2 → 6 |
| KEDA | 5 | 6 | 0 | 0.0 | 2 → 2 |
| AI (full) | 90 | 0 | 1 | 69.2 | 2 → 2 |

(Full data: `data/evaluation/comparison_results.csv`.)

## Per-scenario breakdown

### Spike (30 users, 240 s, ramp-up 60 s)

[Figure placeholders — generated from `data/evaluation/comparison_results.csv`]

| Operator | Replicas at peak | Replicas at end | Scaling lag to first scale |
|----------|------------------|-----------------|------------------------------|
| HPA | 10 | 6 | 15 s |
| KEDA | 10 | 2 | 5 s |
| AI | 2 | 2 | n/a (heal action only) |

### Steady-high (planned Day 15 N=3)

[Day 15 will fill this in.]

### Idle (planned Day 15 N=3)

[Day 15 will fill this in.]

## Ablation summary

`data/evaluation/ablation_results.csv`:

| Variant | Scale | Heal | Noop | Rejected (cooldown) | Applied |
|---------|-------|------|------|---------------------|---------|
| Full AI | 0 | 55 | 0 | 54 | 1 |
| –SHAP | 0 | 55 | 0 | 54 | 1 |
| **–Safety Shield** | 0 | 55 | 0 | 0 | **55** |

The Safety Shield is the paper's strongest safety claim: **without it, the engine would apply 55 unconstrained heal actions in 55 windows**.

## Auto-healing capability (Day-13 evidence)

| Operator | Detects HTTP 500 fault | Heals within 5 min |
|----------|------------------------|---------------------|
| HPA | ❌ | n/a |
| KEDA | ❌ | n/a |
| **AI (full)** | ✅ | ✅ |

Only the AI operator detects anomalies (anomaly_score > threshold when error_rate spikes) and applies a heal action (delete faulty pod).

## Statistical comparison (Day 15 N=3)

[Day 15 will fill this in.]

## Evidence files

- `data/evaluation/comparison_results.csv` — master comparison table
- `data/evaluation/hpa_run_hpa_timeline.txt` — HPA scale event log
- `data/evaluation/keda_run_hpa_timeline.txt` — KEDA scale event log
- `data/evaluation/ai_run_operator_actions.log` — AI operator actions
- `data/evaluation/ablation_results.csv` — ablation counts
- `data/evaluation/locust_*_stats.csv` — Locust run statistics per operator
- `data/evaluation/locust_*_failures.csv` — Locust failure breakdown