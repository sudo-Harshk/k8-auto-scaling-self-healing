#!/usr/bin/env bash
# Training phase (20 min): the MT baseline actuates the deployment so the
# trace covers many replica counts; the SHIELD-AI engine runs in SHADOW mode
# (no actuator) and learns online. Then finalize the models.
source "$(dirname "$0")/lib.sh"
OUT="$ROOT/results_live/training"; mkdir -p "$OUT"
DUR="${TRAIN_SECONDS:-1200}"

port_forwards
stop_all_ops; reset_workload
docker run --rm -v "$ROOT":/code -w /code $IMG scripts/eval/live/train_ml.py init

start_feature_pipeline
start_mt "$OUT"
start_ml "$OUT" "$ROOT/data/replica_model_eval.pkl" skip "$OUT/replica_model_online.pkl"
sleep 20
start_sampler "$OUT"
LOG "training trace ($DUR s)"
run_load train 999 "$DUR" "$OUT"
wait_load_and_collect "$OUT"
stop_sampler "$OUT"
stop_all_ops

docker run --rm -e REQ_PER_REPLICA=$REQ_PER_REPLICA -v "$ROOT":/code -w /code $IMG \
  scripts/eval/live/train_ml.py finalize /code/results_live/training/decisions.log \
  /code/results_live/training/model_report.json
cp "$ROOT/data/replica_model_eval.pkl" "$ROOT/data/anomaly_model_eval.pkl" "$OUT/"
LOG "models ready"
