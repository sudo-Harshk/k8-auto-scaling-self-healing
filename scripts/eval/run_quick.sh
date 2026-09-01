#!/usr/bin/env bash
# scripts/eval/run_quick.sh — small-N test of the N>=10 harness.
#
# Runs N=3 trials × 4 operators × 3 scenarios = 36 trials and produces
# a stats report. Useful for verifying the harness works without
# spending ~3 hours on the full N=10.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
RESULTS_DIR="$ROOT/results_N10"

# Use the Windows Python directly (bash on Windows sees it as `python`)
PY=${PY:-python}

mkdir -p "$RESULTS_DIR"
cd "$ROOT"

N=${1:-3}
RAW="$RESULTS_DIR/comparison_N${N}.csv"
rm -f "$RAW"

echo "==> Quick run: $N trials x 4 operators x 3 scenarios = $((N * 12)) trials"
for seed in $(seq 1 "$N"); do
    for op in hpa keda firm shield-ai; do
        for scen in spike steady idle; do
            echo "  [seed=$seed] $op x $scen"
            "$PY" scripts/eval/run_one_trial.py \
                --operator "$op" \
                --scenario "$scen" \
                --seed "$seed" \
                --csv-out "$RAW"
        done
    done
done

echo ""
echo "==> Generating statistical report"
"$PY" scripts/eval/stats_report.py \
    --input "$RAW" \
    --output "$RESULTS_DIR/stats_report.md" \
    --json-out "$RESULTS_DIR/stats_report.json"

echo ""
echo "==> Done. See:"
echo "    $RAW"
echo "    $RESULTS_DIR/stats_report.md"
echo "    $RESULTS_DIR/stats_report.json"
