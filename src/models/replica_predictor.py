"""Day 7 Replica Predictor: River-ML online regression model.

Trains a HoeffdingAdaptiveTreeRegressor on the Day-6 feature dataset to predict
the optimal number of pod replicas (target_replicas). Online learning: predict,
then learn on each row. Rolling MAE is the prototype acceptance metric
(plan target: < 1.0 replica).

The model is a River Pipeline: StandardScaler -> HoeffdingAdaptiveTreeRegressor.
StandardScaler handles the very different feature scales (request_rate 0-51,
cpu_percent 0-15, etc.); the regressor handles the threshold-style target
pattern (1 / 2 / 4 replicas driven by the by_cpu / by_req heuristic in
build_dataset.py).

Design notes:
- p95_latency_ms, error_rate, current_replicas, day_of_week are constant in the
  Day-6 dataset (p95=4.75, error=0, replicas=2, weekday=3). The model will learn
  they have no predictive power and ignore them. The feature list is kept
  complete so the API matches the Day-9 decision engine and the eventual
  post-completion rework with a realistic microservice will benefit.

- predict() returns None on cold start (no rows seen yet); the public wrapper
  falls back to the midpoint of the allowed range so callers always get an int.

Run (inside the shared Docker image — river is added here on Day 7):

    docker run --rm -v $HOME/k8-auto-scaling-self-healing:/code -w /code \
        k8-ai-ops:dev python src/models/replica_predictor.py

Environment variables:
    FEATURES_CSV   input dataset, default data/features.csv
    MODEL_PATH     output model path, default data/replica_model.pkl
    MIN_REPLICAS   floor for predictions, default 1
    MAX_REPLICAS   ceiling for predictions, default 10
"""
from __future__ import annotations

import logging
import os
import pickle
from pathlib import Path

import pandas as pd
from river import compose, metrics, preprocessing, tree

ROOT = Path(__file__).resolve().parents[2]

LOG = logging.getLogger("replica_predictor")

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
TARGET = "target_replicas"

DEFAULT_FEATURES_CSV = ROOT / "data" / "features.csv"
DEFAULT_MODEL_PATH = ROOT / "data" / "replica_model.pkl"


class ReplicaPredictor:
    """Online replica-count predictor backed by a HoeffdingAdaptiveTreeRegressor."""

    def __init__(self, min_replicas: int = 1, max_replicas: int = 10) -> None:
        self.min_replicas = min_replicas
        self.max_replicas = max_replicas
        self.model = compose.Pipeline(
            preprocessing.StandardScaler(),
            tree.HoeffdingAdaptiveTreeRegressor(
                grace_period=50,
                max_depth=8,
                seed=42,
            ),
        )
        self._trained_count = 0

    def _features(self, row: dict) -> dict:
        return {k: float(row[k]) for k in FEATURES}

    def learn(self, features: dict, target_replicas: int) -> None:
        """Online update: the model sees a (features, target) pair."""
        self.model.learn_one(self._features(features), float(target_replicas))
        self._trained_count += 1

    def predict(self, features: dict) -> int:
        """Predict replica count and round + clamp to [min_replicas, max_replicas]."""
        raw = self.model.predict_one(self._features(features))
        if raw is None:
            # Cold start: midpoint of allowed range.
            return int(round((self.min_replicas + self.max_replicas) / 2))
        rounded = int(round(raw))
        return max(self.min_replicas, min(self.max_replicas, rounded))

    def predict_raw(self, features: dict) -> float | None:
        """Predict without rounding/clamping (for debugging / SHAP)."""
        return self.model.predict_one(self._features(features))

    @property
    def trained_count(self) -> int:
        return self._trained_count

    def save(self, path: str | Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as f:
            pickle.dump(
                (self.model, self.min_replicas, self.max_replicas, self._trained_count),
                f,
            )

    @classmethod
    def load(cls, path: str | Path) -> "ReplicaPredictor":
        with open(path, "rb") as f:
            model, min_replicas, max_replicas, trained_count = pickle.load(f)
        instance = cls(min_replicas=min_replicas, max_replicas=max_replicas)
        instance.model = model
        instance._trained_count = trained_count
        return instance


def _row_to_features(row: pd.Series) -> dict:
    return {k: float(row[k]) for k in FEATURES}


def train_offline(
    csv_path: Path = DEFAULT_FEATURES_CSV,
    model_path: Path = DEFAULT_MODEL_PATH,
    min_replicas: int = 1,
    max_replicas: int = 10,
    verbose: bool = True,
) -> ReplicaPredictor:
    """Train on features.csv row by row (online learning). Save model. Return predictor."""
    df = pd.read_csv(csv_path)
    predictor = ReplicaPredictor(min_replicas=min_replicas, max_replicas=max_replicas)
    mae = metrics.MAE()

    if verbose:
        print(f"Training on {len(df)} rows from {csv_path}")
        print(f"Target distribution: {df[TARGET].value_counts().sort_index().to_dict()}")
        print(f"Features: {FEATURES}")
        print()
        print(f"{'idx':>4} {'scenario':>12} {'true':>4} {'pred':>4} {'err':>5}")
        print("-" * 36)

    errors = []
    for i, row in df.iterrows():
        feats = _row_to_features(row)
        true_y = int(row[TARGET])
        pred_y = predictor.predict(feats)
        # predict-then-learn: update MAE with the prediction we just made
        # (before the model sees the true label).
        mae.update(true_y, float(pred_y))
        errors.append(abs(true_y - pred_y))
        predictor.learn(feats, true_y)

        if verbose and (i < 10 or i == 25 or i == 50 or i == len(df) - 1):
            print(
                f"{i:>4} {row['scenario']:>12} {true_y:>4} {pred_y:>4} "
                f"{abs(true_y - pred_y):>5}"
            )

    if verbose:
        print()
        print(f"Final MAE: {mae.get():.4f}")
        print(f"Mean abs error: {sum(errors)/len(errors):.4f}")
        print(f"Trained on {predictor.trained_count} samples")

    predictor.save(model_path)
    if verbose:
        print(f"Saved model to {model_path}")

    return predictor


def main() -> int:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )
    csv_path = Path(os.environ.get("FEATURES_CSV", DEFAULT_FEATURES_CSV))
    model_path = Path(os.environ.get("MODEL_PATH", DEFAULT_MODEL_PATH))
    min_replicas = int(os.environ.get("MIN_REPLICAS", "1"))
    max_replicas = int(os.environ.get("MAX_REPLICAS", "10"))
    train_offline(csv_path, model_path, min_replicas, max_replicas)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
