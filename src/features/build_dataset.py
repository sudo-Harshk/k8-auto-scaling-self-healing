"""Day 6 Dataset Builder: merge scenario JSONL files into data/features.csv.

Run after all four load scenarios are complete:

    docker run --rm -v $HOME/k8-auto-scaling-self-healing:/code -w /code \
        k8-ai-ops:dev python src/features/build_dataset.py

Reads data/scenario_*.jsonl (written by feature_builder.py during each Locust
scenario), attaches the scenario label and is_anomaly flag, computes the
target_replicas training label, and writes data/features.csv.

Labeling policy (per the Day-6 plan: spikes and no-load states are anomalies):
    baseline     -> is_anomaly=0
    spike        -> is_anomaly=1  (sudden surge)
    steady_high  -> is_anomaly=0  (sustained load becomes the new normal)
    idle         -> is_anomaly=1  (no traffic on an always-on service)

target_replicas heuristic (the ground truth the Day-7 model learns):
    by_cpu = replicas needed to bring per-pod CPU below 60% of its limit
    by_req = replicas needed to keep each pod at <= 15 req/s
    target = clamp(max(by_cpu, by_req), 1, 10)
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
SCENARIO_DIR = ROOT / "data"
OUTPUT = ROOT / "data" / "features.csv"

# filename -> (is_anomaly, scenario_name)
SCENARIO_LABELS = {
    "scenario_baseline.jsonl": (0, "baseline"),
    "scenario_spike.jsonl": (1, "spike"),
    "scenario_steady.jsonl": (0, "steady_high"),
    "scenario_idle.jsonl": (1, "idle"),
}

REQ_PER_REPLICA = 15.0   # comfortable per-pod request rate
CPU_PERCENT_TARGET = 60.0  # keep per-pod CPU below this % of its limit
MIN_REPLICAS = 1
MAX_REPLICAS = 10


def compute_target_replicas(row: pd.Series) -> int:
    n = max(int(round(row["current_replicas"])), 1)
    by_cpu = (
        math.ceil(n * row["cpu_percent"] / CPU_PERCENT_TARGET)
        if row["cpu_percent"] > 0
        else MIN_REPLICAS
    )
    by_req = (
        math.ceil(row["request_rate"] / REQ_PER_REPLICA)
        if row["request_rate"] > 0
        else MIN_REPLICAS
    )
    return max(MIN_REPLICAS, min(MAX_REPLICAS, max(by_cpu, by_req)))


def main() -> int:
    frames = []
    for fname, (is_anomaly, scenario) in SCENARIO_LABELS.items():
        fpath = SCENARIO_DIR / fname
        if not fpath.exists():
            print(f"SKIP: {fpath} not found")
            continue
        with open(fpath) as f:
            records = [json.loads(line) for line in f if line.strip()]
        if not records:
            print(f"SKIP: {fpath} is empty")
            continue
        df = pd.DataFrame(records)
        df["is_anomaly"] = is_anomaly
        df["scenario"] = scenario
        frames.append(df)
        print(f"loaded {fname}: {len(df)} rows, is_anomaly={is_anomaly}")

    if not frames:
        print("ERROR: no scenario files found in data/")
        return 1

    dataset = pd.concat(frames, ignore_index=True)
    dataset["target_replicas"] = dataset.apply(compute_target_replicas, axis=1)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    dataset.to_csv(OUTPUT, index=False)
    print(f"\nwrote {len(dataset)} rows to {OUTPUT}")
    print(f"columns: {list(dataset.columns)}")
    print("\nscenario distribution:")
    print(dataset["scenario"].value_counts().to_string())
    print("\nis_anomaly distribution:")
    print(dataset["is_anomaly"].value_counts().to_string())
    print("\ntarget_replicas distribution:")
    print(dataset["target_replicas"].value_counts().sort_index().to_string())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
