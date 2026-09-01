"""Inspect features_v2.csv per-scenario to understand FIRM behavior."""
import csv
from collections import defaultdict

rows = list(csv.DictReader(open("/code/data/features_v2.csv")))

per_scen_features = defaultdict(list)
for r in rows:
    per_scen_features[r["scenario"]].append({
        "request_rate": float(r["request_rate"]),
        "p95_latency_ms": float(r["p95_latency_ms"]),
        "cpu_percent": float(r["cpu_percent"]),
        "memory_percent": float(r["memory_percent"]),
        "error_rate": float(r["error_rate"]),
        "target_replicas": int(float(r["target_replicas"])),
    })

for s, feats in per_scen_features.items():
    print(f"\n--- {s} ({len(feats)} rows) ---")
    print(f"  request_rate: min={min(f['request_rate'] for f in feats):.1f} max={max(f['request_rate'] for f in feats):.1f} mean={sum(f['request_rate'] for f in feats)/len(feats):.1f}")
    print(f"  p95_latency_ms: min={min(f['p95_latency_ms'] for f in feats):.1f} max={max(f['p95_latency_ms'] for f in feats):.1f} mean={sum(f['p95_latency_ms'] for f in feats)/len(feats):.1f}")
    print(f"  cpu_percent: min={min(f['cpu_percent'] for f in feats):.1f} max={max(f['cpu_percent'] for f in feats):.1f} mean={sum(f['cpu_percent'] for f in feats)/len(feats):.1f}")
    low_p95 = sum(1 for f in feats if f["p95_latency_ms"] < 200)
    low_req = sum(1 for f in feats if f["request_rate"] < 15)
    print(f"  rows with p95 < 200ms: {low_p95}/{len(feats)}")
    print(f"  rows with request_rate < 15: {low_req}/{len(feats)}")
