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

---

## Execution Notes (2026-08-20)

### Two-script architecture
The plan's single `feature_builder.py -> features.csv` is split into:
- `feature_builder.py` — per-scenario JSONL capture (one fresh Kafka consumer group
  per run, `auto_offset_reset="latest"` so scenarios don't bleed into each other's offsets)
- `build_dataset.py` — merge 4 JSONL files, label anomalies, compute target_replicas,
  write `features.csv`

A ~40s settle gap between scenarios keeps window-boundary bleed to at most 1 window.

### Feature percentages vs pod limits, not node capacity
Percentages are computed against podinfo's own pod limits (100m CPU / 128Mi memory per
replica from `ops/manifests/podinfo.yaml`), not node capacity — node-relative numbers on
the 4-vCPU / 16 GiB VM would be near 0% and useless as ML features.

### p95 latency added to the pipeline
`p95_latency_ms` added to `metrics_client.QUERIES` and `stream_processor.METRIC_KEYS`
(additive — the 6 Day-3 fields unchanged). Sourced from podinfo's
`http_request_duration_seconds` histogram. NaN results (idle) mapped to 0.0.

### Verified results (55 rows)
- **Scenario distribution:** baseline=12, spike=11, steady_high=21, idle=11
- **is_anomaly:** 0=33, 1=22 (spike + idle labeled anomalous)
- **target_replicas:** 1=27, 2=19, 4=9 (heuristic: by_cpu and by_req)
- **Columns:** timestamp, service, window_s, samples, cpu_percent, memory_percent,
  request_rate, p95_latency_ms, error_rate, current_replicas, available_replicas,
  hour_of_day, day_of_week, is_anomaly, scenario, target_replicas

### Gotcha: Docker entrypoint is `python`
Running `k8-ai-ops:dev python src/features/feature_builder.py` fails — the image
entrypoint is already `python`, so the command becomes `python python ...`. The
correct form drops the explicit `python`: `k8-ai-ops:dev src/features/feature_builder.py`.

### Known limitation: p95_latency_ms has zero variance
`p95_latency_ms` is 4.75 ms in all 55 rows — podinfo (trivial Go server, no backend
deps) never exceeds ~5 ms p95 even under 100 Locust users. The query is verified
correct; the workload simply has nothing to measure. Kept in the dataset (harmless;
Days 7–9 models will learn to ignore it). **Rework planned post-completion:** after
all 14 days are done, redo dataset + evaluation with a realistic microservice that
has backend dependencies. See `tasks/AMENDMENTS.md` (2026-08-20 known limitation).
