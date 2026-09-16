#!/usr/bin/env bash
# scripts/eval/run_N10.sh — N>=10 statistical evaluation harness.
#
# Runs 10 repetitions of the per-(operator, scenario) comparison with
# random seeds, then calls stats_report.py to produce the final report.
#
# What this script does:
#   1. Builds the per-scenario datasets (or reuses cached features_v2.csv).
#   2. For each seed in 1..10:
#      a. Runs HPA simulation on the spike + steady + idle scenarios.
#      b. Runs KEDA simulation on the spike + steady + idle scenarios.
#      c. Runs SHIELD-AI (full pipeline) on the spike + steady + idle scenarios.
#      d. Runs the FIRM-style threshold baseline on the same scenarios.
#   3. Aggregates results into results_N10/comparison_N10.csv.
#   4. Calls stats_report.py to produce the statistical report
#      (Wilcoxon, Cohen's d, 95% CI).
#
# Output:
#   results_N10/comparison_N10.csv       — raw per-(seed, operator, scenario) results
#   results_N10/stats_report.md          — human-readable statistical report
#   results_N10/stats_report.json        — machine-readable version
#
# Usage:
#   ./scripts/eval/run_N10.sh [N=10]
#
# Total runtime: ~3 hours on a single-node kind cluster (10 trials × 4 controllers
# × 3 scenarios × ~5 min each = ~10 hours raw, ~3 hours with parallel runs).
# For a quick smoke test use ./scripts/eval/run_quick.sh [N=3].
set -euo pipefail

N=${1:-10}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
RESULTS_DIR="$ROOT/results_N10"

# Use the Windows Python directly (bash on Windows sees it as `python`)
PY=${PY:-python}

mkdir -p "$RESULTS_DIR"
cd "$ROOT"

echo "==> Running $N trials × 4 operators × 3 scenarios"
RAW_CSV="$RESULTS_DIR/comparison_N${N}.csv"
echo "seed,operator,scenario,replicas_start,replicas_end,scale_actions,heal_actions,error_rate,p95_latency_ms,scaling_lag_s" > "$RAW_CSV"

for seed in $(seq 1 "$N"); do
    for operator in hpa keda shield-ai firm; do
        for scenario in spike steady idle; do
            echo "  [seed=$seed] $operator × $scenario"
            "$PY" scripts/eval/run_one_trial.py \
                --operator "$operator" \
                --scenario "$scenario" \
                --seed "$seed" \
                --csv-out "$RAW_CSV"
        done
    done
done

echo "==> Generating statistical report"
"$PY" scripts/eval/stats_report.py \
    --input "$RAW_CSV" \
    --output "$RESULTS_DIR/stats_report.md" \
    --json-out "$RESULTS_DIR/stats_report.json"

echo "==> Done. See:"
echo "    $RAW_CSV"
echo "    $RESULTS_DIR/stats_report.md"
echo "    $RESULTS_DIR/stats_report.json"
