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
