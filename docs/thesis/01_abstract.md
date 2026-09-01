# Abstract

## One-paragraph abstract

Kubernetes auto-scaling today is reactive and single-signal. The default Horizontal Pod Autoscaler (HPA) watches CPU utilization and scales based on a fixed target percentage; KEDA extends HPA with event-driven triggers but inherits HPA's lack of formal safety guarantees and multi-signal fusion. Applying machine learning is the natural next step — multi-signal fusion, anomaly detection, online adaptation to non-stationary load — but naive ML-based controllers are unsafe. The Day-15 evaluation of our predecessor system showed the ML-only operator stuck at 2 replicas with a 100% error rate under burst load, while HPA and KEDA both scaled correctly to 10. We present **SHIELD-AI**, a hybrid controller that combines an online machine-learning oracle (River Hoeffding Adaptive Tree Regressor + HalfSpace Trees anomaly detector) with a formally-verified safety shield expressed in TLA+. The shield enforces five safety invariants (replica bounds, bounded scaling step, no conflicting actions, bounded action rate, heal-does-not-scale) plus one liveness property, model-checked exhaustively by TLC across 273,702 reachable states. We contribute: (1) the closed-form TLA+ specification of the ML+Shield composition with a thin ML abstraction, (2) an online-learning controller with an actual feedback loop, and (3) a reproducible artifact with 53 unit tests. Evaluation against HPA, KEDA, and a FIRM-style threshold baseline on workload-v2 (DB-backed Flask) shows SHIELD-AI matches KEDA on recovery time while the Safety Shield prevents the unsafe ML outputs observed in the ML-only ablation. The thesis is supported by `docs/paper/main.tex` (IEEE conference-style, 8 pages, 9 sections, 8 citations).

## Keywords

Kubernetes operators; online machine learning (River); formal verification (TLA+); auto-scaling; auto-healing; Horizontal Pod Autoscaler; KEDA; Prometheus; Kafka; Faust; Hoeffding Adaptive Tree Regressor; runtime safety shield.

## Bullet summary (for the deck and GitHub README)

- **Problem.** HPA is single-signal (CPU only); KEDA inherits HPA's limitations. ML-based controllers are powerful but unsafe under burst load, as demonstrated by our Day-15 evaluation.
- **Method.** End-to-end pipeline (Prometheus → Kafka → Faust 30-s windows → River-ML decision engine → TLA+-verified Safety Shield → Kafka actuator → cluster) with online training of both the replica predictor and anomaly detector.
- **Formal core.** A thin ML-abstraction TLA+ spec exhaustively verifies that *regardless of what the ML oracle outputs*, the Safety Shield's invariants hold. Companion spec produces an ML-only counterexample proving the shield is necessary.
- **Result.** Per-scenario offline replay shows the shield clamps 47/225 unsafe ML proposals (20.9%) to within bounds. Online canonical model MAE 0.82 on the 285-row workload-v2 dataset.
- **Reproducibility.** 53 unit tests, single-command bootstrap via `make demo` (Makefile target), pipeline runs in a single shared `k8-ai-ops:dev` Docker image (Python 3.11-slim).

## Citation key for the paper

```bibtex
@inproceedings{shield-ai-2026,
  title  = {SHIELD-AI: A Formally-Verified Online Learning Controller
            for Safe Kubernetes Auto-Scaling and Self-Healing},
  author = {[Author Name]},
  booktitle = {[Venue, e.g.\ IEEE ICMLA / KDD / EuroSys]},
  year   = {2026},
}
```
