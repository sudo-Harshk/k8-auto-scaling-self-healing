#!/usr/bin/env bash
# scripts/deploy_infra.sh
#
# Create the kind cluster and deploy podinfo, monitoring, kafka, the
# ServiceMonitor, and (Day-14+) HPA. Idempotent — safe to re-run.
#
# Usage (from repo root):
#   ./scripts/deploy_infra.sh
#
# After completion, port-forwards must be started (see scripts/run_pipeline.sh).

set -euo pipefail

LOG() { printf '\033[1;34m[deploy]\033[0m %s\n' "$*"; }
DIE() { printf '\033[1;31m[deploy][FATAL]\033[0m %s\n' "$*" >&2; exit 1; }

cd "$(dirname "$0")/.."

# ---------------------------------------------------------------------------
# 1. Kind cluster
# ---------------------------------------------------------------------------
if ! kind get clusters 2>/dev/null | grep -q '^k8-ai$'; then
  LOG "creating kind cluster k8-ai"
  kind create cluster --config ops/kind/kind-cluster.yaml
else
  LOG "kind cluster k8-ai already exists"
fi

# ---------------------------------------------------------------------------
# 2. Helm repos
# ---------------------------------------------------------------------------
LOG "adding Helm repos"
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts 2>/dev/null || true
helm repo add kedacore https://kedacore.github.io/charts 2>/dev/null || true
helm repo update

# ---------------------------------------------------------------------------
# 3. Namespaces
# ---------------------------------------------------------------------------
LOG "creating namespaces"
for ns in podinfo monitoring kafka; do
  kubectl get namespace "$ns" >/dev/null 2>&1 || \
    kubectl create namespace "$ns"
done

# ---------------------------------------------------------------------------
# 4. Workload
# ---------------------------------------------------------------------------
LOG "applying podinfo manifests"
kubectl apply -f ops/manifests/podinfo.yaml

# ---------------------------------------------------------------------------
# 5. Monitoring
# ---------------------------------------------------------------------------
LOG "deploying kube-prometheus-stack (slim values, no Alertmanager)"
helm upgrade --install kube-prometheus-stack prometheus-community/kube-prometheus-stack \
  -n monitoring \
  -f ops/manifests/monitoring-values.yaml

LOG "applying ServiceMonitor for podinfo"
kubectl apply -f ops/manifests/podinfo-service-monitor.yaml

# ---------------------------------------------------------------------------
# 6. Kafka
# ---------------------------------------------------------------------------
LOG "deploying Kafka (apache/kafka:3.9.1 KRaft)"
kubectl apply -f ops/manifests/kafka.yaml

LOG "creating Kafka topics"
KAFKA_HEAP_OPTS="-Xms128M -Xmx128M" kubectl -n kafka exec deploy/kafka -- \
  /opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --create \
  --topic k8s-metrics --partitions 1 --replication-factor 1 2>/dev/null || true
KAFKA_HEAP_OPTS="-Xms128M -Xmx128M" kubectl -n kafka exec deploy/kafka -- \
  /opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --create \
  --topic k8s-features --partitions 1 --replication-factor 1 2>/dev/null || true
KAFKA_HEAP_OPTS="-Xms128M -Xmx128M" kubectl -n kafka exec deploy/kafka -- \
  /opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --create \
  --topic k8s-decisions --partitions 1 --replication-factor 1 2>/dev/null || true

# ---------------------------------------------------------------------------
# 7. HPA (Day-14 evaluation baseline)
# ---------------------------------------------------------------------------
if [[ -f ops/manifests/podinfo-hpa.yaml ]]; then
  LOG "applying podinfo HPA (disabled by default for Day-14 comparison harness)"
  kubectl apply -f ops/manifests/podinfo-hpa.yaml || true
fi

LOG "all infrastructure deployed"
LOG "next: ./scripts/run_pipeline.sh"