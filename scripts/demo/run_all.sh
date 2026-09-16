#!/usr/bin/env bash
# scripts/demo/run_all.sh — End-to-end golden run for SHIELD-AI.
#
# This script executes the 12-step golden run documented in
# docs/GOLDEN_RUN.md. Each step is idempotent where possible.
#
# Usage:
#   ./scripts/demo/run_all.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$ROOT"

# Color helpers
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # no color

step() {
    echo ""
    echo -e "${BLUE}==> Step $1: $2${NC}"
    echo "----------------------------------------"
}

ok() {
    echo -e "${GREEN}OK${NC}"
}

step 1 "Cluster up (kind)"
if ! kind get clusters 2>/dev/null | grep -q "k8-ai"; then
    make kind-up
else
    echo "kind cluster 'k8-ai' already exists"
fi
ok

step 2 "Build and load shared Docker image"
docker inspect k8-ai-ops:dev >/dev/null 2>&1 || make build-image
make load-image
ok

step 3 "Deploy Kafka (KRaft mode)"
make deploy-kafka
ok

step 4 "Deploy Prometheus + Grafana"
make deploy-prometheus
ok

step 5 "Deploy workload-v2 (DB-backed Flask + SQLite)"
make deploy-workload
ok

step 6 "Start the 4-service pipeline (producer / Faust / decision / actuator)"
make pipeline-up
sleep 10
make pipeline-logs || true
ok

step 7 "Baseline traffic (50 RPS, 5 min)"
echo "  -> sending 50 RPS for 5 min to workload-v2"
make load-baseline
ok

step 8 "Burst traffic (200 RPS, 5 min)"
echo "  -> sending 200 RPS for 5 min to workload-v2"
make load-burst
ok

step 9 "Rampdown traffic (20 RPS, 3 min)"
make load-rampdown
ok

step 10 "Inject podinfo fault and observe healing"
make inject-fault
sleep 60
ok

step 11 "Run TLC model checker on Safety Shield spec"
make tla
make tla-composition
ok

step 12 "Export graphs + statistical report"
make export-graphs
make stats
ok

echo ""
echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}   SHIELD-AI golden run completed successfully   ${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo "Results in:  results_N10/"
echo "Logs in:     logs/"
echo "Models in:   data/"
echo "Paper in:    docs/paper/main.tex"
echo "Deck in:     defense_deck.pdf"
echo ""
