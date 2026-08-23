#!/usr/bin/env bash
# scripts/run_comparison.sh
#
# Day-14 evaluation harness: run each scenario under each operator, capture
# per-scenario metrics, append to data/evaluation/comparison_results.csv.
#
# Usage:
#   ./scripts/run_comparison.sh            # full run (3 ops × 3 scenarios)
#   ./scripts/run_comparison.sh ai spike   # one operator × one scenario
#   ./scripts/run_comparison.sh --n 3 ai   # N=3 repetitions (Day 15)
#
# Outputs (per scenario × operator × run):
#   data/evaluation/run_<timestamp>_<op>_<scenario>.log

set -euo pipefail

LOG() { printf '\033[1;34m[eval]\033[0m %s\n' "$*"; }
DIE() { printf '\033[1;31m[eval][FATAL]\033[0m %s\n' "$*" >&2; exit 1; }

cd "$(dirname "$0")/.."

# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------
N_REPEAT=1
ARGS=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --n) N_REPEAT="$2"; shift 2 ;;
    *)   ARGS+=("$1"); shift ;;
  esac
done

OPERATOR="${ARGS[0]:-}"
SCENARIO="${ARGS[1]:-}"

if [[ -n "$OPERATOR" ]] && [[ "$OPERATOR" != "hpa" && "$OPERATOR" != "keda" && "$OPERATOR" != "ai" ]]; then
  DIE "operator must be one of: hpa, keda, ai (got: $OPERATOR)"
fi
if [[ -n "$SCENARIO" ]] && [[ "$SCENARIO" != "spike" && "$SCENARIO" != "steady" && "$SCENARIO" != "idle" ]]; then
  DIE "scenario must be one of: spike, steady, idle (got: $SCENARIO)"
fi

# ---------------------------------------------------------------------------
# Scenario config (users, duration in seconds)
# ---------------------------------------------------------------------------
SCENARIOS=(
  "spike:100:180"
  "steady:50:300"
  "idle:10:120"
)

run_scenario_locust() {
  local op="$1" scenario="$2" run="$3"
  IFS=':' read -r name users duration <<< "$scenario"
  LOG "scenario=$name users=$users duration=${duration}s op=$op run=$run"

  # Start port-forward to podinfo
  nohup kubectl -n podinfo port-forward svc/podinfo 8070:9898 \
    > /tmp/pf-podinfo.log 2>&1 &
  disown
  sleep 3

  # Drive load
  docker run --rm --network host --name locust-${name}-${run} \
    -v "$PWD":/code -w /code \
    --entrypoint locust k8-ai-ops:dev \
    -f locustfile.py --headless -u "$users" -r 20 -t "${duration}s" \
    --host=http://localhost:8070 \
    --csv=logs/locust_${name}_${op}_${run} \
    --csv-full-history \
    > /tmp/locust-${name}-${run}.log 2>&1
}

capture_scenario() {
  local op="$1" scenario="$2" run="$3" ts="$4"
  IFS=':' read -r name users duration <<< "$scenario"

  LOG "capturing metrics for $op $name run=$run"

  # Append to comparison_results.csv
  python3 - <<EOF
import csv
import subprocess
from datetime import datetime

operator = "$op"
scenario = "$name"
run = "$run"

# Placeholder values — replaced after Prometheus query capture
row = {
    "timestamp": datetime.now().isoformat(),
    "operator": operator,
    "scenario": scenario,
    "run": run,
    "users": $users,
    "duration_s": $duration,
    "scaling_lag_s": "TBD",
    "total_scale_actions": "TBD",
    "total_heal_actions": "TBD",
    "p95_latency_ms_avg": "TBD",
    "p95_latency_ms_max": "TBD",
    "error_rate_avg": "TBD",
    "replicas_start": "TBD",
    "replicas_end": "TBD",
    "safety_rejected_count": "TBD",
}

with open("data/evaluation/comparison_results.csv", "a", newline="") as f:
    w = csv.DictWriter(f, fieldnames=row.keys())
    if f.tell() == 0:
        w.writeheader()
    w.writerow(row)
EOF
}

# ---------------------------------------------------------------------------
# Loop
# ---------------------------------------------------------------------------
mkdir -p data/evaluation

OPS=("hpa" "keda" "ai")
SCENS=("spike" "steady" "idle")

if [[ -n "$OPERATOR" ]]; then OPS=("$OPERATOR"); fi
if [[ -n "$SCENARIO" ]]; then SCENS=("$SCENARIO"); fi

for op in "${OPS[@]}"; do
  ./scripts/swap_operator.sh "$op" >/dev/null
  for scen in "${SCENS[@]}"; do
    for run in $(seq 1 "$N_REPEAT"); do
      ts=$(date +%Y%m%d-%H%M%S)
      run_scenario_locust "$op" "$scen" "$run"
      capture_scenario "$op" "$scen" "$run" "$ts"
      sleep 30  # settle between runs
    done
  done
done

LOG "comparison run complete"
LOG "results: data/evaluation/comparison_results.csv"