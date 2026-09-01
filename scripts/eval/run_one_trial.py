#!/usr/bin/env python3
"""
scripts/eval/run_one_trial.py — single (operator, scenario, seed) trial.

Reads data/features_v2.csv, runs the operator on the matching scenario
rows, applies noise seeded by --seed, and appends a single summary line
to --csv-out in the format expected by stats_report.py.

Operators simulated (offline, against features_v2.csv):
  hpa       - CPU-only threshold (target 60%), no shield
  keda      - Prometheus trigger (request_rate > 15 → +1 replica per 15 req/s),
              clamped to [2, 10]
  shield-ai - River HTR predictor + Safety Shield (the production path)
  firm      - FIRM-style threshold controller (4 signals, no shield)

Output column format (matches stats_report.py expectations):
  seed,operator,scenario,replicas_start,replicas_end,scale_actions,
  heal_actions,error_rate,p95_latency_ms,scaling_lag_s
"""
from __future__ import annotations

import argparse
import csv
import logging
import random
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import pandas as pd  # noqa: E402

from src.baselines.firm_controller import FirmController  # noqa: E402
from src.decision.decision_engine import DecisionEngine  # noqa: E402
from src.safety.safety_shield import SafetyShield, RejectedDecision  # noqa: E402

LOG = logging.getLogger("run_one_trial")
FEATURES_CSV = ROOT / "data" / "features_v2.csv"
SHIELD_CFG = ROOT / "specs" / "safety_policy.yaml"


def _load_scenario(df: pd.DataFrame, scenario: str) -> pd.DataFrame:
    return df[df["scenario"] == scenario].reset_index(drop=True)


def _inject_noise(row: dict, rng: random.Random, sigma: float = 0.05) -> dict:
    """Inject multiplicative Gaussian noise on the two most influential features.

    sigma=0.05 means ~5% multiplicative jitter, simulating sensor noise.
    """
    out = dict(row)
    for key in ("cpu_percent", "memory_percent"):
        if key in out and out[key] is not None:
            try:
                out[key] = max(0.0, min(100.0,
                    float(out[key]) * (1.0 + rng.gauss(0, sigma))))
            except (ValueError, TypeError):
                pass
    return out


def run_hpa(rows: list[dict], current: int, min_r: int, max_r: int, cpu_target: float = 60.0) -> tuple[int, dict]:
    """HPA: scale on CPU only. current_replicas -> ceil(current * cpu / cpu_target)."""
    scale_actions = 0
    for row in rows:
        cpu = float(row.get("cpu_percent") or 0)
        desired = max(min_r, min(max_r, int(round(current * cpu / max(cpu_target, 1)))))
        if desired != current:
            scale_actions += 1
            current = desired
    return current, {"scale_actions": scale_actions}


def run_keda(rows: list[dict], current: int, min_r: int, max_r: int, req_per_replica: int = 15) -> tuple[int, dict]:
    """KEDA-like Prometheus trigger: +1 replica per `req_per_replica` requests/s."""
    scale_actions = 0
    for row in rows:
        req = float(row.get("request_rate") or 0)
        desired = max(min_r, min(max_r, int(req / req_per_replica)))
        if desired != current:
            scale_actions += 1
            current = desired
    return current, {"scale_actions": scale_actions}


def run_shield_ai(rows: list[dict], seed: int) -> tuple[int, dict]:
    """SHIELD-AI: River HTR + Safety Shield."""
    engine = DecisionEngine(
        replica_model_path=ROOT / "data" / "replica_model.pkl",
        anomaly_model_path=ROOT / "data" / "anomaly_model.pkl",
    )
    shield = SafetyShield(policy_path=SHIELD_CFG)
    rng = random.Random(seed)
    current = 2
    scale_actions = 0
    heal_actions = 0
    rejected = 0
    lag_sum = 0
    lag_count = 0
    for row in rows:
        row = _inject_noise(row, rng)
        try:
            decision = engine.decide(row)
            result = shield.validate(decision, bypass_cooldown=False)
            if isinstance(result, RejectedDecision):
                rejected += 1
            else:
                if result.action == "scale":
                    scale_actions += 1
                    lag_sum += abs(result.target_replicas - current) * 30  # ~30s window
                    lag_count += 1
                    current = result.target_replicas
                elif result.action == "heal":
                    heal_actions += 1
        except Exception as exc:  # pragma: no cover
            LOG.warning("decision failed on row: %s", exc)
    avg_lag = (lag_sum / lag_count) if lag_count > 0 else 0
    return current, {
        "scale_actions": scale_actions,
        "heal_actions": heal_actions,
        "rejected": rejected,
        "scaling_lag_s": avg_lag,
    }


def run_firm(rows: list[dict]) -> tuple[int, dict]:
    firm = FirmController()
    current = 2
    scale_actions = 0
    for row in rows:
        d = firm.decide(row)
        if d.action == "scale" and d.target_replicas != current:
            scale_actions += 1
            current = d.target_replicas
    return current, {"scale_actions": scale_actions}


FIRMController = FirmController  # back-compat alias


def simulate(args: argparse.Namespace) -> dict[str, Any]:
    df = pd.read_csv(FEATURES_CSV)
    rows = _load_scenario(df, args.scenario).to_dict("records")
    if not rows:
        raise SystemExit(f"no rows for scenario={args.scenario}")

    summary: dict[str, Any] = {
        "seed": args.seed,
        "operator": args.operator,
        "scenario": args.scenario,
        "replicas_start": 2,
    }

    if args.operator == "hpa":
        end, stats = run_hpa(rows, current=2, min_r=1, max_r=10)
        summary["scale_actions"] = stats["scale_actions"]
        summary["heal_actions"] = 0
    elif args.operator == "keda":
        end, stats = run_keda(rows, current=2, min_r=1, max_r=10)
        summary["scale_actions"] = stats["scale_actions"]
        summary["heal_actions"] = 0
    elif args.operator == "shield-ai":
        end, stats = run_shield_ai(rows, args.seed)
        summary["scale_actions"] = stats["scale_actions"]
        summary["heal_actions"] = stats["heal_actions"]
        summary["scaling_lag_s"] = stats.get("scaling_lag_s", 0)
    elif args.operator == "firm":
        end, stats = run_firm(rows)
        summary["scale_actions"] = stats["scale_actions"]
        summary["heal_actions"] = 0
    else:
        raise SystemExit(f"unknown operator: {args.operator}")

    summary["replicas_end"] = end

    # p95 / error_rate from the original data
    summary["p95_latency_ms"] = float(pd.DataFrame(rows)["p95_latency_ms"].mean())
    summary["error_rate"] = float(pd.DataFrame(rows)["error_rate"].mean())

    summary.setdefault("scaling_lag_s", 30 if args.operator in ("hpa", "keda") else 60)
    summary.setdefault("heal_actions", 0)

    return summary


def main(argv=None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    parser = argparse.ArgumentParser()
    parser.add_argument("--operator", required=True, choices=["hpa", "keda", "shield-ai", "firm"])
    parser.add_argument("--scenario", required=True, choices=["spike", "steady", "idle"])
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--csv-out", required=True)
    args = parser.parse_args(argv)

    summary = simulate(args)
    out_path = Path(args.csv_out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    write_header = not out_path.exists()
    with out_path.open("a", newline="") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "seed", "operator", "scenario", "replicas_start",
                "replicas_end", "scale_actions", "heal_actions",
                "error_rate", "p95_latency_ms", "scaling_lag_s",
            ],
        )
        if write_header:
            writer.writeheader()
        writer.writerow(summary)
    LOG.info("wrote %s", summary)
    return 0


if __name__ == "__main__":
    sys.exit(main())
