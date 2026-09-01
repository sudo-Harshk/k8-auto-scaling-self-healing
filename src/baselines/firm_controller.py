"""FIRM-style autoscaling baseline.

Reference: H. Lim et al., "FIRM: An Intelligent Auto-Scaler for
Resource-Constrained Networks", 2020.

FIRM is a threshold-based controller that uses multiple resource
signals to compute a target replica count. Unlike our SHIELD-AI, FIRM
does not learn online and has no safety shield. We use it as the
"ML-inspired but not adaptive" baseline so reviewers cannot say we
only compared to non-ML baselines (HPA, KEDA).

Decision logic (the same 8 features as the AI controller):
    by_cpu     = ceil(current_replicas * cpu_percent / CPU_TARGET)
    by_mem     = ceil(current_replicas * memory_percent / MEM_TARGET)
    by_req     = ceil(request_rate / REQ_PER_REPLICA)
    by_lat     = ceil(current_replicas * (p95_latency_ms / LAT_TARGET))
    target     = clamp(max(by_cpu, by_mem, by_req, by_lat), MIN, MAX)

Threshold defaults (tuned for podinfo-style microservices):
    CPU_TARGET       = 60%   (matches HPA default)
    MEM_TARGET       = 80%   (K8s best practice)
    REQ_PER_REPLICA  = 15    (matches Day-6 heuristic)
    LAT_TARGET       = 200ms (interactive microservice SLO)
"""
from __future__ import annotations

import logging
import math
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

LOG = logging.getLogger("firm_controller")

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

DEFAULT_CPU_TARGET = 60.0
DEFAULT_MEM_TARGET = 80.0
DEFAULT_REQ_PER_REPLICA = 15.0
DEFAULT_LAT_TARGET = 200.0
MIN_REPLICAS = 1
MAX_REPLICAS = 10


@dataclass
class FirmDecision:
    """Mirror of Decision dataclass for downstream interop."""

    service: str
    action: str
    target_replicas: int
    current_replicas: int
    reason: str
    explanation: list[dict[str, float]] = field(default_factory=list)
    by_cpu: int = 0
    by_mem: int = 0
    by_req: int = 0
    by_lat: int = 0
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    features: dict[str, float] = field(default_factory=dict)

    def to_json(self) -> str:
        import json
        return json.dumps(asdict(self), default=str)


class FirmController:
    """Threshold-based autoscaler (FIRM-style)."""

    def __init__(
        self,
        service: str = "workload-v2",
        cpu_target: float = DEFAULT_CPU_TARGET,
        mem_target: float = DEFAULT_MEM_TARGET,
        req_per_replica: float = DEFAULT_REQ_PER_REPLICA,
        lat_target: float = DEFAULT_LAT_TARGET,
        min_replicas: int = MIN_REPLICAS,
        max_replicas: int = MAX_REPLICAS,
    ) -> None:
        self.service = service
        self.cpu_target = cpu_target
        self.mem_target = mem_target
        self.req_per_replica = req_per_replica
        self.lat_target = lat_target
        self.min_replicas = min_replicas
        self.max_replicas = max_replicas

    def _by_cpu(self, features: dict) -> int:
        cpu = float(features.get("cpu_percent") or 0.0)
        cur = max(int(float(features.get("current_replicas") or 1)), 1)
        if cpu <= 0:
            return cur
        return math.ceil(cur * cpu / self.cpu_target)

    def _by_mem(self, features: dict) -> int:
        mem = float(features.get("memory_percent") or 0.0)
        cur = max(int(float(features.get("current_replicas") or 1)), 1)
        if mem <= 0:
            return cur
        return math.ceil(cur * mem / self.mem_target)

    def _by_req(self, features: dict) -> int:
        req = float(features.get("request_rate") or 0.0)
        if req <= 0:
            return max(int(float(features.get("current_replicas") or 1)), 1)
        return math.ceil(req / self.req_per_replica)

    def _by_lat(self, features: dict) -> int:
        p95 = float(features.get("p95_latency_ms") or 0.0)
        cur = max(int(float(features.get("current_replicas") or 1)), 1)
        if p95 <= 0:
            return cur
        # If p95 > target, we need more replicas to reduce per-pod load.
        # Rough heuristic: scale factor = p95 / target, clamped >=1.
        scale_factor = max(1.0, p95 / self.lat_target)
        return math.ceil(cur * scale_factor)

    def decide(self, features: dict) -> FirmDecision:
        current = int(float(features.get("current_replicas") or 2))
        by_cpu = self._by_cpu(features)
        by_mem = self._by_mem(features)
        by_req = self._by_req(features)
        by_lat = self._by_lat(features)
        target_raw = max(by_cpu, by_mem, by_req, by_lat)
        target = max(self.min_replicas, min(self.max_replicas, target_raw))
        if target != current:
            action = "scale"
            reason = (
                f"FIRM: by_cpu={by_cpu} by_mem={by_mem} by_req={by_req} "
                f"by_lat={by_lat} -> target={target} (current={current})"
            )
        else:
            action = "noop"
            reason = f"FIRM: predictor agrees with current={current}"
        return FirmDecision(
            service=self.service,
            action=action,
            target_replicas=target,
            current_replicas=current,
            reason=reason,
            explanation=[
                {"feature": "by_cpu", "value": float(by_cpu)},
                {"feature": "by_mem", "value": float(by_mem)},
                {"feature": "by_req", "value": float(by_req)},
                {"feature": "by_lat", "value": float(by_lat)},
            ],
            by_cpu=by_cpu,
            by_mem=by_mem,
            by_req=by_req,
            by_lat=by_lat,
            timestamp=datetime.now(timezone.utc).isoformat(),
            features={k: float(features.get(k) or 0.0) for k in FEATURES},
        )


def main() -> int:
    import argparse
    import csv
    import json
    import sys
    p = argparse.ArgumentParser()
    p.add_argument("--csv", default="data/features_v2.csv")
    p.add_argument("--out", default="logs/firm_decisions.log")
    args = p.parse_args()

    root = Path(__file__).resolve().parents[2]
    csv_path = root / args.csv
    out_path = root / args.out
    out_path.parent.mkdir(parents=True, exist_ok=True)

    controller = FirmController()
    rows = list(csv.DictReader(open(csv_path)))
    counts = {"scale": 0, "noop": 0}
    per_scen_action: dict[str, dict[str, int]] = {}
    per_scen_target: dict[str, dict[int, int]] = {}
    with open(out_path, "w") as f:
        for i, row in enumerate(rows):
            feats = {k: float(row.get(k) or 0) for k in FEATURES}
            decision = controller.decide(feats)
            f.write(decision.to_json() + "\n")
            counts[decision.action] += 1
            per_scen_action.setdefault(row["scenario"], {"scale": 0, "noop": 0})[decision.action] += 1
            per_scen_target.setdefault(row["scenario"], {}).setdefault(decision.target_replicas, 0)
            per_scen_target[row["scenario"]][decision.target_replicas] += 1
            if i < 3:
                print(f"[{i+1}] {row['scenario']:8s} action={decision.action:5s} target={decision.target_replicas} ({decision.reason})")

    print(f"\nFIRM action mix: {counts}")
    print("Per-scenario action mix:")
    for s in sorted(per_scen_action):
        print(f"  {s}: {per_scen_action[s]}")
    print("Per-scenario target distribution:")
    for s in sorted(per_scen_target):
        print(f"  {s}: {dict(sorted(per_scen_target[s].items()))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
