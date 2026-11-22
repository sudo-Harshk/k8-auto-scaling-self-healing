"""Analyse live evaluation runs -> per-run metrics, statistics, figures.

usage: python scripts/eval/live/analyze.py results_live/runs results_live/analysis

Metric definitions (stated identically in the paper, Sec. "Metrics"):
  p95_ms / p99_ms     end-to-end latency percentiles over the whole run (Locust)
  error_pct           failed requests (non-2xx or > 2 s timeout) / all requests
  slo_viol_pct        % of 1-s intervals whose p95 > SLO_MS or error ratio > 1 %
  replica_min         integral of spec.replicas over the run (replica-minutes; cost)
  underprov_pct       % of time with spec.replicas < demand, where
                      demand = ceil(offered_rps / REQ_PER_REPLICA)
  scale_events        number of changes of spec.replicas
  oscillations        number of direction reversals of spec.replicas
  policy_viol         replica changes that break the v2 safety policy
                      (up-step > max(4, current), down-step > 2,
                       up < 15 s or down < 60 s after the previous change)
  reaction_s          (spike) seconds from the load step (t=60 s) to first scale-up
  recovery_s          (spike) seconds from the load step until the SLO holds again
                      for 20 consecutive seconds
"""
from __future__ import annotations

import math
import sys
from itertools import combinations  # noqa: F401
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from scipy import stats  # noqa: E402

OPS = ["hpa", "keda", "mt", "ml-only", "shield-ai"]
LABEL = {"hpa": "HPA", "keda": "KEDA", "mt": "MT (FIRM-inspired)",
         "ml-only": "ML-only", "shield-ai": "SHIELD-AI"}
COLOR = {"hpa": "#4C72B0", "keda": "#DD8452", "mt": "#8172B3",
         "ml-only": "#C44E52", "shield-ai": "#55A868"}
METRICS = ["p95_ms", "p99_ms", "error_pct", "slo_viol_pct", "replica_min",
           "underprov_pct", "scale_events", "oscillations", "policy_viol",
           "reaction_s", "recovery_s"]
LOWER_IS_BETTER = set(METRICS)


def read_meta(d: Path) -> dict:
    out = {}
    for line in (d / "meta.env").read_text().splitlines():
        k, _, v = line.partition("=")
        out[k] = v
    return out


def policy_violations(ch: pd.DataFrame) -> int:
    v, last_t = 0, None
    for _, r in ch.iterrows():
        d = r.new - r.old
        if d > max(4, r.old) or -d > 2:
            v += 1
        if last_t is not None:
            gap = r.t - last_t
            if (d > 0 and gap < 15 - 2) or (d < 0 and gap < 60 - 2):  # 2 s sampling slack
                v += 1
        last_t = r.t
    return v


def run_metrics(d: Path) -> tuple[dict, pd.DataFrame, pd.DataFrame]:
    m = read_meta(d)
    slo = float(m["slo_ms"]); rpr = float(m["req_per_replica"]); dur = float(m["duration"])
    t0 = float((d / "load_start_epoch").read_text().strip())

    st = pd.read_csv(d / "run_stats.csv")
    agg = st[st["Name"] == "Aggregated"].iloc[0]
    hist = pd.read_csv(d / "run_stats_history.csv")
    hist = hist[(hist["Name"] == "Aggregated") & (hist["Timestamp"] > 1e9)].copy()
    hist["t"] = hist["Timestamp"] - hist["Timestamp"].min()
    h = hist[(hist["t"] >= 5) & (hist["Requests/s"] > 0)]
    bad = (h["95%"] > slo) | (h["Failures/s"] > 0.01 * h["Requests/s"])

    rep = pd.read_csv(d / "replicas.csv").dropna()
    rep["t"] = rep["epoch"] - t0
    rep = rep[(rep["t"] >= 0) & (rep["t"] <= dur)].reset_index(drop=True)
    rep["spec_replicas"] = rep["spec_replicas"].astype(float)

    # replica-minutes (step integral)
    tt = rep["t"].to_numpy(); rr = rep["spec_replicas"].to_numpy()
    rmin = float(np.sum(rr[:-1] * np.diff(tt)) / 60.0) if len(tt) > 1 else float("nan")

    # demand from the offered load (users == offered req/s under constant pacing)
    users = hist.set_index("t")["User Count"]
    off = np.interp(tt, users.index.to_numpy(), users.to_numpy())
    demand = np.clip(np.ceil(off / rpr), 2, 20)
    under = float(np.mean(rr < demand) * 100)

    ch = rep.loc[rep["spec_replicas"].diff().fillna(0) != 0, ["t", "spec_replicas"]].copy()
    ch["old"] = rep["spec_replicas"].shift(1).loc[ch.index]
    ch["new"] = ch["spec_replicas"]
    deltas = np.sign(ch["new"] - ch["old"]).to_numpy()
    osc = int(np.sum(deltas[1:] != deltas[:-1])) if len(deltas) > 1 else 0

    res = {
        "scenario": m["scenario"], "op": m["op"], "seed": int(m["seed"]),
        "p95_ms": float(agg["95%"]), "p99_ms": float(agg["99%"]),
        "mean_ms": float(agg["Average Response Time"]),
        "requests": int(agg["Request Count"]),
        "error_pct": 100.0 * float(agg["Failure Count"]) / max(float(agg["Request Count"]), 1),
        "slo_viol_pct": float(bad.mean() * 100) if len(h) else float("nan"),
        "replica_min": rmin, "mean_replicas": float(np.mean(rr)), "max_replicas": float(np.max(rr)),
        "underprov_pct": under, "scale_events": int(len(ch)), "oscillations": osc,
        "policy_viol": policy_violations(ch),
        "reaction_s": float("nan"), "recovery_s": float("nan"),
    }
    if m["scenario"] == "spike":
        up = ch[(ch["t"] >= 60) & (ch["new"] > ch["old"])]
        res["reaction_s"] = float(up["t"].iloc[0] - 60) if len(up) else float(dur - 60)
        after = h[h["t"] >= 60].copy()
        after["ok"] = ~((after["95%"] > slo) | (after["Failures/s"] > 0.01 * after["Requests/s"]))
        rec = float(dur - 60)
        ok = after["ok"].to_numpy(); ts = after["t"].to_numpy()
        for i in range(len(ok)):
            j = i
            while j < len(ok) and ok[j] and ts[j] - ts[i] < 20:
                j += 1
            if j < len(ok) and ok[i:j + 1].all() and ts[j] - ts[i] >= 20:
                rec = float(ts[i] - 60); break
        res["recovery_s"] = rec

    # shield accounting
    sa = d / "safety_audit.log"
    if sa.exists():
        import json
        recs = [json.loads(x) for x in sa.read_text().splitlines() if x.strip()]
        res["shield_validated"] = len(recs)
        res["shield_modified"] = sum(1 for r in recs if r["modifications"] and not r["rejected"])
        res["shield_rejected"] = sum(1 for r in recs if r["rejected"])
    rep_out = rep.assign(demand=demand)
    return res, rep_out, hist


def cliffs_delta(a, b) -> float:
    a, b = np.asarray(a), np.asarray(b)
    if len(a) == 0 or len(b) == 0:
        return float("nan")
    gt = sum((x > y) for x in a for y in b); lt = sum((x < y) for x in a for y in b)
    return (gt - lt) / (len(a) * len(b))


def holm(pvals: list[float]) -> list[float]:
    idx = np.argsort(pvals); m = len(pvals); adj = [0.0] * m; run = 0.0
    for k, i in enumerate(idx):
        run = max(run, (m - k) * pvals[i]); adj[i] = min(1.0, run)
    return adj


def main(runs_dir: str, out_dir: str) -> None:
    runs = sorted(p for p in Path(runs_dir).iterdir() if (p / "DONE").exists())
    out = Path(out_dir); (out / "fig").mkdir(parents=True, exist_ok=True)
    rows, traces = [], {}
    for d in runs:
        try:
            r, rep, hist = run_metrics(d)
        except Exception as exc:  # noqa: BLE001
            print(f"!! {d.name}: {exc}"); continue
        rows.append(r); traces[(r["scenario"], r["op"], r["seed"])] = (rep, hist)
    df = pd.DataFrame(rows)
    df.to_csv(out / "per_run_metrics.csv", index=False)
    print(f"{len(df)} runs analysed")

    # ---------- summary table mean ± SD ----------
    lines = ["# Live evaluation results\n",
             f"Runs: {len(df)}. Values: mean ± SD over seeds (n per cell shown).\n"]
    summ = []
    for sc in sorted(df["scenario"].unique()):
        lines.append(f"\n## Scenario: {sc}\n")
        cols = [c for c in METRICS if not (sc != "spike" and c in ("reaction_s", "recovery_s"))]
        lines.append("| Operator | n | " + " | ".join(cols) + " |")
        lines.append("|---|---|" + "---|" * len(cols))
        for op in OPS:
            g = df[(df.scenario == sc) & (df.op == op)]
            if g.empty:
                continue
            cells = []
            for c in cols:
                mu, sd = g[c].mean(), g[c].std(ddof=1)
                cells.append(f"{mu:.1f} ± {sd:.1f}" if not math.isnan(mu) else "–")
                summ.append({"scenario": sc, "op": op, "metric": c, "mean": mu, "sd": sd, "n": len(g)})
            lines.append(f"| {LABEL[op]} | {len(g)} | " + " | ".join(cells) + " |")
    pd.DataFrame(summ).to_csv(out / "summary_mean_sd.csv", index=False)

    # ---------- significance: SHIELD-AI vs each other operator ----------
    lines.append("\n## SHIELD-AI vs. each baseline (two-sided Mann–Whitney U, Holm-corrected per scenario×metric family; Cliff's δ, negative = SHIELD-AI lower)\n")
    sig = []
    for sc in sorted(df["scenario"].unique()):
        s = df[(df.scenario == sc) & (df.op == "shield-ai")]
        for c in METRICS:
            fam = []
            for op in OPS:
                if op == "shield-ai":
                    continue
                o = df[(df.scenario == sc) & (df.op == op)]
                a, b = s[c].dropna(), o[c].dropna()
                if len(a) < 2 or len(b) < 2:
                    continue
                if np.allclose(np.r_[a, b], np.r_[a, b][0]):
                    p = 1.0
                else:
                    p = float(stats.mannwhitneyu(a, b, alternative="two-sided").pvalue)
                fam.append({"scenario": sc, "metric": c, "vs": op, "p": p,
                            "cliffs_delta": cliffs_delta(a, b),
                            "shield_median": float(np.median(a)), "other_median": float(np.median(b))})
            if fam:
                adj = holm([f["p"] for f in fam])
                for f, pa in zip(fam, adj):
                    f["p_holm"] = pa
                sig.extend(fam)
    sg = pd.DataFrame(sig)
    sg.to_csv(out / "significance.csv", index=False)
    if not sg.empty:
        lines.append("| Scenario | Metric | vs | SHIELD median | other median | δ | p (Holm) |")
        lines.append("|---|---|---|---|---|---|---|")
        for _, r in sg.iterrows():
            lines.append(f"| {r.scenario} | {r.metric} | {LABEL[r.vs]} | {r.shield_median:.1f} | "
                         f"{r.other_median:.1f} | {r.cliffs_delta:+.2f} | {r.p_holm:.3f} |")

    # ---------- shield accounting ----------
    if "shield_validated" in df:
        s = df[df.op == "shield-ai"][["scenario", "seed", "shield_validated", "shield_modified", "shield_rejected"]]
        lines.append("\n## Shield accounting (SHIELD-AI runs)\n")
        lines.append(s.groupby("scenario")[["shield_validated", "shield_modified", "shield_rejected"]]
                     .sum().to_markdown())
    (out / "RESULTS.md").write_text("\n".join(lines), encoding="utf-8")

    # ---------- figures ----------
    plt.rcParams.update({"font.size": 9, "figure.dpi": 150})
    for sc in sorted(df["scenario"].unique()):
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(7, 5.2), sharex=True)
        grid = np.arange(0, 361, 2)
        dem_done = False
        for op in OPS:
            reps = [traces[k] for k in traces if k[0] == sc and k[1] == op]
            if not reps:
                continue
            R = np.array([np.interp(grid, r[0]["t"], r[0]["spec_replicas"]) for r in reps])
            ax1.plot(grid, R.mean(0), color=COLOR[op], label=LABEL[op], lw=1.4)
            ax1.fill_between(grid, R.min(0), R.max(0), color=COLOR[op], alpha=0.12)
            if not dem_done:
                D = np.array([np.interp(grid, r[0]["t"], r[0]["demand"]) for r in reps])
                ax1.plot(grid, D.mean(0), "k--", lw=1, label="demand")
                dem_done = True
            P = []
            for r in reps:
                h = r[1]
                P.append(np.interp(grid, h["t"], h["95%"]))
            ax2.plot(grid, np.median(P, 0), color=COLOR[op], lw=1.2)
        slo = float(read_meta(runs[0])["slo_ms"])
        ax2.axhline(slo, color="k", ls=":", lw=1); ax2.set_yscale("log")
        ax1.set_ylabel("replicas"); ax2.set_ylabel("p95 latency (ms)"); ax2.set_xlabel("time (s)")
        ax1.legend(ncol=3, fontsize=7, loc="upper left"); ax1.set_title(f"Scenario: {sc}")
        fig.tight_layout(); fig.savefig(out / "fig" / f"timeline_{sc}.png"); plt.close(fig)

    for c in ["slo_viol_pct", "replica_min", "oscillations", "policy_viol", "p95_ms"]:
        fig, ax = plt.subplots(figsize=(7, 3))
        scs = sorted(df["scenario"].unique()); w = 0.16
        for i, op in enumerate(OPS):
            mu = [df[(df.scenario == s) & (df.op == op)][c].mean() for s in scs]
            sd = [df[(df.scenario == s) & (df.op == op)][c].std(ddof=1) for s in scs]
            ax.bar(np.arange(len(scs)) + (i - 2) * w, mu, w, yerr=sd, color=COLOR[op], label=LABEL[op], capsize=2)
        ax.set_xticks(range(len(scs))); ax.set_xticklabels(scs); ax.set_ylabel(c)
        ax.legend(ncol=5, fontsize=6); fig.tight_layout(); fig.savefig(out / "fig" / f"bar_{c}.png"); plt.close(fig)
    print(f"-> {out}/RESULTS.md, figures in {out}/fig")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
