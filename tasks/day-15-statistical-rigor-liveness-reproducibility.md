# Day 15 — Statistical Rigor, Liveness & Reproducibility

## Task
Strengthen the paper with statistically rigorous evaluation (N=3 runs), add a liveness property to the TLA+ spec, retrain the anomaly detector on a larger dataset, and ship the full reproducibility script bundle.

## Aim
Move the paper from workshop-quality to real conference-quality (SCC, ICSOC, NCA tier).

## Why this day exists

Day 14 delivered a single-run 3-way comparison. Single-run is anecdotal; reviewers expect statistics. This day closes the rigor gap and adds a second TLA+ property (liveness) — the second-strongest paper claim after safety.

## Steps

1. **Statistical rigor — N=3 runs**
   - Re-run all 9 scenario × operator combinations (HPA / KEDA / AI × spike / steady / idle) × 3 repetitions
   - Capture mean ± std for: scaling lag, total actions, p95 latency, error rate, replica count at end
   - Compute effect size (Cohen's d) between AI and HPA, AI and KEDA
   - Output: `data/evaluation/comparison_results_N3.csv`

2. **Liveness in TLA+**
   - Add `LivenessEventuallyScaleUp` property to `specs/SafetyShield.tla`:
     > "If `predicted_replicas > current_replicas` for `>= 2 consecutive windows`, then eventually a `scale-up` decision is emitted before `next_window` elapses."
   - Run TLC, expect counterexamples initially; refine spec
   - Re-verify all 5 safety invariants still hold
   - Document in `docs/SafetyShield.md` Section 7 (currently says "liveness is future work")
   - Add unit test in `tests/test_safety_shield.py` for liveness simulation

3. **Larger training set + retrained detector**
   - Concatenate Day-6 dataset + Day-13 evaluation windows + Day-14 N=3 windows
   - Retrain anomaly detector on the combined set
   - Measure new organic detection rate (target: 65%+ vs Day-8's 55%)
   - Commit updated `data/anomaly_model.pkl`

4. **Better ablation (Day-14 was 1 run; Day-15 is N=3)**
   - For each ablation variant (full AI, –SHAP, –Shield): 3 runs each
   - Add variant: AI with liveness property (after step 2)

5. **Reproducibility scripts**
   - `scripts/bootstrap_vm.sh` — install Docker, kind, Helm, Java, tla2tools
   - `scripts/build_image.sh` — rebuild `k8-ai-ops:dev`
   - `scripts/deploy_infra.sh` — apply podinfo, monitoring, kafka, HPA, KEDA
   - `scripts/run_pipeline.sh` — start producer + Faust + engine + operator
   - `scripts/stop_all.sh` — cleanup
   - `scripts/swap_operator.sh` — disable/enable HPA/KEDA/AI in turn

6. **Documentation update**
   - AMENDMENTS entries for: N=3 results, liveness property, retrained detector, new scripts
   - Day-15 execution notes in `tasks/day-15-*.md`
   - Cumulative table update in `milestones/MILESTONES.md`

## Outcome

- `data/evaluation/comparison_results_N3.csv` with 27 rows (3 ops × 3 scenarios × 3 runs)
- Liveness property verified by TLC in `specs/SafetyShield.tla`
- Retrained `data/anomaly_model.pkl` with documented detection rate improvement
- 6 reproducibility scripts in `scripts/`
- All artifacts committed, VM synced

## Verification

- [ ] N=3 results show statistically meaningful difference (or honest "no significant difference" with discussion)
- [ ] TLC reports "No error has been found" after liveness property added
- [ ] Updated detection rate > Day-8's 55%
- [ ] All scripts run end-to-end on a fresh VM
- [ ] 24 unit tests + new liveness test all pass

## Time estimate: 8 hours

## Risk register

| Risk | Mitigation |
|------|-----------|
| N=3 runs take too long | Compress scenarios to 2 min each; total wall time ~ 2 hours |
| TLC finds counterexample for liveness | Budget 1 hour for spec refinement; if unfixable, drop liveness and document why |
| Anomaly detector retrain doesn't improve | Document the result; the 55% organic / 100% injected split is still defensible |
| Reproducibility scripts fail on fresh VM | Test on the existing VM first, fix, then verify on fresh container |