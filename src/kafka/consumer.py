"""Day 4 Kafka consumer: verify the k8s-metrics stream end to end.

Subscribes to `k8s-metrics` and prints every message as formatted JSON. Purely a
verification/debug tool - the real consumer is the Day-5 Faust stream processor.

Run (inside the k8-ai-ops container, host networking):

    docker run --rm --network host \
        -v $PWD:/code -w /code k8-ai-ops:dev src/kafka/consumer.py

Environment variables:
    KAFKA_BOOTSTRAP  default localhost:9094 (Kafka EXTERNAL listener via port-forward)
    KAFKA_TOPIC      default k8s-metrics
"""
from __future__ import annotations

import json
import logging
import os

from kafka import KafkaConsumer

LOG = logging.getLogger("kafka_consumer")

KAFKA_BOOTSTRAP = os.environ.get("KAFKA_BOOTSTRAP", "localhost:9094")
KAFKA_TOPIC = os.environ.get("KAFKA_TOPIC", "k8s-metrics")


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    consumer = KafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP,
        auto_offset_reset="earliest",
        group_id="day4-verification",
        value_deserializer=lambda b: json.loads(b.decode("utf-8")),
    )
    LOG.info("listening on topic=%s bootstrap=%s", KAFKA_TOPIC, KAFKA_BOOTSTRAP)
    for msg in consumer:
        print(
            json.dumps(
                {
                    "partition": msg.partition,
                    "offset": msg.offset,
                    "key": msg.key.decode("utf-8") if msg.key else None,
                    "value": msg.value,
                },
                indent=2,
            ),
            flush=True,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
