#!/usr/bin/env bash
# Live evaluation matrix: OPS x SCENARIOS x N repetitions.
# Run order is randomised per repetition (interleaved) to avoid drift bias.
#
#   OPS="hpa keda mt ml-only shield-ai" SCENARIOS="spike diurnal bursty" N=5 \
#     ./scripts/eval/live/run_matrix.sh
#
# Split across two VMs with e.g. SEEDS="1 2 3" on VM-A and SEEDS="4 5 6" on VM-B.
source "$(dirname "$0")/lib.sh"
OPS="${OPS:-hpa keda mt ml-only shield-ai}"
SCENARIOS="${SCENARIOS:-spike diurnal bursty}"
SEEDS="${SEEDS:-$(seq -s ' ' 1 ${N:-5})}"
DUR="${DURATION:-360}"
TAG="${TAG:-$(hostname)}"
RES="$ROOT/results_live/runs"; mkdir -p "$RES"

[[ -f "$ROOT/data/replica_model_eval.pkl" ]] || { echo "run train_ml.sh first"; exit 1; }
LOG "REQ_PER_REPLICA=$REQ_PER_REPLICA PEAK_RPS=$PEAK_RPS SLO_MS=$SLO_MS seeds=[$SEEDS]"
port_forwards

for seed in $SEEDS; do
  combos=()
  for sc in $SCENARIOS; do for op in $OPS; do combos+=("$sc:$op"); done; done
  mapfile -t combos < <(printf '%s\n' "${combos[@]}" | shuf --random-source=<(yes $seed))
  for c in "${combos[@]}"; do
    sc=${c%%:*}; op=${c##*:}
    rd="$RES/${sc}__${op}__s${seed}"
    [[ -f "$rd/DONE" ]] && { LOG "skip $rd"; continue; }
    rm -rf "$rd"; mkdir -p "$rd"
    LOG "=== scenario=$sc op=$op seed=$seed"
    pgrep -f "port-forward.*9094" >/dev/null || port_forwards
    stop_all_ops; reset_workload; sleep 20          # quiet period
    start_op "$op" "$rd"; sleep 25                   # controller warm-up
    start_sampler "$rd"
    run_load "$sc" "$seed" "$DUR" "$rd"
    wait_load_and_collect "$rd"
    sleep 5; stop_sampler "$rd"
    stop_all_ops
    printf 'scenario=%s\nop=%s\nseed=%s\nduration=%s\nreq_per_replica=%s\npeak_rps=%s\nslo_ms=%s\nhost=%s\n' \
      "$sc" "$op" "$seed" "$DUR" "$REQ_PER_REPLICA" "$PEAK_RPS" "$SLO_MS" "$TAG" > "$rd/meta.env"
    touch "$rd/DONE"
  done
done
reset_workload
LOG "matrix finished -> $RES"
