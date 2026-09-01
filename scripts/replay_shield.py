"""Replay offline decisions through the Safety Shield to count modifications/rejections."""
import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, "/code")
from src.safety.safety_shield import SafetyShield, Decision, RejectedDecision

# Build a Decision from each CSV row + its computed target
with open("/code/data/features_v2.csv") as f:
    rows = list(csv.DictReader(f))

import pickle

with open("/code/data/replica_model.pkl", "rb") as f:
    model, min_r, max_r, _ = pickle.load(f)

FEATURES = ["cpu_percent", "memory_percent", "request_rate", "p95_latency_ms",
            "error_rate", "current_replicas", "hour_of_day", "day_of_week"]

def predict_one(features):
    raw = model.predict_one(features)
    if raw is None:
        return int(round((min_r + max_r) / 2))
    return max(min_r, min(max_r, int(round(raw))))

shield = SafetyShield(
    policy_path=Path("/code/specs/safety_policy.yaml"),
    audit_log_path=Path("/tmp/safety_audit_replay.log"),
)

action_count = Counter()
mod_count = 0
reject_count = 0
violation_per_scenario = defaultdict(int)

violation_records = []

for i, row in enumerate(rows):
    feats = {k: float(row.get(k) or 0) for k in FEATURES}
    predicted = predict_one(feats)
    current = int(float(row.get("current_replicas") or 2))

    decision = Decision(
        service="workload-v2",
        action="scale" if predicted != current else "noop",
        target_replicas=predicted,
        current_replicas=current,
        reason="offline replay",
    )

    shield._last_action_time = 0.0
    outcome = shield.validate(decision, bypass_cooldown=True)

    if isinstance(outcome, RejectedDecision):
        reject_count += 1
        violation_per_scenario[row["scenario"]] += 1
        violation_records.append((i, row["scenario"], "rejected", outcome.reason))
    else:
        action_count[outcome.action] += 1
        if outcome.target_replicas != predicted:
            mod_count += 1
            violation_records.append((i, row["scenario"], "modified", f"{predicted}->{outcome.target_replicas}"))

print(f"\nTotal decisions: {len(rows)}")
print(f"Rejected (violations): {reject_count} ({100*reject_count/len(rows):.1f}%)")
print(f"Modified (clamped): {mod_count} ({100*mod_count/len(rows):.1f}%)")
print(f"Per-scenario violations:")
for s in sorted(violation_per_scenario):
    print(f"  {s}: {violation_per_scenario[s]}")
print()
print(f"Action mix after shield: {dict(action_count)}")
print()
print(f"Sample violations:")
for v in violation_records[:10]:
    print(f"  idx={v[0]} scen={v[1]} {v[2]}: {v[3]}")
