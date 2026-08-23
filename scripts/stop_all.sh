#!/usr/bin/env bash
# scripts/stop_all.sh
#
# Stop every pipeline Docker container and kill port-forwards. Idempotent.
#
# Usage (from repo root):
#   ./scripts/stop_all.sh

set -euo pipefail

LOG() { printf '\033[1;34m[stop]\033[0m %s\n' "$*"; }

LOG "stopping AI pipeline containers"
for c in ai-producer faust-e2e engine-e2e operator-e2e locust-bg locust-spike; do
  if docker ps -a --format '{{.Names}}' | grep -qx "$c"; then
    docker rm -f "$c" >/dev/null 2>&1 && LOG "  stopped $c"
  fi
done

LOG "killing kubectl port-forwards"
pkill -f "kubectl .* port-forward" 2>/dev/null && LOG "  port-forwards killed" || LOG "  no port-forwards running"

LOG "cleanup complete"