#!/usr/bin/env bash
# scripts/run_comparison_N3.sh
#
# Day-15 N=3 statistical comparison harness.
#
# Runs each (operator, scenario) combination 3 times with 60s scenarios
# to fit in the 90-min Day-15 budget. Captures Prometheus metrics
# automatically into data/evaluation/comparison_results_N3.csv.
#
# Usage:
#   ./scripts/run_comparison_N3.sh             # full run (3 ops × 3 scenarios × 3 reps = 27 runs)
#   ./scripts/run_comparison_N3.sh ai spike    # one op × one scenario × 3 reps = 3 runs
#
# Wall time: ~50-60 min for full run, ~7 min for one op × one scenario.

set -euo pipefail

LOG() { printf '\033[1;34m[n3]\033[0m %s\n' "$*"; }
DIE() { printf '\033[1;31m[n3][FATAL]\033[0m %s\n' "$*" >&2; exit 1; }

cd "$(dirname "$0")/.."

N_REPEAT="${N_REPEAT:-3}"
SCEN_DURATION="${SCEN_DURATION:-60}"   # 60s per scenario (was 120-300)

OPERATOR="${1:-}"
SCENARIO="${2:-}"

if [[ -n "$OPERATOR" ]] && [[ "$OPERATOR" != "hpa" && "$OPERATOR" != "keda" && "$OPERATOR" != "ai" ]]; then
    DIE "operator must be one of: hpa, keda, ai (got: $OPERATOR)"
fi
if [[ -n "$SCENARIO" ]] && [[ "$SCENARIO" != "spike" && "$SCENARIO" != "steady" && "$SCENARIO" != "idle" ]]; then
    DIE "scenario must be one of: spike, steady, idle (got: $SCENARIO)"
fi

# ---------------------------------------------------------------------------
# Scenarios (name:users:duration)
# ---------------------------------------------------------------------------
SCENARIOS=(
    "spike:100:${SCEN_DURATION}"
    "steady:50:${SCEN_DURATION}"
    "idle:10:${SCEN_DURATION}"
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

start_podinfo_pf() {
    nohup kubectl -n podinfo port-forward svc/podinfo 8070:9898 \
        > /tmp/pf-podinfo.log 2>&1 &
    disown
    sleep 3
}

run_locust() {
    local op="$1" name="$2" users="$3" duration="$4" run="$5"
    # Restart port-forward to podinfo before each run (the previous one may have died)
    pkill -f "port-forward.*podinfo.*8070" 2>/dev/null || true
    sleep 1
    nohup kubectl -n podinfo port-forward svc/podinfo 8070:9898 \
        > /tmp/pf-podinfo.log 2>&1 &
    disown
    sleep 3

    docker run --rm --network host --name "locust-${name}-${op}-r${run}" \
        -v "$PWD":/code -w /code \
        --entrypoint locust k8-ai-ops:dev \
        -f locustfile.py --headless -u "$users" -r 20 -t "${duration}s" \
        --host=http://localhost:8070 \
        --csv="logs/locust_${name}_${op}_r${run}" \
        --csv-full-history \
        > "/tmp/locust-${name}-${op}-r${run}.log" 2>&1 || true
}

capture_metrics() {
    local op="$1" name="$2" users="$3" duration="$4" run="$5" ts="$6"

    # Use a standalone Python script for metric capture (avoids heredoc indent issues)
    python3 scripts/_capture_metrics.py "$op" "$name" "$users" "$duration" "$run" "$ts"
}

# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------
mkdir -p data/evaluation

OPS=("hpa" "keda" "ai")
SCENS=("spike" "steady" "idle")
[[ -n "$OPERATOR" ]] && OPS=("$OPERATOR")
[[ -n "$SCENARIO" ]] && SCENS=("$SCENARIO")

LOG "starting N=$N_REPEAT comparison (ops=${OPS[*]} scenarios=${SCENS[*]})"

# Ensure port-forward to podinfo is up
start_podinfo_pf

for op in "${OPS[@]}"; do
    LOG "=== switching to operator: $op ==="
    ./scripts/swap_operator.sh "$op" >/dev/null
    sleep 5
    for scen in "${SCENARIOS[@]}"; do
        for run in $(seq 1 "$N_REPEAT"); do
            IFS=':' read -r name users duration <<< "$scen"
            # Skip scenarios not in SCENS filter (if a scenario was selected)
            if [[ -n "$SCENARIO" ]] && [[ "$name" != "$SCENARIO" ]]; then
                continue
            fi
            ts=$(date +%Y%m%d-%H%M%S)
            LOG "  [$op][$name][run $run/$N_REPEAT] users=$users duration=${duration}s ts=$ts"
            run_locust "$op" "$name" "$users" "$duration" "$run"
            capture_metrics "$op" "$name" "$users" "$duration" "$run" "$ts"
            sleep 15  # settle
        done
    done
done

LOG "=== N=$N_REPEAT comparison complete ==="
LOG "results: data/evaluation/comparison_results_N3.csv"
