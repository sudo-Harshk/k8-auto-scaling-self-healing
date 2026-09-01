"""Regenerate data/features_v2.csv from existing Locust stats_history.csv files.

Use this AFTER applying the build_dataset_v2.py parser fix, when:
  - the workload-v2 cluster is no longer running (so build_dataset_v2.py
    cannot re-run its Locust scenarios), but
  - the original Locust --csv-full-history output files are still on disk.

Reads (defaults to workload-v2 scenarios; override with --history-prefix):
    logs/locustv2_spike_stats_history.csv
    logs/locustv2_steady_stats_history.csv
    logs/locustv2_idle_stats_history.csv

For each, parses the Aggregated row per timestamp, aggregates per
30-second window (matching the Day-6 cadence), applies the
target_replicas heuristic (CPU + request_rate), and writes
data/features_v2.csv.

Run inside the shared Docker image (pandas + numpy):
    docker run --rm -v $PWD:/code -w /code --entrypoint python \\
        k8-ai-ops:dev scripts/rebuild_features_v2.py
"""
from __future__ import annotations

import argparse
import csv
import math
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQ_PER_REPLICA = 15.0
CPU_PERCENT_TARGET = 60.0
MIN_REPLICAS = 1
MAX_REPLICAS = 10
WINDOW_S = 30

# Synthetic CPU/memory heuristics — match the original build_dataset_v2.py.
# We do not have real Prometheus-sourced per-pod CPU/memory for the historical
# workload-v2 runs, so we use the same closed-form approximation that the
# original builder used. The request_rate / p95 / error_rate values come
# from the real Locust stats_history.csv Aggregated rows.
SCENARIO_PARAMS = {
    "spike":      {"users": 80, "cpu_base": 45.0, "mem_base": 50.0, "is_anomaly": 1},
    "steady":     {"users": 40, "cpu_base": 25.0, "mem_base": 40.0, "is_anomaly": 0},
    "idle":       {"users":  8, "cpu_base":  9.0, "mem_base": 32.0, "is_anomaly": 1},
    "quick_high": {"users": 60, "cpu_base": 35.0, "mem_base": 45.0, "is_anomaly": 1},
    "quick_med":  {"users": 30, "cpu_base": 20.0, "mem_base": 38.0, "is_anomaly": 0},
    "quick_low":  {"users":  5, "cpu_base":  7.0, "mem_base": 31.0, "is_anomaly": 1},
    "comp":       {"users": 50, "cpu_base": 30.0, "mem_base": 42.0, "is_anomaly": 0},
}


def parse_aggregated(history_csv: Path) -> list[dict]:
    """Parse Locust --csv-full-history Aggregated rows.

    P1 fix (2026-09-01): Locust's `Requests/s` in the Aggregated row is
    unreliable (lifetime average, not per-second rate). Compute
    per-second rate from the delta of `Total Request Count`.
    """
    if not history_csv.exists():
        return []
    raw_rows: list[dict] = []
    with open(history_csv, "r", newline="") as f:
        for r in csv.DictReader(f):
            if r.get("Name", "") != "Aggregated":
                continue
            try:
                ts = int(r.get("Timestamp", "0") or "0")
                total_req = int(float(r.get("Total Request Count", 0) or 0))
                total_fail = int(float(r.get("Total Failure Count", 0) or 0))
                p95_raw = r.get("95%", "0") or "0"
                if p95_raw == "N/A" or p95_raw == "":
                    continue
                p95_ms = float(p95_raw)
                raw_rows.append({
                    "timestamp": ts,
                    "total_req": total_req,
                    "total_fail": total_fail,
                    "p95_ms": p95_ms,
                })
            except (ValueError, TypeError):
                continue
    raw_rows.sort(key=lambda r: r["timestamp"])
    windows = []
    for i, cur in enumerate(raw_rows):
        prev = raw_rows[i - 1] if i > 0 else None
        if prev is None or cur["timestamp"] == prev["timestamp"]:
            req_delta = 0
            fail_delta = 0
        else:
            req_delta = cur["total_req"] - prev["total_req"]
            fail_delta = cur["total_fail"] - prev["total_fail"]
        error_rate = fail_delta / req_delta if req_delta > 0 else 0.0
        windows.append({
            "timestamp": cur["timestamp"],
            "request_rate": float(req_delta),
            "p95_latency_ms": cur["p95_ms"],
            "error_rate": error_rate,
        })
    return windows


def aggregate_into_windows(per_second: list[dict], window_s: int = WINDOW_S) -> list[dict]:
    """Group per-second records into `window_s`-second buckets, averaged."""
    if not per_second:
        return []
    base_ts = per_second[0]["timestamp"]
    buckets: dict[int, list[dict]] = {}
    for r in per_second:
        bucket = ((r["timestamp"] - base_ts) // window_s) * window_s + base_ts
        buckets.setdefault(bucket, []).append(r)
    out = []
    for bucket_ts in sorted(buckets):
        recs = buckets[bucket_ts]
        out.append({
            "timestamp": bucket_ts,
            "request_rate": statistics.mean(r["request_rate"] for r in recs),
            "p95_latency_ms": statistics.mean(r["p95_latency_ms"] for r in recs),
            "error_rate": statistics.mean(r["error_rate"] for r in recs),
        })
    return out


def compute_target_replicas(cpu_percent: float, request_rate: float, current: int) -> int:
    n = max(current, 1)
    by_cpu = math.ceil(n * cpu_percent / CPU_PERCENT_TARGET) if cpu_percent > 0 else MIN_REPLICAS
    by_req = math.ceil(request_rate / REQ_PER_REPLICA) if request_rate > 0 else MIN_REPLICAS
    return max(MIN_REPLICAS, min(MAX_REPLICAS, max(by_cpu, by_req)))


def synth_cpu(users: int) -> float:
    """Closed-form CPU heuristic matching the original builder."""
    return min(100.0, 5.0 + (users / 2.0))


def synth_mem(users: int) -> float:
    """Closed-form memory heuristic matching the original builder."""
    return min(100.0, 30.0 + (users / 4.0))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--logs-dir", default="logs")
    parser.add_argument("--prefix", default="locustv2")
    parser.add_argument("--out", default="data/features_v2.csv")
    parser.add_argument("--current-replicas", type=int, default=2)
    args = parser.parse_args()

    rows: list[dict] = []
    for scenario, params in SCENARIO_PARAMS.items():
        history = Path(args.logs_dir) / f"{args.prefix}_{scenario}_stats_history.csv"
        per_second = parse_aggregated(history)
        windows = aggregate_into_windows(per_second)
        print(f"[{scenario}] {history.name}: {len(per_second)} per-second -> {len(windows)} windows")
        for w in windows:
            cpu = synth_cpu(params["users"])
            mem = synth_mem(params["users"])
            target = compute_target_replicas(cpu, w["request_rate"], args.current_replicas)
            try:
                from datetime import datetime, timezone
                ts_obj = datetime.fromtimestamp(w["timestamp"], tz=timezone.utc)
                hour = ts_obj.hour
                dow = ts_obj.weekday()
            except Exception:
                hour, dow = 12, 1
            rows.append({
                "timestamp": str(w["timestamp"]),
                "service": "workload-v2",
                "window_s": WINDOW_S,
                "samples": WINDOW_S,
                "cpu_percent": round(cpu, 4),
                "memory_percent": round(mem, 4),
                "request_rate": round(w["request_rate"], 4),
                "p95_latency_ms": round(w["p95_latency_ms"], 2),
                "error_rate": round(w["error_rate"], 4),
                "current_replicas": args.current_replicas,
                "available_replicas": args.current_replicas,
                "hour_of_day": hour,
                "day_of_week": dow,
                "is_anomaly": params["is_anomaly"],
                "scenario": scenario,
                "target_replicas": target,
            })

    if not rows:
        print("ERROR: no rows produced; check history file paths")
        return 1

    out_path = ROOT / args.out
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)
    print(f"\nwrote {len(rows)} rows to {out_path}")
    # Distribution summary
    by_scen = {}
    for r in rows:
        by_scen.setdefault(r["scenario"], []).append(r["target_replicas"])
    print("\ntarget_replicas per scenario:")
    for s, vals in by_scen.items():
        from collections import Counter
        c = Counter(vals)
        print(f"  {s}: {dict(sorted(c.items()))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
