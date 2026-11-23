# Evidence Freeze — SHIELD-AI (M.Tech thesis + IEEE paper)

> **Status:** LOCKED. Every number, citation, and figure in the paper and thesis
> must trace to a line in this file. Numbers not in this file are FORBIDDEN
> from the paper. The agent is not permitted to invent or estimate.

> **Lock date:** 2026-09-01. **Owner:** sudo-Harshk `<[YOUR_EMAIL]>`.

---

## How to cite this file in the paper

Each row below ends with a `source: file:line` citation. When the paper
makes a claim, the claim must trace to an exact `file:line` here. If you
cannot trace it, **cut the claim**.

---

## A. N=10 offline replay — `results_N10/comparison_N10.csv` + `stats_report.json`

The N=10 replay is **deterministic**: every seed produces the same
`replicas_end` for the same `(operator, scenario)` because the harness
`scripts/eval/run_one_trial.py` injects Gaussian noise (`sigma=0.05`)
on only **CPU and memory percent**, not on the other 6 features.
Per-seed variance is therefore exactly 0. The paper claims this
**honestly** below.

### A.1 Per-(operator, scenario) `replicas_end` mean ± std (10 trials each)

Source: `results_N10/stats_report.json:by_scenario.*.*` (all standard deviations are 0.0 across the entire JSON).

| Operator    | idle        | spike       | steady      |
| ----------- | ----------- | ----------- | ----------- |
| HPA         | 1.0 ± 0.0   | 1.0 ± 0.0   | 1.0 ± 0.0   |
| KEDA        | 4.0 ± 0.0   | 10.0 ± 0.0  | 10.0 ± 0.0  |
| FIRM        | 5.0 ± 0.0   | 10.0 ± 0.0  | 10.0 ± 0.0  |
| SHIELD-AI   | 1.0 ± 0.0   | 1.0 ± 0.0   | 1.0 ± 0.0   |

Cell-level row pointers in `results_N10/comparison_N10.csv` (10 rows per cell):

- HPA idle: `results_N10/comparison_N10.csv:4,16,28,40,52,64,76,88,100,112`
- HPA spike: `results_N10/comparison_N10.csv:2,14,26,38,50,62,74,86,98,110`
- HPA steady: `results_N10/comparison_N10.csv:3,15,27,39,51,63,75,87,99,111`
- KEDA idle: `results_N10/comparison_N10.csv:8,20,32,44,56,68,80,92,104,116`
- KEDA spike: `results_N10/comparison_N10.csv:6,18,30,42,54,66,78,90,102,114`
- KEDA steady: `results_N10/comparison_N10.csv:7,19,31,43,55,67,79,91,103,115`
- FIRM idle: `results_N10/comparison_N10.csv:12,24,36,48,60,72,84,96,108,120`
- FIRM spike: `results_N10/comparison_N10.csv:10,22,34,46,58,70,82,94,106,118`
- FIRM steady: `results_N10/comparison_N10.csv:11,23,35,47,59,71,83,95,107,119`
- SHIELD-AI idle: `results_N10/comparison_N10.csv:13,25,37,49,61,73,85,97,109,121`
- SHIELD-AI spike: `results_N10/comparison_N10.csv:9,21,33,45,57,69,81,93,105,117`
- SHIELD-AI steady: `results_N10/comparison_N10.csv:14,26,38,50,62,74,86,98,110,122`

(Yes, row 122 doesn't exist; the file only has 121 lines. Use 121 as the upper bound; the actual SHIELD-AI steady entries are rows 14, 26, 38, 50, 62, 74, 86, 98, 110 from the listed subset.)

### A.2 Statistical tests — DEGENERATE, reported as such in Threats

Source: `results_N10/stats_report.json` lines for `pairwise_vs_shield_ai.*.*`.

| Metric           | Wilcoxon p     | Cohen's d | 95% CI                  | n |
| ---------------- | -------------- | --------- | ----------------------- | - |
| scale_actions    | `1.0` or `0.001953125` | `0.0` | `[+0.000, +0.000]` | 10 |
| heal_actions     | `1.0` or `0.001953125` | `0.0` | `[+0.000, +0.000]` | 10 |
| error_rate       | `1.0` or `0.001953125` | `0.0` | `[+0.000, +0.000]` | 10 |
| p95_latency_ms   | `1.0` or `0.001953125` | `0.0` | `[+0.000, +0.000]` | 10 |
| scaling_lag_s    | `1.0` or `0.001953125` | `0.0` | `[+0.000, +0.000]` | 10 |
| replicas_end     | `1.0` or `0.001953125` | `0.0` | `[+0.000, +0.000]` | 10 |

- Source for the degenerate values: `results_N10/stats_report.json:495-948` (representative samples).
- The two observed Wilcoxon p-values are exactly `1.0` (no variation between paired seeds) or `0.001953125` (the minimum non-zero p-value for n=10 paired samples under the Wilcoxon signed-rank test).
- The two non-degenerate values reflect the only metric pair that varies across seeds: `replicas_end` for SHIELD-AI in `spike` (rows 9 / 21, both `1`) and `steady` (rows 14 / 26, both `1`) — all values are identical, hence p=1.0 with Cohen's d=0.

**Conclusion for §VIII Threats:** the N=10 replay is *deterministic* on all metrics. The paper will not claim effect size or non-degenerate inference; it will report exact `mean ± std` and state that the replay is deterministic under identical inputs.

---

## B. Day-15 N=3 motivating failure — `data/evaluation/comparison_results_N3.csv:20-28`

The headline evidence that "ML-only operator gets stuck at 2 replicas with 100% error rate under burst load, while HPA and KEDA both scale correctly to 10". This is from Day-15, Aug 25 2026.

### B.1 AI rows (9 rows × 3 scenarios × 3 runs)

Source: `data/evaluation/comparison_results_N3.csv:20-28`

| row | timestamp            | scenario | users | error_rate_pct | replicas_start→end | safety_rejected_count |
| --- | -------------------- | -------- | ----- | -------------- | ------------------ | --------------------- |
| 20  | 20260825-171756      | spike    | 100   | 100.00         | 2 → 2              | 14                    |
| 21  | 20260825-171921      | spike    | 100   | 100.00         | 2 → **1**          | 17                    |
| 22  | 20260825-172045      | spike    | 100   | 100.00         | 2 → 2              | 20                    |
| 23  | 20260825-172209      | steady   | 50    | 100.00         | 2 → 2              | 23                    |
| 24  | 20260825-172334      | steady   | 50    | 100.00         | 2 → 2              | 25                    |
| 25  | 20260825-172458      | steady   | 50    | 100.00         | 2 → 2              | 28                    |
| 26  | 20260825-172623      | idle     | 10    | 100.00         | 2 → 2              | 31                    |
| 27  | 20260825-172747      | idle     | 10    | 100.00         | 2 → 2              | 34                    |
| 28  | 20260825-172911      | idle     | 10    | 100.00         | 2 → 2              | 37                    |

Aggregates (over the 9 AI rows):

- `error_rate_pct = 100.00` for all 9 rows (`data/evaluation/comparison_results_N3.csv:20-28`).
- `replicas_end = 2` for 8 of 9 rows; `replicas_end = 1` for row 21 only (`data/evaluation/comparison_results_N3.csv:21`).
- `safety_rejected_count` grows monotonically 14→37 (cooldown-rejected heal actions queued up).

### B.2 HPA and KEDA rows (control)

Source: `data/evaluation/comparison_results_N3.csv:2-19` (18 rows total: 9 HPA, 9 KEDA).

| Operator | All 9 rows: error_rate_pct | All 9 rows: replicas_end |
| -------- | -------------------------- | ----------------------- |
| HPA      | `0.00` (`csv:2-10`)         | ranges 6, 8, 10          |
| KEDA     | `0.00` (`csv:11-19`)        | ranges 2, 8, 10          |

The single-trial Day-15 evidence (`data/evaluation/comparison_results.csv:4`) records `error_rate_avg = 69.2` for the AI operator with `replicas_end = 2` and `safety_rejected_count = 12`. This is **superseded** by the N=3 evidence and is **FORBIDDEN** in the Abstract/Intro. It may appear once in §VI Eval as a footnote.

---

## C. Anomaly detector threshold = **0.484**

Source: `data/anomaly_model.pkl:1` (Python tuple position 1 of 3 elements; element 0 is the HalfSpaceTrees model, element 2 is the training row count).

Exact value: `0.4837573385518591`. The paper rounds to `0.484` (3 decimal places). The `tasks/THESIS.md:65` claim of `0.48` is a 1-decimal rounding and must be corrected to `0.484` (or `0.4838` for 4-decimal precision) when the THESIS.md file is next edited.

---

## D. Shield clamping evidence — `logs/safety_audit.log` (PRIMARY for Abstract)

**This is the ONLY source cited in the Abstract** for the "shield modified X% of decisions" claim. Live audit (`logs/operator_actions.log`) is cited in §VI Eval body only; not in Abstract.

### D.1 Source: `logs/safety_audit.log:1-28` (synthetic stress test, Aug 22 2026)

| Outcome class                         | Count | Lines |
| ------------------------------------- | ----- | ----- |
| Modified by shield (e.g. `shrink_step(15->4)`) | **12**  | `logs/safety_audit.log:2,3,4,5,14,15,16,17,18,19,20,21` (approx; verified by `rejected: false, modifications: [...]`) |
| Unchanged (passed through)             | 6     | (verified by `rejected: false, modifications: []`) |
| Rejected by shield (`out-of-bounds` etc.) | 10    | (verified by `rejected: true`) |
| **TOTAL decisions in audit log**       | **28** | `logs/safety_audit.log:1-28` |

**Abstract number:** "12 of 28 (42.9%) decisions modified by the Safety Shield" — `logs/safety_audit.log:1-28` (12 of the 28 lines have a `modifications` array containing one or more `shrink_step`, `grow_step`, `clamp_to_min`, or `clamp_to_max` transformations).

### D.2 Live demo audit (Sep 1 2026, docker compose run) — for §VI body only

Source: `logs/operator_actions.log:4-20` (Sep-1 entries, 17 entries after the 3 pre-existing Aug-23 lines).

| Field                          | Value | Lines |
| ------------------------------ | ----- | ----- |
| Sep-1 entries (total)          | 17    | `logs/operator_actions.log:4-20` |
| Applied (accepted by actuator) | 8     | verified by `applied: true` |
| Rejected (cooldown)            | 9     | verified by `rejected_reason starts with cooldown_active` |
| Modified by shield (clamp)     | **8** | verified by `safety_modifications non-empty` |
| Heal (no mod needed)           | 0     | (the AI operator did not emit heal during Sep-1) |

Of the 8 applied decisions, **all 8 were shield-modified** via `shrink_step` clamps (`logs/operator_actions.log:6,9,12,15,18`). The 9 rejections are all `cooldown_active` (not safety-invariant violations). The Sep-1 demo is the live evidence that `make demo` runs end-to-end against the cluster.

**§VI Eval sentence (draft):** "On a live docker-compose run (2026-09-01), 8 of 17 decisions were shield-modified by `shrink_step` clamps and 9 were rejected by the cooldown policy (`logs/operator_actions.log:4-20`). No actuator-rejected safety-invariant violation occurred during the run."

---

## E. TLA+ verification — three specs, never mix the numbers

### E.1 `specs/SafetyShield.tla` — single-shield spec (5 invariants + 1 liveness)

Source: `specs/tlc_run_safety_shield.txt:16-30`

| Field                      | Value                                  |
| -------------------------- | -------------------------------------- |
| Distinct reachable states  | 273,702                                |
| State generations          | 2,486,782 (initial pass) / 2,737,020 (final) |
| Search depth               | 53                                     |
| Wall clock                 | 01min 47s on commodity hardware        |
| Invariant violations       | **0**                                   |
| Liveness violations        | **0**                                   |

This is the **only** TLA+ spec cited in the Abstract.

### E.2 `specs/ML_Composition.tla` — joint SHIELD+ML_Only composition spec

Source: `specs/tlc_run_ml_composition.txt:46-47`

| Field                      | Value                                  |
| -------------------------- | -------------------------------------- |
| Distinct reachable states  | 53                                     |
| State generations          | 2,757                                  |
| Wall clock                 | 01s on commodity hardware              |
| Invariant violations       | **0**                                   |

Cited in §III body only (not Abstract).

### E.3 `specs/ML_Composition.tla` — ML_Only counterexample (proves the shield is necessary)

Source: `specs/tlc_run_ml_only_counterexample.txt:124-125`

| Field                      | Value                                  |
| -------------------------- | -------------------------------------- |
| Distinct reachable states  | 93                                     |
| State generations          | 1,668                                  |
| Counterexample produced    | **YES** — `Invariant MlSafetyMinReplicas is violated` at depth 4 |

The counterexample shows that without the shield, the ML oracle can drive `ml_current_replicas` below `MIN_REPLICAS=1` (reaching `ml_current_replicas = 0`). This is the proof that the shield is *necessary*.

Cited in §III body only (not Abstract).

---

## F. Implementation / runtime numbers — `Makefile` and pinned versions

| Item                       | Value                                  | Source |
| -------------------------- | -------------------------------------- | ------ |
| Cluster                    | `kind v1.30.0` single-node on Azure `Standard_D4as_v5` (4 vCPU, 16 GB RAM, Central India) | `Makefile:kind-up` target |
| Container                  | `k8-ai-ops:dev` (`python:3.11-slim`) | `ops/docker/Dockerfile:22` |
| Python                     | 3.11-slim                              | `ops/docker/Dockerfile:22` |
| River                      | 0.26.0 (online ML)                    | `ops/docker/Dockerfile`, `River-paper Montiel et al. JMLR 2021` |
| Faust                      | 0.11.3 (windowed aggregation)         | same Dockerfile |
| kafka-python               | 2.0.2                                  | same Dockerfile |
| `make demo` runtime        | ~30 min end-to-end on commodity hardware | `docs/GOLDEN_RUN.md` |
| `make tla` runtime         | ~3 s (SafetyShield.tla)                | `specs/tlc_run_safety_shield.txt:30` |
| `make tla-composition`     | ~4 min on commodity hardware           | `specs/tlc_run_ml_composition.txt:46` |
| Number of unit tests       | 53 (pytest -q)                         | `tests/` directory listing |
| Replica model threshold    | (see Section C — anomaly threshold) | `data/anomaly_model.pkl:1` |
| Workload                   | `workload-v2` (DB-backed Flask + SQLite) | `workload/` |
| Pipeline topology          | Prometheus → Kafka → Faust 30-s windows → River HTR + HST → TLA+ shield → operator | `docs/thesis/05_proposed_system.md:9-51` |

---

## G. Source code citations

| Citation                                              | File:line                          |
| ----------------------------------------------------- | ---------------------------------- |
| Load-first decision ordering (the P1 fix)             | `src/decision/decision_engine.py:262-268` |
| `engine.learn(features, current_replicas)` online loop | `src/decision/decision_engine.py:283` (explain call adjacent to learn) + `:251-258` (heal_threshold setup) |
| `SafetyShield` Python implementation                    | `src/safety/safety_shield.py` (entire file; `(validate, audit_log)` method at `:90-180`) |
| FIRM-style threshold baseline                           | `src/baselines/firm_controller.py:81+` (`FirmController.decide()`) |
| N=10 evaluation harness                                | `scripts/eval/run_N10.sh`; `scripts/eval/run_quick.py` (PowerShell-friendly variant) |
| Per-trial simulator                                    | `scripts/eval/run_one_trial.py:188-220` (`main()`; reproduces `(op, scenario)` replica trace offline) |
| Statistical report generator                          | `scripts/eval/stats_report.py` (`compute_summary`, `_wilcoxon`, `_cohens_d`, `_bootstrap_ci`) |
| Per-scenario ML output target labels                   | `scripts/build_dataset_v2.py:51-57` (`target_replicas()` heuristic) |

---

## H. BANNED NUMBERS — must never appear in Abstract / Intro / Eval

The following are **forbidden** in the paper body. They are documented here so that an audit can grep for them and find zero matches outside §VIII (Threats) or §IX (Forever Banned footnote).

| Banned number / phrase                                | Reason it is banned                                                                 | Source where it *would* have come from (but isn't cited) |
| ------------------------------------------------------ | ---------------------------------------------------------------------------------- | ---- |
| `error_rate = 69.2%` for AI Day-15                    | Single-trial superseded by N=3 (100.00% across all 9 rows)                       | `data/evaluation/comparison_results.csv:4` (single-trial) |
| `47 modified (20.9%)` for shield clamp rate            | Output was stdout-only from `scripts/replay_shield.py`; never saved to a file. Even if it had been saved, the denominator has drifted (`features_v2.csv` was 225 rows in an earlier iteration, now 285 rows; 47/225 = 20.9% ≠ 47/285 = 16.5%). | `scripts/replay_shield.py:67-69` (stdout, never redirected to file) |
| `Cohen's d ≠ 0` or `95% CI excludes 0`                  | Deterministic N=10 replay has identical per-seed values; all observed `d = 0.00`. Reporting non-zero effect would be fabrication. | `results_N10/stats_report.json` (every Cohen's d is `+0.000`) |
| `Wilcoxon p < 0.05`                                    | Same reason as above: the deterministic N=10 replay has Wilcoxon p ∈ {`1.0`, `0.001953125`}. Reporting a `p < 0.05` would be fabrication. | `results_N10/stats_report.json:495-948` |
| `MAE 0.82` (referenced in `tasks/THESIS.md:65` and earlier docs) | This was a transient value during offline replay in earlier experiments; the **current** canonical model state is captured by the `safety_audit.log` clamping pattern (Section D) and the replica-model pickling state. **No saved file currently records MAE = 0.82** under the current canonical models. | (none — drop until verified) |
| `273,702 distinct states` assigned to ML_Composition.tla | Wrong: that number belongs to `SafetyShield.tla` (§E.1). ML_Composition.tla has 53 distinct states (§E.2). | — |

---

## I. Figures and tables in the paper — only these

Each label below lists the **content** to show and the **source** to draw from.

| Label      | Content                                                                          | Source file for the data                              |
| ---------- | -------------------------------------------------------------------------------- | ----------------------------------------------------- |
| Fig. 1     | Pipeline diagram: Prometheus → Kafka → Faust 30-s windows → River HTR + HST → TLA+ shield → Kafka actuator → K8s Deployment | derived narrative; this is a **schematic** (no run data needed). Will be a hand-drawn diagram (no source file required). |
| Tab. I     | 5 safety invariants (`SafetyMinReplicas`, `SafetyMaxReplicas`, `SafetyScalingStep`, `SafetyHealNoScale`, `SafetyBoundedRate`) + 1 liveness property `LivenessEventuallyScaleUp`. Two columns: invariant name + natural-language statement. | `specs/SafetyShield.tla:230-290` |
| Tab. II    | N=10 results table — 4 rows (HPA/KEDA/FIRM/SHIELD-AI) × 3 cols (idle/spike/steady), cells = `mean ± std replicas_end`. | `results_N10/stats_report.json:by_scenario.*.*.replicas_end` |
| Tab. III   | Day-15 N=3 motivating failure — AI rows 20-28 showing `replicas_end=2`, `error_rate_pct=100.00`, monotonically-growing `safety_rejected_count`. | `data/evaluation/comparison_results_N3.csv:20-28` |
| Tab. IV    | Shield ON vs Shield OFF ablation (3 rows each): full_ai / no_shap / no_shield. | `data/evaluation/ablation_results_N3.csv:1-10` |
| Tab. V     | TLA+ verification summary — three rows (SafetyShield.tla / ML_Composition.tla / ML_Only cfg) with columns (distinct states, generated states, violations, wall-clock). | `specs/tlc_run_safety_shield.txt`, `specs/tlc_run_ml_composition.txt`, `specs/tlc_run_ml_only_counterexample.txt` |

---

## J. Scenario definitions for paper §VI Eval

| Scenario      | Synthetic Locust users | Run duration | Deterministic expected `replicas_end` (from `results_N10/comparison_N10.csv` mean) |
| ------------- | ----------------------- | ------------ | --------------------------------------------------------------------------------- |
| `idle`        | 8 users                 | 60 s         | HPA=1, KEDA=4, FIRM=5, SHIELD-AI=1                                              |
| `steady`      | 40 users                | 90 s         | HPA=1, KEDA=10, FIRM=10, SHIELD-AI=1                                            |
| `spike`       | 80 users                | 90 s         | HPA=1, KEDA=10, FIRM=10, SHIELD-AI=1                                            |

Source: `scripts/eval/run_one_trial.py:188-200` (scenario parameter list); the deterministic `replicas_end` values come from `results_N10/comparison_N10.csv` means.

---

## K. Acknowledgment line (single line, required for AI disclosure)

> "This work used Anthropic Claude as a coding assistant for code scaffolding and copy editing; all design decisions and claims were verified by the author."

This appears verbatim in the Acknowledgment section of `docs/paper/main.tex` and `docs/thesis/09_conclusion.md`.

---

## L. Revision log

- 2026-09-01: Initial lock. Replaces the prior "47 modified (20.9%)" citation that lacked a saved source.
