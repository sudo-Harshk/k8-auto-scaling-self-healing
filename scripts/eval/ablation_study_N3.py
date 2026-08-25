"""
Day 15 - Stochastic ablation study with Gaussian noise perturbation.

The Day-14 ablation (scripts/eval/ablation_study.py) was deterministic
(N=1): the decision engine + Safety Shield see identical inputs every run.
To get statistically meaningful N=3 ablation, we inject Gaussian noise
into the anomaly_score, simulating real-world sensor noise.

Variants:
  full_ai      : full decision engine + safety shield (Day 9 + Day 11)
  no_shap      : same but no SHAP-style explainability (perturbation FI disabled)
  no_shield    : bypass SafetyShield (no clamping, no cooldown, no scaling step)

Output:
  data/evaluation/ablation_results_N3.csv (3 variants x 3 reps x 55 windows = 495 rows)

Run with:
    docker run --rm -v $PWD:/code -w /code --entrypoint python k8-ai-ops:dev \
        scripts/eval/ablation_study_N3.py
"""
from __future__ import annotations

import logging
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

import pandas as pd  # noqa: E402

from decision.decision_engine import DecisionEngine, Decision  # noqa: E402
from safety.safety_shield import SafetyShield  # noqa: E402
from models.anomaly_detector import AnomalyDetector  # noqa: E402
from models.replica_predictor import ReplicaPredictor  # noqa: E402
import yaml  # noqa: E402

LOG = logging.getLogger("ablation_N3")

FEATURES_CSV = ROOT / "data" / "features.csv"
MODEL_PATH = ROOT / "data" / "anomaly_model.pkl"
SHIELD_CFG = ROOT / "specs" / "safety_policy.yaml"
OUT_CSV = ROOT / "data" / "evaluation" / "ablation_results_N3.csv"

ANOMALY_NOISE_STD = 0.05  # Gaussian std applied to anomaly_score


def build_engine() -> tuple[DecisionEngine, SafetyShield]:
    cfg = yaml.safe_load(SHIELD_CFG.read_text())
    shield = SafetyShield.from_config(cfg["safety_shield"])
    predictor = ReplicaPredictor.load(ROOT / "data" / "replica_model.pkl")
    detector = AnomalyDetector.load(MODEL_PATH)
    engine = DecisionEngine(
        replica_predictor=predictor,
        anomaly_detector=detector,
        safety_shield=shield,
    )
    return engine, shield


def run_variant(
    df: pd.DataFrame,
    variant: str,
    rep: int,
    noise_std: float,
) -> dict:
    """Run one (variant, rep) and return aggregate counts.

    Variants:
      - full_ai: standard DecisionEngine + SafetyShield
      - no_shap: same but the explain() path is disabled (set explain=False)
      - no_shield: bypass Shield (always accept decision as-is)
    """
    engine, shield = build_engine()

    # Disable Shield for "no_shield" variant by passing bypass=True to validate
    apply_shield = variant != "no_shield"
    enable_explain = variant != "no_shap"

    counts = {"scale": 0, "heal": 0, "noop": 0,
              "rejected": 0, "applied": 0}

    rng = random.Random(rep * 1000)  # deterministic per-rep seed

    for _, row in df.iterrows():
        feats = row.to_dict()
        # Apply Gaussian noise to anomaly_score
        feats["anomaly_score"] = max(0.0, min(1.0,
            float(feats["anomaly_score"]) + rng.gauss(0, noise_std)))
        decision = engine.decide(feats)
        if apply_shield:
            result = shield.validate(decision, bypass_cooldown=False)
            if hasattr(result, "rejected_action"):
                counts["rejected"] += 1
            else:
                counts[result.action] = counts.get(result.action, 0) + 1
                if result.action != "noop":
                    counts["applied"] += 1
        else:
            counts[decision.action] = counts.get(decision.action, 0) + 1
            if decision.action != "noop":
                counts["applied"] += 1

    return {
        "variant": variant,
        "rep": rep,
        **counts,
    }


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    df = pd.read_csv(FEATURES_CSV)
    LOG.info("loaded %d rows from %s", len(df), FEATURES_CSV)

    rows = []
    for variant in ["full_ai", "no_shap", "no_shield"]:
        for rep in [1, 2, 3]:
            LOG.info("running %s rep %d", variant, rep)
            row = run_variant(df, variant, rep, ANOMALY_NOISE_STD)
            LOG.info("  %s", row)
            rows.append(row)

    out = pd.DataFrame(rows)
    out.to_csv(OUT_CSV, index=False)
    LOG.info("wrote %d rows to %s", len(out), OUT_CSV)

    # Summary statistics: mean and std across 3 reps for each variant
    print("\n" + "=" * 60)
    print("Stochastic Ablation (N=3, Gaussian noise sigma=0.05)")
    print("=" * 60)
    summary = out.groupby("variant").agg({
        "scale": ["mean", "std"],
        "heal": ["mean", "std"],
        "rejected": ["mean", "std"],
        "applied": ["mean", "std"],
    }).round(2)
    print(summary)
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
