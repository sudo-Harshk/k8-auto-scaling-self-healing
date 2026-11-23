"""Model preparation for the live evaluation (paper revision).

  init      create fresh, untrained models for the evaluation workload
  finalize  after the training trace: pick the anomaly threshold from the
            training-score distribution and report predictor accuracy

The training trace (scenario `train`, a random walk) is disjoint from the
three test scenarios (spike, diurnal, bursty).
"""
from __future__ import annotations

import json
import pickle
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402

from src.decision.decision_engine import demand_replicas  # noqa: E402
from src.models.anomaly_detector import AnomalyDetector  # noqa: E402
from src.models.replica_predictor import ReplicaPredictor  # noqa: E402

REPLICA = ROOT / "data" / "replica_model_eval.pkl"
ANOMALY = ROOT / "data" / "anomaly_model_eval.pkl"


def init() -> None:
    ReplicaPredictor(min_replicas=2, max_replicas=20, grace_period=10).save(REPLICA)
    det = AnomalyDetector(threshold=1.0)  # placeholder; set in finalize
    det.save(ANOMALY)
    print(f"fresh models -> {REPLICA}, {ANOMALY}")


def finalize(decisions_log: str, out_json: str) -> None:
    import os
    lo, hi = 2, 20
    rows = [json.loads(l) for l in open(decisions_log, encoding="utf-8") if l.strip()]
    feats = [r["features"] for r in rows]

    # 1. Re-fit the anomaly detector on the training windows; threshold =
    #    99th percentile of the training scores (i.e. ~1 % false-alarm budget).
    # River's HalfSpaceTrees assumes features in [0, 1]; without scaling every
    # window falls into the same mass region and scores 0. Standard River usage
    # is MinMaxScaler | HalfSpaceTrees.
    from river import anomaly, compose, preprocessing
    det = AnomalyDetector(threshold=None)
    det.model = compose.Pipeline(
        preprocessing.MinMaxScaler(),
        anomaly.HalfSpaceTrees(n_trees=10, height=8, window_size=10, seed=42))
    scores = []
    for f in feats:
        scores.append(det.score(f))
        det.learn(f)
    warm = scores[10:] or scores
    thr = float(np.percentile(warm, 99))
    det.set_threshold(thr)
    det.save(ANOMALY)

    # 2. Prequential (predict-then-learn) accuracy of the forecasting label on
    #    the training trace, re-run on a fresh model for an unbiased figure.
    m = ReplicaPredictor(min_replicas=lo, max_replicas=hi, grace_period=10)
    errs, naive = [], []
    for prev, cur in zip(feats[:-1], feats[1:]):
        y = demand_replicas(cur, lo, hi)
        yhat = m.predict(prev)
        errs.append(abs(yhat - y))
        naive.append(abs(int(round(prev.get("current_replicas") or lo)) - y))
        m.learn(prev, y)
    # Retrain the shipped model with 3 passes over the training trace.
    final = ReplicaPredictor(min_replicas=lo, max_replicas=hi, grace_period=10)
    for _ in range(3):
        for prev, cur in zip(feats[:-1], feats[1:]):
            final.learn(prev, demand_replicas(cur, lo, hi))
    final.save(REPLICA)

    res = {
        "training_windows": len(feats),
        "anomaly_threshold_p99": thr,
        "anomaly_score_mean": float(np.mean(warm)),
        "anomaly_score_p50": float(np.percentile(warm, 50)),
        "anomaly_score_p95": float(np.percentile(warm, 95)),
        "predictor_prequential_MAE": float(np.mean(errs)) if errs else None,
        "predictor_prequential_RMSE": float(np.sqrt(np.mean(np.square(errs)))) if errs else None,
        "naive_last_value_MAE": float(np.mean(naive)) if naive else None,
        "req_per_replica": float(os.environ.get("REQ_PER_REPLICA", "15")),
    }
    Path(out_json).write_text(json.dumps(res, indent=2))
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    if sys.argv[1] == "init":
        init()
    else:
        finalize(sys.argv[2], sys.argv[3])
