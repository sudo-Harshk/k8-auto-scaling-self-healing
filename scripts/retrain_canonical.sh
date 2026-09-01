#!/usr/bin/env bash
# Retrain the canonical models from features_v2.csv.
#
# Replaces data/replica_model.pkl and data/anomaly_model.pkl with fresh
# versions trained on the 285-row workload-v2 dataset (vs the 55-row
# podinfo-only features.csv the originals were trained on).
#
# Old models are backed up to data/.archive/<timestamp>/ before overwrite.
#
# Two run modes:
#   1. On VM (host has docker + repo):
#        bash scripts/retrain_canonical.sh
#   2. Inside the shared Docker image (River + pandas + sklearn present):
#        docker run --rm -v $PWD:/code -w /code --entrypoint bash \
#            k8-ai-ops:dev scripts/retrain_canonical.sh

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# Detect Python: prefer `python` (in container), fall back to `python3` (host).
if command -v python >/dev/null 2>&1; then
    PY=python
elif command -v python3 >/dev/null 2>&1; then
    PY=python3
else
    echo "ERROR: neither 'python' nor 'python3' on PATH"
    exit 1
fi

# Detect River: required for retrain. If missing, error with a helpful hint.
if ! "$PY" -c "import river" 2>/dev/null; then
    echo "ERROR: 'river' not importable via $PY"
    echo "If running on the VM host, run inside the shared image instead:"
    echo "  docker run --rm -v \"\$(pwd):/code\" -w /code --entrypoint bash \\"
    echo "      k8-ai-ops:dev scripts/retrain_canonical.sh"
    exit 1
fi

TS="$(date -u +%Y%m%dT%H%M%SZ)"
ARCHIVE="data/.archive/${TS}"
mkdir -p "$ARCHIVE"

echo "=== P1 retrain: canonical replica + anomaly models ==="
echo "Source dataset:  data/features_v2.csv (workload-v2, 285 rows)"
echo "Backup folder:   ${ARCHIVE}"
echo "Python:          ${PY}"

# --------------------------------------------------------------- backup
for f in replica_model.pkl anomaly_model.pkl; do
    if [ -f "data/${f}" ]; then
        cp "data/${f}" "${ARCHIVE}/${f}"
        echo "Backed up data/${f} -> ${ARCHIVE}/${f}"
    fi
done

# --------------------------------------------------------------- retrain
echo ""
echo "--- Retraining replica model ---"
FEATURES_CSV=data/features_v2.csv \
    MODEL_PATH=data/replica_model.pkl \
    "$PY" src/models/replica_predictor.py

echo ""
echo "--- Retraining anomaly model ---"
FEATURES_CSV=data/features_v2.csv \
    MODEL_PATH=data/anomaly_model.pkl \
    "$PY" src/models/anomaly_detector.py

echo ""
echo "=== Done. New canonical models ==="
ls -la data/replica_model.pkl data/anomaly_model.pkl
echo ""
echo "Backup at ${ARCHIVE}/"
echo ""
echo "Verify with:"
echo "  $PY -m pytest tests/test_p1_scale_heal_separation.py -v"
echo "  $PY src/decision/decision_engine.py --offline --csv data/features_v2.csv"
