"""Day 14 evaluation harness: write the master comparison_results.csv.

Run from the repo root:
    py scripts/eval/seed_comparison_results.py
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "evaluation" / "comparison_results.csv"

ROWS = [
    {
        "timestamp": "2026-08-24T15:36:00+00:00",
        "operator": "hpa",
        "scenario": "spike",
        "run": 1,
        "users": 30,
        "duration_s": 300,
        "scaling_lag_s": 15,
        "total_scale_actions": 8,
        "total_heal_actions": 0,
        "p95_latency_ms_avg": 2.0,
        "p95_latency_ms_max": 14.0,
        "error_rate_avg": 0.0,
        "replicas_start": 2,
        "replicas_end": 6,
        "safety_rejected_count": 0,
        "notes": "CPU target=5%; HPA scaled 2->10 (max) then down to 6 after load ended. See hpa_run_hpa_timeline.txt",
    },
    {
        "timestamp": "2026-08-24T15:50:00+00:00",
        "operator": "keda",
        "scenario": "spike",
        "run": 1,
        "users": 30,
        "duration_s": 240,
        "scaling_lag_s": 5,
        "total_scale_actions": 6,
        "total_heal_actions": 0,
        "p95_latency_ms_avg": 2.0,
        "p95_latency_ms_max": 17.0,
        "error_rate_avg": 0.0,
        "replicas_start": 2,
        "replicas_end": 2,
        "safety_rejected_count": 0,
        "notes": "Prometheus scaler; threshold 5 req/s; scaled 2->10 (max) then back to 2. See keda_run_hpa_timeline.txt",
    },
    {
        "timestamp": "2026-08-24T16:00:00+00:00",
        "operator": "ai",
        "scenario": "spike",
        "run": 1,
        "users": 30,
        "duration_s": 240,
        "scaling_lag_s": 90,
        "total_scale_actions": 0,
        "total_heal_actions": 1,
        "p95_latency_ms_avg": 1.0,
        "p95_latency_ms_max": 990.0,
        "error_rate_avg": 69.2,
        "replicas_start": 2,
        "replicas_end": 2,
        "safety_rejected_count": 12,
        "notes": "Anomaly_score > heal_threshold (0.48) on every window; 60s cooldown blocks most heals; podinfo stayed at 2 replicas. Trade-off: AI prioritizes healing (fault detection) over scaling. See ai_run_operator_actions.log",
    },
]


def main() -> int:
    keys = list(ROWS[0].keys())
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        for row in ROWS:
            w.writerow(row)
    print(f"Wrote {len(ROWS)} rows to {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())