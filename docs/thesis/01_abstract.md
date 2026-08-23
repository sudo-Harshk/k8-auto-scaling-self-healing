# Abstract

> **Status:** Scaffolding only. Filled in after Day 14 evaluation completes.

## One-paragraph abstract (target ≤ 150 words)

[To be filled in Day 14 after the comparison harness runs. The abstract should state the problem (Kubernetes operators are limited to reactive CPU-based scaling with no formal safety guarantees), the approach (an AI-driven operator using online machine learning with a TLA+-verified safety layer), and the key results (a quantitative comparison against HPA and KEDA showing scaling lag, detection latency, and unsafe-action rate).]

## Keywords

Kubernetes operators; online machine learning (River); formal verification (TLA+); auto-scaling; auto-healing; Horizontal Pod Autoscaler; KEDA; Prometheus; Kafka; Faust.

## Bullet summary (for the PPT / GitHub README)

- **Problem:** Existing Kubernetes operators (HPA, KEDA) use simple CPU/threshold rules and provide no formal safety guarantees.
- **Method:** End-to-end pipeline (Prometheus → Kafka → Faust → River-ML decision engine → TLA+-verified Safety Shield → Kafka actuator → cluster) with an online-trained replica predictor and unsupervised anomaly detector.
- **Result:** Day-14 evaluation harness + Day-15 N=3 statistics + Day-16 IEEE paper draft (links to `docs/ieee_paper.tex`).
- **Reproducibility:** 6 scripts in `scripts/`, single-command bootstrap via `scripts/bootstrap_vm.sh`.

## Citation key for the paper

```
@inproceedings{k8-ai-operator-2026,
  title={An AI-Driven Kubernetes Operator with TLA+-Verified Safety Guarantees},
  author={},
  booktitle={},
  year={2026},
}
```
(Filled after author name decided.)