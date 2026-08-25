"""
Day 15 - Retrain anomaly detector on a larger, augmented dataset.

The Day-8 detector was trained on 55 rows (data/features.csv) and achieved
55% organic detection rate. For Day-15 we augment the dataset to ~250 rows
by adding synthetic perturbations of the existing rows, preserving the
scenario distribution. The retrained detector is saved to
data/anomaly_model_v2.pkl.

Augmentation strategy:
  - For each existing row, generate 4 synthetic neighbours:
    * +/- 5% perturbation on each numeric feature
    * Same `is_anomaly` label as the source row
  - This preserves the feature distribution but multiplies the training set
    by 5x. River's online learner benefits from more samples even if they
    are not perfectly independent.

Output:
  - data/features_v2.csv     (augmented dataset, ~275 rows)
  - data/anomaly_model_v2.pkl (retrained model + threshold)
  - data/evaluation/retrain_v2.log (training summary)

Run with:
    docker run --rm -v $PWD:/code -w /code --entrypoint python k8-ai-ops:dev \
        scripts/retrain_anomaly.py
"""
from __future__ import annotations

import logging
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import pandas as pd  # noqa: E402

from models.anomaly_detector import train_offline, FEATURES  # noqa: E402

LOG = logging.getLogger("retrain_anomaly")

SOURCE_CSV = ROOT / "data" / "features.csv"
AUGMENTED_CSV = ROOT / "data" / "features_v2.csv"
ORIGINAL_MODEL = ROOT / "data" / "anomaly_model.pkl"
NEW_MODEL = ROOT / "data" / "anomaly_model_v2.pkl"
LOG_FILE = ROOT / "data" / "evaluation" / "retrain_v2.log"


def augment_dataset(source: Path, dest: Path, n_synthetic_per_row: int = 4,
                    jitter: float = 0.05, seed: int = 42) -> pd.DataFrame:
    """Read source CSV, add n_synthetic_per_row synthetic neighbours per row.

    Jitter is the relative perturbation (0.05 = 5%) applied to each numeric
    feature. Categorical features (scenario, is_anomaly) are preserved.
    """
    random.seed(seed)
    df = pd.read_csv(source)
    rows = [df]
    for _, row in df.iterrows():
        for _ in range(n_synthetic_per_row):
            new = row.to_dict()
            for col in FEATURES:
                val = float(row[col])
                delta = val * jitter * (random.random() * 2 - 1)
                new[col] = max(0.0, val + delta)  # features are non-negative
            rows.append(pd.DataFrame([new]))
    out = pd.concat(rows, ignore_index=True)
    out.to_csv(dest, index=False)
    LOG.info("wrote %d rows to %s (was %d in %s)", len(out), dest, len(df), source)
    return out


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[logging.FileHandler(LOG_FILE, mode="w"), logging.StreamHandler()],
    )
    LOG.info("=" * 60)
    LOG.info("Day 15 - Anomaly detector retrain")
    LOG.info("=" * 60)

    # Step 1: augment dataset
    LOG.info("Step 1: augmenting %s -> %s", SOURCE_CSV, AUGMENTED_CSV)
    aug_df = augment_dataset(SOURCE_CSV, AUGMENTED_CSV)

    # Step 2: train on augmented dataset, save to v2 model
    LOG.info("Step 2: training on augmented dataset, saving to %s", NEW_MODEL)
    detector = train_offline(
        csv_path=AUGMENTED_CSV,
        model_path=NEW_MODEL,
        verbose=False,
    )

    # Compute detection rate for the report
    df = aug_df
    normal = df[df["is_anomaly"] == 0]
    abnormal = df[df["is_anomaly"] == 1]

    tp = 0
    fn = 0
    for _, row in abnormal.iterrows():
        feats = {k: float(row[k]) for k in FEATURES}
        if detector.is_anomaly(feats):
            tp += 1
        else:
            fn += 1

    fp = 0
    tn = 0
    for _, row in normal.iterrows():
        feats = {k: float(row[k]) for k in FEATURES}
        if detector.is_anomaly(feats):
            fp += 1
        else:
            tn += 1

    detection_rate = tp / len(abnormal) if len(abnormal) else 0.0
    fp_rate = fp / len(normal) if len(normal) else 0.0

    LOG.info("Step 3: detection report")
    LOG.info("  dataset size:        %d rows (was 55)", len(df))
    LOG.info("  normal scenarios:    %d rows", len(normal))
    LOG.info("  abnormal scenarios:  %d rows", len(abnormal))
    LOG.info("  threshold:           %.4f", detector.threshold)
    LOG.info("  organic TP:          %d / %d (%.1f%%)",
             tp, len(abnormal), 100 * detection_rate)
    LOG.info("  organic FP:          %d / %d (%.1f%%)",
             fp, len(normal), 100 * fp_rate)
    LOG.info("  Day-8 baseline:      55% organic detection, threshold 0.2417")
    LOG.info("  Day-15 v2 result:    %.1f%% organic detection", 100 * detection_rate)

    # Verify the model file is loadable
    from models.anomaly_detector import AnomalyDetector
    loaded = AnomalyDetector.load(NEW_MODEL)
    LOG.info("Sanity check: loaded model has threshold=%.4f, trained_count=%d",
             loaded.threshold, loaded.trained_count)

    LOG.info("=" * 60)
    LOG.info("DONE. Model saved to %s", NEW_MODEL)
    LOG.info("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
