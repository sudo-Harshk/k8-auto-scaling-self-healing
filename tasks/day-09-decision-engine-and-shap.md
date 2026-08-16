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
