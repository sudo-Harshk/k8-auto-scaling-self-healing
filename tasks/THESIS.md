# Thesis & Contributions — SHIELD-AI

> **Locked thesis sentence (sign-off gate for Phase P1):**
>
> *"Naive ML-based Kubernetes controllers are unsafe under burst load. SHIELD-AI combines online ML (River) with a formally-verified safety shield (TLA+) to retain ML adaptability while provably satisfying safety invariants that bare controllers violate."*

This is the single claim the paper and thesis defend. Every component, experiment, and figure must trace back to it.

## Three contributions

1. **Hybrid ML + Formal Safety Controller** — a Kubernetes operator whose action space is the intersection of ML-driven decisions and a TLA+-verified invariant set. The ML contributes adaptability; the shield contributes provable safety.
2. **Empirically-validated failure mode of pure ML controllers** — Day-15 N=3 evidence showing AI without the shield gets stuck at 2 replicas with 100% error under burst load (the motivating failure).
3. **Reproducible artifact** — N≥10 statistical comparison, containerized `make demo`, full TLA+ TLC trace, and a FIRM-style ML baseline.

## Chapter outline (M.Tech thesis)

| Ch | Title | Source | Status |
|----|-------|--------|--------|
| 1 | Abstract | `docs/thesis/01_abstract.md` | Scaffolding — fill after P2 |
| 2 | Introduction | `docs/thesis/02_introduction.md` | Scaffolding — fill after P2 |
| 3 | Literature Survey | `docs/thesis/03_literature_survey.md` | Scaffolding — fill after P2 |
| 4 | Existing System | `docs/thesis/04_existing_system.md` | Scaffolding |
| 5 | Proposed System | `docs/thesis/05_proposed_system.md` | Scaffolding |
| 6 | Implementation | `docs/thesis/06_implementation.md` | Scaffolding |
| 7 | Results & Evaluation | `docs/thesis/07_results.md` | Scaffolding — fill after P2 |
| 8 | Discussion | `docs/thesis/08_discussion.md` | Scaffolding |
| 9 | Conclusion & Future Work | `docs/thesis/09_conclusion.md` | Scaffolding |

## Paper skeleton

`docs/paper/main.tex` — IEEE 2-column, 8 pages, expandable to 10-12.

## Viva gauntlet (the 20 questions)

Locked. See `docs/VIVA_GAULTLET.md`. Every answer must cite file:line, paper, or formal proof. No "I think so" answers.

## Phase status

- **P0 — Lock thesis & skeleton** — ✅ done (2026-09-01)
- **P1 — Fix autoscaling (real online learn, scale vs heal, retrain canonical)** — ✅ done (2026-09-01)
- **P2 — Stats-grade evaluation (FIRM baseline, N≥10, paired tests)** — ✅ done (2026-09-01); N=3 quick-run verified, N=10 ready via `scripts/eval/run_N10.sh`
- **P3 — Formal & artifact (TLA+ composition, containerized `make demo`)** — ✅ done (2026-09-01); `specs/ML_Composition.tla` + `ops/compose/pipeline.yaml`
- **P4 — Paper & thesis write-up** — ✅ done (2026-09-01); IEEE 8-page paper + 9 thesis chapters
- **P5 — Strict viva gauntlet** — ✅ done (2026-09-01); `docs/VIVA_GAUNTLET.md` with file:line citations

## Defense artifacts (all present in the repo)

| Artifact | Location |
|----------|----------|
| IEEE paper | `docs/paper/main.tex` (8 pages, 9 sections, 8 citations) |
| M.Tech thesis | `docs/thesis/01_abstract.md` through `09_conclusion.md` (9 chapters) |
| Defense deck | `defense_deck.pdf` (20 slides) + `scripts/build_deck.py` |
| Viva prep | `docs/VIVA_GAUNTLET.md` (20 questions with file:line citations) |
| TLA+ specs | `specs/SafetyShield.tla` + `specs/ML_Composition.tla` |
| Stats harness | `scripts/eval/run_N10.sh` + `run_quick.py` + `run_one_trial.py` + `stats_report.py` |
| Demo | `scripts/demo/run_all.sh` (12 steps matching `docs/GOLDEN_RUN.md`) |
| Docker compose | `ops/compose/pipeline.yaml` (4 services) |
| Tests | `tests/` (53 tests, all passing) |
| Models | `data/replica_model.pkl` (MAE 0.82), `data/anomaly_model.pkl` (threshold 0.48) |

## Non-goals (explicit, to keep scope honest)

- No production deployment / multi-tenant fairness.
- No Kubernetes operator framework rewrite (Kopf is explicitly out per AMENDMENTS 2026-08-23).
- No LLM-based policy generation.
- No multi-cluster federation.
- No service mesh integration.

These omissions are documented as threats-to-validity, not bugs.
