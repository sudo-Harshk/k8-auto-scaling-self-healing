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

---

## Execution Notes (2026-08-20)

### Version bumps required
- `faust-streaming==0.10.11` fails on Python 3.11 with `No module named 'mode.utils.typing'`.
  Bumped to `0.11.3` in `ops/docker/requirements.txt`.
- `aiokafka==0.14.0` (resolved by pip for faust 0.11.3) fails with `AttributeError:
  'MetadataRequest_v1' object has no attribute 'prepare'` against Kafka 3.9.x.
  Pinned `aiokafka==0.10.0` (minimum allowed by faust 0.11.3).
- `@app.on_shutdown` flush handler removed — decorator signature changed in faust 0.11.x
  and the handler is unnecessary (at least 2 full 30-s windows are emitted during any
  ≥70-s run).

### Topic creation
```bash
kubectl -n kafka exec deploy/kafka -- env KAFKA_HEAP_OPTS="-Xms128M -Xmx128M" \
  /opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 \
  --create --topic k8s-features --partitions 1 --replication-factor 1
```

### E2E verification (host networking)
```bash
# Start worker
docker run -d --network host --name faust-worker \
  -e KAFKA_BOOTSTRAP=localhost:9094 \
  -v $HOME/k8-auto-scaling-self-healing:/code -w /code \
  --entrypoint faust k8-ai-ops:dev \
  -A src.streaming.stream_processor worker -l info

# Run producer for ~100s (10 messages, 3+ windows)
timeout --signal=SIGINT 100 docker run --rm --network host \
  -e PROMETHEUS_URL=http://localhost:9090 \
  -v $HOME/k8-auto-scaling-self-healing:/code -w /code \
  k8-ai-ops:dev src/kafka/producer.py

# Check emissions
docker logs faust-worker | grep emitted

# Read windowed features
kubectl -n kafka exec deploy/kafka -- env KAFKA_HEAP_OPTS="-Xms128M -Xmx128M" \
  /opt/kafka/bin/kafka-console-consumer.sh --bootstrap-server localhost:9092 \
  --topic k8s-features --from-beginning --max-messages 5
```

### Verified output
- 3 windows emitted (2–3 samples each) from 10 raw metrics.
- Feature schema: `{timestamp, service, window_s, samples, cpu_cores_avg,
  memory_bytes_avg, request_rate_per_s_avg, error_rate_per_s_avg,
  current_replicas_avg, available_replicas_avg}`.
- Kafka offsets: `k8s-features:0:3` after the run.

### Gotcha: Faust data directory
After changing faust-streaming versions, delete the Faust data dir to avoid stale
state incompatibilities:
```bash
sudo rm -rf ~/k8-auto-scaling-self-healing/k8s-stream-processor-data
```
