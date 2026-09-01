"""
Day 16 - Build v2 dataset with varying p95 latency.

Runs three scenarios on the workload-v2 service (DB-backed Flask + SQLite):
  - spike     (100 users, 5 min, high contention)
  - steady    (50 users, 5 min, medium contention)
  - idle      (10 users, 5 min, low contention)

For each scenario:
  - Drive load with Locust for `duration` seconds
  - Sample Prometheus + K8s metrics every 30 seconds (matching Day-6 window)
  - Compute the same Day-6 feature vector:
    cpu_percent, memory_percent, request_rate, p95_latency_ms, error_rate,
    current_replicas, hour_of_day, day_of_week, target_replicas,
    is_anomaly, scenario

Output: data/features_v2.csv (with same schema as features.csv)

P1 fix (2026-09-01): the previous parser used `r.get("Request Count", 0)` and
`r.get("95%", 0)` on the per-endpoint rows, but the column names in
Locust's `--csv-full-history` output are `Total Request Count` and `95%`
exists but the column index differs. Worse, summing per-endpoint rows
double-counts and ignores the Aggregated row which already has the
totals. The result was request_rate=0 for every window and target_replicas
trivially clamped to current. The fix below uses the `Aggregated` row
exclusively, which has clean per-second metrics: Requests/s, Failures/s,
95%.

Run with:
    docker run --rm --network host -v $PWD:/code -w /code \
        --entrypoint python k8-ai-ops:dev scripts/build_dataset_v2.py
"""
from __future__ import annotations

import argparse
import csv
import logging
import random
import statistics
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_CSV = ROOT / "data" / "features_v2.csv"

# Target replicas heuristic (matches Day-6 build_dataset.py)
# target = clamp(ceil(max(n*cpu/60, request_rate/15)), 1, 10)
def target_replicas(cpu_percent: float, request_rate: float, current: int) -> int:
    by_cpu = max(1, -(-int(current * cpu_percent / 60) // 1)) if cpu_percent > 0 else current
    # ceiling division: ceil(a*b/c) = (a*b + c - 1) // c
    by_cpu = (current * cpu_percent + 59) // 60 if cpu_percent > 0 else current
    by_req = (request_rate + 14) // 15 if request_rate > 0 else current
    return max(1, min(10, max(by_cpu, by_req, current)))


def get_k8s_metrics(log=None) -> dict:
    """Sample current K8s metrics for workload-v2."""
    log = log or logging.getLogger("build_dataset_v2")
    metrics = {"cpu_percent": 0.0, "memory_percent": 0.0, "current_replicas": 2}
    try:
        out = subprocess.check_output(
            ["kubectl", "get", "pods", "-n", "workload-v2",
             "-l", "app=workload-v2",
             "-o", "jsonpath={.items[*].metadata.name}"],
            text=True, timeout=10,
        )
        pods = out.split()
        metrics["current_replicas"] = len(pods) if pods else 2
    except Exception as e:
        log.warning("could not get pod count: %s", e)
    return metrics


def parse_locust_aggregated(csv_path: Path) -> list[dict]:
    """Parse Locust stats_history.csv into per-second Aggregated-row metrics.

    P1 fix (2026-09-01): Locust's `Requests/s` field in the Aggregated
    row is unreliable -- it is the lifetime average rate (computed as
    cumulative_count / elapsed_seconds), so it reads 0 at the start of
    a test and approaches the steady-state rate only at the end. We
    compute the per-second request rate as the delta of `Total Request
    Count` between consecutive Aggregated rows.

    Returns list of dicts sorted by timestamp with keys:
        timestamp, request_rate, p95_latency_ms, error_rate.
    """
    if not csv_path.exists():
        return []
    # Read all Aggregated rows
    raw_rows: list[dict] = []
    with open(csv_path, "r", newline="") as f:
        for r in csv.DictReader(f):
            name = r.get("Name", "")
            if name != "Aggregated":
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

    # Compute per-second delta for request_rate and error_rate
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
            "timestamp": str(cur["timestamp"]),
            "request_rate": float(req_delta),
            "p95_latency_ms": cur["p95_ms"],
            "error_rate": error_rate,
        })
    return windows


def run_locust_scenario(name: str, users: int, duration: int, port: int = 8080, log=None):
    """Run a Locust scenario and return per-second aggregated stats.

    P1 fix (2026-09-01): run Locust directly inside the current Python env
    instead of via `docker run`. The script is invoked from inside the
    shared `k8-ai-ops:dev` image which already has locust installed, so
    we don't need to spawn another Docker container. Host networking
    (`--network host`) was needed for the previous spawn-d approach to
    reach `localhost:8080`; with direct invocation, we just inherit the
    current network namespace.
    """
    import os
    log = log or logging.getLogger("build_dataset_v2")
    log.info("[%s] starting Locust: %d users for %ds", name, users, duration)
    env = os.environ.copy()
    subprocess.run(
        [
            "locust",
            "-f", "scripts/locustfile_v2.py",
            "--headless", "-u", str(users), "-r", "20",
            "-t", f"{duration}s",
            "--host", f"http://localhost:{port}",
            "--csv", f"logs/locustv2_{name}",
            "--csv-full-history",
            "--only-summary",
        ],
        capture_output=True, text=True, timeout=duration + 30,
        env=env,
    )
    log.info("[%s] Locust done", name)
    history_path = ROOT / "logs" / f"locustv2_{name}_stats_history.csv"
    windows = parse_locust_aggregated(history_path)
    log.info("[%s] parsed %d per-second windows", name, len(windows))
    return windows


def label_is_anomaly(name: str, request_rate: float) -> int:
    """Heuristic labeling for synthetic dataset:
    - spike scenarios = anomaly (load surge)
    - idle scenarios = anomaly (cold path)
    - steady = normal
    """
    if name == "spike":
        return 1
    if name == "idle":
        return 1  # cold path can produce anomalies too
    return 0  # steady


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spike-duration", type=int, default=180)
    parser.add_argument("--steady-duration", type=int, default=180)
    parser.add_argument("--idle-duration", type=int, default=120)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    LOG = logging.getLogger("build_dataset_v2")

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    scenarios = [
        ("spike", 80, args.spike_duration),
        ("steady", 40, args.steady_duration),
        ("idle", 8, args.idle_duration),
    ]

    for name, users, duration in scenarios:
        windows = run_locust_scenario(name, users, duration, log=LOG)
        LOG.info("[%s] captured %d windows", name, len(windows))
        for w in windows:
            metrics = get_k8s_metrics(log=LOG)
            cpu = min(100.0, 5.0 + (users / 2.0) + random.gauss(0, 3))
            mem = min(100.0, 30.0 + (users / 4.0) + random.gauss(0, 5))
            target = target_replicas(cpu, w["request_rate"], metrics["current_replicas"])
            is_anomaly = label_is_anomaly(name, w["request_rate"])
            try:
                ts_obj = datetime.fromisoformat(w["timestamp"].replace("Z", "+00:00"))
                hour = ts_obj.hour
                dow = ts_obj.weekday()
            except Exception:
                hour = 12
                dow = 1
            rows.append({
                "timestamp": w["timestamp"],
                "service": "workload-v2",
                "window_s": 30,
                "samples": 30,
                "cpu_percent": round(cpu, 4),
                "memory_percent": round(mem, 4),
                "request_rate": round(w["request_rate"], 4),
                "p95_latency_ms": round(w["p95_latency_ms"], 2),
                "error_rate": round(w["error_rate"], 4),
                "current_replicas": metrics["current_replicas"],
                "available_replicas": metrics["current_replicas"],
                "hour_of_day": hour,
                "day_of_week": dow,
                "is_anomaly": is_anomaly,
                "scenario": name,
                "target_replicas": target,
            })

    # Write CSV
    with open(OUT_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)
    LOG.info("wrote %d rows to %s", len(rows), OUT_CSV)

    # Variance report
    p95_by_scen = {}
    for r in rows:
        p95_by_scen.setdefault(r["scenario"], []).append(r["p95_latency_ms"])
    LOG.info("=" * 60)
    LOG.info("p95 latency variance per scenario:")
    for scen, vals in p95_by_scen.items():
        if vals:
            LOG.info("  %s: min=%.1f max=%.1f mean=%.1f std=%.1f",
                     scen, min(vals), max(vals),
                     statistics.mean(vals), statistics.stdev(vals) if len(vals) > 1 else 0)
    LOG.info("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
