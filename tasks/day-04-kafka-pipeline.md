# Day 4 — Kafka Streaming Pipeline

## Task
Deploy Kafka and build a producer/consumer pair that streams metrics from Prometheus into Kafka.

## Aim
Create the real-time message bus that connects observability to stream processing.

## Requirements

- Helm 3
- Bitnami Kafka Helm chart or Strimzi operator
- Python `kafka-python` or `confluent-kafka`
- Working Prometheus and metrics client from Day 3

## Steps

1. **Deploy Kafka in the cluster**
   - Install Kafka (single broker is enough) and Zookeeper in a `kafka` namespace.
   - Wait for all pods to be Ready.

2. **Create Kafka topic `k8s-metrics`**
   - Use `kafka-topics.sh` inside the Kafka pod or a Kubernetes Job.
   - Set partitions to 1 and replication factor to 1 for local development.

3. **Write `producer.py`**
   - Poll Prometheus every 10–15 seconds using the metrics client from Day 3.
   - Serialize metrics as JSON.
   - Publish to the `k8s-metrics` topic.

4. **Write `consumer.py`**
   - Subscribe to the `k8s-metrics` topic.
   - Print each message to verify the pipeline.

5. **Run producer and consumer together**
   - Start the consumer in one terminal.
   - Start the producer in another terminal.
   - Confirm messages flow continuously.

## Outcome

- Kafka is running inside the kind cluster.
- `k8s-metrics` topic exists.
- Prometheus metrics are continuously published to Kafka.
- A consumer can read and display the messages.

## Verification Commands

```bash
kubectl get pods -n kafka
kubectl exec -it kafka-pod -n kafka -- kafka-topics.sh --list --bootstrap-server localhost:9092
python src/kafka/consumer.py
```

Expected result: consumer prints JSON metric messages in real time.
