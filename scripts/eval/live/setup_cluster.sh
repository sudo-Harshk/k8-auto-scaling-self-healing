#!/usr/bin/env bash
# One-time setup of the evaluation cluster on a fresh Ubuntu 22.04/24.04 VM.
#   ./bootstrap.sh                          # installs docker, kind, kubectl, helm, java (existing script)
#   ./scripts/eval/live/setup_cluster.sh    # this file (~10 min)
set -euo pipefail
cd "$(dirname "$0")/../../.."
LOG() { printf '\033[1;34m[setup]\033[0m %s\n' "$*"; }
L=scripts/eval/live

LOG "kind cluster shield-eval (1 control-plane + 3 workers)"
kind get clusters | grep -q '^shield-eval$' || kind create cluster --config $L/kind-eval.yaml
kubectl config use-context kind-shield-eval

LOG "building + loading pipeline image"
docker build -t k8-ai-ops:dev ops/docker/
kind load docker-image k8-ai-ops:dev --name shield-eval

LOG "metrics-server (needed by HPA)"
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/download/v0.7.2/components.yaml
kubectl -n kube-system patch deploy metrics-server --type=json -p \
  '[{"op":"add","path":"/spec/template/spec/containers/0/args/-","value":"--kubelet-insecure-tls"},
    {"op":"add","path":"/spec/template/spec/containers/0/args/-","value":"--metric-resolution=15s"}]'

LOG "helm repos"
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts >/dev/null 2>&1 || true
helm repo add kedacore https://kedacore.github.io/charts >/dev/null 2>&1 || true
helm repo update >/dev/null

LOG "kube-prometheus-stack"
helm upgrade --install kube-prometheus-stack prometheus-community/kube-prometheus-stack \
  -n monitoring --create-namespace -f ops/manifests/monitoring-values.yaml \
  --set prometheus.prometheusSpec.scrapeInterval=5s \
  --set prometheus.prometheusSpec.nodeSelector.tier=infra --wait --timeout 10m

LOG "KEDA"
helm upgrade --install keda kedacore/keda -n keda --create-namespace \
  --set nodeSelector.tier=infra --wait --timeout 5m

LOG "Kafka"
kubectl create namespace kafka --dry-run=client -o yaml | kubectl apply -f -
kubectl apply -f ops/manifests/kafka.yaml -n kafka --validate=false
kubectl -n kafka patch deploy kafka -p '{"spec":{"template":{"spec":{"nodeSelector":{"tier":"infra"}}}}}' || true
kubectl -n kafka rollout status deploy/kafka --timeout=300s
for t in k8s-metrics k8s-features k8s-decisions; do
  kubectl -n kafka exec deploy/kafka -- /opt/kafka/bin/kafka-topics.sh \
    --bootstrap-server localhost:9092 --create --if-not-exists --topic $t \
    --partitions 1 --replication-factor 1
done

LOG "workload + loadgen namespace"
kubectl apply -f $L/manifests/podinfo-eval.yaml
kubectl create namespace loadgen --dry-run=client -o yaml | kubectl apply -f -
kubectl -n podinfo rollout status deploy/podinfo --timeout=180s

LOG "done. next: $L/calibrate.sh"
