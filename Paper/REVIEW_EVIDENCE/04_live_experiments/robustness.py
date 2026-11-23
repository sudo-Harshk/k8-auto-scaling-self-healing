"""Hardware-blocked robustness check.
Seeds 1-3 ran on VM A (Standard_D4as_v4), seeds 4-5 on VM B (Standard_D4ads_v7).
Within one seed all five controllers ran on the same VM, so a per-seed
comparison removes the hardware effect.
usage: python robustness.py results_live/analysis/per_run_metrics.csv out.md"""
import sys, pandas as pd
d = pd.read_csv(sys.argv[1]); d["vm"] = d.seed.map(lambda s: "A (D4as_v4)" if s <= 3 else "B (D4ads_v7)")
out = ["# Hardware-blocked robustness check\n",
       "Seeds 1-3: VM A (Standard_D4as_v4); seeds 4-5: VM B (Standard_D4ads_v7); both 4 vCPU / 16 GB.\n",
       "## Per-VM means\n"]
M = ["slo_viol_pct", "error_pct", "p95_ms", "replica_min", "oscillations", "policy_viol"]
for m in M:
    out += [f"\n### {m}\n", d.groupby(["scenario", "vm", "op"])[m].mean().unstack("op").round(1).to_markdown(), ""]
out.append("\n## Seeds (of 5) in which SHIELD-AI is strictly lower than the baseline, same seed and same VM\n")
rows = []
for sc in sorted(d.scenario.unique()):
    p = d[d.scenario == sc].pivot_table(index="seed", columns="op", values=M)
    for b in ["hpa", "keda", "mt", "ml-only"]:
        r = {"scenario": sc, "vs": b}
        for m in M:
            r[m] = f"{int((p[m]['shield-ai'] < p[m][b]).sum())}/5"
        rows.append(r)
out.append(pd.DataFrame(rows).to_markdown(index=False))
open(sys.argv[2], "w", encoding="utf-8").write("\n".join(out)); print("\n".join(out[-1:]))
