"""Day 4 Kafka producer: stream podinfo metrics from Prometheus into Kafka.

Polls the Day-3 metrics client every POLL_INTERVAL seconds (default 10, within the
Day-4 plan's 10-15s), serializes each snapshot as JSON, and publishes it to the
`k8s-metrics` topic (key: workload name). This is the head of the pipeline:
Prometheus -> Kafka -> (Day 5) Faust -> ... -> operator.

Run (inside the k8-ai-ops container, host networking so localhost port-forwards
to Prometheus and Kafka are reachable):

    docker run --rm --network host \
        -e PROMETHEUS_URL=http://localhost:9090 \
        -v $PWD:/code -w /code k8-ai-ops:dev src/kafka/producer.py

Environment variables:
    PROMETHEUS_URL   default http://host.docker.internal:9090 (metrics-client default)
    KAFKA_BOOTSTRAP  default localhost:9094 (Kafka EXTERNAL listener via port-forward)
    KAFKA_TOPIC      default k8s-metrics
    POLL_INTERVAL    seconds between samples, default 10
"""
from __future__ import annotations

import json
import logging
import os
import sys
import time
from pathlib import Path

# Make `from src.metrics...` work when invoked as `python src/kafka/producer.py`.
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from kafka import KafkaProducer  # noqa: E402

from src.metrics.metrics_client import PodinfoMetricsClient  # noqa: E402

LOG = logging.getLogger("kafka_producer")

KAFKA_BOOTSTRAP = os.environ.get("KAFKA_BOOTSTRAP", "localhost:9094")
KAFKA_TOPIC = os.environ.get("KAFKA_TOPIC", "k8s-metrics")
POLL_INTERVAL = float(os.environ.get("POLL_INTERVAL", "10"))


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    client = PodinfoMetricsClient()  # fail-fast if Prometheus is unreachable
    producer = KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        key_serializer=lambda k: k.encode("utf-8"),
        acks="all",
    )
    LOG.info(
        "producing to topic=%s bootstrap=%s every %.0fs",
        KAFKA_TOPIC, KAFKA_BOOTSTRAP, POLL_INTERVAL,
    )
    sent = 0
    try:
        while True:
            snapshot = client.get_current_metrics()
            producer.send(KAFKA_TOPIC, key="podinfo", value=snapshot).get(timeout=10)
            sent += 1
            LOG.info("sent #%d: %s", sent, snapshot)
            time.sleep(POLL_INTERVAL)
    except KeyboardInterrupt:
        LOG.info("stopping (keyboard interrupt) after %d messages", sent)
    finally:
        producer.flush()
        producer.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
