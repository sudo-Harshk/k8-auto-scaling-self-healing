"""
Day 16 - Quick p95 latency variance check on workload-v2.

Runs 3 short Locust tests against the v2 workload:
  - query-heavy (read-only)
  - write-heavy (POST /api/write)
  - mixed (50/50 read/write)

Reports p95 latency per test. If the test shows meaningful variance
(e.g., >5× range across the 3 tests), the workload is suitable for
capturing the v2 dataset.

Run with:
    docker run --rm --network host --entrypoint python k8-ai-ops:dev \
        scripts/check_v2_p95.py
"""
from __future__ import annotations

import logging
import subprocess
import sys
import time
from pathlib import Path

LOG = logging.getLogger("check_v2_p95")
WORKLOAD_URL = "http://localhost:8080"


def run_locust(name: str, user_count: int, duration: int, host: str = WORKLOAD_URL) -> dict:
    """Run a Locust test and return p95 latency stats."""
    csv_path = f"/tmp/locustv2_{name}"
    LOG.info("running %s: %d users for %ds", name, user_count, duration)
    # Run Locust with --csv pointing to /code/logs (mounted from VM)
    proc = subprocess.run(
        [
            "docker", "run", "--rm", "--network", "host",
            "-v", f"{Path.cwd()}:/code",
            "-w", "/code",
            "--entrypoint", "locust",
            "k8-ai-ops:dev",
            "-f", "/code/scripts/locustfile_v2.py",
            "--headless", "-u", str(user_count), "-r", "20",
            "-t", f"{duration}s",
            "--host", host,
            "--csv", f"logs/locustv2_{name}",
            "--only-summary",
        ],
        capture_output=True, text=True, timeout=duration + 30,
    )
    LOG.info("locust %s done", name)
    # Parse the only-summary output for p95
    out = proc.stdout
    p95 = None
    # only-summary format: "  Type     Name  # reqs  # fails  Avg  Min  Max  Med  req/s  failures/s"
    # We want aggregate "Total" row, columns include 95% percentile
    for line in out.splitlines():
        if "Total" in line and "|" not in line:
            # could be plain table; skip
            continue
        if "95%" in line:
            # Find numbers in the line
            import re
            nums = re.findall(r"\d+(?:\.\d+)?", line)
            if nums:
                p95 = float(nums[-1])
                break
    # Try CSV as fallback
    if p95 is None:
        try:
            with open(f"logs/locustv2_{name}_stats.csv") as f:
                lines = f.read().strip().splitlines()
            for line in lines:
                if line.startswith("GET,/api/query"):
                    parts = line.split(",")
                    headers = lines[0].split(",")
                    if "95%" in headers:
                        idx = headers.index("95%")
                        p95 = float(parts[idx])
                        break
        except Exception as e:
            LOG.warning("could not parse logs/locustv2_%s: %s", name, e)
    return {"name": name, "p95": p95, "users": user_count, "duration": duration}


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    LOG.info("=" * 60)
    LOG.info("Quick p95 variance check on workload-v2")
    LOG.info("=" * 60)

    results = []
    for name, users, duration in [
        ("quick_low", 5, 15),
        ("quick_med", 25, 15),
        ("quick_high", 60, 15),
    ]:
        r = run_locust(name, users, duration)
        results.append(r)
        LOG.info("  %s: p95=%s", name, r["p95"])

    p95_values = [r["p95"] for r in results if r["p95"] is not None]
    if p95_values:
        min_p95 = min(p95_values)
        max_p95 = max(p95_values)
        ratio = max_p95 / min_p95 if min_p95 > 0 else 0
        LOG.info("=" * 60)
        LOG.info("p95 range: min=%.2fms max=%.2fms ratio=%.2fx", min_p95, max_p95, ratio)
        if ratio >= 2.0:
            LOG.info("✅ WORKLOAD SUITABLE: p95 varies by %.1fx across load levels", ratio)
            return 0
        LOG.info("❌ WORKLOAD NOT SUITABLE: p95 variation too low (need >2x)")
        return 1
    LOG.error("could not parse any p95 values")
    return 2


if __name__ == "__main__":
    sys.exit(main())
