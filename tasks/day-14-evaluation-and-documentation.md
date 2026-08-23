# Day 14 — Evaluation, Dashboards & Final Documentation

## Task
Measure system performance, build an audit dashboard, and finalize the thesis report and presentation.

## Aim
Quantify the value of the AI-driven operator and produce the final M.Tech deliverables.

## Requirements

- Results from Day 13 testing
- Grafana access
- Locust reports
- Thesis template (Word/LaTeX/Google Docs)
- Original PPT file

## Steps

1. **Define evaluation metrics and SLOs**
   - Example SLOs:
     - p95 latency < 500 ms
     - Availability > 99%
     - CPU utilization between 40% and 80%
   - Define comparison scenarios:
     - Baseline: default HPA only
     - Proposed: your AI-driven operator

2. **Run comparison experiments**
   - Run the same Locust load profile twice:
     - Once with default HPA
     - Once with your AI operator active
   - Record p95 latency, availability, replica counts, and CPU usage.

3. **Analyze results**
   - Compute SLO compliance for both scenarios.
   - Show that your system adapts faster or maintains better SLOs.

4. **Build an audit dashboard**
   - Create a simple web page or Grafana dashboard showing:
     - Recent decisions
     - Approved vs rejected actions
     - Current replica counts
     - Anomaly scores

5. **Write final thesis sections**
   - Include:
     - Abstract
     - Introduction
     - Literature Survey
     - Existing System
     - Proposed System
     - System Architecture
     - Implementation
     - Results and Discussion
     - Conclusion and Future Work
     - References

6. **Update the PPT**
   - Add results, screenshots, and evaluation graphs.
   - Add a demo video or screenshots.

7. **Prepare a short demo script**
   - 5-minute walkthrough of the system.

## Outcome

- Evaluation table/graphs comparing default HPA vs AI operator.
- Audit dashboard showing decisions and system state.
- Completed thesis report.
- Updated project presentation.
- Demo script ready.

## Verification

Check that you can answer these questions with data:

- How much faster does your system scale compared to HPA?
- How quickly does it detect and heal a faulty pod?
- What percentage of decisions were approved by the Safety Shield?
- Did SLO compliance improve?

---

## Execution Plan (2026-08-23, finalized)

### Phases (estimated 6–8 hours)

| Phase | Task | Time |
|-------|------|------|
| 1 | HPA baseline install + smoke test | 45 min |
| 2 | KEDA install (optional) + 3-way setup | 1 h |
| 3 | Run comparison harness (HPA / KEDA / AI × 3 scenarios) | 3 h |
| 4 | Ablation study (full AI / –SHAP / –Shield) | 1 h |
| 5 | Thesis chapters (8 files in `docs/thesis/`) | 1.5 h |
| 6 | PPT, demo script, reproducibility scripts | 45 min |

### Metrics captured per scenario

- `replicas` over time (Prometheus: `kube_deployment_spec_replicas`)
- `request_rate` over time (Prometheus: `rate(http_requests_total[1m])`)
- `cpu_percent` over time (Prometheus: `rate(container_cpu_usage_seconds_total[1m])`)
- `p95_latency_ms` over time (Prometheus: `histogram_quantile(0.95, …)` — note: documented constant for podinfo; expected to vary after Day-16 rework)
- `error_rate` over time (Prometheus: `rate(http_requests_total{status=~"5.."}[1m])`)
- `scaling_lag_s` (time from load increase to first scale action)
- `total_actions` (count of scale + heal actions per scenario)
- `safety_rejected_count` (Safety Shield rejections per AI run)

### Scenarios

| Scenario | Users | Duration | Notes |
|----------|-------|----------|-------|
| Spike | 100 | 3 min | Ramp in 60 s |
| Steady-high | 50 | 5 min | Constant load |
| Idle | 10 | 2 min | Baseline |

### Output files (filled during execution)

- `data/evaluation/comparison_results.csv` — master comparison table
- `data/evaluation/comparison_summary.md` — human-readable summary
- `docs/thesis/01_abstract.md` … `09_conclusion.md` — thesis chapters
- `docs/final_ppt.md` — slide outline
- `docs/demo_script.md` — 5-min walkthrough
- `scripts/run_comparison.sh` — reproducible harness
- `scripts/swap_operator.sh` — disable/enable HPA / KEDA / AI

### Deviation from original plan

Original Day-14 plan was single-run, M.Tech style. **Expanded to a 3-day cycle (Day 14–16)** per user decision (see AMENDMENTS 2026-08-23). This page covers Day 14 only; Day 15 (statistical rigor N=3, liveness TLA+, larger training set) and Day 16 (p95-variability rework, IEEE paper draft, Grafana dashboard JSON) are tracked separately.
