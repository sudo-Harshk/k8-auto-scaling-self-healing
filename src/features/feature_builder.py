"""Day 6 Feature Builder: consume k8s-features, enrich, write one JSONL per scenario.

Runs alongside a Locust load scenario: consumes the Faust windowed records from
`k8s-features` in real time, derives the Day-6 feature vector (percentages against
podinfo's own pod limits, time-of-day features), and appends each record as one
JSON line to OUTPUT_FILE. After all scenarios, `build_dataset.py` merges the JSONL
files into `data/features.csv` with labels.

Percentages are computed against the pod's own limits (ops/manifests/podinfo.yaml:
100m CPU / 128Mi memory per replica), not node capacity - node-relative numbers on
a 4 vCPU / 16 GiB VM would be near-zero and useless as ML features.

Run (inside k8-ai-ops:dev, host networking, Kafka port-forward active):

    docker run -d --network host --name feature-collector \
        -e KAFKA_BOOTSTRAP=localhost:9094 \
        -e OUTPUT_FILE=/code/data/scenario_baseline.jsonl \
        -e TIMEOUT_SECS=345 \
        -v $HOME/k8-auto-scaling-self-healing:/code -w /code \
        k8-ai-ops:dev python src/features/feature_builder.py

Environment variables:
    KAFKA_BOOTSTRAP          broker EXTERNAL listener, default localhost:9094
    KAFKA_TOPIC              topic to consume, default k8s-features
    OUTPUT_FILE              JSONL output path, default data/scenario_raw.jsonl
    TIMEOUT_SECS             stop consuming after this many seconds, default 300
    CPU_LIMIT_CORES_PER_POD  pod CPU limit, default 0.1 (matches podinfo.yaml)
    MEM_LIMIT_BYTES_PER_POD  pod memory limit, default 134217728 (128Mi)
"""
from __future__ import annotations

import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path

from kafka import KafkaConsumer

LOG = logging.getLogger("feature_builder")

KAFKA_BOOTSTRAP = os.environ.get("KAFKA_BOOTSTRAP", "localhost:9094")
KAFKA_TOPIC = os.environ.get("KAFKA_TOPIC", "k8s-features")
OUTPUT_FILE = os.environ.get("OUTPUT_FILE", "data/scenario_raw.jsonl")
TIMEOUT_SECS = float(os.environ.get("TIMEOUT_SECS", "300"))

CPU_LIMIT_CORES_PER_POD = float(os.environ.get("CPU_LIMIT_CORES_PER_POD", "0.1"))
MEM_LIMIT_BYTES_PER_POD = float(
    os.environ.get("MEM_LIMIT_BYTES_PER_POD", str(128 * 1024 * 1024))
)


def enrich(record: dict) -> dict:
    """Turn one Faust windowed record into the Day-6 feature vector."""
    ts = datetime.fromisoformat(record["timestamp"])
    replicas = max(float(record.get("current_replicas_avg") or 0.0), 1.0)

    def num(key: str) -> float:
        return float(record.get(key) or 0.0)

    return {
        "timestamp": record["timestamp"],
        "service": record.get("service", "podinfo"),
        "window_s": record.get("window_s", 30),
        "samples": record.get("samples", 0),
        # Percentages vs the workload's own pod limits.
        "cpu_percent": round(
            num("cpu_cores_avg") / (CPU_LIMIT_CORES_PER_POD * replicas) * 100, 4
        ),
        "memory_percent": round(
            num("memory_bytes_avg") / (MEM_LIMIT_BYTES_PER_POD * replicas) * 100, 4
        ),
        # Pass-through workload signals.
        "request_rate": round(num("request_rate_per_s_avg"), 4),
        "p95_latency_ms": round(num("p95_latency_ms_avg"), 4),
        "error_rate": round(num("error_rate_per_s_avg"), 4),
        "current_replicas": round(num("current_replicas_avg"), 2),
        "available_replicas": round(num("available_replicas_avg"), 2),
        # Time features (VM clock is UTC).
        "hour_of_day": ts.hour,
        "day_of_week": ts.weekday(),  # 0 = Monday
    }


def main() -> int:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )

    out_path = Path(OUTPUT_FILE)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    consumer = KafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP,
        auto_offset_reset="latest",  # only this scenario's windows
        group_id=f"feature-builder-{int(time.time())}",
        value_deserializer=lambda b: json.loads(b.decode("utf-8")),
    )
    LOG.info(
        "consuming topic=%s  timeout=%ss  output=%s",
        KAFKA_TOPIC, TIMEOUT_SECS, out_path,
    )

    count = 0
    deadline = time.time() + TIMEOUT_SECS
    # Line-buffered so a docker stop / timeout kill never loses buffered rows.
    with open(out_path, "w", buffering=1) as f:
        while time.time() < deadline:
            records = consumer.poll(timeout_ms=2000)
            for msgs in records.values():
                for msg in msgs:
                    row = enrich(msg.value)
                    f.write(json.dumps(row) + "\n")
                    count += 1
                    LOG.info(
                        "recorded #%d  cpu=%.2f%%  mem=%.2f%%  req=%.2f/s  "
                        "p95=%.1fms  repl=%.0f",
                        count,
                        row["cpu_percent"],
                        row["memory_percent"],
                        row["request_rate"],
                        row["p95_latency_ms"],
                        row["current_replicas"],
                    )
    consumer.close()
    LOG.info("done: wrote %d records to %s", count, out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
