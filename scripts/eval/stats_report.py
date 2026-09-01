#!/usr/bin/env python3
"""
scripts/eval/stats_report.py — generate statistical report from raw trials.

Reads a CSV produced by run_N10.sh (one row per seed × operator × scenario),
groups by operator + scenario, computes:
  - per-(operator, scenario): mean ± std
  - paired Wilcoxon signed-rank test (SHIELD-AI vs HPA, KEDA, FIRM)
  - Cohen's d effect size with 95% CI (bootstrap, n=1000)
  - per-metric summary table in Markdown and JSON

Usage:
    python scripts/eval/stats_report.py \\
        --input results_N10/comparison_N10.csv \\
        --output results_N10/stats_report.md \\
        --json-out results_N10/stats_report.json

Output:
  - Markdown report (human-readable, used in the thesis Ch. 7)
  - JSON report (machine-readable, used by scripts/build_deck.py for slides)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]

METRIC_COLS = [
    "scale_actions", "heal_actions", "error_rate",
    "p95_latency_ms", "scaling_lag_s", "replicas_end",
]

PAIRWISE_BASELINES = ["hpa", "keda", "firm"]
PRIMARY = "shield-ai"


def _cohens_d(a: np.ndarray, b: np.ndarray) -> float:
    """Cohen's d effect size (positive = a > b)."""
    if len(a) < 2 or len(b) < 2:
        return 0.0
    diff = a.mean() - b.mean()
    pooled = np.sqrt((a.var(ddof=1) + b.var(ddof=1)) / 2)
    if pooled == 0:
        return 0.0
    return float(diff / pooled)


def _bootstrap_ci(a: np.ndarray, b: np.ndarray, n_boot: int = 1000, alpha: float = 0.05) -> tuple[float, float]:
    """Bootstrap 95% CI on Cohen's d."""
    rng = np.random.default_rng(42)
    diffs = []
    for _ in range(n_boot):
        sa = rng.choice(a, size=len(a), replace=True)
        sb = rng.choice(b, size=len(b), replace=True)
        diffs.append(_cohens_d(sa, sb))
    lo = float(np.percentile(diffs, 100 * alpha / 2))
    hi = float(np.percentile(diffs, 100 * (1 - alpha / 2)))
    return lo, hi


def _wilcoxon(a: np.ndarray, b: np.ndarray) -> tuple[float, float]:
    """Paired Wilcoxon signed-rank test. Returns (statistic, p-value)."""
    from scipy.stats import wilcoxon
    if len(a) != len(b) or len(a) < 2:
        return 0.0, 1.0
    try:
        stat, p = wilcoxon(a, b, zero_method="wilcox", alternative="two-sided")
        return float(stat), float(p)
    except ValueError:
        # All differences are zero
        return 0.0, 1.0


def compute_summary(df: pd.DataFrame) -> dict[str, Any]:
    """Build the full statistical summary tree."""
    summary: dict[str, Any] = {
        "n_seeds": int(df["seed"].nunique()),
        "operators": sorted(df["operator"].unique().tolist()),
        "scenarios": sorted(df["scenario"].unique().tolist()),
        "by_scenario": {},
        "pairwise_vs_shield_ai": {},
    }

    # Per-(operator, scenario) summary
    for scenario in summary["scenarios"]:
        scenario_summary: dict[str, Any] = {}
        sub = df[df["scenario"] == scenario]
        for op in summary["operators"]:
            op_sub = sub[sub["operator"] == op]
            if op_sub.empty:
                continue
            row: dict[str, Any] = {"n": int(len(op_sub))}
            for m in METRIC_COLS:
                if m in op_sub.columns:
                    vals = op_sub[m].astype(float).to_numpy()
                    row[m] = {
                        "mean": float(np.mean(vals)),
                        "std": float(np.std(vals, ddof=1)) if len(vals) > 1 else 0.0,
                        "min": float(np.min(vals)),
                        "max": float(np.max(vals)),
                    }
            scenario_summary[op] = row
        summary["by_scenario"][scenario] = scenario_summary

    # Pairwise: SHIELD-AI vs each baseline, per scenario, per metric
    for scenario in summary["scenarios"]:
        sub = df[df["scenario"] == scenario]
        sa = sub[sub["operator"] == PRIMARY]
        if sa.empty:
            continue
        scenario_pair: dict[str, Any] = {}
        for baseline in PAIRWISE_BASELINES:
            bl = sub[sub["operator"] == baseline]
            if bl.empty:
                continue
            metric_results: dict[str, Any] = {}
            for m in METRIC_COLS:
                a = sa[m].astype(float).to_numpy()
                b = bl[m].astype(float).to_numpy()
                # Pair by seed
                merged = pd.DataFrame({"seed": list(range(1, max(len(a), len(b)) + 1))})
                # Re-key for pairing
                a_dict = dict(zip(sa["seed"].astype(int).tolist(), a))
                b_dict = dict(zip(bl["seed"].astype(int).tolist(), b))
                common = sorted(set(a_dict) & set(b_dict))
                if len(common) < 2:
                    continue
                pa = np.array([a_dict[k] for k in common])
                pb = np.array([b_dict[k] for k in common])
                stat, p = _wilcoxon(pa, pb)
                d = _cohens_d(pa, pb)
                lo, hi = _bootstrap_ci(pa, pb)
                metric_results[m] = {
                    "wilcoxon_stat": stat,
                    "wilcoxon_p": p,
                    "cohens_d": d,
                    "ci95_low": lo,
                    "ci95_high": hi,
                    "n_pairs": len(common),
                }
            scenario_pair[baseline] = metric_results
        summary["pairwise_vs_shield_ai"][scenario] = scenario_pair

    return summary


def render_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# SHIELD-AI Statistical Report (N≥10)",
        "",
        f"_Generated by `scripts/eval/stats_report.py` from `results_N10/comparison_N*.csv`._",
        "",
        f"**N seeds:** {summary['n_seeds']}",
        f"**Operators:** {', '.join(summary['operators'])}",
        f"**Scenarios:** {', '.join(summary['scenarios'])}",
        "",
        "## 1. Per-scenario summary (mean ± std)",
        "",
    ]
    for scenario, ops in summary["by_scenario"].items():
        lines.append(f"### Scenario: {scenario}")
        lines.append("")
        lines.append("| Operator | n | scale_actions | heal_actions | error_rate | p95 (ms) | lag (s) | replicas_end |")
        lines.append("|---|---|---|---|---|---|---|---|")
        for op, row in ops.items():
            n = row["n"]
            sa = f"{row['scale_actions']['mean']:.2f}±{row['scale_actions']['std']:.2f}"
            ha = f"{row['heal_actions']['mean']:.2f}±{row['heal_actions']['std']:.2f}"
            er = f"{row['error_rate']['mean']:.3f}±{row['error_rate']['std']:.3f}"
            p95 = f"{row['p95_latency_ms']['mean']:.1f}±{row['p95_latency_ms']['std']:.1f}"
            lag = f"{row['scaling_lag_s']['mean']:.1f}±{row['scaling_lag_s']['std']:.1f}"
            re = f"{row['replicas_end']['mean']:.2f}±{row['replicas_end']['std']:.2f}"
            lines.append(f"| {op} | {n} | {sa} | {ha} | {er} | {p95} | {lag} | {re} |")
        lines.append("")

    lines.append("## 2. Pairwise SHIELD-AI vs each baseline (Wilcoxon + Cohen's d with 95% CI)")
    lines.append("")
    for scenario, baselines in summary["pairwise_vs_shield_ai"].items():
        lines.append(f"### Scenario: {scenario}")
        lines.append("")
        for baseline, metrics in baselines.items():
            lines.append(f"**SHIELD-AI vs {baseline}**")
            lines.append("")
            lines.append("| Metric | Wilcoxon p | Cohen's d | 95% CI low | 95% CI high | n |")
            lines.append("|---|---|---|---|---|---|")
            for m, r in metrics.items():
                lines.append(
                    f"| {m} | {r['wilcoxon_p']:.4f} | {r['cohens_d']:+.3f} | "
                    f"{r['ci95_low']:+.3f} | {r['ci95_high']:+.3f} | {r['n_pairs']} |"
                )
            lines.append("")
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Raw comparison CSV from run_N10.sh")
    parser.add_argument("--output", help="Markdown report output path")
    parser.add_argument("--json-out", help="JSON report output path")
    args = parser.parse_args(argv)

    df = pd.read_csv(args.input)
    summary = compute_summary(df)

    if args.output:
        md = render_markdown(summary)
        Path(args.output).write_text(md, encoding="utf-8")
        print(f"Wrote markdown report to {args.output}")
    if args.json_out:
        Path(args.json_out).write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print(f"Wrote JSON report to {args.json_out}")
    if not (args.output or args.json_out):
        print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
