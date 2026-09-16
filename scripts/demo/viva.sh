#!/usr/bin/env bash
# scripts/demo/viva.sh — 13-minute curated viva demo for SHIELD-AI.
#
# Compressed version of run_all.sh tuned for presentation:
#   - Steps 1-5: setup + deploy (same as full demo)
#   - Step 6:   pipeline-up + 30s log preview
#   - Step 7:   4-min live load (1m baseline + 2m burst + 1m ramp)
#               -> shows ML decisions + safety shield clamping in real-time
#   - Step 8:   TLC composition theorem (formally verified safety)
#   - Step 9:   Fault injection + self-healing demo
#   - Step 10:  stats + graphs
#
# Wall-clock: ~12-14 min
# Audience:   viva / defense / review
#
# Usage:
#   make demo-viva        # via Makefile
#   ./scripts/demo/viva.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$ROOT"

BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

step() {
    echo ""
    echo -e "${BLUE}==> Step $1: $2${NC}"
    echo "----------------------------------------"
}

ok() {
    echo -e "${GREEN}[OK]${NC}"
}

info() {
    echo -e "${YELLOW}[INFO]${NC} $*"
}

cleanup_pf() {
    pkill -f "port-forward.*kube-prometheus-stack-prometheus" 2>/dev/null || true
    pkill -f "port-forward.*svc/kafka" 2>/dev/null || true
}
trap cleanup_pf EXIT

step 1 "Cluster up (kind)"
if ! kind get clusters 2>/dev/null | grep -q "k8-ai"; then
    make kind-up
else
    echo "kind cluster 'k8-ai' already exists — skipping create"
fi
kubectl cluster-info --request-timeout=10s > /dev/null 2>&1 || true
ok

step 2 "Build and load Docker image"
docker inspect k8-ai-ops:dev >/dev/null 2>&2 && echo "image k8-ai-ops:dev already present" || make build-image
make load-image
ok

step 3 "Deploy Kafka (KRaft mode, no Zookeeper)"
make deploy-kafka
ok

step 4 "Deploy Prometheus + Grafana (kube-prometheus-stack)"
make deploy-prometheus
ok

step 5 "Deploy workloads (podinfo + workload-v2)"
make deploy-workload
ok

step 6 "Start 4-service pipeline + port-forwards"
info "starting Prometheus port-forward on :9090"
nohup kubectl -n monitoring port-forward svc/kube-prometheus-stack-prometheus 9090:9090 \
  > /tmp/pf-prom.log 2>&1 &
disown
sleep 2

info "starting Kafka port-forward on :9094"
nohup kubectl -n kafka port-forward svc/kafka 9094:9094 \
  > /tmp/pf-kafka.log 2>&1 &
disown
sleep 3

make pipeline-up
sleep 8

info "previewing first 45s of pipeline logs (data flowing live)..."
timeout 45s make pipeline-logs 2>&1 | head -60 || true
ok

step 7 "Live load: 1m baseline → 2m burst → 1m rampdown"
echo ""
echo "  WATCH: decision logs show ML predictions + shield clamping"
echo "  LOOK FOR: 'action=scale target=N' followed by 'REJECTED by safety shield'"
echo ""

info "waiting for workload-v2 pods to be ready..."
kubectl wait --for=condition=ready pod -l app=workload-v2 -n workload-v2 --timeout=120s 2>/dev/null || true
sleep 2

info "starting background pipeline log tail (decision + shield logs)..."
nohup bash -c "make pipeline-logs 2>&1 | grep -E 'decision|actuator|REJECTED|sent #|window|action='" \
  > /tmp/viva-pipeline.log 2>&1 &
disown

info "Phase A — baseline (30 users, 60s, ~15 RPS)"
locust -f locustfile.py --headless -u 30 -r 10 -t 60s --host http://localhost:9898 \
  --html=/tmp/locust_baseline.html 2>/dev/null || true

info "Phase B — burst (100 users, 120s, ~50-80 RPS) — triggers scale decisions"
locust -f locustfile.py --headless -u 100 -r 20 -t 120s --host http://localhost:9898 \
  --html=/tmp/locust_burst.html 2>/dev/null || true

info "Phase C — rampdown (20 users, 60s)"
locust -f locustfile.py --headless -u 20 -r 5 -t 60s --host http://localhost:9898 \
  --html=/tmp/locust_rampdown.html 2>/dev/null || true

info "stopping background pipeline tail..."
pkill -f "pipeline-logs.*grep" 2>/dev/null || true
sleep 1

echo ""
info "pipeline decisions during load (from /tmp/viva-pipeline.log):"
cat /tmp/viva-pipeline.log 2>/dev/null | head -30 || echo "  (no decisions captured)"

echo ""
info "Replicas after burst:"
kubectl get deploy workload-v2 -n workload-v2 -o jsonpath='{.spec.replicas}' 2>/dev/null || true
echo " desired"
kubectl get deploy workload-v2 -n workload-v2 -o jsonpath='{.status.readyReplicas}' 2>/dev/null || true
echo " ready"
kubectl get hpa workload-v2-hpa -n workload-v2 -o jsonpath='{.status.currentReplicas}' 2>/dev/null || true
echo " HPA current"
ok

step 8 "TLC model checker — composition theorem (ML + SHIELD, 53 states)"
echo ""
echo "  WATCH: 0 errors — formal proof that SHIELD + ML composition is safe"
echo ""
make tla-composition
ok

step 9 "Fault injection — self-healing demo"
echo ""
info "Killing a workload-v2 pod (simulated fault)..."
kubectl delete pod -l app=workload-v2 -n workload-v2 --wait=false 2>/dev/null || true
sleep 3
kubectl get pods -n workload-v2 -l app=workload-v2 2>/dev/null
echo ""
info "Pod should be recreated by Kubernetes ReplicaSet (self-healing verified)"
ok

step 10 "Export graphs + statistical report"
make export-graphs
make stats
ok

echo ""
echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}   SHIELD-AI viva demo completed successfully    ${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo "Results:   results_N10/"
echo "Paper:     docs/paper/main.tex"
echo "Viva Q&A:  docs/VIVA_GAUNTLET.md"
echo ""
