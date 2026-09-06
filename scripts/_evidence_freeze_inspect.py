"""Inspect evidence sources cited by evidence-freeze.md."""
import json, sys

print("=" * 60)
print("SECTION B: Day-15 N=3 verification")
print("=" * 60)
fn = "data/evaluation/comparison_results_N3.csv"
with open(fn) as f:
    lines = f.readlines()
hdr = [x.strip() for x in lines[0].strip().split(",")]
print("header:", hdr)
ai = [l.strip().split(",") for l in lines[1:] if "ai" in l]
print("AI row count:", len(ai))
cols = {n: i for i, n in enumerate(hdr)}
errs = [r[cols["error_rate_pct"]] for r in ai]
rep_ends = [r[cols["replicas_end"]] for r in ai]
print("error_rate_pct values:", set(errs))
print("replicas_end values:", set(rep_ends))
print()
print("All 9 AI rows:")
for i, r in enumerate(ai):
    print(
        f"  row{20+i} ts={r[cols['timestamp']]} scen={r[cols['scenario']]} "
        f"err={r[cols['error_rate_pct']]} replicas={r[cols['replicas_start']]}"
        f"->{r[cols['replicas_end']]} shield_rej={r[cols['safety_rejected_count']]}"
    )

print()
print("=" * 60)
print("SECTION B: Day-15 single trial (superseded)")
print("=" * 60)
fn = "data/evaluation/comparison_results.csv"
with open(fn) as f:
    print(f.read())

print()
print("=" * 60)
print("SECTION C: Anomaly threshold pickle")
print("=" * 60)
import pickle
with open("data/anomaly_model.pkl", "rb") as f:
    obj = pickle.load(f)
print(f"type={type(obj).__name__}, len={len(obj)}")
print(f"threshold at index 1 = {obj[1]}")

print()
print("=" * 60)
print("SECTION A: N=10 statistics")
print("=" * 60)
fn = "results_N10/stats_report.json"
with open(fn) as f:
    s = json.load(f)
print("n_seeds:", s["n_seeds"])
print("operators:", s["operators"])
print("scenarios:", s["scenarios"])
print()
print("replicas_end (mean ± std) by (op, scenario):")
for scen in s["scenarios"]:
    for op in s["operators"]:
        d = s["by_scenario"][scen][op]["replicas_end"]
        print(f"  {op:10s} {scen:7s}: mean={d['mean']} std={d['std']} n={d.get('min','')}")

print()
print("Wilcoxon p + Cohen's d samples (first scenario):")
first_scen = list(s["pairwise_vs_shield_ai"].keys())[0]
for baseline, metrics in s["pairwise_vs_shield_ai"][first_scen].items():
    print(f"  shield-ai vs {baseline}:")
    for met, d in metrics.items():
        print(
            f"    {met:18s}: p={d['wilcoxon_p']:.4f} d={d['cohens_d']:+.3f} "
            f"CI=[{d['ci95_low']:+.3f}, {d['ci95_high']:+.3f}] n={d['n_pairs']}"
        )
    break  # only first baseline to keep output short

print()
print("=" * 60)
print("SECTION E: SafetyShield TLC")
print("=" * 60)
fn = "specs/tlc_run_safety_shield.txt"
with open(fn) as f:
    text = f.read()
for line in text.splitlines():
    if any(k in line for k in ["distinct states found", "states generated", "Finished in", "No error has been found"]):
        print("  ", line.strip())

print()
print("=" * 60)
print("SECTION E: ML_Composition TLC")
print("=" * 60)
fn = "specs/tlc_run_ml_composition.txt"
with open(fn) as f:
    text = f.read()
for line in text.splitlines():
    if any(k in line for k in ["distinct states found", "states generated", "Finished in", "No error has been found"]):
        print("  ", line.strip())

print()
print("=" * 60)
print("SECTION E: ML_Only counterexample TLC")
print("=" * 60)
fn = "specs/tlc_run_ml_only_counterexample.txt"
with open(fn) as f:
    text = f.read()
for line in text.splitlines():
    if any(k in line for k in ["distinct states found", "states generated", "Finished in", "violated"]):
        print("  ", line.strip())
