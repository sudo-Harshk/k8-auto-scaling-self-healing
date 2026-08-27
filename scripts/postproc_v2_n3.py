"""
Day 18 - Post-process v2 N=3 comparison: read Locust CSVs and fill TBD values
in data/evaluation/comparison_v2_N3.csv.

The CSV filename pattern from run_comparison_v2_N3.sh is:
    logs/locustv2n3_{scenario}_{operator}_r{run}_stats.csv
"""
from __future__ import annotations

import csv
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOG = logging.getLogger("postproc_v2_n3")
CSV_PATH = ROOT / "data" / "evaluation" / "comparison_v2_N3.csv"
LOG_DIR = ROOT / "logs"


def read_locust_stats(scenario: str, op: str, run: int) -> dict:
    path = LOG_DIR / f"locustv2n3_{scenario}_{op}_r{run}_stats.csv"
    if not path.exists():
        return {}
    with open(path) as f:
        rows = list(csv.DictReader(f))
    total_row = next((r for r in rows if r.get("Name") == "Total"), rows[-1] if rows else {})
    p95_vals = []
    err_count = 0
    req_count = 0
    for r in rows:
        name = r.get("Name", "")
        if name.startswith("Total") or name.startswith("Aggregated"):
            continue
        try:
            p95_vals.append(float(r.get("95%", 0) or 0))
        except (ValueError, TypeError):
            pass
        try:
            err_count += int(float(r.get("Failure Count", 0) or 0))
            req_count += int(float(r.get("Request Count", 0) or 0))
        except (ValueError, TypeError):
            pass
    avg_p95 = sum(p95_vals) / len(p95_vals) if p95_vals else 0.0
    max_p95 = max(p95_vals) if p95_vals else 0.0
    err_rate = err_count / req_count if req_count else 0.0
    return {
        "p95_latency_ms_avg": f"{avg_p95:.2f}",
        "p95_latency_ms_max": f"{max_p95:.2f}",
        "error_rate_pct": f"{err_rate * 100:.2f}",
    }


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    if not CSV_PATH.exists():
        LOG.error("CSV not found: %s", CSV_PATH)
        return 1
    with open(CSV_PATH) as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    LOG.info("loaded %d rows", len(rows))

    fixed = 0
    for r in rows:
        if r.get("p95_latency_ms_avg") != "TBD":
            continue
        scen = r["scenario"]
        op = "hpa" if "hpa" in r["operator"].lower() or r["operator"].lower().endswith("hpa") else \
             ("keda" if "keda" in r["operator"].lower() or r["operator"].lower().endswith("keda") else "ai")
        # The capture script wrote operator as "workload-v2" for ALL three.
        # Determine operator from row index: rows 0-8 are hpa, 9-17 are keda, 18-26 are ai.
        try:
            row_idx = rows.index(r)
        except ValueError:
            row_idx = -1
        if row_idx < 9:
            op = "hpa"
        elif row_idx < 18:
            op = "keda"
        else:
            op = "ai"
        stats = read_locust_stats(scen, op, int(r["run"]))
        if stats:
            r.update(stats)
            fixed += 1
            LOG.info("fixed row %d: %s %s r%s -> p95_avg=%s",
                     row_idx, op, scen, r["run"], stats["p95_latency_ms_avg"])
        else:
            LOG.warning("could not find CSV for %s %s r%s", op, scen, r["run"])

    with open(CSV_PATH, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)
    LOG.info("fixed %d rows, wrote %s", fixed, CSV_PATH)
    return 0


if __name__ == "__main__":
    sys.exit(main())