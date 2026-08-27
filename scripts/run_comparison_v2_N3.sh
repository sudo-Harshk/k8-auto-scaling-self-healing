#!/usr/bin/env bash
# scripts/run_comparison_v2_N3.sh
#
# Day 18 - N=3 comparison of HPA / KEDA / AI on workload-v2.
# Reuses scripts/_capture_metrics.py but with workload-v2 namespace env vars.

set -euo pipefail
LOG() { printf '\033[1;34m[v2_n3]\033[0m %s\n' "$*"; }
DIE() { printf '\033[1;31m[v2_n3][FATAL]\033[0m %s\n' "$*" >&2; exit 1; }

cd "$(dirname "$0")/.."

OUT_CSV="data/evaluation/comparison_v2_N3.csv"
rm -f "$OUT_CSV"
LOG "starting N=3 comparison on workload-v2"

SCENARIOS=("spike:80:60" "steady:40:60" "idle:8:45")
N_REPEAT=3

setup_hpa() {
    LOG "[hpa] enabling HPA on workload-v2"
    kubectl -n workload-v2 delete scaledobject --all --ignore-not-found 2>/dev/null || true
    # Stop AI pipeline
    ./scripts/stop_all.sh 2>/dev/null || true
    kubectl apply -f ops/manifests/workload-v2-hpa.yaml
    sleep 5
}

setup_keda() {
    LOG "[keda] enabling KEDA on workload-v2"
    kubectl -n workload-v2 delete hpa --all --ignore-not-found 2>/dev/null || true
    ./scripts/stop_all.sh 2>/dev/null || true
    kubectl apply -f ops/manifests/workload-v2-keda.yaml
    sleep 5
}

setup_ai() {
    LOG "[ai] enabling AI pipeline on workload-v2"
    kubectl -n workload-v2 delete hpa --all --ignore-not-found 2>/dev/null || true
    kubectl -n workload-v2 delete scaledobject --all --ignore-not-found 2>/dev/null || true
    WORKLOAD_NAMESPACE=workload-v2 WORKLOAD_DEPLOYMENT=workload-v2 nohup ./scripts/run_pipeline.sh > /tmp/ai-v2-n3.log 2>&1 &
    disown -a
    sleep 15
}

run_locust() {
    local op="$1" name="$2" users="$3" duration="$4" run="$5"
    LOG "  [$op][$name][run $run/$N_REPEAT] users=$users duration=${duration}s"
    # Ensure port-forward to workload-v2 is alive
    pkill -f "port-forward.*workload" 2>/dev/null || true
    sleep 1
    nohup kubectl -n workload-v2 port-forward svc/workload-v2 8080:8080 > /tmp/pf-wkld.log 2>&1 &
    disown -a
    sleep 5
    docker run --rm --network host --name "locust-${name}-${op}-r${run}" \
        -v "$PWD":/code -w /code \
        --entrypoint locust k8-ai-ops:dev \
        -f scripts/locustfile_v2.py \
        --headless -u "$users" -r 20 -t "${duration}s" \
        --host=http://localhost:8080 \
        --csv="logs/locustv2n3_${name}_${op}_r${run}" \
        --csv-full-history \
        > "/tmp/locust-v2-n3-${name}-${op}-r${run}.log" 2>&1 || true
    sleep 8  # let operator react
    python3 scripts/_capture_metrics.py workload-v2 "$name" "$users" "$duration" "$run" "$(date +%Y%m%d-%H%M%S)-v2"
}

for op in hpa keda ai; do
    setup_$op
    for scen in "${SCENARIOS[@]}"; do
        IFS=':' read -r name users duration <<< "$scen"
        # Reset replicas
        kubectl scale deploy workload-v2 -n workload-v2 --replicas=2 2>/dev/null || true
        sleep 5
        for run in $(seq 1 "$N_REPEAT"); do
            run_locust "$op" "$name" "$users" "$duration" "$run"
        done
    done
done

# Fix CSV header: the _capture_metrics.py output has podinfo-specific column names
# Convert "p95_latency_ms" / "request_count" etc. to workload-v2
LOG "renaming CSV to v2_N3"
mv data/evaluation/comparison_v2_N3.csv data/evaluation/comparison_v2_N3.csv.tmp 2>/dev/null || true
mv data/evaluation/comparison_results_N3.csv data/evaluation/comparison_v2_N3.csv 2>/dev/null || true
rm -f data/evaluation/comparison_v2_N3.csv.tmp

LOG "N=3 complete: $OUT_CSV"
wc -l "$OUT_CSV"