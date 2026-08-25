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
sys.path.insert(0, str(ROOT))

import pandas as pd  # noqa: E402

from src.decision.decision_engine import DecisionEngine  # noqa: E402
from src.safety.safety_shield import SafetyShield, RejectedDecision  # noqa: E402

LOG = logging.getLogger("ablation_N3")

FEATURES_CSV = ROOT / "data" / "features.csv"
MODEL_PATH = ROOT / "data" / "anomaly_model.pkl"
SHIELD_CFG = ROOT / "specs" / "safety_policy.yaml"
OUT_CSV = ROOT / "data" / "evaluation" / "ablation_results_N3.csv"

ANOMALY_NOISE_STD = 0.05  # Gaussian std applied to anomaly_score


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
      - no_shield: bypass SafetyShield (always accept decision as-is)
    """
    engine = DecisionEngine(
        replica_model_path=ROOT / "data" / "replica_model.pkl",
        anomaly_model_path=MODEL_PATH,
    )
    shield = SafetyShield(policy_path=SHIELD_CFG)

    apply_shield = variant != "no_shield"
    enable_explain = variant != "no_shap"

    counts = {"scale": 0, "heal": 0, "noop": 0,
              "rejected": 0, "applied": 0}

    rng = random.Random(rep * 1000)  # deterministic per-rep seed
    rows = df.to_dict("records")
    means = engine._compute_feature_means(rows)

    for row in rows:
        # Apply Gaussian noise to anomaly_score
        row = dict(row)
        row["anomaly_score"] = max(0.0, min(1.0,
            float(row["anomaly_score"]) + rng.gauss(0, noise_std)))
        decision = engine.decide(row, feature_means=means)
        if not enable_explain:
            decision.explanation = []
        if apply_shield:
            result = shield.validate(decision, bypass_cooldown=False)
            if isinstance(result, RejectedDecision):
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
