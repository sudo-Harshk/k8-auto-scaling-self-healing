"""Day 8 Anomaly Detector: River HalfSpaceTrees on the Day-6 feature dataset.

HalfSpaceTrees is an unsupervised online anomaly detector. We train it on the
`is_anomaly=0` (normal) rows — baseline + steady_high — then score the
`is_anomaly=1` (spike + idle) rows and choose a threshold that separates the
two score distributions.

Higher `score_one` value = more anomalous. The threshold is selected as the
midpoint between the max normal score and the min abnormal score (computed on
the offline dataset). The threshold is saved with the model so Day 9 can call
`is_anomaly(features)` directly.

Run (inside the shared Docker image — river is already installed):

    docker run --rm -v $HOME/k8-auto-scaling-self-healing:/code -w /code \
        k8-ai-ops:dev src/models/anomaly_detector.py

Environment variables:
    FEATURES_CSV      input dataset, default data/features.csv
    MODEL_PATH        output model path, default data/anomaly_model.pkl
"""
from __future__ import annotations

import logging
import os
import pickle
from pathlib import Path

import pandas as pd
from river.anomaly import HalfSpaceTrees

ROOT = Path(__file__).resolve().parents[2]

LOG = logging.getLogger("anomaly_detector")

FEATURES = [
    "cpu_percent",
    "memory_percent",
    "request_rate",
    "p95_latency_ms",
    "error_rate",
    "current_replicas",
    "hour_of_day",
    "day_of_week",
]

DEFAULT_FEATURES_CSV = ROOT / "data" / "features.csv"
DEFAULT_MODEL_PATH = ROOT / "data" / "anomaly_model.pkl"


class AnomalyDetector:
    """Online anomaly detector backed by River HalfSpaceTrees.

    Higher `score()` value indicates more anomalous input. `is_anomaly()` returns
    `True` when the score exceeds the (configurable) threshold. The threshold is
    fitted offline by `train_offline()` and persisted with the model so callers
    do not need to know it.
    """

    def __init__(
        self,
        threshold: float | None = None,
        n_trees: int = 10,
        height: int = 8,
        window_size: int = 10,
        seed: int = 42,
    ) -> None:
        self.model = HalfSpaceTrees(
            n_trees=n_trees,
            height=height,
            window_size=window_size,
            seed=seed,
        )
        self.threshold = threshold
        self._trained_count = 0

    def _features(self, row: dict) -> dict:
        return {k: float(row[k]) for k in FEATURES}

    def learn(self, features: dict) -> None:
        """Online update: feed a normal feature vector for the model to learn."""
        self.model.learn_one(self._features(features))
        self._trained_count += 1

    def score(self, features: dict) -> float:
        """Anomaly score (higher = more anomalous)."""
        return self.model.score_one(self._features(features))

    def is_anomaly(self, features: dict) -> bool:
        """Return True if the score exceeds the configured threshold."""
        if self.threshold is None:
            return False
        return self.score(features) > self.threshold

    def set_threshold(self, threshold: float) -> None:
        self.threshold = threshold

    @property
    def trained_count(self) -> int:
        return self._trained_count

    def save(self, path: str | Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as f:
            pickle.dump(
                (self.model, self.threshold, self._trained_count), f,
            )

    @classmethod
    def load(cls, path: str | Path) -> "AnomalyDetector":
        with open(path, "rb") as f:
            model, threshold, trained_count = pickle.load(f)
        instance = cls(threshold=threshold)
        instance.model = model
        instance._trained_count = trained_count
        return instance


def _row_to_features(row: pd.Series) -> dict:
    return {k: float(row[k]) for k in FEATURES}


def train_offline(
    csv_path: Path = DEFAULT_FEATURES_CSV,
    model_path: Path = DEFAULT_MODEL_PATH,
    verbose: bool = True,
) -> AnomalyDetector:
    """Train on normal rows, score both populations, choose threshold, save."""
    df = pd.read_csv(csv_path)
    normal_mask = df["is_anomaly"] == 0
    abnormal_mask = df["is_anomaly"] == 1
    normal_df = df[normal_mask]
    abnormal_df = df[abnormal_mask]

    detector = AnomalyDetector()

    if verbose:
        print(f"Training on {len(normal_df)} normal rows from {csv_path}")
        print(f"  normal scenarios:  {sorted(normal_df['scenario'].unique())}")
        print(f"Will test on {len(abnormal_df)} abnormal rows")
        print(f"  abnormal scenarios: {sorted(abnormal_df['scenario'].unique())}")
        print()

    # Phase 1: train on normal rows only (no scoring - first window is silent).
    for _, row in normal_df.iterrows():
        feats = _row_to_features(row)
        detector.learn(feats)

    # Phase 2: score normal rows (post-training, scores are non-zero).
    normal_scores: list[float] = []
    for _, row in normal_df.iterrows():
        feats = _row_to_features(row)
        normal_scores.append(detector.score(feats))

    # Phase 3: score abnormal rows.
    abnormal_scores: list[float] = []
    for _, row in abnormal_df.iterrows():
        feats = _row_to_features(row)
        abnormal_scores.append(detector.score(feats))

    if verbose:
        print(f"Normal scores:   min={min(normal_scores):.4f}  "
              f"max={max(normal_scores):.4f}  "
              f"mean={sum(normal_scores)/len(normal_scores):.4f}")
        print(f"Abnormal scores: min={min(abnormal_scores):.4f}  "
              f"max={max(abnormal_scores):.4f}  "
              f"mean={sum(abnormal_scores)/len(abnormal_scores):.4f}")

    threshold = (max(normal_scores) + min(abnormal_scores)) / 2
    detector.set_threshold(threshold)

    if verbose:
        print(f"\nThreshold (midpoint): {threshold:.4f}")
        # Apply threshold to each score to compute confusion matrix.
        tp = sum(1 for s in abnormal_scores if s > threshold)
        fn = sum(1 for s in abnormal_scores if s <= threshold)
        fp = sum(1 for s in normal_scores if s > threshold)
        tn = sum(1 for s in normal_scores if s <= threshold)
        print(f"\nConfusion at threshold:")
        print(f"  true anomalies correctly flagged: {tp}/{len(abnormal_scores)}")
        print(f"  false negatives (missed):         {fn}/{len(abnormal_scores)}")
        print(f"  false positives (false alarm):    {fp}/{len(normal_scores)}")
        print(f"  true negatives correctly cleared: {tn}/{len(normal_scores)}")

    detector.save(model_path)
    if verbose:
        print(f"\nSaved model + threshold to {model_path}")
        print(f"Trained on {detector.trained_count} samples")

    return detector


def main() -> int:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )
    csv_path = Path(os.environ.get("FEATURES_CSV", DEFAULT_FEATURES_CSV))
    model_path = Path(os.environ.get("MODEL_PATH", DEFAULT_MODEL_PATH))
    train_offline(csv_path, model_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
