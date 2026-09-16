#!/usr/bin/env bash
# scripts/demo/preflight.sh — Idempotent pre-flight checks for the viva demo.
#
# Ensures the kind cluster, docker image, infrastructure, and pipeline are all
# running before the demo steps begin. Every check is idempotent: it skips
# whatever is already present.
#
# Usage (source from viva.sh):
#   source "$(dirname "${BASH_SOURCE[0]}")/preflight.sh"
#   preflight

set -euo pipefail

# Color helpers (must be defined before calling info/skip)
BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info() { echo -e "${YELLOW}[preflight]${NC} $*"; }
skip() { echo -e "${YELLOW}[preflight]${NC} ${GREEN}[skip]${NC} $*"; }
warn() { echo -e "${YELLOW}[preflight]${NC} ${YELLOW}[warn]${NC} $*"; }

preflight() {
    info "=== pre-flight checks ==="

    # --- Cluster ---
    info "checking kind cluster..."
    if kind get clusters 2>/dev/null | grep -q "k8-ai"; then
        skip "kind cluster 'k8-ai' already exists"
    else
        info "creating kind cluster (first run, ~30s)..."
        make kind-up
    fi

    # --- Docker image ---
    info "checking k8-ai-ops:dev image..."
    if docker image inspect k8-ai-ops:dev >/dev/null 2>&1; then
        skip "k8-ai-ops:dev image present"
    else
        info "building k8-ai-ops:dev image (~5 min first time)..."
        make build-image
    fi
    info "loading image into kind..."
    make load-image

    # --- Kafka ---
    info "checking Kafka..."
    if kubectl get ns kafka >/dev/null 2>&1; then
        skip "Kafka namespace present"
        kubectl -n kafka get pods --field-selector=status.phase=Running | grep -q kafka \
          && skip "Kafka broker running" \
          || info "Kafka not ready — deploying..."
        kubectl apply -f ops/manifests/kafka.yaml -n kafka --validate=false 2>/dev/null || true
        kubectl wait --for=condition=ready pod -l app=kafka -n kafka --timeout=120s 2>/dev/null \
          || warn "Kafka pod not ready yet (will retry later)"
    else
        info "deploying Kafka..."
        make deploy-kafka
    fi

    # --- Prometheus ---
    info "checking Prometheus..."
    if kubectl get ns monitoring >/dev/null 2>&1; then
        skip "monitoring namespace present"
    else
        info "deploying Prometheus..."
        make deploy-prometheus
    fi

    # --- Workloads ---
    info "checking workloads..."
    if kubectl get ns workload-v2 >/dev/null 2>&1; then
        skip "workload namespaces present"
    else
        info "deploying workloads..."
        make deploy-workload
    fi

    # --- Pipeline + port-forwards ---
    info "checking pipeline..."
    if docker ps --format '{{.Names}}' 2>/dev/null | grep -q "shield-ai-producer"; then
        skip "pipeline containers already running"
    else
        info "starting Prometheus port-forward on :9090..."
        pkill -f "port-forward.*kube-prometheus-stack-prometheus" 2>/dev/null || true
        nohup kubectl -n monitoring port-forward svc/kube-prometheus-stack-prometheus 9090:9090 \
          > /tmp/pf-prom.log 2>&1 &
        disown
        sleep 2

        info "starting Kafka port-forward on :9094..."
        pkill -f "port-forward.*svc/kafka" 2>/dev/null || true
        nohup kubectl -n kafka port-forward svc/kafka 9094:9094 \
          > /tmp/pf-kafka.log 2>&1 &
        disown
        sleep 3

        info "starting pipeline containers..."
        make pipeline-up
        sleep 8

        info "verifying pipeline is alive..."
        docker ps --format '{{.Names}}' 2>/dev/null | grep shield-ai \
          && info "pipeline containers running" \
          || warn "pipeline containers may not have started — check: docker ps"
    fi

    # --- Tools ---
    info "checking tools..."
    command -v tlc >/dev/null 2>&1 \
      && skip "tlc on PATH" \
      || warn "tlc not found — step 8 (TLC) will show pre-recorded trace"

    command -v locust >/dev/null 2>&1 \
      && skip "locust on PATH" \
      || { info "installing locust..."; pip3 install locust 2>/dev/null || true; }

    info "=== pre-flight complete ==="
    echo ""
}
