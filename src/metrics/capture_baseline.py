"""Orchestrated Day 3 baseline capture: drive Locust + poll Prometheus into a CSV.

Runs the project's Day 3 baseline scenario:
    - 10 users
    - spawn rate 1 user/sec
    - 5-minute duration
    - Prometheus metrics sampled every 10 seconds

The Locust process is spawned as a subprocess (with the same docker image we use for
the metrics capture). Prometheus is polled via the metrics_client module in the same
Python process. Both run together for the configured duration, then the subprocess
exits and the CSV is finalised.

Usage (inside the Docker container):

    python src/metrics/capture_baseline.py
        # defaults: duration=300s, users=10, spawn=1, interval=10s
    python src/metrics/capture_baseline.py --duration 60 --users 5 --interval 5

Outputs:
    data/baseline_metrics.csv      per-sample snapshot of all six metrics
    logs/locust_baseline_stats.csv Locust end-of-run stats (per-endpoint summary)

Environment variables:
    PROMETHEUS_URL  default http://host.docker.internal:9090
    LOCUST_HOST     default http://host.docker.internal:8070
"""
from __future__ import annotations

import argparse
import csv
import logging
import os
import subprocess
import sys
import time
from pathlib import Path

# Make `from src.metrics...` work when invoked as `python src/metrics/capture_baseline.py`.
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.metrics.metrics_client import PodinfoMetricsClient  # noqa: E402

LOG = logging.getLogger("capture_baseline")

DATA_DIR = ROOT / "data"
LOGS_DIR = ROOT / "logs"

DEFAULT_PROM_URL = os.environ.get("PROMETHEUS_URL", "http://host.docker.internal:9090")
DEFAULT_LOCUST_HOST = os.environ.get("LOCUST_HOST", "http://host.docker.internal:8070")

CSV_FIELDS = [
    "timestamp",
    "cpu_cores",
    "memory_bytes",
    "request_rate_per_s",
    "error_rate_per_s",
    "current_replicas",
    "available_replicas",
]


def _run_locust(users: int, spawn: int, duration_s: int, host: str) -> subprocess.Popen:
    """Start `locust --headless ...` as a background process."""
    cmd = [
        "locust",
        "-f", str(ROOT / "locustfile.py"),
        "--host", host,
        "--headless",
        "-u", str(users),
        "-r", str(spawn),
        "-t", f"{duration_s}s",
        "--csv", str(LOGS_DIR / "locust_baseline"),  # writes _stats.csv + _stats_history.csv + _failures.csv
        "--only-summary",  # don't spam stdout with per-second tables
    ]
    LOG.info("starting locust: %s", " ".join(cmd))
    return subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)


def _capture_metrics(client: PodinfoMetricsClient, csv_path: Path,
                     duration_s: int, interval_s: int) -> int:
    """Sample Prometheus every `interval_s` for `duration_s` seconds, write rows."""
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    rows = 0
    deadline = time.monotonic() + duration_s
    with csv_path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_FIELDS)
        writer.writeheader()
        # Pad the loop by one interval so we capture a final snapshot after Locust
        # finishes (useful for steady-state baseline observation).
        while time.monotonic() < deadline + interval_s:
            snap = client.get_current_metrics()
            writer.writerow({k: snap.get(k) for k in CSV_FIELDS})
            fh.flush()
            rows += 1
            LOG.info("row %d: %s", rows, {k: snap.get(k) for k in CSV_FIELDS})
            if time.monotonic() >= deadline + interval_s:
                break
            time.sleep(interval_s)
    return rows


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    p = argparse.ArgumentParser(description="Day 3 baseline capture")
    p.add_argument("--duration", type=int, default=300, help="Locust run duration (s)")
    p.add_argument("--users", type=int, default=10, help="Locust user count")
    p.add_argument("--spawn", type=int, default=1, help="Locust spawn rate (users/s)")
    p.add_argument("--interval", type=int, default=10, help="Prometheus sample interval (s)")
    p.add_argument("--prometheus-url", default=DEFAULT_PROM_URL, help="Prometheus URL")
    p.add_argument("--locust-host", default=DEFAULT_LOCUST_HOST, help="Locust target host")
    args = p.parse_args()

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    csv_path = DATA_DIR / "baseline_metrics.csv"
    if csv_path.exists():
        LOG.info("overwriting existing %s", csv_path)

    client = PodinfoMetricsClient(url=args.prometheus_url)
    LOG.info("connected to Prometheus at %s", client.url)
    LOG.info("locust target host: %s", args.locust_host)
    LOG.info("plan: %d users, spawn %d/s, %ds, sample every %ds",
             args.users, args.spawn, args.duration, args.interval)

    locust_proc = _run_locust(args.users, args.spawn, args.duration, args.locust_host)
    try:
        rows = _capture_metrics(client, csv_path, args.duration, args.interval)
    finally:
        # If metrics loop finished first (it normally won't because it pads by one
        # interval), give Locust a moment to flush and exit; otherwise terminate it.
        try:
            locust_proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            LOG.warning("locust still running, terminating")
            locust_proc.terminate()
            try:
                locust_proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                locust_proc.kill()

    LOG.info("wrote %d rows to %s", rows, csv_path)
    LOG.info("locust exit code: %d", locust_proc.returncode)

    # Surface the tail of Locust's stdout so the run summary is visible.
    out = locust_proc.stdout.read() if locust_proc.stdout else ""
    if out:
        print("\n--- Locust output (tail) ---")
        print("\n".join(out.splitlines()[-25:]))

    print(f"\nWrote {rows} rows to {csv_path}")
    print(f"Locust CSV stats: {LOGS_DIR / 'locust_baseline_stats.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())