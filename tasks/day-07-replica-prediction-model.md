# Day 7 — Replica Prediction Model

## Task
Train a River-ML online regression model to predict the optimal number of pod replicas.

## Aim
Given current feature values, output a recommended replica count for scaling.

## Requirements

- `river` library
- `data/features.csv` from Day 6
- Python project environment

## Steps

1. **Choose a River-ML regressor**
   - Use `river.tree.HoeffdingAdaptiveTreeRegressor` or `river.linear_model.LinearRegression`.

2. **Write `replica_predictor.py`**
   - Define a `ReplicaPredictor` class.
   - Initialize the model and any preprocessing (standardization, one-hot encoding for time features).
   - Implement `learn(features, target_replicas)` for online updates.
   - Implement `predict(features)` to return a replica count.

3. **Train incrementally on Day 6 data**
   - Iterate through `data/features.csv` row by row.
   - Call `learn` on each row.
   - Predict after every N rows to compute rolling error.

4. **Post-process predictions**
   - Round to nearest integer.
   - Clamp between a minimum and maximum replica count.

5. **Evaluate with rolling MAE**
   - Track mean absolute error between predicted and actual target replicas.
   - Print final MAE.

6. **Save model state**
   - Serialize the model using `pickle` or River's built-in serialization.

## Outcome

- A working `predict_replicas(features)` function.
- Rolling MAE is acceptable for a prototype (e.g., MAE < 1 replica).
- Model can be saved and loaded.

## Verification

```bash
python src/models/replica_predictor.py
```

Expected result: script prints predicted vs actual replica counts and final MAE.

---

## Execution Notes (2026-08-20)

### Model choice
HoeffdingAdaptiveTreeRegressor per the plan's first option. Handles the
threshold-pattern target (1/2/4) better than LinearRegression.

### Training results (55 rows, predict-then-learn)
- **Final MAE: 0.2364** (well under the plan's bar of < 1.0)
- Trained on 55 samples, saved to `data/replica_model.pkl`
- Smoke test on hand-crafted features:
  - spike-like (51 req/s) → predicts 4
  - baseline-like (5 req/s) → predicts 1
  - idle-like (0.7 req/s) → predicts 1
  - overload (80 req/s) → predicts 6 (extrapolates sensibly)

### Pipeline architecture
`compose.Pipeline(preprocessing.StandardScaler(), tree.HoeffdingAdaptiveTreeRegressor(grace_period=50, max_depth=8, seed=42))`.

### River 3.11 compat patch
Required — see `tasks/AMENDMENTS.md` (2026-08-20). One-line sed after `pip install`.

### ReplicaPredictor public API
- `predict(features_dict) -> int` (rounded + clamped to [min_replicas, max_replicas])
- `predict_raw(features_dict) -> float | None` (unrounded, for SHAP/Day 9)
- `learn(features_dict, target_replicas)`
- `save(path)` / `ReplicaPredictor.load(path)` (pickle)
- `trained_count` property

### Gotchas
- Cold start: `predict_one` returns `None` until the model has seen at least one row.
  Public `predict()` returns the midpoint of the allowed range until then.
- `from src.models.replica_predictor import ReplicaPredictor` requires `PYTHONPATH=/code`
  when running inside the container (the Dockerfile's WORKDIR is /code but the `src`
  package needs to be on `sys.path`).
