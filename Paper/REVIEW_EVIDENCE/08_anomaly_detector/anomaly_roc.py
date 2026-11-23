"""Offline ROC/PR evaluation of the anomaly detector and justification of its threshold.

Data: data/features_v2.csv (285 labelled 30 s windows; is_anomaly = 1 for the
spike and idle regimes, 0 for steady). Labels mark abnormal load regimes, not
injected faults.

Protocol (same detector and threshold rule as the live system, see train_ml.py):
  * MinMaxScaler | HalfSpaceTrees(n_trees=10, height=8, window_size=10, seed=42)
  * learn on the first 60 % of the normal windows (time order) only
  * threshold = 99th percentile of the scores on those training windows
  * test on the held-out 40 % normal windows + all abnormal windows
usage: python anomaly_roc.py data/features_v2.csv out_dir
"""
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from river import anomaly, compose, preprocessing
from sklearn.metrics import (auc, average_precision_score, precision_recall_curve,
                             roc_auc_score, roc_curve)

FEATS = ["cpu_percent", "memory_percent", "request_rate", "p95_latency_ms",
         "error_rate", "current_replicas", "hour_of_day", "day_of_week"]

src, out = sys.argv[1], Path(sys.argv[2])
out.mkdir(parents=True, exist_ok=True)
d = pd.read_csv(src).sort_values("timestamp").reset_index(drop=True)
normal = d[d.is_anomaly == 0]
n_train = int(0.6 * len(normal))
train = normal.iloc[:n_train]
test = pd.concat([normal.iloc[n_train:], d[d.is_anomaly == 1]])

model = compose.Pipeline(preprocessing.MinMaxScaler(),
                         anomaly.HalfSpaceTrees(n_trees=10, height=8, window_size=10, seed=42))
train_scores = []
for _, r in train.iterrows():
    x = {k: float(r[k]) for k in FEATS}
    train_scores.append(model.score_one(x))
    model.learn_one(x)
warm = train_scores[10:]
thr = float(np.percentile(warm, 99))

y = test.is_anomaly.to_numpy()
s = np.array([model.score_one({k: float(r[k]) for k in FEATS}) for _, r in test.iterrows()])


def point(t):
    pred = s > t
    tp = int(((pred == 1) & (y == 1)).sum()); fp = int(((pred == 1) & (y == 0)).sum())
    fn = int(((pred == 0) & (y == 1)).sum()); tn = int(((pred == 0) & (y == 0)).sum())
    prec = tp / (tp + fp) if tp + fp else float("nan")
    rec = tp / (tp + fn)
    return {"threshold": round(t, 4), "TP": tp, "FP": fp, "FN": fn, "TN": tn,
            "precision": round(prec, 3), "recall": round(rec, 3),
            "FPR": round(fp / (fp + tn), 3),
            "F1": round(2 * prec * rec / (prec + rec), 3) if tp else 0.0}


fpr, tpr, _ = roc_curve(y, s)
pr, rc, _ = precision_recall_curve(y, s)
res = {
    "data": src, "train_normal_windows": len(train),
    "test_normal_windows": int((y == 0).sum()), "test_abnormal_windows": int((y == 1).sum()),
    "roc_auc": round(float(roc_auc_score(y, s)), 3),
    "pr_auc_average_precision": round(float(average_precision_score(y, s)), 3),
    "threshold_p99": point(thr),
    "threshold_2x_p99_heal_gate": point(2 * thr),
    "per_regime_detection_at_p99": {
        sc: round(float((s[(test.scenario == sc).to_numpy()] > thr).mean()), 3)
        for sc in sorted(test.scenario.unique())},
}
(out / "anomaly_roc.json").write_text(json.dumps(res, indent=2))
print(json.dumps(res, indent=2))

fig, ax = plt.subplots(1, 2, figsize=(8, 3.3))
ax[0].plot(fpr, tpr, color="#2a6ebb"); ax[0].plot([0, 1], [0, 1], ":", color="grey")
p = res["threshold_p99"]
ax[0].scatter([p["FPR"]], [p["recall"]], color="#c0392b", zorder=3, label=f"p99 threshold ({thr:.3f})")
ax[0].set_xlabel("False-positive rate"); ax[0].set_ylabel("True-positive rate")
ax[0].set_title(f"ROC (AUC = {res['roc_auc']})"); ax[0].legend(fontsize=7, loc="lower right")
ax[1].plot(rc, pr, color="#2a6ebb")
ax[1].scatter([p["recall"]], [p["precision"]], color="#c0392b", zorder=3)
ax[1].axhline(y.mean(), ls=":", color="grey", label="chance")
ax[1].set_xlabel("Recall"); ax[1].set_ylabel("Precision")
ax[1].set_title(f"PR (AP = {res['pr_auc_average_precision']})"); ax[1].legend(fontsize=7)
fig.tight_layout(); fig.savefig(out / "fig_anomaly_roc_pr.png", dpi=200)
