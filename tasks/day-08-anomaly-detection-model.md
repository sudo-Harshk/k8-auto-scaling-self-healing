# Day 8 — Anomaly Detection Model

## Task
Train a River-ML online anomaly detector using Half-Space Trees to identify abnormal behavior.

## Aim
Detect metric patterns that indicate faults, crashes, or unexpected load for auto-healing.

## Requirements

- `river` library
- `data/features.csv` from Day 6
- Python project environment

## Steps

1. **Choose an anomaly detector**
   - Use `river.anomaly.HalfSpaceTrees`.

2. **Write `anomaly_detector.py`**
   - Define an `AnomalyDetector` class.
   - Initialize Half-Space Trees with appropriate feature bounds.
   - Implement `learn(features)` for online training on normal data.
   - Implement `predict(features)` to return an anomaly score.

3. **Train on normal data first**
   - Filter `data/features.csv` to rows where `is_anomaly=0`.
   - Pass these through `learn` to establish normal behavior.

4. **Test on abnormal data**
   - Pass rows where `is_anomaly=1` through `predict`.
   - Compare anomaly scores between normal and abnormal rows.

5. **Set a threshold**
   - Choose a threshold that separates normal from abnormal scores.
   - Implement `is_anomaly(features)` that returns True/False based on the threshold.

6. **Save model state**
   - Serialize the detector for reuse.

## Outcome

- A working `detect_anomaly(features)` function.
- Anomaly scores are clearly higher for abnormal windows.
- A fixed threshold is chosen and documented.

## Verification

```bash
python src/models/anomaly_detector.py
```

Expected result: script prints anomaly scores for normal vs abnormal samples and the chosen threshold.
