# Chapter 8 — Discussion

> **Status:** Scaffolding. Filled after Day 14 evaluation.

## 8.1 Architecture choices revisited

[To be filled. Discuss Kafka vs in-memory bus, River vs offline-trained models, TLA+ vs runtime assertions only, Kafka actuator vs Custom Resource watches. Trade-offs explicitly stated.]

## 8.2 Deviations from the original 14-day plan

A full list lives in `tasks/AMENDMENTS.md`. Summary:

| Day | Original plan | Actual implementation | Reason |
|-----|---------------|----------------------|--------|
| 1 | Sock Shop workload | podinfo | RAM ceiling; better CNCF fit; built-in fault injection |
| 3 | Host venv | Shared Docker image | Locust+gevent+3.12 incompatibility |
| 5 | Faust 0.10.x | Faust 0.11.3 | mode.utils.typing compat with 3.11 |
| 9 | SHAP library | Perturbation-based FI | SHAP's TreeExplainer doesn't support River |
| 10 | TLA+ Toolbox | CLI (java + tla2tools.jar) on VM | Reproducibility; no GUI needed |
| 12 | Kopf operator | kafka-python + kubernetes client | Trigger is Kafka, not K8s resource watches |
| 13 | "Train on full pipeline from Day 1" | Three critical bugs found + fixed (operator sort-key, decision engine field mismatch, heal-saturation) | Online mode never tested before |
| 14 | Single-run M.Tech evaluation | 3-day cycle (Days 14-16) with N=3 runs, liveness, p95 rework, IEEE paper | User decision; closer to publication-ready |

## 8.3 Bugs found during E2E (Day 13 retrospective)

Three bugs that were not caught earlier because:
1. **Operator sort-key tuple-negation** (`actuator.py:139`) — only triggered when 2+ pods existed with different restart counts; smoke test had homogeneous pods.
2. **Decision engine field-name mismatch** — Faust emits `cpu_cores_avg`, decision engine looked for `cpu_percent`. Online mode never run before; offline mode passed because CSV column names matched.
3. **Heal-saturation on baseline traffic** — every 30-s window crossed the anomaly threshold. Runtime-only behavior.

This is a real lesson: **online modes of components must be tested online before E2E evaluation**, not just smoke-tested.

## 8.4 What we would do differently

1. **Build a workload generator early.** Day-16's p95 rework is forced by podinfo's triviality. A DB-backed workload from Day 1 would have saved the rework.
2. **Define evaluation metrics on Day 1.** We didn't capture "scaling lag" until Day 14. Adding Prometheus recording rules for evaluation metrics from Day 1 would have made Day 14 trivial.
3. **Test online modes online, smoke-test offline modes offline.** Day 9's offline test gave false confidence.
4. **Run Day 6's feature builder against the live Faust stream earlier.** The field-name mismatch would have been caught on Day 5, not Day 13.

## 8.5 Open questions

(Filled after Day 14.)

## 8.6 Why this project is publishable

[To be filled. Argue architecture novelty, formal verification depth, reproducibility.]