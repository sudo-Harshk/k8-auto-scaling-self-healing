#!/usr/bin/env python3
"""
Helper to run the stats harness from PowerShell where bash env-var passing is awkward.
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

N = int(sys.argv[1]) if len(sys.argv) > 1 else 3
out_csv = ROOT / "results_N10" / f"comparison_N{N}.csv"
out_csv.parent.mkdir(exist_ok=True)
out_csv.unlink(missing_ok=True)

operators = ["hpa", "keda", "firm", "shield-ai"]
scenarios = ["spike", "steady", "idle"]

count = 0
for seed in range(1, N + 1):
    for op in operators:
        for scen in scenarios:
            count += 1
            print(f"  [{count}/{N*12}] seed={seed} {op} x {scen}")
            subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "eval" / "run_one_trial.py"),
                    "--operator", op,
                    "--scenario", scen,
                    "--seed", str(seed),
                    "--csv-out", str(out_csv),
                ],
                check=True,
                cwd=ROOT,
            )

# Stats report
subprocess.run(
    [
        sys.executable,
        str(ROOT / "scripts" / "eval" / "stats_report.py"),
        "--input", str(out_csv),
        "--output", str(ROOT / "results_N10" / "stats_report.md"),
        "--json-out", str(ROOT / "results_N10" / "stats_report.json"),
    ],
    check=True,
    cwd=ROOT,
)

print("Done. See:")
print(f"  {out_csv}")
print(f"  {ROOT / 'results_N10' / 'stats_report.md'}")
print(f"  {ROOT / 'results_N10' / 'stats_report.json'}")
