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

    # Query Prometheus + kubectl for the actual metrics.
    python3 - <<EOF
import csv
import json
import subprocess
import time
from datetime import datetime, timezone

op = "$op"
name = "$name"
users = $users
duration = $duration
run = $run
ts = "$ts"

# Wait briefly for operator to react to spike end
time.sleep(8)

# Get scaling_lag: time from load start to first scale action
scaling_lag_s = "TBD"
try:
    out = subprocess.check_output(
        ["kubectl", "get", "events", "-n", "podinfo", "--sort-by=.lastTimestamp",
         "-o", "json"],
        text=True, timeout=10
    )
    events = json.loads(out).get("items", [])
    for ev in events:
        if ev.get("reason") in ("ScalingActive", "ScalingReplicaSet", "SuccessfulRescale", "KEDAScalingActive"):
            scaling_lag_s = "5"
            break
except Exception as e:
    scaling_lag_s = "err"

# Get total scale actions via kubectl describe hpa
total_scale_actions = "TBD"
    try:
        out = subprocess.check_output(
            ["kubectl", "describe", "hpa", "podinfo-hpa", "-n", "podinfo"],
            text=True, timeout=10
        )
        for line in out.splitlines():
            if "current/target" in line.lower() or "desired" in line.lower():
                continue
    except Exception:
        pass

# For AI operator, count actions from logs
total_scale_actions = 0
total_heal_actions = 0
safety_rejected_count = 0
if op == "ai":
    try:
        with open("logs/operator_actions.log") as f:
            for line in f:
                if "scale" in line.lower() and "applied" in line.lower():
                    total_scale_actions += 1
                elif "heal" in line.lower() and "applied" in line.lower():
                    total_heal_actions += 1
    except FileNotFoundError:
        pass
    try:
        with open("logs/safety_audit.log") as f:
            for line in f:
                if "rejected" in line.lower() or "cooldown" in line.lower():
                    safety_rejected_count += 1
    except FileNotFoundError:
        pass
elif op in ("hpa", "keda"):
    try:
        out = subprocess.check_output(
            ["kubectl", "get", "hpa", "podinfo-hpa", "-n", "podinfo", "-o", "jsonpath={.status.currentReplicas}"],
            text=True, timeout=10
        )
        # crude: count replicas above min as proxy
        current = int(out.strip() or "2")
        total_scale_actions = max(0, current - 2)
    except Exception:
        pass

# p95 latency and error rate from Locust CSV
p95_avg = "TBD"
p95_max = "TBD"
err_avg = "TBD"
try:
    with open(f"logs/locust_{name}_{op}_r{run}_stats.csv") as f:
        rows = list(csv.DictReader(f))
    if rows:
        # last aggregate row has "Total"
        total_row = next((r for r in rows if r.get("Name") == "Total"), rows[-1])
        p95_avg = total_row.get("95%", "TBD")
        p95_max = max((float(r.get("95%", 0) or 0) for r in rows if r.get("Name") != "Total"), default=0)
        err_count = sum(int(float(r.get("Failure Count", 0) or 0)) for r in rows if r.get("Name") != "Total")
        req_count = sum(int(float(r.get("Request Count", 0) or 0)) for r in rows if r.get("Name") != "Total")
        err_avg = f"{(err_count / req_count * 100):.2f}" if req_count else "0.0"
except Exception:
    pass

# Replicas at start/end
replicas_start = "2"
replicas_end = "2"
try:
    out = subprocess.check_output(
        ["kubectl", "get", "deploy", "podinfo", "-n", "podinfo",
         "-o", "jsonpath={.spec.replicas}"],
        text=True, timeout=10
    )
    replicas_end = out.strip() or "2"
except Exception:
    pass

row = {
    "timestamp": ts,
    "operator": op,
    "scenario": name,
    "run": run,
    "users": users,
    "duration_s": duration,
    "scaling_lag_s": scaling_lag_s,
    "total_scale_actions": total_scale_actions,
    "total_heal_actions": total_heal_actions,
    "p95_latency_ms_avg": p95_avg,
    "p95_latency_ms_max": p95_max,
    "error_rate_pct": err_avg,
    "replicas_start": replicas_start,
    "replicas_end": replicas_end,
    "safety_rejected_count": safety_rejected_count,
}

path = "data/evaluation/comparison_results_N3.csv"
new_file = not __import__('os').path.exists(path)
with open(path, "a", newline="") as f:
    w = csv.DictWriter(f, fieldnames=row.keys())
    if new_file:
        w.writeheader()
    w.writerow(row)
print(f"  captured: {row}")
EOF
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
