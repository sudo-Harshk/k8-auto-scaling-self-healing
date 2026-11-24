"""Analyse the self-healing study (results_live/heal_runs).

Per run (window = fault time .. end of load; for FAULT=0 runs a nominal fault
time of load_start + FAULT_AT is used so the windows are comparable):
  slo_viol_pct   % of 1 s Locust intervals with p95 > SLO or failure ratio > 1 %
  error_pct      failed / total requests in the window
  p95_mean_ms    mean of the per-second p95 in the window
  recovery_s     seconds from the fault until the SLO holds for 20 s in a row
                 (censored at the end of the run)
  heals          applied heal actions (actuator log)
  correct_heal   first applied heal after the fault deleted the faulty pod
  detect_s       fault -> first applied heal
  false_heals    applied heals in FAULT=0 runs, before the fault, or on a healthy pod
usage: python analyze_heal.py results_live/heal_runs results_live/heal_analysis
"""
import json
import sys
from datetime import datetime
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu

ARMS = {"shield-heal": "SHIELD-AI (heal)", "shield-heal-gated": "SHIELD-AI (heal, anomaly-gated)", "shield-noheal": "SHIELD-AI (no heal)", "hpa": "HPA"}
M = ["slo_viol_pct", "error_pct", "p95_mean_ms", "recovery_s", "heals",
     "correct_heal", "detect_s", "false_heals"]


def meta(d):
    return dict(l.strip().split("=", 1) for l in open(d / "meta.env") if "=" in l)


def ts(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()


def run_metrics(d):
    m = meta(d); slo = float(m["slo_ms"]); fault = m["fault"] == "1"
    t0 = float(open(d / "load_start_epoch").read())
    f = json.load(open(d / "fault.json")) if (d / "fault.json").exists() else None
    tf = f["epoch"] if f else t0 + float(m["fault_at"])
    h = pd.read_csv(d / "run_stats_history.csv")
    h = h[(h["Name"] == "Aggregated") & (h["Timestamp"] > 1e9)].copy()
    w = h[h["Timestamp"] >= tf]
    rps = w["Requests/s"].clip(lower=1e-9)
    bad = (w["95%"] > slo) | ((w["Failures/s"] / rps) > 0.01)
    rec = float(w["Timestamp"].max() - tf) if len(w) else float("nan")
    run = 0
    for t, b in zip(w["Timestamp"], bad):
        run = 0 if b else run + 1
        if run >= 20:
            rec = float(t - 19 - tf); break
    heals = []
    p = d / "operator_actions.log"
    if p.exists():
        for l in open(p):
            if l.strip():
                a = json.loads(l)
                if a.get("action") == "heal" and a.get("applied"):
                    heals.append((ts(a["timestamp"]), a.get("pod_name")))
    after = [x for x in heals if x[0] >= tf]
    first = after[0] if after else None
    correct = bool(fault and first and f and first[1] == f["pod"])
    false = len(heals) if not fault else sum(1 for t, pod in heals if t < tf or (f and pod != f["pod"]))
    tot_req = w["Requests/s"].sum(); tot_fail = w["Failures/s"].sum()
    return {"arm": m["arm"], "fault": int(fault), "seed": int(m["seed"]),
            "slo_viol_pct": float(bad.mean() * 100) if len(w) else float("nan"),
            "error_pct": float(100 * tot_fail / tot_req) if tot_req else float("nan"),
            "p95_mean_ms": float(w["95%"].mean()), "recovery_s": rec,
            "heals": len(heals), "correct_heal": int(correct),
            "detect_s": float(first[0] - tf) if (fault and first) else float("nan"),
            "false_heals": int(false), "fault_pod": f["pod"] if f else ""}


def cliffs(a, b):
    a, b = np.asarray(a), np.asarray(b)
    return float(((a[:, None] > b[None, :]).sum() - (a[:, None] < b[None, :]).sum()) / (len(a) * len(b)))


def main(src, out):
    out = Path(out); out.mkdir(parents=True, exist_ok=True)
    runs = sorted(p for p in Path(src).iterdir() if (p / "DONE").exists() and "__s99" not in p.name)
    # A fault run without fault.json means the injection failed: no pod was frozen.
    bad = [p for p in runs if "__f1__" in p.name and not (p / "fault.json").exists()]
    runs = [p for p in runs if p not in bad]
    df = pd.DataFrame([run_metrics(d) for d in runs])
    df.to_csv(out / "heal_per_run.csv", index=False)
    lines = ["# Self-healing study\n", f"Runs: {len(df)} (pilot seed 99 excluded).\n"]
    if bad:
        lines.append("Excluded (fault injection failed, no fault.json): " + ", ".join(p.name for p in bad) + "\n")
    for fault in (1, 0):
        sub = df[df.fault == fault]
        if sub.empty:
            continue
        lines.append(f"\n## {'Fault injected' if fault else 'No fault (false-heal control)'}\n")
        g = sub.groupby("arm")[M]
        tab = g.mean().round(2).astype(str) + " ± " + g.std().round(2).astype(str)
        tab.insert(0, "n", sub.groupby("arm").size())
        tab.index = [ARMS.get(i, i) for i in tab.index]
        lines.append(tab.to_markdown())
    rows = []
    f1 = df[df.fault == 1]
    for a, b in combinations(ARMS, 2):
        for metric in ["slo_viol_pct", "error_pct", "p95_mean_ms", "recovery_s"]:
            x = f1[f1.arm == a][metric].dropna(); y = f1[f1.arm == b][metric].dropna()
            if len(x) >= 2 and len(y) >= 2:
                p = mannwhitneyu(x, y, alternative="two-sided").pvalue
                rows.append({"metric": metric, "a": ARMS[a], "b": ARMS[b],
                             "median_a": x.median(), "median_b": y.median(),
                             "cliffs_delta": round(cliffs(x, y), 2), "p": p})
    if rows:
        st = pd.DataFrame(rows)
        st["p_holm"] = np.nan
        for metric, g in st.groupby("metric"):          # Holm within each metric family
            order = g["p"].sort_values().index
            k = len(order); run = 0.0
            for i, idx in enumerate(order):
                run = max(run, min(1.0, (k - i) * st.at[idx, "p"])); st.at[idx, "p_holm"] = run
        st.to_csv(out / "heal_significance.csv", index=False)
        lines += ["\n## Pairwise tests (fault runs; two-sided Mann–Whitney U, Holm within metric)\n",
                  st.round(4).to_markdown(index=False)]
    # Pre-registered extension test (PREREGISTRATION.md): heal vs no heal, all seeds
    h = f1[f1.arm == "shield-heal"]; n = f1[f1.arm == "shield-noheal"]
    if len(h) >= 2 and len(n) >= 2:
        from scipy.stats import fisher_exact
        p1 = mannwhitneyu(h.recovery_s, n.recovery_s, alternative="two-sided").pvalue
        dh = int((h.recovery_s >= 230).sum()); dn = int((n.recovery_s >= 230).sum())
        p2 = fisher_exact([[dh, len(h) - dh], [dn, len(n) - dn]]).pvalue
        lines += ["\n## Pre-registered test: heal vs no heal (fault runs, all seeds)\n",
                  f"n = {len(h)} vs {len(n)}",
                  f"- Primary, time to recover: median {h.recovery_s.median():.0f} s vs {n.recovery_s.median():.0f} s, "
                  f"Mann–Whitney p = {p1:.4f}, Cliff's δ = {cliffs(h.recovery_s, n.recovery_s):.2f}",
                  f"- Secondary, still degraded at end (recovery ≥ 230 s): {dh}/{len(h)} vs {dn}/{len(n)}, "
                  f"Fisher exact p = {p2:.4f}"]
    (out / "HEAL_RESULTS.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
