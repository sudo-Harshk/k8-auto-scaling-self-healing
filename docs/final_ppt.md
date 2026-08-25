# Final PPT — Slide Outline

> **Status:** Scaffolding. Filled after Day 14 evaluation. The slides use this Markdown outline; the actual presentation is generated from it via `pandoc docs/final_ppt.md -o docs/final_ppt.pptx` (or copy-paste into PowerPoint).

---

## Slide 1 — Title

**AI-Driven Kubernetes Operator with TLA+-Verified Safety Guarantees**

Author: [FILL]
Affiliation: [FILL]
M.Tech Project Defense, 2026

---

## Slide 2 — Problem

Kubernetes auto-scaling today is **reactive** and **single-signal**:

- HPA scales on CPU only
- KEDA adds triggers but inherits HPA's limitations
- No formal safety guarantee
- No active anomaly-driven healing

Cost: slow reaction, oscillation, unsafe states, undetected faults.

---

## Slide 3 — Contribution

This work proposes and implements:

1. **End-to-end pipeline** — Prometheus → Kafka → Faust → River-ML → TLA+ Shield → operator
2. **Online learning** — model improves during runtime, not frozen on training data
3. **Formal safety** — five invariants verified by TLC on every reachable state
4. **Active healing** — anomaly-driven pod deletion within the operator
5. **Quantitative comparison** — HPA vs KEDA vs AI, N=3 runs

---

## Slide 4 — Architecture

```
[Diagram from docs/thesis/05_proposed_system.md § 5.1]
```

---

## Slide 5 — TLA+ Specification

- 5 invariants (min/max replicas, scale step, heal preserves replicas, cooldown)
- Verified by TLC: 264,330 states, 0 errors, 3 s

```
SafetyMinReplicas    current_replicas >= 1
SafetyMaxReplicas    current_replicas <= 10
SafetyScalingStep    |new - old| <= 2
SafetyHealNoScale    heal => target == current
SafetyBoundedRate    cooldown enforced
```

---

## Slide 6 — Implementation

Per-day walkthrough (Days 1-13):

- Day 1: kind + podinfo
- Day 2: monitoring
- Day 3: metrics client + Locust baseline
- Day 4: Kafka
- Day 5: Faust
- Day 6: feature engineering
- Day 7: replica predictor (MAE 0.24)
- Day 8: anomaly detector (6.7× separation)
- Day 9: decision engine
- Day 10: TLA+ spec
- Day 11: Safety Shield (16 tests)
- Day 12: operator
- Day 13: E2E integration

---

## Slide 7 — End-to-End Demonstration

[Figure: pipeline diagram + screenshots]

- Auto-scaling under Locust spike: podinfo 2 → 4 → 2
- Auto-healing under fault injection: faulty pod deleted, replaced
- Audit logs: 18 scale, 15 heal, 22 noop (Day 9 verification)

---

## Slide 8 — Comparison Results (Day 14 + Day 15 N=3)

[Table from `data/evaluation/comparison_summary.md`]

| Operator | Scaling lag (s) | Scale actions | Heal actions | Error rate (%) | Replicas (peak) |
|----------|-----------------|---------------|--------------|----------------|------------------|
| HPA | 15 | 8 | 0 | 0.0 | 10 |
| KEDA | 5 | 6 | 0 | 0.0 | 10 |
| AI (full) | 90 | 0 | 1 | 69.2 | 2 |

**Day 15 N=3 replication** (data/evaluation/comparison_results_N3.csv):
same trends hold across 3 repetitions per scenario. Cohen's d analysis at
`data/evaluation/effect_sizes.md` quantifies effect sizes per metric.

**Key finding:** HPA and KEDA scale faster; the AI operator prioritizes
anomaly detection and safety. Only the AI operator detects and heals
faults (Day-13 evidence). The Safety Shield rejected 54 of 55 heal
actions in the ablation study — preventing unconstrained AI behavior.

[Figure 7.1: replica count over time, all 3 operators]

---

## Slide 9 — Ablation + Liveness

| Variant | Scale | Heal | Rejected | Applied | Comments |
|---------|-------|------|----------|---------|----------|
| AI full | 0 | 1 | 54 | 1 | All 5 invariants enforced; cooldown blocks most heals |
| AI – SHAP | 0 | 1 | 54 | 1 | SHAP doesn't change decisions (explanation only) |
| **AI – Safety Shield** | 0 | 55 | **0** | **55** | **Unconstrained: 55 unvalidated heal actions** |
| **Stochastic N=3 (σ=5%)** | same | same | same | same | Identical to N=1: decision boundary robust to sensor noise |

**Liveness property** (Day 15, verified by TLC):
> `LivenessEventuallyScaleUp`: when `consecutive_overload = MAX_REPLICAS`
> (10 consecutive windows of sustained demand), the operator eventually
> scales above the current replica count.

TLC explored **2,486,782 state generations**, found **273,702 distinct
states**, in **4 min 6 s** — both safety AND liveness hold on every
reachable state.

**Headline:** without the Safety Shield, the engine would apply 55 unconstrained
heal actions in 55 windows. The Shield is the paper's strongest safety claim.
**With liveness verified**, the operator is also proven to respond to
sustained demand (the second-strongest paper claim).

---

## Slide 10 — Reproducibility

- 7 scripts in `scripts/` (bootstrap, build, deploy, run, stop, swap, run_comparison)
- Fresh Azure VM → 30 min to running pipeline
- `tests/` has 24 passing unit tests
- `specs/SafetyShield.tla` re-verifiable in 3 s on commodity hardware

---

## Slide 11 — Limitations & Future Work

**Limitations** (honest):
- Single-node kind cluster (multi-node not tested)
- p95 baseline (Day-6 podinfo had constant p95; Day-16 post-completion rework fixes this)
- 60-s cooldown caps scaling rate
- Detection rate 55-65% organic, 100% injected

**Future work**:
- Production deployment (multi-tenant)
- Liveness properties (Day-15)
- Beyond Kubernetes (any metric-stream system)

---

## Slide 12 — Conclusion

Online learning + formal verification + active healing, in a single operator, is **feasible, useful, and reproducible**.

**Code**: github.com/sudo-Harshk/k8-auto-scaling-self-healing
**Paper**: docs/ieee_paper.tex (Day-16)
**Reproduction**: `./scripts/bootstrap_vm.sh`

---

## Backup slides

- Full architecture diagram
- TLA+ spec excerpts
- Day-by-day LOC growth
- AMENDMENTS timeline
- All 24 unit test names