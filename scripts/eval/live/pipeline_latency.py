"""End-to-end decision-to-actuation latency of the SHIELD-AI pipeline.

For every actuator log entry (operator_actions.log) the matching decision is the
most recent decision (decisions.log) emitted at or before it. The difference
covers: Kafka publish -> Kafka consume -> live replica read -> shield validation
-> audit write -> Kubernetes API patch. It is measured on the same host clock.
usage: python pipeline_latency.py results_live/runs out.json
"""
import bisect
import json
import sys
from datetime import datetime
from pathlib import Path

import numpy as np


def ts(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()


runs = sorted(p for p in Path(sys.argv[1]).iterdir() if p.name.split("__")[1] in ("shield-ai", "ml-only"))
res = {}
for op in ("shield-ai", "ml-only"):
    lat, lat_applied, rej = [], [], 0
    for r in [p for p in runs if p.name.split("__")[1] == op]:
        dec = sorted(ts(json.loads(l)["timestamp"]) for l in open(r / "decisions.log") if l.strip())
        for l in open(r / "operator_actions.log"):
            if not l.strip():
                continue
            a = json.loads(l)
            t = ts(a["timestamp"]); i = bisect.bisect_right(dec, t) - 1
            if i < 0:
                continue
            ms = (t - dec[i]) * 1000
            if ms > 15000:          # no decision in the same window: not a match
                continue
            lat.append(ms)
            if a.get("applied"):
                lat_applied.append(ms)
            else:
                rej += 1
    q = lambda v, p: round(float(np.percentile(v, p)), 1) if v else None
    res[op] = {"actuations": len(lat), "applied": len(lat_applied), "rejected_by_shield": rej,
               "all_ms": {"p50": q(lat, 50), "p95": q(lat, 95), "p99": q(lat, 99), "max": q(lat, 100)},
               "applied_ms": {"p50": q(lat_applied, 50), "p95": q(lat_applied, 95)}}
Path(sys.argv[2]).write_text(json.dumps(res, indent=2))
print(json.dumps(res, indent=2))
