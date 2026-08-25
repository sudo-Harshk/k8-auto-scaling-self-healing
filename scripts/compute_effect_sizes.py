"""
Day 15 - Cohen's d + statistical analysis of the N=3 comparison.

Reads `data/evaluation/comparison_results_N3.csv` (or `comparison_results.csv`
as fallback) and computes for each (operator, scenario, metric):
  - mean
  - std
  - Cohen's d between AI vs HPA, AI vs KEDA
  - p95 latency mean / max
  - error rate mean
  - total scale/heal actions

Output: `data/evaluation/effect_sizes.md` (human-readable report)

Run with:
    docker run --rm -v $PWD:/code -w /code --entrypoint python k8-ai-ops:dev \
        scripts/compute_effect_sizes.py
"""
from __future__ import annotations

import logging
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
N3_CSV = ROOT / "data" / "evaluation" / "comparison_results_N3.csv"
FALLBACK_CSV = ROOT / "data" / "evaluation" / "comparison_results.csv"
OUT_MD = ROOT / "data" / "evaluation" / "effect_sizes.md"

LOG = logging.getLogger("effect_sizes")


def cohen_d(a: list[float], b: list[float]) -> float:
    """Compute Cohen's d between two samples."""
    if len(a) < 2 or len(b) < 2:
        return float("nan")
    mean_a = sum(a) / len(a)
    mean_b = sum(b) / len(b)
    var_a = sum((x - mean_a) ** 2 for x in a) / (len(a) - 1)
    var_b = sum((x - mean_b) ** 2 for x in b) / (len(b) - 1)
    pooled_std = math.sqrt((var_a + var_b) / 2)
    if pooled_std == 0:
        return 0.0
    return (mean_a - mean_b) / pooled_std


def safe_float(s) -> float:
    try:
        return float(s)
    except (ValueError, TypeError):
        return float("nan")


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    csv_path = N3_CSV if N3_CSV.exists() else FALLBACK_CSV
    LOG.info("Reading %s", csv_path)

    # Read CSV manually (no pandas dependency to avoid version mismatch)
    rows = []
    with open(csv_path) as f:
        header = f.readline().strip().split(",")
        for line in f:
            values = line.strip().split(",")
            rows.append(dict(zip(header, values)))
    LOG.info("Read %d rows", len(rows))

    # Group by (operator, scenario)
    groups: dict[tuple[str, str], list[dict]] = {}
    for r in rows:
        key = (r["operator"], r["scenario"])
        groups.setdefault(key, []).append(r)

    # Metrics to analyze
    metric_cols = [
        ("scaling_lag_s", "Scaling lag (s)", True),  # lower is better
        ("p95_latency_ms_avg", "p95 latency avg (ms)", True),
        ("p95_latency_ms_max", "p95 latency max (ms)", True),
        ("error_rate_pct", "Error rate (%)", True),
        ("total_scale_actions", "Total scale actions", False),
        ("total_heal_actions", "Total heal actions", False),
    ]

    scenarios = sorted({s for _, s in groups.keys()})
    lines = []
    lines.append("# Effect sizes: AI vs HPA / KEDA")
    lines.append("")
    lines.append(f"Source: `{csv_path.relative_to(ROOT)}` ({len(rows)} rows)")
    lines.append("")
    lines.append("Cohen's d interpretation (positive = AI better than baseline):")
    lines.append("- |d| < 0.2: negligible")
    lines.append("- 0.2 <= |d| < 0.5: small")
    lines.append("- 0.5 <= |d| < 0.8: medium")
    lines.append("- |d| >= 0.8: large")
    lines.append("")

    for scenario in scenarios:
        lines.append(f"## Scenario: {scenario}")
        lines.append("")
        for col, label, lower_better in metric_cols:
            ai_vals = [safe_float(r[col]) for r in groups.get(("ai", scenario), [])]
            hpa_vals = [safe_float(r[col]) for r in groups.get(("hpa", scenario), [])]
            keda_vals = [safe_float(r[col]) for r in groups.get(("keda", scenario), [])]

            # Skip if any group has no data
            if not any(v == v for v in ai_vals + hpa_vals + keda_vals):
                continue

            d_ai_hpa = cohen_d(ai_vals, hpa_vals) if hpa_vals else float("nan")
            d_ai_keda = cohen_d(ai_vals, keda_vals) if keda_vals else float("nan")

            # Flip sign so positive = AI better when lower_better
            if lower_better:
                d_ai_hpa = -d_ai_hpa
                d_ai_keda = -d_ai_keda

            ai_mean = sum(v for v in ai_vals if v == v) / max(1, sum(1 for v in ai_vals if v == v))
            hpa_mean = sum(v for v in hpa_vals if v == v) / max(1, sum(1 for v in hpa_vals if v == v))
            keda_mean = sum(v for v in keda_vals if v == v) / max(1, sum(1 for v in keda_vals if v == v))

            lines.append(f"### {label}")
            lines.append(f"- AI:   {ai_mean:.2f} (n={len(ai_vals)})")
            lines.append(f"- HPA:  {hpa_mean:.2f} (n={len(hpa_vals)})")
            lines.append(f"- KEDA: {keda_mean:.2f} (n={len(keda_vals)})")
            if not math.isnan(d_ai_hpa):
                interp = ("large" if abs(d_ai_hpa) >= 0.8 else
                          "medium" if abs(d_ai_hpa) >= 0.5 else
                          "small" if abs(d_ai_hpa) >= 0.2 else "negligible")
                lines.append(f"- Cohen's d (AI vs HPA): **{d_ai_hpa:+.2f}** ({interp})")
            if not math.isnan(d_ai_keda):
                interp = ("large" if abs(d_ai_keda) >= 0.8 else
                          "medium" if abs(d_ai_keda) >= 0.5 else
                          "small" if abs(d_ai_keda) >= 0.2 else "negligible")
                lines.append(f"- Cohen's d (AI vs KEDA): **{d_ai_keda:+.2f}** ({interp})")
            lines.append("")

    OUT_MD.write_text("\n".join(lines))
    LOG.info("Wrote %s", OUT_MD)
    return 0


if __name__ == "__main__":
    sys.exit(main())
