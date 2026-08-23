# Chapter 7 — Results and Discussion

> **Status:** Scaffolding. Filled after Day 14 evaluation runs.

## 7.1 Evaluation methodology

[To be filled after Day 14.]

- Scenarios: spike (100 users / 3 min), steady-high (50 users / 5 min), idle (10 users / 2 min)
- Operators compared: vanilla HPA, KEDA (Prometheus scaler), AI-driven operator
- Metrics: scaling lag (s), total actions, p95 latency (ms), error rate, replica count over time
- Repeat count: N=3 (per Day 15 plan)

## 7.2 Headline results table (TBD)

| Operator | Scaling lag (s) | Total actions | p95 latency (ms) | Error rate (%) |
|----------|----------------|--------------|------------------|----------------|
| Vanilla HPA | _TBD_ | _TBD_ | _TBD_ | _TBD_ |
| KEDA | _TBD_ | _TBD_ | _TBD_ | _TBD_ |
| AI operator (full) | _TBD_ | _TBD_ | _TBD_ | _TBD_ |

(Values filled in from `data/evaluation/comparison_results_N3.csv` after Day 15.)

## 7.3 Auto-scaling under load (scenario: spike)

[Figure: replica count over time for each operator under spike load. AI operator responds to request_rate increase; HPA responds to CPU utilization (slower for I/O-bound workloads); KEDA between the two.]

## 7.4 Auto-healing under fault injection (scenario: chaos)

[Figure: time from fault injection to operator action. AI operator detects anomaly in ~30 s (one Faust window) and deletes faulty pod within cooldown. HPA does not detect the fault (no anomaly signal).]

## 7.5 Ablation: which components contribute

| Variant | Scaling lag (s) | Unsafe actions (rejected) | Healing time (s) |
|---------|----------------|--------------------------|------------------|
| AI full | _TBD_ | 0 (by design) | _TBD_ |
| AI – SHAP | _TBD_ | 0 | _TBD_ |
| AI – Safety Shield | _TBD_ | not enforced | _TBD_ |
| AI + liveness (Day-15) | _TBD_ | 0 | _TBD_ |

## 7.6 p95 latency evidence (Day-16)

[Figure: p95 latency distribution under spike load. After the v2 (DB-backed) workload is deployed in Day 16, p95 varies meaningfully. Show the distribution as a histogram. Contrast with the constant 4.75 ms in the original Day-6 dataset.]

## 7.7 Discussion

### 7.7.1 Why the AI operator scales faster (or doesn't)

[To be filled.]

### 7.7.2 Why the Safety Shield matters

The Safety Shield rejects unsafe actions before they reach the cluster. In the AI-minus-Shield ablation, we expect to see zero rejections (no enforcement) but also no scaling-trend drift. In the full AI, all rejected actions appear in `logs/safety_audit.log` and are listed in Chapter 7.5.

### 7.7.3 Why online learning matters

River-ML's online fit means the predictor and anomaly detector improve during production runtime. Day 15 captures this empirically by retraining on a larger dataset (concatenation of Day 6 + Day 13 + Day 14 windows) and reporting the new detection rate.

### 7.7.4 What HPA does better

[Honest comparison. HPA is simpler, requires no extra infrastructure, and is battle-tested. The AI operator's value is in (a) multi-signal decision making, (b) anomaly-driven healing, (c) formal safety — not raw scaling speed.]

## 7.8 Limitations

1. **p95 latency baseline.** Day-6's podinfo workload had constant p95 (no backend dependency). Day-16's DB-backed workload fixes this. The reported results are after the rework.
2. **Single-node kind cluster.** Multi-node scheduling not exercised. Acknowledge this limits realism.
3. **Single workload (post-rework).** Day 16 swaps to a Flask + SQLite workload; results generalize to I/O-bound microservices but not to all workload classes.
4. **Cooldown caps scaling rate.** 60 s cooldown means no more than ~5 scale actions per 5-minute window. This is intentional safety but caps responsiveness during rapid oscillations.
5. **HalfSpaceTrees with small dataset.** 33-row training set on Day 8; 200+ rows by Day 15. Documented in AMENDMENTS.
6. **River + Python 3.11 patch.** One-line sed strip of PEP 695 generic syntax. Tested; alternative is upgrading to Python 3.12 which breaks kafka-python and Faust.

## 7.9 Threats to validity

- **Internal:** single VM, single kind cluster, single workload. Results may not generalize.
- **External:** production traffic patterns differ from synthetic Locust.
- **Construct:** the comparison metrics (scaling lag, healing time) are proxies for "operator quality" which is itself a multi-dimensional construct.
- **Conclusion:** all claims are scoped to the experimental setup; broader claims require broader evaluation.