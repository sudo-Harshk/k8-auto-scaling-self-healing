# Day 5 — Faust Stream Processor

## Task
Implement a Faust streaming application that consumes raw metrics, aggregates them into windows, and outputs clean feature records.

## Aim
Prepare streaming metrics for the online ML model by cleaning and windowing them.

## Requirements

- Python 3.10+
- `faust-streaming` package
- Kafka running with the `k8s-metrics` topic from Day 4

## Steps

1. **Install Faust**
   - Add `faust-streaming` to your virtual environment.

2. **Create `stream_processor.py`**
   - Define a Faust app with Kafka broker configuration.
   - Define input topic `k8s-metrics` and output topic `k8s-features`.

3. **Implement metric parsing agent**
   - Consume messages from `k8s-metrics`.
   - Parse JSON and extract numeric metric values.

4. **Add tumbling window aggregation**
   - Group by service/deployment name.
   - Aggregate over 30-second windows to compute averages (CPU%, memory%, request rate, latency, error rate, pod count).

5. **Produce windowed records**
   - Emit one feature vector per service per window to `k8s-features`.
   - Include a timestamp and service name.

6. **Verify the processor**
   - Start the Faust worker.
   - Run the Kafka producer from Day 4.
   - Use a consumer on `k8s-features` to verify clean records.

## Outcome

- Faust stream processor is running.
- Raw Prometheus metrics are transformed into 30-second windowed feature records.
- Clean records are available on the `k8s-features` topic.

## Verification Command

```bash
faust -A src.streaming.stream_processor worker -l info
```

Expected result: logs show messages consumed from `k8s-metrics` and produced to `k8s-features`.
