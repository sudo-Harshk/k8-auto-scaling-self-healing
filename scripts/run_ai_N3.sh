#!/usr/bin/env bash
# scripts/run_ai_N3.sh
#
# Run the AI operator portion of the N=3 comparison (spike, steady, idle x 3 reps).
# Assumes:
#   - AI pipeline already running (docker ps shows ai-producer, faust-e2e, engine-e2e, operator-e2e)
#   - Port-forward to podinfo on 8070 is active
#   - N=3 CSV already has 18 rows from HPA + KEDA runs

set -euo pipefail
cd "$(dirname "$0")/.."

LOG() { printf '\033[1;34m[ai_n3]\033[0m %s\n' "$*"; }

LOG "starting AI N=3 portion (9 runs)"

for scen in "spike:100:60" "steady:50:60" "idle:10:60"; do
    name=$(echo "$scen" | cut -d: -f1)
    users=$(echo "$scen" | cut -d: -f2)
    duration=$(echo "$scen" | cut -d: -f3)
    for run in 1 2 3; do
        ts=$(date +%Y%m%d-%H%M%S)
        LOG "[$name][run $run/3] users=$users duration=${duration}s ts=$ts"
        docker run --rm --network host --name "locust-${name}-ai-r${run}" \
            -v "$PWD":/code -w /code \
            --entrypoint locust k8-ai-ops:dev \
            -f locustfile.py --headless -u "$users" -r 20 -t "${duration}s" \
            --host=http://localhost:8070 \
            --csv="logs/locust_${name}_ai_r${run}" \
            --csv-full-history \
            > "/tmp/locust-${name}-ai-r${run}.log" 2>&1 || true
        sleep 15
        python3 scripts/_capture_metrics.py ai "$name" "$users" "$duration" "$run" "$ts"
    done
done

LOG "AI N=3 portion complete"
