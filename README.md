# SHIELD-AI — A Formally-Verified Online Learning Controller for Kubernetes Auto-Scaling and Self-Healing

M.Tech project: a formally-safe autonomous Kubernetes controller that unifies
online-machine-learning auto-scaling and auto-healing behind a
TLA+-verified Safety Shield. Built across 18 days; verified end-to-end on a
live `kind` cluster on Azure (`Standard_D4as_v5`, Ubuntu 24.04 LTS, cgroup v2,
Central India).

## Thesis (locked)

> **Naive ML-based Kubernetes controllers are unsafe under burst load.
> SHIELD-AI combines online ML (River Hoeffding Adaptive Tree Regressor +
> Half-Space-Trees anomaly detection) with a formally-verified safety
> shield (TLA+ / TLC) to retain ML adaptability while provably satisfying
> safety invariants that bare controllers violate.**

## Three contributions

1. **Hybrid ML + Formal Safety Controller** — a Kubernetes operator whose
   action space is the intersection of ML-driven decisions and a
   TLA+-verified invariant set. ML contributes adaptability; the shield
   contributes provable safety.
2. **Empirically-validated failure mode of pure ML controllers** —
   the Day-15 N=3 replication in
   `data/evaluation/comparison_results_N3.csv:20-28` shows the ML-only
   operator producing **100.00% error rate** and stuck replicas at
   `≤ 2` across all 9 AI runs, while HPA and KEDA both scale correctly
   to `10`.
3. **Reproducible artifact** — 53 unit tests, `make demo` 12-step golden
   run, containerized docker compose, three TLC model-checking trace
   files in `specs/tlc_run_*.txt`, and a deterministic N=10 offline
   evaluation in `results_N10/`.

## Pipeline (Fig. 1 of paper)

```
Prometheus (10s scrape)
        │ k8s-metrics Kafka topic
        ▼
Python producer
        │
        ▼
Faust 30-s windowed aggregator
        │ k8s-features Kafka topic
        ▼
Decision Engine (River HTR + Half-Space-Trees)
        │
        ▼
Safety Shield  ←  TLA+ state machine  (TLC verified offline)
        │ k8s-decisions Kafka topic
        ▼
Kafka actuator (re-validates, then patches Deployment.spec.replicas
                     or deletes a pod via the official Kubernetes client)
        │
        ▼
workload-v2 Deployment (DB-backed Flask + SQLite)
```

Three Kafka topics thread the data through: `k8s-metrics → k8s-features
→ k8s-decisions`. Diagram in `docs/paper/main.tex` §II (TikZ).

## Stack (pinned versions)

| Layer | Version | Source |
|-------|---------|--------|
| Kubernetes (kind) | `v1.30.0` single-node | `ops/kind/kind-cluster.yaml` |
| Cloud | Azure `Standard_D4as_v5` (4 vCPU AMD EPYC, 16 GB RAM) | infrastructure |
| Container image | `k8-ai-ops:dev` built on `python:3.11-slim` | `ops/docker/Dockerfile` |
| Python ML | **River 0.26.0** (HTR + HST + online learning) | `River`, Montiel et al. 2020 |
| Stream processing | **Faust 0.11.3** (30-s manual-window aggregation) | `faust-streaming` |
| Message bus | **Kafka 3.9.1 KRaft** (no Zookeeper) | Kafka, Kreps et al. 2013 |
| Kubernetes client | **Python `kubernetes` 30.1.0** | official client |
| Formal verification | **TLA+ / TLC 2026.08.21.155922** | Lamport 1994 + TLC |
| Monitoring | **Prometheus** (`kube-prometheus-stack`) | Prometheus |
| Load generator | **Locust 2.31.1** | Locust |

## Evidence freeze (read this before reading the paper)

**`evidence-freeze.md`** is the single source of truth for every number
that appears in the IEEE paper (`docs/paper/main.tex`) and the M.Tech
thesis (`docs/thesis/*.md`).

If a number is not in `evidence-freeze.md`, it does not exist and
must not be cited. Sections A-L cover N=10 offline replay, Day-15 N=3
motivating failure, anomaly threshold, shield clamping audit, three
TLC specs, source code citations, banned numbers (such as `47 (20.9%)`
and `69.2%`), figure/table inventory, and the AI-disclosure
acknowledgment line.

The audit script `scripts/_phase5_audit.py` enforces this:
```
SOURCED (in both main + EF): 57
UNSOURCED (in main, NOT in EF): 0
```
Run from repo root: `python scripts/_phase5_audit.py`. If
`UNSOURCED > 0`, exit code is `1`.

## Defense artifacts (as of 2026-09-01)

| Artifact | Location | Status |
|----------|----------|--------|
| IEEE paper (PDF) | `docs/paper/main.pdf` | **5 pages**, IEEE conference, 20 refs, 0 warnings |
| IEEE paper (source) | `docs/paper/main.tex` | `\bibliography{refs}`, no `[?]` |
| IEEE refs (BibTeX) | `docs/paper/refs.bib` | 20 entries with DOI/URL |
| M.Tech thesis (PDF) | `docs/thesis/thesis.pdf` | 28 pages, pandoc + xelatex |
| M.Tech thesis (source) | `docs/thesis/01_abstract.md` through `09_conclusion.md` | 9 chapters, fully populated |
| Defense deck (20 slides) | `defense_deck.pdf` | built via `python scripts/build_deck.py` |
| Viva prep | `docs/VIVA_GAUNTLET.md` | 20 questions with file:line citations |
| Single source of truth | `evidence-freeze.md` | sections A-L |
| Claim audit script | `scripts/_phase5_audit.py` | 57 sourced / 0 unsourced |
| TLC trace (single shield, 273,702 states) | `specs/tlc_run_safety_shield.txt` | finished 01m47s, 0 violations |
| TLC trace (joint SHIELD path, 53 states) | `specs/tlc_run_ml_composition.txt` | finished 1s, 0 violations |
| TLC trace (ML-only counterexample, 93 states) | `specs/tlc_run_ml_only_counterexample.txt` | `MlSafetyMinReplicas` violated |
| N=10 deterministic offline replay | `results_N10/comparison_N10.csv` + `stats_report.{md,json}` | 4 ops × 3 scenarios × 10 trials |
| Day-15 N=3 motivating failure (100% error) | `data/evaluation/comparison_results_N3.csv:20-28` | 9 rows, all 100% / replicas_end ≤ 2 |
| Shield OFF ablation | `data/evaluation/ablation_results_N3.csv` | full=no_shield: 55 of 55 heal applied |
| Live docker-compose audit | `logs/operator_actions.log:4-20` | 8 shield-modified, 9 cooldown-rejected |
| Synthetic shield stress audit (used in Abstract) | `logs/safety_audit.log:1-28` | **12 of 28 modified = 42.9%** |
| Anomaly threshold (`data/anomaly_model.pkl:1`) | `0.484` (`0.4837573385518591` exact) | `evidence-freeze.md §C` |
| 53 unit tests | `tests/test_*.py` | **53/53 pass** |
| Live audit chain (Docker) | `ops/compose/pipeline.yaml` | 4 services (producer, stream, decision, actuator) |

## Repo layout

```
README.md                        # this file
LICENSE                         (not yet committed)
Makefile                        # make demo / eval / tla / tla-composition / stats / paper

docs/
├── GOLDEN_RUN.md               # 12-step reproducible demo
├── paper/                       # IEEE paper (target venue)
│   ├── main.tex                 # 5pp IEEE conference, 20 refs
│   ├── main.pdf                 # built artifact
│   └── refs.bib                 # 20 BibTeX entries
├── thesis/                      # M.Tech thesis source
│   ├── 01_abstract.md
│   ├── 02_introduction.md
│   ├── 03_literature_survey.md
│   ├── 04_existing_system.md
│   ├── 05_proposed_system.md
│   ├── 06_implementation.md
│   ├── 07_results.md
│   ├── 08_discussion.md
│   ├── 09_conclusion.md
│   └── thesis.pdf               # pandoc + xelatex artifact
├── VIVA_GAUNTLET.md             # 20-question viva prep with file:line
└── landing-page/                # optional static site (not paper deliverable)

evidence-freeze.md              # SINGLE SOURCE OF TRUTH for paper numbers
scripts/
├── _phase5_audit.py             # CI gate: every number in main.tex must trace to evidence-freeze.md
├── _evidence_freeze_inspect.py  # re-runs all evidence-freeze assertions from raw data
├── build_dataset_v2.py
├── build_deck.py                # defense_deck.pdf generator
├── replay_shield.py             # offline replay (banned output, see EF §H)
├── retrain_*.sh                 # model retraining
├── eval/                         # N=10 harness + stats report + ablation
│   ├── run_N10.sh               # canonical entry (used by make eval)
│   ├── run_quick.py             # PowerShell-friendly small-N runner
│   ├── run_one_trial.py         # per-trial simulator
│   └── stats_report.py          # per-(op, scenario) mean ± std + Wilcoxon + Cohen's d + 95% CI
├── smoke_test_scripts.py
└── demo/
    └── run_all.sh                # 12-step golden run driver

src/
├── metrics/                      # Prometheus + kube-state-metrics client
├── kafka/                        # producer / consumer
├── streaming/                    # Faust 30-s windowed aggregator
├── features/                     # feature engineering
├── models/                       # River HTR + HalfSpaceTrees
├── decision/                     # decision engine (load-first at :262-268)
├── safety/                       # SafetyShield Python + TLA+
├── kopf_operator/                # Kafka consumer + K8s actuator
└── baselines/
    └── firm_controller.py        # FIRM-style threshold baseline

ops/
├── compose/pipeline.yaml         # 4-service live demo docker-compose
├── docker/Dockerfile             # k8-ai-ops:dev (Python 3.11-slim, River, Faust, k8s client)
├── kafka/                        # KRaft manifests
├── manifests/                    # podinfo, workload-v2, ServiceMonitor
└── kind/kind-cluster.yaml

specs/
├── SafetyShield.tla              # 5 invariants + 1 liveness
├── SafetyShield.cfg
├── ML_Composition.tla            # SHIELD path + ML_Only path
├── ML_Composition.cfg
├── ML_Only_counterexample.cfg    # proves the shield is necessary
├── safety_policy.yaml            # runtime policy consumed by Python shield
├── tlc_run_safety_shield.txt     # TLC trace, 273,702 states
├── tlc_run_ml_composition.txt    # joint spec, 53 states
└── tlc_run_ml_only_counterexample.txt  # counterexample trace

results_N10/
├── comparison_N10.csv            # 121 rows (header + 120 deterministic trials)
├── comparison_N3.csv             # legacy N=3 file (not cited in current paper)
├── stats_report.md               # per-(op, scenario) summary
├── stats_report.json             # machine-readable
└── test.csv                      # legacy dev artifact (gitignored candidate)

data/
├── anomaly_model.pkl             # HalfSpaceTrees + threshold 0.484
├── replica_model.pkl             # HoeffdingAdaptiveTreeRegressor
├── features_v2.csv               # 285 rows from live workload-v2 traffic
├── evaluation/                   # Day-15 CSV + effect sizes
└── .archive/                     # timestamped backups before retrain

tests/                            # 53 unit tests
├── test_actuator.py
├── test_decision_engine.py
├── test_liveness.py
├── test_p1_scale_heal_separation.py
├── test_safety_shield.py
├── test_v2_models.py
└── __init__.py

tasks/
├── THESIS.md                     # central thesis tracker (now reflects locked state)
└── AMENDMENTS.md                 # day-by-day decisions (final closing entry appended 2026-09-01)

defense_deck.pdf                  # 20-slide deck
locustfile.py                     # load generator entrypoint
```

## Single-command demo

```bash
make tla                  # TLC on SafetyShield.tla (~3 s, 273,702 states, 0 errors)
make tla-composition      # TLC on ML_Composition.tla (~4 min, 53 states, 0 errors)
make paper                # pdflatex + bibtex + pdflatex x2 -> docs/paper/main.pdf
make demo                 # 12-step golden run on kind (~30 min)
make eval                 # N=10 deterministic offline replay (~3 h)
make stats                # regenerate results_N10/stats_report.md
```

Each target is idempotent where possible.

## Daily ops (Azure VM: `k8-vm`)

```bash
ssh k8-vm                                     # Azure VM alias
docker start k8-ai-control-plane              # only if kind node stopped
kubectl -n monitoring port-forward svc/kube-prometheus-stack-prometheus 9090:9090 &
kubectl -n kafka port-forward svc/kafka 9094:9094 &
kubectl -n workload-v2 port-forward svc/workload-v2 8080:8080 &  # for live compose demo
```

The Windows laptop setup (Days 1-3) remains as a fallback. See
`tasks/AMENDMENTS.md` (2026-08-18) for the laptop-vs-VM history.

## Build plan

See `tasks/README.md` for the 18-day plan. Days 1-18 are implemented in
order; each day is committed and tagged (`day-1` … `day-18-v2-n3`).

Final phase (`P0`-`P5`) closed all the rescue-plan gaps; see
`tasks/THESIS.md` and `tasks/AMENDMENTS.md` (2026-09-01 closing entry).
All commits authored by `sudo-Harshk <harshk1744@gmail.com>`.

## Status — Day-by-day build

- [x] Day 1 — Cluster & Workload Deployment
- [x] Day 2 — Monitoring Stack
- [x] Day 3 — Metrics API & Baseline Load Test
- [x] Day 4 — Kafka Streaming Pipeline
- [x] Day 5 — Faust Stream Processor
- [x] Day 6 — Feature Engineering & Dataset
- [x] Day 7 — Replica Prediction Model
- [x] Day 8 — Anomaly Detection Model
- [x] Day 9 — Decision Engine & SHAP Explainability → replaced with leave-one-out perturbation
- [x] Day 10 — TLA+ Safety Shield Specification
- [x] Day 11 — Safety Shield Implementation
- [x] Day 12 — Kubernetes Operator (Kafka actuator, not Kopf)
- [x] Day 13 — End-to-End Integration & Chaos Testing
- [x] Day 14 — Evaluation, Dashboards & Final Documentation
- [x] Day 15 — Statistical Rigor, Liveness & Reproducibility
- [x] Day 16 — p95 Variability Rework, IEEE Paper Draft, Dashboard
- [x] Day 17 — Paper Strengthening for Viva Defense (Threat Model + Production Roadmap)
- [x] Day 18 — Close Research Gaps (workload-v2 AI pipeline + Day-13 E2E + N=3 v2 + 5 tests)

## Rescue plan (P0 → P5, all closed)

| Phase | Goal | Status | Where |
|-------|------|--------|-------|
| **P0 (thesis lock)** | freeze thesis sentence, primary scaffold, golden run outline | ✅ done | `tasks/THESIS.md`, `docs/paper/main.tex`, `docs/VIVA_GAUNTLET.md` |
| **P0 (evidence freeze)** | single source of truth for every number in paper | ✅ done | **`evidence-freeze.md`** (sections A-L) |
| **P0 (refs)** | 8 → 20 BibTeX entries, Related Work rewritten | ✅ done | `docs/paper/refs.bib`, `docs/paper/main.tex §VII` |
| **P0 (sections)** | 8-section paper rewrite, every claim cited | ✅ done | `docs/paper/main.tex` (5pp, 20 refs, 0 `[?]`) |
| **P1 (rigor)** | Threats + Reproducibility para | ✅ done | `docs/paper/main.tex §VIII` (5 threats + 6 make targets) |
| **P1 (IEEE)** | IEEE compliance, captioned figs/tabs, ≤200-word abstract | ✅ done | `docs/paper/main.tex` (clean build, 0 warnings) |
| **P2 (final audit)** | every Abstract sentence traces to evidence-freeze.md | ✅ done | `scripts/_phase5_audit.py` (57 sourced / 0 unsourced) |
| **P3 (formal)** | TLA+ composition theorem + ML-only counterexample | ✅ done | `specs/ML_Composition.tla` |
| **P3 (artifact)** | docker-compose live pipeline | ✅ done | `ops/compose/pipeline.yaml` |
| **P4 (paper)** | IEEE 8/6 pages → trimmed to 5pp | ✅ done | `docs/paper/main.pdf` |
| **P4 (thesis)** | 9 chapters, 28 pages | ✅ done | `docs/thesis/thesis.pdf` |
| **P5 (viva)** | 20 questions with file:line citations | ✅ done | `docs/VIVA_GAUNTLET.md` |

## How to verify every claim before submission

Run from repo root:

```bash
python scripts/_phase5_audit.py       # 57 sourced, 0 unsourced
python -m pytest tests/ -q --tb=line  # 53 passed
ssh k8-vm 'cd ~/k8-auto-scaling-self-healing && make tla && make tla-composition && make paper && make stats'
```

If any of these fail, the paper is not ready.

## Acknowledgment

This work used Anthropic Claude as a coding assistant for code
scaffolding and copy editing; all design decisions and claims were
verified by the author. (See `evidence-freeze.md §K` and `docs/paper/main.tex`
Acknowledgment.)
