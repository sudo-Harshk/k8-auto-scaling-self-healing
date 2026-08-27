#!/usr/bin/env bash
# scripts/run_pipeline.sh
#
# Start the four AI pipeline services in detached Docker containers on the
# host (network host so they share the host's port-forwards) plus the
# Prometheus and Kafka port-forwards themselves.
#
# Usage (from repo root):
#   ./scripts/run_pipeline.sh
#
# Day 18: pass WORKLOAD_NAMESPACE and WORKLOAD_DEPLOYMENT env vars to point the
# pipeline at workload-v2 instead of podinfo. Defaults preserve Days 1-15 behavior.
#
# Stop with scripts/stop_all.sh.

set -euo pipefail

LOG() { printf '\033[1;34m[pipeline]\033[0m %s\n' "$*"; }
DIE() { printf '\033[1;31m[pipeline][FATAL]\033[0m %s\n' "$*" >&2; exit 1; }

cd "$(dirname "$0")/.."

KAFKA_BOOTSTRAP="${KAFKA_BOOTSTRAP:-localhost:9094}"
PROMETHEUS_URL="${PROMETHEUS_URL:-http://localhost:9090}"
KAFKA_TOPIC_METRICS="${KAFKA_TOPIC_METRICS:-k8s-metrics}"
KAFKA_TOPIC_DECISIONS="${KAFKA_TOPIC_DECISIONS:-k8s-decisions}"
WORKLOAD_NAMESPACE="${WORKLOAD_NAMESPACE:-podinfo}"
WORKLOAD_DEPLOYMENT="${WORKLOAD_DEPLOYMENT:-podinfo}"

LOG "target workload: namespace=$WORKLOAD_NAMESPACE deployment=$WORKLOAD_DEPLOYMENT"

# ---------------------------------------------------------------------------
# Port-forwards (Prometheus, Kafka)
# ---------------------------------------------------------------------------
LOG "starting port-forwards (Prometheus 9090, Kafka 9094)"
nohup kubectl -n monitoring port-forward svc/kube-prometheus-stack-prometheus 9090:9090 \
  > /tmp/pf-prom.log 2>&1 &
disown
nohup kubectl -n kafka port-forward svc/kafka 9094:9094 \
  > /tmp/pf-kafka.log 2>&1 &
disown
sleep 5

curl -sf "${PROMETHEUS_URL}/-/healthy" >/dev/null || DIE "Prometheus not reachable"

# ---------------------------------------------------------------------------
# Producer (Prometheus -> Kafka)
# ---------------------------------------------------------------------------
LOG "starting ai-producer"
docker rm -f ai-producer 2>/dev/null || true
docker run -d --rm --network host --name ai-producer \
  -e PROMETHEUS_URL="${PROMETHEUS_URL}" \
  -e KAFKA_BOOTSTRAP="${KAFKA_BOOTSTRAP}" \
  -e KAFKA_TOPIC="${KAFKA_TOPIC_METRICS}" \
  -e POLL_INTERVAL=10 \
  -e WORKLOAD_NAMESPACE="${WORKLOAD_NAMESPACE}" \
  -e WORKLOAD_DEPLOYMENT="${WORKLOAD_DEPLOYMENT}" \
  -v "$PWD":/code -w /code \
  k8-ai-ops:dev \
  src/kafka/producer.py

# ---------------------------------------------------------------------------
# Faust worker (k8s-metrics -> 30s windows -> k8s-features)
# ---------------------------------------------------------------------------
LOG "starting faust-e2e"
docker rm -f faust-e2e 2>/dev/null || true
docker run -d --rm --network host --name faust-e2e \
  -e KAFKA_BOOTSTRAP="${KAFKA_BOOTSTRAP}" \
  -e WORKLOAD_NAMESPACE="${WORKLOAD_NAMESPACE}" \
  -e WORKLOAD_DEPLOYMENT="${WORKLOAD_DEPLOYMENT}" \
  -v "$PWD":/code -w /code \
  --entrypoint faust k8-ai-ops:dev \
  -A src.streaming.stream_processor worker -l info

# ---------------------------------------------------------------------------
# Decision engine (k8s-features -> SafetyShield -> k8s-decisions)
# ---------------------------------------------------------------------------
LOG "starting engine-e2e"
docker rm -f engine-e2e 2>/dev/null || true
docker run -d --rm --network host --name engine-e2e \
  -e KAFKA_BOOTSTRAP="${KAFKA_BOOTSTRAP}" \
  -e WORKLOAD_NAMESPACE="${WORKLOAD_NAMESPACE}" \
  -e WORKLOAD_DEPLOYMENT="${WORKLOAD_DEPLOYMENT}" \
  -v "$PWD":/code -w /code \
  k8-ai-ops:dev \
  src/decision/decision_engine.py

# ---------------------------------------------------------------------------
# Operator (k8s-decisions -> Kubernetes API)
# ---------------------------------------------------------------------------
LOG "starting operator-e2e"
docker rm -f operator-e2e 2>/dev/null || true
docker run -d --rm --network host --name operator-e2e \
  -e WORKLOAD_NAMESPACE="${WORKLOAD_NAMESPACE}" \
  -e WORKLOAD_DEPLOYMENT="${WORKLOAD_DEPLOYMENT}" \
  -v "$HOME/.kube":/root/.kube:ro \
  -v "$PWD":/code -w /code \
  k8-ai-ops:dev \
  src/kopf_operator/actuator.py

sleep 10
LOG "pipeline running:"
docker ps --format "table {{.Names}}\t{{.Status}}" | grep -E '(ai-producer|faust-e2e|engine-e2e|operator-e2e)' || true

LOG "Kafka offsets after warmup:"
KAFKA_HEAP_OPTS="-Xms128M -Xmx128M" kubectl -n kafka exec deploy/kafka -- \
  /opt/kafka/bin/kafka-get-offsets.sh --bootstrap-server localhost:9092 \
  --topic k8s-metrics 2>&1 || true
KAFKA_HEAP_OPTS="-Xms128M -Xmx128M" kubectl -n kafka exec deploy/kafka -- \
  /opt/kafka/bin/kafka-get-offsets.sh --bootstrap-server localhost:9092 \
  --topic k8s-features 2>&1 || true
KAFKA_HEAP_OPTS="-Xms128M -Xmx128M" kubectl -n kafka exec deploy/kafka -- \
  /opt/kafka/bin/kafka-get-offsets.sh --bootstrap-server localhost:9092 \
  --topic k8s-decisions 2>&1 || true