# Day 9 — Decision Engine & SHAP Explainability

## Task
Combine the replica predictor and anomaly detector into a decision engine, and add SHAP-based explanations.

## Aim
Generate explainable scaling/healing actions that can be validated and executed.

## Requirements

- `replica_predictor.py` from Day 7
- `anomaly_detector.py` from Day 8
- `shap` library (or River feature importances as fallback)
- Kafka topic `k8s-features` from Day 5

## Steps

1. **Write `decision_engine.py`**
   - Load the trained replica predictor and anomaly detector.
   - Define decision rules:
     - If anomaly score > threshold → action = `heal`, target service.
     - Else if predicted replicas != current replicas → action = `scale`, target = predicted replicas.
     - Else → action = `noop`.

2. **Format the decision object**
   - Include fields:
     - `service`
     - `action` (`scale` or `heal`)
     - `target_replicas`
     - `reason`
     - `confidence` or `anomaly_score`
     - `timestamp`

3. **Add SHAP explanations**
   - Compute SHAP values for the replica prediction.
   - Select the top 2–3 features driving the decision.
   - Include them in the decision object as `explanation`.
   - If SHAP is too complex for River models, use model-specific feature contributions or simple feature ranking.

4. **Produce decisions to Kafka**
   - Publish the decision object to the `k8s-decisions` topic as JSON.

5. **Log every decision**
   - Write decisions to `logs/decisions.log` for audit.

6. **Test the engine offline**
   - Feed a few feature vectors from `data/features.csv`.
   - Verify decisions make sense.

## Outcome

- A decision engine that outputs `scale`, `heal`, or `noop` actions.
- Every decision includes a human-readable reason and explanation.
- Decisions are published to the `k8s-decisions` Kafka topic.

## Verification

```bash
python src/decision/decision_engine.py
```

Expected result: printed decisions with actions, reasons, and explanations.

---

## Execution Notes (2026-08-21)

### Decision rule (single rule, deterministic)
```
if anomaly_score > threshold:
    action = "heal"
    target_replicas = current_replicas
elif predicted_replicas != current_replicas:
    action = "scale"
    target_replicas = predicted_replicas
else:
    action = "noop"
    target_replicas = current_replicas
```

Heal is intentionally scale-neutral: the operator (Day 12) takes it to mean
"delete the unhealthy pod" without changing replica count. Scale is the
only action that changes `target_replicas`. Noop is the steady state
(~40% of decisions in the offline run).

### Explainability — perturbation-based feature importance, NOT SHAP
The plan listed "shap or River feature importances as fallback". SHAP's
`TreeExplainer` is XGBoost/sklearn-only; SHAP's `KernelExplainer` is too
slow for an online loop. **Decision: use model-agnostic leave-one-out
perturbation.**

For each feature, replace it with the column mean and re-predict; the
feature whose perturbation causes the largest absolute change in
predicted replica count is the top contributor. Top 2 are reported in the
decision object's `explanation` field. This is well-established in the
interpretability literature (Fisher, Rudin, 2018) and is defensible.

No new dependencies (no `shap`, no `scikit-learn`). Pure Python.

### Decision object schema (locked for Day 12)
```json
{
  "service": "podinfo",
  "action": "scale",
  "target_replicas": 3,
  "current_replicas": 2,
  "reason": "predictor says 3 (current=2)",
  "explanation": [
    {"feature": "request_rate", "delta": 1.21},
    {"feature": "cpu_percent", "delta": 0.62}
  ],
  "anomaly_score": 0.18,
  "predicted_replicas_raw": 2.8,
  "timestamp": "2026-08-21T02:16:29.83+00:00",
  "features": {"cpu_percent": ..., "memory_percent": ..., ...}
}
```

### Offline verification (55 rows)
- 18 scale, 15 heal, 22 noop (decision mix)
- Top features for scale decisions: `memory_percent` (delta~1.0),
  `hour_of_day` (delta~0.77), `request_rate` (delta~0.35).
- All 55 decisions logged to `logs/decisions.log` (newline-delimited JSON).
- 8 of 12 baseline rows were scaled down (2 → 1) — correctly.
- 2 of 12 baseline rows were falsely flagged as heal (anomaly score
  0.4834 / 0.3350 > 0.2417 threshold). Documented Day-8 limitation.

### Public API
- `DecisionEngine.decide(record, feature_means=None) -> Decision`
- `DecisionEngine.explain(features, top_n=2) -> list[dict]`
- `DecisionEngine.log(decision)`
- `DecisionEngine.publish(decision)` — Kafka producer to `k8s-decisions`
- `DecisionEngine.close()` — flush + close producer
- CLI: `--offline` (default-csv run) or default-online Kafka consumer

### Online mode
The script supports an online mode that consumes Faust's `k8s-features`
topic and emits decisions to `k8s-decisions`. Used in Day 13 E2E. Today
we verified offline; the Kafka path is the same `KafkaProducer` class
used on Day 4.

### Gotchas
- The anomaly detector's first-window scores (0.0) are real — those rows
  produce `noop` actions, not `heal`. Heal only fires when the score
  exceeds 0.2417.
- `predict_raw` returns unrounded float (e.g., 2.8); `predict` rounds
  to integer. The decision object carries both for downstream consumers.
- `KAFKA_BOOTSTRAP` defaults to `localhost:9094` (the host-side
  port-forward). From inside the kind cluster, the in-cluster broker is
  `kafka.kafka.svc.cluster.local:9092` — Day 13 will pass that via env.

### No new deps
The Day-9 plan called for `shap==0.46.0` and `scikit-learn`. Neither was
added — the perturbation approach is pure Python. `requirements.txt` is
unchanged.
