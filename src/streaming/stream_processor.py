"""Day 5 Faust stream processor: k8s-metrics -> 30s window -> k8s-features.

Consumes raw metric snapshots from the Day-4 Kafka producer, buckets them into
30-second tumbling windows (manual bucketing, no RocksDB dependency), computes
per-window averages for the six Day-3 metric fields, and emits one feature
record per completed window to the `k8s-features` topic.

Manual bucketing by floor(epoch/30) is chosen over Faust's built-in Table-based
windowing because `faust-streaming`'s window-close callbacks are version-flaky
and pull in RocksDB machinery unnecessary for dev. See tasks/AMENDMENTS.md.

Run (Azure VM, port-forwards for Prometheus :9090 and Kafka :9094 active):

    docker run --rm --network host \
        -e KAFKA_BOOTSTRAP=localhost:9094 \
        --entrypoint faust \
        -v $PWD:/code -w /code k8-ai-ops:dev \
        -A src.streaming.stream_processor worker -l info

Environment variables:
    KAFKA_BOOTSTRAP   broker EXTERNAL listener address, default localhost:9094
    KAFKA_TOPIC_IN    input topic, default k8s-metrics
    KAFKA_TOPIC_OUT   output topic, default k8s-features
"""
from __future__ import annotations

import json
import logging
import math
import os
from datetime import datetime, timezone

import faust

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

BROKER_URL = f"kafka://{os.environ.get('KAFKA_BOOTSTRAP', 'localhost:9094')}"
TOPIC_IN = os.environ.get("KAFKA_TOPIC_IN", "k8s-metrics")
TOPIC_OUT = os.environ.get("KAFKA_TOPIC_OUT", "k8s-features")
WINDOW_S = 30

# The six metric fields from Day-3 QUERIES; these are averaged per window.
METRIC_KEYS = [
    "cpu_cores",
    "memory_bytes",
    "request_rate_per_s",
    "error_rate_per_s",
    "current_replicas",
    "available_replicas",
]

# ---------------------------------------------------------------------------
# Faust app
# ---------------------------------------------------------------------------

app = faust.App(
    "k8s-stream-processor",
    broker=BROKER_URL,
    topic_partitions=1,
    broker_max_poll_interval=500,
    autodiscover=False,
)

raw_topic = app.topic(TOPIC_IN)
feature_topic = app.topic(TOPIC_OUT, key_type=str)

# ---------------------------------------------------------------------------
# Window state  (module-level dict; concurrency=1 by default in Faust)
# ---------------------------------------------------------------------------

_buckets: dict[int, dict] = {}


def _bucket_id(iso_ts: str) -> int:
    """Floor an ISO-8601 timestamp to a WINDOW_S-second bucket id."""
    return int(math.floor(datetime.fromisoformat(iso_ts).timestamp() / WINDOW_S))


def _emit_bucket(bucket_id: int) -> dict | None:
    """Return the averaged feature record for a completed bucket and remove it."""
    acc = _buckets.pop(bucket_id, None)
    if not acc or acc["_n"] == 0:
        return None
    n = acc["_n"]
    ts = datetime.fromtimestamp(bucket_id * WINDOW_S, tz=timezone.utc).isoformat(
        timespec="seconds"
    )
    record: dict = {
        "timestamp": ts,
        "service": "podinfo",
        "window_s": WINDOW_S,
        "samples": n,
    }
    for k in METRIC_KEYS:
        record[f"{k}_avg"] = acc[k] / n
    return record


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------

LOG = logging.getLogger("faust")


@app.agent(raw_topic)
async def process(stream: faust.Stream) -> None:  # type: ignore[type-arg]
    """Consume raw metric snapshots; emit averaged feature records on window close."""
    async for msg in stream:
        try:
            # Faust delivers raw bytes (value_type unset => raw codec).
            if isinstance(msg, bytes):
                msg = json.loads(msg)

            bucket = _bucket_id(msg["timestamp"])

            # Close every bucket that precedes the current one.
            for closed_id in sorted(bid for bid in _buckets if bid < bucket):
                feat = _emit_bucket(closed_id)
                if feat:
                    await feature_topic.send(
                        key="podinfo",
                        value=json.dumps(feat).encode("utf-8"),
                    )
                    LOG.info(
                        "emitted window %s  samples=%d",
                        feat["timestamp"],
                        feat["samples"],
                    )

            # Accumulate into the current bucket.
            if bucket not in _buckets:
                _buckets[bucket] = {k: 0.0 for k in METRIC_KEYS}
                _buckets[bucket]["_n"] = 0
            for k in METRIC_KEYS:
                _buckets[bucket][k] += msg.get(k, 0.0)
            _buckets[bucket]["_n"] += 1

        except Exception as exc:
            LOG.warning("failed to process message: %s", exc)


@app.task
async def on_start() -> None:
    LOG.info(
        "stream processor ready  window=%ds  broker=%s  in=%s  out=%s",
        WINDOW_S,
        BROKER_URL,
        TOPIC_IN,
        TOPIC_OUT,
    )
