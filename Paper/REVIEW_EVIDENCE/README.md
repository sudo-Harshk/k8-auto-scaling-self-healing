# Evidence for the Response to Reviewer: SHIELD-AI revision

For every reviewer point this file gives:
- **Answer**: what the revised paper says.
- **Evidence**: the file in this folder that proves it.
- **How it was produced**: the exact command or procedure, so anyone can re-run it.

Repository: `sudo-Harshk/k8-auto-scaling-self-healing`, branch `paper-revision-eval`.
Paths below are relative to this folder (`Paper/REVIEW_EVIDENCE/`) unless they start with a repo path.

Environment used:
- **Formal verification and unit tests:** local Windows laptop, Python 3, Java + `tools/tla2tools.jar` (TLA+ tools v1.8.0).
- **Live experiments:** two Azure VMs, both 4 vCPU / 16 GB RAM / Ubuntu 24.04 but different types: VM A = Standard_D4as_v4, VM B = Standard_D4ads_v7. The hardware effect is disclosed in the paper and handled by a per-seed analysis (`04_live_experiments/analysis/ROBUSTNESS.md`).
  - VM A ran seeds 1–3; VM B ran seeds 4–5.
  - Both used the same code commit (`9c9744d`), the same calibration file and the **byte-identical trained model files**. VM B's repo was copied from VM A.
  - Robustness script: `python scripts/eval/live/robustness.py results_live/analysis/per_run_metrics.csv ROBUSTNESS.md`
- **Cluster on each VM:** kind v1.30, 1 control plane + 3 workers (`scripts/eval/live/kind-eval.yaml`).

---

## Section A: Evaluation (baselines, workloads, metrics, repetition, statistics, ablation)

| # | Reviewer point | Answer | Evidence | How it was produced |
|---|---|---|---|---|
| A1 | No comparison with HPA / KEDA / FIRM | 5 controllers compared live: HPA, KEDA, MT (FIRM-inspired threshold controller), ML-only, SHIELD-AI (ML+shield) | `04_live_experiments/RESULTS.md`, `04_live_experiments/runs/*` | `SEEDS="1 2 3" bash scripts/eval/live/run_matrix.sh` (VM A), `SEEDS="4 5" …` (VM B), then `python scripts/eval/live/analyze.py` |
| A2 | Workloads not described | `spike`, `diurnal` and `bursty` Locust shapes with seeded ±15 % noise. Training uses a separate `train` random walk, disjoint from the tests. | repo `scripts/eval/live/locust_scenarios.py` | Load generator runs as a pod inside the cluster (`lib.sh: run_load`) |
| A3 | Metrics undefined | SLO violation % (p95 > 250 ms per 5 s window), error %, mean replicas (cost proxy), scaling actions, oscillations | repo `scripts/eval/live/analyze.py` (definitions in code) and paper §Evaluation | Computed from Locust `run_stats_history.csv` and the 5 s `replicas.csv` sampler |
| A4 | Non-determinism: repeated runs | N = 5 seeds × 3 scenarios × 5 controllers = 75 live runs, executed in randomised order | `04_live_experiments/runs/<scenario>__<controller>__s<seed>/` (one folder per run) | `run_matrix.sh` shuffles the order and marks each finished run with a `DONE` file |
| A5 | Statistics | Mann–Whitney U (two-sided), Holm-corrected; Cliff's δ effect size; mean ± sd | `04_live_experiments/RESULTS.md` (stats tables) | `analyze.py` |
| A6 | Ablation (ML-only vs ML+shield) | `ml-only` = same model and same pipeline with the shield disabled (`NO_SHIELD=1`) | `04_live_experiments/RESULTS.md`, ablation rows | repo `src/kopf_operator/actuator.py` (`NO_SHIELD` env), `lib.sh` line 94 |
| A7 | Old N=10 / v1 results | The old N=10 table was an **offline deterministic replay**, not live runs. The v1 live AI runs had 100 % errors. These are disclosed honestly and replaced. | `07_old_v1_evidence/comparison_results_N3.csv` (rows 20–28: AI 100 % error, HPA/KEDA 0 %) | Original v1 data, copied unchanged from `data/evaluation/` |
| A8 | Capacity and SLO basis | One 25m-CPU pod serves 104.8 rps within SLO. Scaling target = 60 % of that = 62.9 rps/replica; peak load 1006 rps (≈16 replicas). | `03_calibration_training/calibration/calibration.env`, `run_stats_history.csv` | `bash scripts/eval/live/calibrate.sh` (staircase 15→150 rps, 30 s steps, against 1 replica) |
| A9 | ML model quality | Predictor prequential MAE 3.22 replicas vs 6.31 for the naive last-value baseline (87 training windows). Anomaly threshold = p99 of training scores. | `03_calibration_training/model_report.json` | `bash scripts/eval/live/train_ml.sh` → `train_ml.py finalize` |

## Section B: Consistency and correctness of claims

| # | Reviewer point | Answer | Evidence | How it was produced |
|---|---|---|---|---|
| B1 | CPS leftovers | Removed | `Paper/SHIELD_AI_revised.md` | Manual edit |
| B2 | Flink vs Faust | Faust throughout, matching the code | repo `src/streaming/stream_processor.py` (Faust app) | Code inspection |
| B3 | 6 vs 5 layers | 5 layers throughout | `Paper/SHIELD_AI_revised.md` §Architecture | Manual edit |
| B4 | Cooldown `% 11 ≥ 6` units | Replaced by explicit seconds: up 15 s, down 60 s. The same rule appears in the TLA+ model (`COOLDOWN_UP/DOWN`), the policy and the code. | `01_formal_verification/safety_policy_v2.yaml`, `SafetyShieldV2.tla` | Manual edit + tests in `02_tests` |
| B5 | "17 decisions/min" | Wrong. The log shows 17 decisions in ≈8 min ≈ 2.1/min. | repo `logs/` v1 decision log timestamps; see `Paper/REVIEW_ANSWERS.md` | Timestamp difference first→last decision |
| B6 | 273,702 states vs 28 proposals | Different things. 273,702 = states explored by TLC for the **v1** model. 28 = hand-made proposals in a Python stress audit. | `07_old_v1_evidence/tlc_run_v1_273702_states.txt`; `06_audit_recount/` | TLC output; audit log |
| B7 | 28-audit contradiction | Recount: **12 modified, 10 rejected (9 cooldown, 1 delete_pod), 6 passed → 22/28 corrected**, not "all 28" | `06_audit_recount/recount_output.txt` | `python recount_audit.py safety_audit_first28.log` (input = first 28 lines of repo `logs/safety_audit.log`) |
| B8 | 9/17 rejections are throttling | Stated openly: 9 were cooldown rejections | same as B7 | same as B7 |
| B9 | 100 % error claim cites internal report | Internal report removed. The data is shown directly, with root causes (label collapse to identity, a no-op that reset the cooldown, stale replica count, port-forward pinning) | `07_old_v1_evidence/comparison_results_N3.csv` | — |

## Section C: Formal verification (TLA+)

| # | Reviewer point | Answer | Evidence | How it was produced |
|---|---|---|---|---|
| C1 | Weak / trivial invariants | v1 had two trivial ones (`current_replicas ∈ 1..MAX`, `clock ≥ 0`). v2 treats the ML as **untrusted** (any output 0..25) and checks 5 invariants + 2 action properties. **No error found; 2,535,840 distinct states, depth 28.** | `01_formal_verification/tlc_run_v2_safety.txt` | `java -cp tools/tla2tools.jar tlc2.TLC -config SafetyShieldV2_safety.cfg SafetyShieldV2.tla` |
| C2 | Liveness | `LivenessEventuallyScaleUp` holds under fairness: 234,639 states | `01_formal_verification/tlc_run_v2_liveness.txt` | same, with `-config SafetyShieldV2_liveness.cfg` |
| C3 | Do the properties have teeth? | Mutation test: 7 mutants, each disabling one shield rule. **All 7 detected**, each by the property it targets. | `01_formal_verification/tlc_run_v2_mutants.txt` | Each rule removed in turn, then TLC re-run (log contains every run) |
| C4 | Model ↔ code conformance | 12 v2 unit tests check the Python shield against the same policy. Full suite: **65 passed**. | `02_tests/pytest_output.txt`; repo `tests/test_safety_shield_v2.py` | `python -m pytest tests -q` |
| C5 | Overhead | Shield validation: median 0.35 ms, p99 0.71 ms (laptop) | `05_shield_overhead/shield_overhead_laptop.json` | `python bench_shield.py` |

## Section D: References

| # | Reviewer point | Answer |
|---|---|---|
| D1 | Internal files cited | Removed (e.g. `synthetic_stress_audit.py` and `verify_evidence_freeze.py` were cited but **do not exist** in the repo) |
| D2 | FIRM misattributed | Qiu et al., "FIRM: An Intelligent Fine-grained Resource Management Framework for SLO-Oriented Microservices", OSDI 2020; RL-based. Our baseline is honestly labelled *FIRM-inspired threshold controller*. |
| D3 | Bad DOI [20] | Fixed |
| D4 | Unrelated self-citations [21]–[23] | Removed |
| D5 | Uncited references | Removed or cited |

## Section E: Writing and missing sections

Threats to Validity added, Section VI numbering fixed, ethics section rewritten without first person, repository link added, TLA+ listing added, all tables and figures added. See `Paper/SHIELD_AI_revised.md`.

---

## Known limitations (stated in the paper, not hidden)
1. The anomaly threshold is the p99 of training scores with a 2× gate. In the scaling experiments **no heal action fired**, so the self-healing path is verified formally and by unit tests, not by these live runs.
2. MT is a FIRM-*inspired* threshold controller, not the original RL-based FIRM.
3. The live cluster is kind on one VM per seed group. Absolute latencies are not production numbers; the comparison between controllers is fair because all five ran under identical conditions.

---

## Section F: Items added in the second pass (figures/tables list of the review)

| # | Reviewer item | Answer | Evidence | How it was produced |
|---|---|---|---|---|
| F1 | "Min replica rule alone is not responsible for 25 proposals" is unclear | Withdrawn. Per-rule counts: step 11, min 1 (with step), max 0, heal 1, cooldown 9, unknown action 1, passed 6 (paper Table IV) | `06_audit_recount/recount_output.txt` (last line) | `python recount_audit.py safety_audit_first28.log` |
| F2 | Python enforcement code and TLC configuration not shown | Paper Listings 1–3 | `01_formal_verification/SafetyShieldV2_safety.cfg`; repo `src/safety/safety_shield.py` | — |
| F3 | ML accuracy table | Paper Table IX | `03_calibration_training/model_report.json`, `08_anomaly_detector/anomaly_roc.json` | see F4 |
| F4 | Anomaly ROC/PR + threshold justification | ROC-AUC 0.806, AP 0.950; p99 threshold → precision 1.00, recall 0.22, FPR 0.00. **Heal gate 2×thr ≈ 1.8 is unreachable (HST scores ∈ [0,1]); max live score 0.995 in 1,138 decisions → no heal could fire.** Disclosed in paper §VI-E. | `08_anomaly_detector/` (JSON + figure) | `python scripts/eval/live/anomaly_roc.py data/features_v2.csv results_live/anomaly_eval` (train on first 60 % of normal windows, test on rest + all abnormal) |
| F5 | Kafka / latency overhead of the shield | Decision→actuation median 529 ms with shield vs 537 ms without (applied changes); shield check 55 µs | `09_pipeline_overhead/pipeline_latency.json`, `05_shield_overhead/shield_overhead_vm.json` | `python scripts/eval/live/pipeline_latency.py results_live/runs out.json` (matches each actuator entry to the latest decision; same host clock) |
| F6 | More than 10 replicas / multi-node | 4-node cluster, replicas 2–20; spike peaks 16–20 replicas | `04_live_experiments/analysis/per_run_metrics.csv` (`max_replicas`) | — |
| F7 | Old Figs. 2–4 with unreadable source notes | Removed; replaced by Listings 1–3, Table IV and live data | — | — |

## Section G: Self-healing study (fault injection)

| # | Question | Answer | Evidence | How it was produced |
|---|---|---|---|---|
| G1 | Does self-healing work live? | Localisation yes, recovery no. 10 heals in 15 fault runs, all on the frozen pod; 0 false heals in 15 fault-free runs. Pre-registered recovery test null (18 s vs 17 s, p = 0.95) | `10_self_healing/heal_analysis/HEAL_RESULTS.md`, `heal_per_run.csv`, `PREREGISTRATION.md` | `run_heal.sh` on VM B (seeds 1–5: 35 runs; extension seeds 6–15: heal and no-heal fault arms), then `python scripts/eval/live/analyze_heal.py results_live/heal_runs results_live/heal_analysis` |
| G2 | Does the anomaly detector trigger healing? | No: with the anomaly gate, 0/5 heals; an aggregate score does not see a single-pod fault | same, row "heal, anomaly-gated" | same |
| G3 | Is recovery faster with healing? | No. Mann–Whitney p = 0.95; still degraded at end 1/15 vs 4/15 (Fisher p = 0.33). Cause: ReplicaSet scale-down deletes unready pods first (frozen pod removed in 9/15 no-heal runs) | `heal_analysis/HEAL_RESULTS.md` (section "Pre-registered test"), run `events.txt` | pre-registered tests in `analyze_heal.py` |
| G5 | Failed injections | 5 runs froze no pod (target pod was terminating); excluded and repeated after a script fix | `results_live/heal_runs_invalid/`, `PREREGISTRATION.md` (deviation log), `heal2_main.log` | — |
| G4 | Figure | Fig. 5 | `10_self_healing/fig_heal.png` | `python Paper/figures/make_fig_heal.py` |

Raw run folders: `results_live/heal_runs/<arm>__f<fault>__s<seed>/` (Locust stats, decision/actuator logs, `fault.json`, `pods_end.json`, `events.txt`).

## Note
The raw folders of the 75 runs are committed once, at `results_live/runs/` (the local copy in `04_live_experiments/runs/` is not duplicated in git).
