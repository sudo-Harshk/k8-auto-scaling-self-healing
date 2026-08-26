"""
Day 16 - Single-run comparison of HPA / KEDA / AI on workload-v2.

Runs a single spike scenario on the workload-v2 DB-backed service with each
operator enabled (HPA / KEDA / AI). Captures scaling lag, replica count,
and p95 latency. N=1 only — the goal is a quick v2 demo, not full
statistical analysis.

Output: data/evaluation/comparison_v2_N1.csv (3 rows)

Run with:
    bash scripts/run_comparison_v2_N1.sh
"""
from __future__ import annotations

import csv
import json
import logging
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOG = logging.getLogger("comparison_v2")
OUT_CSV = ROOT / "data" / "evaluation" / "comparison_v2_N1.csv"


def get_hpa_replicas() -> int:
    try:
        out = subprocess.check_output(
            ["kubectl", "get", "hpa", "workload-v2-hpa", "-n", "workload-v2",
             "-o", "jsonpath={.status.currentReplicas}"],
            text=True, timeout=10,
        )
        return int(out.strip() or "2")
    except Exception:
        return 0


def get_scaled_replicas() -> int:
    try:
        out = subprocess.check_output(
            ["kubectl", "get", "scaledobject", "workload-v2-keda", "-n", "workload-v2",
             "-o", "jsonpath={.status.currentReplicas}"],
            text=True, timeout=10,
        )
        return int(out.strip() or "2")
    except Exception:
        return 0


def get_pod_count() -> int:
    try:
        out = subprocess.check_output(
            ["kubectl", "get", "pods", "-n", "workload-v2",
             "-l", "app=workload-v2",
             "-o", "jsonpath={.items[*].metadata.name}"],
            text=True, timeout=10,
        )
        return len(out.split()) if out.strip() else 0
    except Exception:
        return 0


def get_ai_replicas() -> int:
    """Read the current workload-v2 deployment's spec.replicas (set by operator)."""
    try:
        out = subprocess.check_output(
            ["kubectl", "get", "deploy", "workload-v2", "-n", "workload-v2",
             "-o", "jsonpath={.spec.replicas}"],
            text=True, timeout=10,
        )
        return int(out.strip() or "2")
    except Exception:
        return 0


def run_locust(users: int = 80, duration: int = 60) -> dict:
    """Run Locust against workload-v2. Returns aggregate p95/error."""
    csv_path = "logs/locustv2_comp"
    LOG.info("running Locust: %d users for %ds", users, duration)
    proc = subprocess.run(
        [
            "docker", "run", "--rm", "--network", "host",
            "-v", f"{ROOT}:/code", "-w", "/code",
            "--entrypoint", "locust", "k8-ai-ops:dev",
            "-f", "scripts/locustfile_v2.py",
            "--headless", "-u", str(users), "-r", "20",
            "-t", f"{duration}s",
            "--host", "http://localhost:8080",
            "--csv", csv_path,
            "--csv-full-history",
            "--only-summary",
        ],
        capture_output=True, text=True, timeout=duration + 30,
    )
    LOG.info("Locust done")
    # Parse stats_history.csv for aggregate
    history = ROOT / f"{csv_path}_stats_history.csv"
    p95_vals, req_count, fail_count = [], 0, 0
    if history.exists():
        with open(history) as f:
            for r in csv.DictReader(f):
                name = r.get("Name", "")
                if name.startswith("Total") or name.startswith("Aggregated"):
                    continue
                try:
                    p95_vals.append(float(r.get("95%", 0) or 0))
                except (ValueError, TypeError):
                    pass
                try:
                    req_count += int(float(r.get("Request Count", 0) or 0))
                    fail_count += int(float(r.get("Failure Count", 0) or 0))
                except (ValueError, TypeError):
                    pass
    avg_p95 = sum(p95_vals) / len(p95_vals) if p95_vals else 0
    err_rate = fail_count / req_count if req_count else 0
    return {
        "p95_avg_ms": round(avg_p95, 2),
        "request_count": req_count,
        "error_rate": round(err_rate, 4),
    }


def setup_operator(op: str):
    """Enable one operator, disable the others, on workload-v2."""
    LOG.info("switching to operator: %s", op)
    if op == "hpa":
        subprocess.run(
            ["kubectl", "delete", "-n", "workload-v2", "scaledobject",
             "--all", "--ignore-not-found"], check=False,
        )
        subprocess.run(
            ["kubectl", "apply", "-f", "ops/manifests/workload-v2-hpa.yaml"],
            check=False,
        )
    elif op == "keda":
        subprocess.run(
            ["kubectl", "delete", "-n", "workload-v2", "hpa",
             "--all", "--ignore-not-found"], check=False,
        )
        subprocess.run(
            ["kubectl", "apply", "-f", "ops/manifests/workload-v2-keda.yaml"],
            check=False,
        )
    elif op == "ai":
        subprocess.run(
            ["kubectl", "delete", "-n", "workload-v2", "hpa",
             "--all", "--ignore-not-found"], check=False,
        )
        subprocess.run(
            ["kubectl", "delete", "-n", "workload-v2", "scaledobject",
             "--all", "--ignore-not-found"], check=False,
        )
    time.sleep(8)


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for op in ["hpa", "keda", "ai"]:
        setup_operator(op)
        start_replicas = get_pod_count()
        # Reset to 2 replicas
        subprocess.run(
            ["kubectl", "scale", "deploy", "workload-v2", "-n", "workload-v2",
             "--replicas=2"], check=False,
        )
        time.sleep(5)
        start_replicas = get_pod_count()
        LOG.info("[%s] starting replicas=%d", op, start_replicas)
        stats = run_locust(users=80, duration=60)
        end_replicas = get_pod_count()
        rows.append({
            "operator": op,
            "users": 80,
            "duration_s": 60,
            "start_replicas": start_replicas,
            "end_replicas": end_replicas,
            "p95_avg_ms": stats["p95_avg_ms"],
            "request_count": stats["request_count"],
            "error_rate": stats["error_rate"],
        })
        LOG.info("[%s] done: %s", op, rows[-1])

    with open(OUT_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)
    LOG.info("wrote %d rows to %s", len(rows), OUT_CSV)
    return 0


if __name__ == "__main__":
    sys.exit(main())
