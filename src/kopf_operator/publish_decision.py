"""Publish a test decision to the k8s-decisions Kafka topic.

Used by Day 12 smoke testing to drive the operator without standing up the
full Day-9 decision engine. Also serves as a manual injection tool for
exploring behavior.

Run (inside the shared Docker image; reach the host's Kafka port-forward via
--network host):

    docker run --rm --network host -v $PWD:/code -w /code k8-ai-ops:dev \\
        src/kopf_operator/publish_decision.py --action scale --target 4 --current 2
"""
from __future__ import annotations

import argparse
import json
import logging
import os
from datetime import datetime, timezone

from kafka import KafkaProducer

DEFAULT_BOOTSTRAP = os.environ.get("KAFKA_BOOTSTRAP", "localhost:9094")
DEFAULT_TOPIC = os.environ.get("KAFKA_TOPIC", "k8s-decisions")

LOG = logging.getLogger("publish_decision")


def main() -> int:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )
    p = argparse.ArgumentParser()
    p.add_argument("--bootstrap", default=DEFAULT_BOOTSTRAP)
    p.add_argument("--topic", default=DEFAULT_TOPIC)
    p.add_argument("--action", required=True, choices=["scale", "heal", "noop"])
    p.add_argument("--target", required=True,
                   help="target_replicas (for scale) or pod_name hint (for heal)")
    p.add_argument("--current", type=int, default=2,
                   help="current_replicas (operator context)")
    p.add_argument("--reason", default="manual smoke test injection")
    p.add_argument("--service", default="podinfo")
    args = p.parse_args()

    payload = {
        "service": args.service,
        "action": args.action,
        "target_replicas": int(args.target) if args.action == "scale" else args.current,
        "current_replicas": args.current,
        "reason": args.reason,
        "explanation": [],
        "anomaly_score": 0.0,
        "predicted_replicas_raw": float(args.target) if args.action == "scale" else 0.0,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "features": {"target_pod": args.target} if args.action == "heal" else {},
    }

    producer = KafkaProducer(
        bootstrap_servers=args.bootstrap,
        value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
    )
    future = producer.send(args.topic, value=payload)
    record = future.get(timeout=10)
    producer.flush()
    producer.close()
    print(f"published to {args.topic} partition={record.partition} offset={record.offset}")
    print(json.dumps(payload, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())