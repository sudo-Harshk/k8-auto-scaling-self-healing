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

## Slide 8 — Comparison Results (Day 14)

[Table from `data/evaluation/comparison_summary.md`]

| Operator | Scaling lag (s) | p95 latency (ms) | Heal time (s) | Unsafe actions |
|----------|-----------------|------------------|---------------|----------------|
| HPA | TBD | TBD | TBD | TBD |
| KEDA | TBD | TBD | TBD | TBD |
| AI (full) | TBD | TBD | TBD | 0 |

---

## Slide 9 — Ablation

| Variant | Scaling lag | Heal time | Comments |
|---------|-------------|-----------|----------|
| AI full | TBD | TBD | All 5 invariants enforced |
| AI – SHAP | TBD | TBD | Raw decision engine output |
| AI – Safety Shield | TBD | TBD | No invariants enforced |
| AI + liveness (Day-15) | TBD | TBD | New liveness property added |

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