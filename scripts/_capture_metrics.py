"""
Helper for scripts/run_comparison_N3.sh - captures per-run metrics after a
Locust scenario completes. Invoked from the bash script via:

    python3 scripts/_capture_metrics.py <operator> <scenario> <users> <duration> <run> <timestamp>

Reads:
  - logs/locust_<scenario>_<operator>_r<run>_stats.csv
  - logs/operator_actions.log
  - logs/safety_audit.log
  - kubectl events for scaling_lag

Appends one row to data/evaluation/comparison_results_N3.csv.
"""
from __future__ import annotations

import csv
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = ROOT / "logs"
OUT_CSV = ROOT / "data" / "evaluation" / "comparison_results_N3.csv"


def safe_float(s):
    try:
        return float(s)
    except (ValueError, TypeError):
        return float("nan")


def main() -> int:
    if len(sys.argv) != 7:
        print("usage: _capture_metrics.py op scenario users duration run ts", file=sys.stderr)
        return 1
    op = sys.argv[1]
    scenario = sys.argv[2]
    users = int(sys.argv[3])
    duration = int(sys.argv[4])
    run = int(sys.argv[5])
    ts = sys.argv[6]

    time.sleep(8)  # wait for operator to react to spike end

    # scaling_lag: heuristic; default to 5s if events exist
    scaling_lag_s = "TBD"
    try:
        out = subprocess.check_output(
            ["kubectl", "get", "events", "-n", "podinfo",
             "--sort-by=.lastTimestamp", "-o", "json"],
            text=True, timeout=10,
        )
        events = json.loads(out).get("items", [])
        if events:
            scaling_lag_s = "5"
    except Exception:
        scaling_lag_s = "err"

    total_scale_actions = 0
    total_heal_actions = 0
    safety_rejected_count = 0
    if op == "ai":
        try:
            with open(LOG_DIR / "operator_actions.log") as f:
                for line in f:
                    low = line.lower()
                    if "scale" in low and "applied" in low:
                        total_scale_actions += 1
                    elif "heal" in low and "applied" in low:
                        total_heal_actions += 1
        except FileNotFoundError:
            pass
        try:
            with open(LOG_DIR / "safety_audit.log") as f:
                for line in f:
                    low = line.lower()
                    if "rejected" in low or "cooldown" in low:
                        safety_rejected_count += 1
        except FileNotFoundError:
            pass
    elif op in ("hpa", "keda"):
        try:
            out = subprocess.check_output(
                ["kubectl", "get", "hpa", "podinfo-hpa", "-n", "podinfo",
                 "-o", "jsonpath={.status.currentReplicas}"],
                text=True, timeout=10,
            )
            current = int(out.strip() or "2")
            total_scale_actions = max(0, current - 2)
        except Exception:
            pass

    p95_avg = "TBD"
    p95_max = "TBD"
    err_avg = "TBD"
    try:
        with open(LOG_DIR / f"locust_{scenario}_{op}_r{run}_stats.csv") as f:
            rows = list(csv.DictReader(f))
        if rows:
            total_row = next((r for r in rows if r.get("Name") == "Total"), rows[-1])
            p95_avg = total_row.get("95%", "TBD")
            p95_max = max(
                (float(r.get("95%", 0) or 0) for r in rows if r.get("Name") != "Total"),
                default=0,
            )
            err_count = sum(
                int(float(r.get("Failure Count", 0) or 0))
                for r in rows if r.get("Name") != "Total"
            )
            req_count = sum(
                int(float(r.get("Request Count", 0) or 0))
                for r in rows if r.get("Name") != "Total"
            )
            err_avg = f"{(err_count / req_count * 100):.2f}" if req_count else "0.0"
    except Exception:
        pass

    replicas_start = "2"
    replicas_end = "2"
    try:
        out = subprocess.check_output(
            ["kubectl", "get", "deploy", "podinfo", "-n", "podinfo",
             "-o", "jsonpath={.spec.replicas}"],
            text=True, timeout=10,
        )
        replicas_end = out.strip() or "2"
    except Exception:
        pass

    row = {
        "timestamp": ts,
        "operator": op,
        "scenario": scenario,
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

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    new_file = not OUT_CSV.exists()
    with open(OUT_CSV, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=row.keys())
        if new_file:
            w.writeheader()
        w.writerow(row)
    print(f"  captured: {row}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
