# Day 6 — Feature Engineering & Dataset

## Task
Define the feature vector and create an observed dataset from different load scenarios.

## Aim
Feed meaningful, normalized inputs to the River-ML models for both replica prediction and anomaly detection.

## Requirements

- pandas
- numpy
- Saved metrics from Days 3–5
- Locust load generator
- Running podinfo and Kafka pipeline

## Steps

1. **Define the feature vector**
   - For the podinfo deployment (single workload), define:
     - `cpu_percent`
     - `memory_percent`
     - `request_rate`
     - `p95_latency_ms`
     - `error_rate`
     - `current_replicas`
     - `hour_of_day`
     - `day_of_week`

2. **Write `feature_builder.py`**
   - Read raw or windowed records.
   - Compute percentages and normalized values.
   - Return a dictionary/list ready for River-ML.

3. **Run varied load scenarios**
   - **Baseline:** 10 users for 5 minutes.
   - **Spike:** ramp to 100 users quickly, hold for 3 minutes, then drop.
   - **Steady high:** 50 users for 10 minutes.
   - **Idle:** no load for 5 minutes.

4. **Collect feature vectors**
   - Save each windowed record to `data/features.csv`.

5. **Label obvious anomalies**
   - Manually mark windows during spikes, crashes, or no-load states as `is_anomaly=1`.
   - Mark normal windows as `is_anomaly=0`.

6. **Compute target replica count**
   - For each window, estimate the ideal replica count based on CPU and request rate.
   - Save as `target_replicas` column.

## Outcome

- A CSV file `data/features.csv` with feature vectors.
- Feature vectors cover normal, spike, idle, and high-load behavior.
- Each record has a `target_replicas` label and an `is_anomaly` label.

## Verification

```bash
python src/features/feature_builder.py
head data/features.csv
```

Expected result: CSV has columns for all features, target replicas, and anomaly labels.
