#!/usr/bin/env python3
"""
scripts/eval/export_graphs.py — Generate paper figures from pipeline decision logs.

Reads from:
  - logs/operator_actions.log   (pre-recorded N=10 audit log)
  - /tmp/viva-*.log             (live demo captures from viva.sh)
  - results_N10/comparison_N10.csv  (pre-recorded N=10 comparison)

Produces:
  - results_N10/replicas_over_time.png
  - results_N10/decisions_over_time.png
  - results_N10/shield_action_breakdown.png
  - results_N10/replicas_timeseries.csv
  - results_N10/decisions_timeseries.csv

Usage:
  python scripts/eval/export_graphs.py --output results_N10
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False


ROOT = Path(__file__).resolve().parents[2]
OPERATOR_LOG = ROOT / "logs" / "operator_actions.log"
LIVE_LOAD_LOG = Path("/tmp/viva-load.log")
LIVE_HEAL_LOG = Path("/tmp/viva-heal.log")


def parse_operator_log(path: Path):
    """Parse logs/operator_actions.log into structured rows."""
    rows = []
    if not path.exists():
        return rows
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        # Format: timestamp level=... target=... replicas=... action=... modified=... reason=...
        row = {"raw": line}
        m = re.search(r"action=(\w+)", line)
        if m:
            row["action"] = m.group(1)
        m = re.search(r"target=(\S+)", line)
        if m:
            row["target"] = m.group(1)
        m = re.search(r"modified=(\S+)", line)
        if m:
            row["modified"] = m.group(1)
        m = re.search(r"cooldown", line)
        if m:
            row["cooldown"] = True
        m = re.search(r"shield_\w+", line)
        if m:
            row["shield"] = m.group(0)
        m = re.search(r"replicas[=_]?(\d+)", line)
        if m:
            row["replicas"] = int(m.group(1))
        rows.append(row)
    return rows


def parse_live_log(path: Path):
    """Parse /tmp/viva-*.log from live demo capture."""
    rows = []
    if not path.exists():
        return rows
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        row = {"raw": line}
        m = re.search(r"sent #(\d+)", line)
        if m:
            row["sent_id"] = int(m.group(1))
        m = re.search(r"available_replicas[= ](\d+\.?\d*)", line)
        if m:
            row["available_replicas"] = float(m.group(1))
        m = re.search(r"current_replicas[= ](\d+\.?\d*)", line)
        if m:
            row["current_replicas"] = float(m.group(1))
        m = re.search(r"action=(\w+)", line)
        if m:
            row["action"] = m.group(1)
        m = re.search(r"REJECTED", line)
        if m:
            row["rejected"] = True
        rows.append(row)
    return rows


def decisions_summary(rows):
    """Count action types from parsed rows."""
    counts = {"scale": 0, "heal": 0, "noop": 0, "reject": 0, "cooldown": 0}
    for r in rows:
        a = r.get("action", "").lower()
        if a in counts:
            counts[a] += 1
        if r.get("rejected") or r.get("modified"):
            counts["reject"] += 1
        if r.get("cooldown"):
            counts["cooldown"] += 1
    return counts


def export_replicas_timeseries(rows, out_dir: Path):
    """Write replicas_over_time.csv from live log rows."""
    csv_path = out_dir / "replicas_timeseries.csv"
    with open(csv_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["timestamp", "available_replicas", "current_replicas", "event"])
        for r in rows:
            ts = r.get("timestamp", "")
            w.writerow([
                ts,
                r.get("available_replicas", ""),
                r.get("current_replicas", ""),
                r.get("action", ""),
            ])
    print(f"  wrote {csv_path}")


def export_decisions_timeseries(rows, out_dir: Path):
    """Write decisions_timeseries.csv."""
    csv_path = out_dir / "decisions_timeseries.csv"
    with open(csv_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["action", "target", "modified", "cooldown", "rejected"])
        for r in rows:
            w.writerow([
                r.get("action", ""),
                r.get("target", ""),
                r.get("modified", ""),
                "yes" if r.get("cooldown") else "",
                "yes" if r.get("rejected") else "",
            ])
    print(f"  wrote {csv_path}")


def plot_replicas_over_time(out_dir: Path):
    """Generate replicas_over_time.png."""
    if not HAS_MATPLOTLIB:
        return
    plt.figure(figsize=(10, 4))
    ax = plt.gca()

    # Try live load log
    rows = parse_live_log(LIVE_LOAD_LOG)
    if rows:
        ts = list(range(len(rows)))
        avail = [r.get("available_replicas", None) for r in rows]
        curr = [r.get("current_replicas", None) for r in rows]
        ax.plot(ts, avail, label="available_replicas", marker="o", markersize=2)
        ax.plot(ts, curr, label="current_replicas", marker="x", markersize=2)

    ax.set_xlabel("Sample (30s windows)")
    ax.set_ylabel("Replicas")
    ax.set_title("Workload-v2 Replicas Over Time (Live Demo)")
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    out = out_dir / "replicas_over_time.png"
    plt.savefig(out)
    plt.close()
    print(f"  wrote {out}")


def plot_decisions_over_time(out_dir: Path):
    """Generate decisions_over_time.png bar chart."""
    if not HAS_MATPLOTLIB:
        return
    plt.figure(figsize=(8, 4))

    # Aggregate from all sources
    all_rows = []
    for p in [OPERATOR_LOG, LIVE_LOAD_LOG, LIVE_HEAL_LOG]:
        all_rows.extend(parse_live_log(p) if "viva" in str(p) else parse_operator_log(p))

    counts = decisions_summary(all_rows)
    actions = list(counts.keys())
    values = list(counts.values())

    plt.bar(actions, values, color=["#2196F3", "#4CAF50", "#9E9E9E", "#FF5722", "#FF9800"])
    plt.ylabel("Count")
    plt.title("Shield-AI Decision Breakdown")
    for i, v in enumerate(values):
        if v > 0:
            plt.text(i, v + 0.5, str(v), ha="center")
    plt.tight_layout()
    out = out_dir / "decisions_over_time.png"
    plt.savefig(out)
    plt.close()
    print(f"  wrote {out}")


def plot_shield_breakdown(out_dir: Path):
    """Generate shield_action_breakdown.png — accepted vs modified vs rejected."""
    if not HAS_MATPLOTLIB:
        return
    plt.figure(figsize=(6, 6))

    rows = parse_operator_log(OPERATOR_LOG)
    accepted = sum(1 for r in rows if not r.get("modified") and not r.get("rejected"))
    modified = sum(1 for r in rows if r.get("modified"))
    rejected = sum(1 for r in rows if r.get("rejected"))

    labels = ["Accepted\n(no shield)", "Modified\n(shield clamped)", "Rejected\n(cooldown)"]
    sizes = [accepted, modified, rejected]
    colors = ["#4CAF50", "#FF9800", "#F44336"]
    explode = (0, 0.05, 0.1)

    if sum(sizes) == 0:
        plt.text(0.5, 0.5, "No decision data available.\nRun the demo first.",
                  ha="center", va="center", transform=plt.gca().transAxes)
        plt.axis("off")
    else:
        plt.pie(sizes, explode=explode, labels=labels, colors=colors,
                autopct="%1.0f%%", startangle=90)
        plt.title("Safety Shield Action Breakdown\n(pre-recorded N=10 audit log)")

    plt.tight_layout()
    out = out_dir / "shield_action_breakdown.png"
    plt.savefig(out)
    plt.close()
    print(f"  wrote {out}")


def main():
    parser = argparse.ArgumentParser(description="Export demo figures to PNG/CSV.")
    parser.add_argument("--output", required=True, help="Output directory")
    args = parser.parse_args()

    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"[export_graphs] Generating figures in {out_dir}")

    # CSV exports (always run, no dependency on matplotlib)
    live_rows = parse_live_log(LIVE_LOAD_LOG)
    if live_rows:
        export_replicas_timeseries(live_rows, out_dir)
        export_decisions_timeseries(live_rows, out_dir)
    else:
        print("  (no live log found at /tmp/viva-load.log — skipping timeseries CSVs)")

    # PNG exports (need matplotlib)
    if HAS_MATPLOTLIB:
        plot_replicas_over_time(out_dir)
        plot_decisions_over_time(out_dir)
        plot_shield_breakdown(out_dir)
    else:
        print("  matplotlib not available — skipping PNG exports (pip install matplotlib for figures)")
        print("  CSVs are still exported and usable for stats")

    print(f"[export_graphs] Done — output in {out_dir}")


if __name__ == "__main__":
    sys.exit(main())
