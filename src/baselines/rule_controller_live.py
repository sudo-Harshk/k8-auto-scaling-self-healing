"""Live multi-threshold baseline controller ("MT", FIRM-inspired).

Paper revision: the multi-signal threshold baseline previously existed only as
an offline replay over a CSV. This module runs it LIVE on the same feature
stream (Kafka `k8s-features`) and actuates the same Deployment as SHIELD-AI,
so every controller is evaluated on identical inputs, cadence and bounds.

It is deliberately NOT called FIRM: FIRM (Qiu et al., OSDI 2020) is an
RL-based fine-grained resource manager. This controller is the rule-based,
multi-signal threshold policy described in src/baselines/firm_controller.py
(max of CPU-, memory-, request- and latency-derived replica targets). It has
no shield and no learning.

Environment:
    KAFKA_BOOTSTRAP, KAFKA_TOPIC_IN (default k8s-features)
    WORKLOAD_NAMESPACE, WORKLOAD_DEPLOYMENT
    MIN_REPLICAS, MAX_REPLICAS, REQ_PER_REPLICA, CPU_TARGET_PCT, LAT_TARGET_MS
    MT_ACTIONS_LOG (default logs/mt_actions.log)
"""
from __future__ import annotations

import json
import logging
import os
import signal
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from kafka import KafkaConsumer  # noqa: E402

from src.baselines.firm_controller import FirmController  # noqa: E402
from src.decision.decision_engine import DecisionEngine  # noqa: E402
from src.kopf_operator.actuator import K8sOperator  # noqa: E402

LOG = logging.getLogger("mt_controller")


def main() -> int:
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    ns = os.environ.get("WORKLOAD_NAMESPACE", "podinfo")
    dep = os.environ.get("WORKLOAD_DEPLOYMENT", "podinfo")
    ctl = FirmController(
        service=dep,
        cpu_target=float(os.environ.get("CPU_TARGET_PCT", "60")),
        req_per_replica=float(os.environ.get("REQ_PER_REPLICA", "15")),
        lat_target=float(os.environ.get("LAT_TARGET_MS", "200")),
        min_replicas=int(os.environ.get("MIN_REPLICAS", "2")),
        max_replicas=int(os.environ.get("MAX_REPLICAS", "20")),
    )
    op = K8sOperator(namespace=ns, deployment=dep)
    log_path = Path(os.environ.get("MT_ACTIONS_LOG", ROOT / "logs" / "mt_actions.log"))
    log_path.parent.mkdir(parents=True, exist_ok=True)

    consumer = KafkaConsumer(
        os.environ.get("KAFKA_TOPIC_IN", "k8s-features"),
        bootstrap_servers=os.environ.get("KAFKA_BOOTSTRAP", "localhost:9094"),
        auto_offset_reset="latest",
        enable_auto_commit=True,
        group_id=os.environ.get("CONSUMER_GROUP", "mt-controller"),
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
    )
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))
    LOG.info("MT controller live on %s/%s", ns, dep)

    for msg in consumer:
        # Same feature normalisation as the SHIELD-AI decision engine.
        feats = DecisionEngine._featurise(DecisionEngine, msg.value)  # type: ignore[arg-type]
        try:
            feats["current_replicas"] = float(op.get_current_replicas())
        except Exception as exc:  # noqa: BLE001
            LOG.warning("live replica read failed: %s", exc)
        d = ctl.decide(feats)
        applied = False
        before = after = int(feats["current_replicas"])
        if d.action == "scale":
            try:
                before, after = op.apply_scale(d.target_replicas)
                applied = True
            except Exception as exc:  # noqa: BLE001
                LOG.error("scale failed: %s", exc)
        rec = {"timestamp": datetime.now(timezone.utc).isoformat(),
               "action": d.action, "target": d.target_replicas,
               "before": before, "after": after, "applied": applied,
               "reason": d.reason}
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec) + "\n")
        LOG.info("%s", d.reason)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
