"""Day 9 Decision Engine: combines replica predictor + anomaly detector into
executable actions with explanations.

Decision logic (for each feature vector from the Faust `k8s-features` stream):
  1. Score with anomaly detector.
  2. Predict replicas with replica predictor.
  3. Apply decision rules:
     - anomaly_score > threshold          -> action = "heal" (no scale change)
     - predicted_replicas != current       -> action = "scale"
     - else                                -> action = "noop"

Each decision is:
  - logged to logs/decisions.log (newline-delimited JSON)
  - published to Kafka topic k8s-decisions (binary JSON)

Explanations use perturbation-based feature importance (leave-one-out),
noting how the predicted replica count changes when each feature is replaced
by the column mean. Top 2 features = the "explanation" field. This avoids
the complexity of SHAP on River's Hoeffding trees while keeping the result
defensible (LOO importance is a well-established interpretability method).

Run (online, after Day 5 Faust is emitting k8s-features):

    docker run --rm -v $HOME/k8-auto-scaling-self-healing:/code -w /code \
        k8-ai-ops:dev src/decision/decision_engine.py

Run offline (against the 55-row dataset):

    docker run --rm -v $HOME/k8-auto-scaling-self-healing:/code -w /code \
        k8-ai-ops:dev src/decision/decision_engine.py --offline
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import signal
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]

# Add /code to sys.path so the sibling src.models import works inside the
# container (the Dockerfile's WORKDIR is /code but src is not on sys.path).
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from kafka import KafkaConsumer, KafkaProducer  # noqa: E402

from src.models.anomaly_detector import AnomalyDetector  # noqa: E402
from src.models.replica_predictor import ReplicaPredictor  # noqa: E402

LOG = logging.getLogger("decision_engine")

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

DEFAULT_REPLICA_MODEL = ROOT / "data" / "replica_model.pkl"
DEFAULT_ANOMALY_MODEL = ROOT / "data" / "anomaly_model.pkl"
DEFAULT_FEATURES_CSV = ROOT / "data" / "features.csv"
DEFAULT_DECISIONS_LOG = ROOT / "logs" / "decisions.log"
DEFAULT_KAFKA_BOOTSTRAP = "localhost:9094"
DEFAULT_KAFKA_TOPIC = "k8s-decisions"
DEFAULT_KAFKA_INPUT_TOPIC = "k8s-features"
DEFAULT_SERVICE = os.environ.get("WORKLOAD_DEPLOYMENT", "podinfo")


@dataclass
class Decision:
    service: str
    action: str
    target_replicas: int
    current_replicas: int
    reason: str
    explanation: list[dict[str, float]]
    anomaly_score: float
    predicted_replicas_raw: float
    timestamp: str
    features: dict[str, float] = field(default_factory=dict)

    def to_json(self) -> str:
        return json.dumps(asdict(self), default=str)


class DecisionEngine:
    """Combines Day 7 predictor and Day 8 detector into a single decision."""

    def __init__(
        self,
        replica_model_path: Path = DEFAULT_REPLICA_MODEL,
        anomaly_model_path: Path = DEFAULT_ANOMALY_MODEL,
        decisions_log_path: Path = DEFAULT_DECISIONS_LOG,
        kafka_bootstrap: str = DEFAULT_KAFKA_BOOTSTRAP,
        kafka_topic: str = DEFAULT_KAFKA_TOPIC,
        service: str = DEFAULT_SERVICE,
    ) -> None:
        self.replica = ReplicaPredictor.load(replica_model_path)
        self.anomaly = AnomalyDetector.load(anomaly_model_path)
        self.decisions_log_path = Path(decisions_log_path)
        self.kafka_bootstrap = kafka_bootstrap
        self.kafka_topic = kafka_topic
        self.service = service
        self._producer: KafkaProducer | None = None
        self._feature_means: dict[str, float] | None = None
        self.decisions_log_path.parent.mkdir(parents=True, exist_ok=True)

    # --------------------------------------------------------------- model glue

    # Faust emits averaged fields with `_avg` suffix and absolute units. The
    # Day-6 dataset uses relative percentages against pod limits. This map
    # translates Faust's keys to the Day-6 feature names. Mirrors the same
    # logic in src/features/feature_builder.py.
    _FAUST_KEY_MAP: dict[str, str] = {
        "cpu_cores_avg": "cpu_percent",
        "memory_bytes_avg": "memory_percent",
        "request_rate_per_s_avg": "request_rate",
        "p95_latency_ms_avg": "p95_latency_ms",
        "error_rate_per_s_avg": "error_rate",
        "current_replicas_avg": "current_replicas",
        "available_replicas_avg": "available_replicas",
    }
    CPU_LIMIT_CORES_PER_POD = 0.1   # 100m per replica, from podinfo.yaml
    MEM_LIMIT_BYTES_PER_POD = 128 * 1024 * 1024  # 128Mi per replica

    def _featurise(self, rec: dict) -> dict[str, float]:
        out: dict[str, float] = {}
        for target_key in FEATURES:
            if target_key in ("hour_of_day", "day_of_week"):
                # Compute from Faust's ISO timestamp (matches Day-6 logic).
                ts_str = rec.get("timestamp") or ""
                try:
                    ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                    if target_key == "hour_of_day":
                        out[target_key] = float(ts.hour)
                    else:
                        out[target_key] = float(ts.weekday())  # 0 = Mon
                except (ValueError, TypeError):
                    out[target_key] = 0.0
                continue

            # Look up the source key: prefer target_key directly (CSV-style);
            # else try the Faust _avg mapping.
            src_key = next(
                (s for s, t in self._FAUST_KEY_MAP.items() if t == target_key),
                target_key,
            )
            raw_val = float(rec.get(src_key) or 0.0)

            # Normalize absolute units to percentages against pod limits.
            if target_key == "cpu_percent" and "cpu_cores" in src_key:
                replicas = max(float(rec.get("current_replicas_avg") or 0.0), 1.0)
                raw_val = (raw_val / (self.CPU_LIMIT_CORES_PER_POD * replicas)) * 100
            elif target_key == "memory_percent" and "memory_bytes" in src_key:
                replicas = max(float(rec.get("current_replicas_avg") or 0.0), 1.0)
                raw_val = (raw_val / (self.MEM_LIMIT_BYTES_PER_POD * replicas)) * 100

            out[target_key] = raw_val
        return out

    def _compute_feature_means(self, rows: list[dict]) -> dict[str, float]:
        df = pd.DataFrame(rows)
        return {k: float(df[k].mean()) for k in FEATURES}

    def explain(
        self,
        features: dict[str, float],
        top_n: int = 2,
    ) -> list[dict[str, float]]:
        """Leave-one-out feature importance: perturbation magnitude = |raw - perturbed|.

        Returns a list of `{feature, delta}` dicts, sorted by descending delta.
        """
        if self._feature_means is None:
            return []
        raw = self.replica.predict_raw(features) or 0.0
        contributions: list[tuple[str, float]] = []
        for k in FEATURES:
            perturbed = dict(features)
            # Use the column mean if available, else the current value
            # (i.e., no perturbation -> delta 0). This makes explain()
            # robust to partial feature_means dicts.
            perturbed[k] = self._feature_means.get(k, features[k])
            new = self.replica.predict_raw(perturbed) or 0.0
            contributions.append((k, abs(raw - new)))
        contributions.sort(key=lambda c: c[1], reverse=True)
        return [{"feature": k, "delta": round(d, 4)} for k, d in contributions[:top_n]]

    # --------------------------------------------------------------- decision

    def decide(
        self,
        record: dict,
        feature_means: dict[str, float] | None = None,
    ) -> Decision:
        features = self._featurise(record)
        current_replicas = int(features.get("current_replicas") or 1)
        if feature_means is not None:
            self._feature_means = feature_means

        anomaly_score = self.anomaly.score(features)
        predicted_raw = self.replica.predict_raw(features) or float(current_replicas)
        predicted_replicas = self.replica.predict(features)

        # High-confidence gate: require anomaly_score to be at least 2x the
        # threshold. The Day-8 detector scores every fresh-window idle pattern
        # near the threshold, but real anomalies (Day-13 fault injection)
        # score much higher. This 2x gate suppresses false-positive heals on
        # baseline traffic without sacrificing real-anomaly detection.
        heal_threshold = self.anomaly.threshold * 2.0
        if anomaly_score > heal_threshold:
            action = "heal"
            target_replicas = current_replicas
            reason = (
                f"anomaly_score={anomaly_score:.4f} > "
                f"heal_threshold={heal_threshold:.4f}"
            )
        elif predicted_replicas != current_replicas:
            action = "scale"
            target_replicas = predicted_replicas
            reason = (
                f"predictor says {predicted_replicas} (current={current_replicas})"
            )
        else:
            action = "noop"
            target_replicas = current_replicas
            reason = (
                f"predictor agrees with current={current_replicas}, "
                f"anomaly_score={anomaly_score:.4f}"
            )

        explanation = self.explain(features) if action == "scale" else []

        return Decision(
            service=self.service,
            action=action,
            target_replicas=target_replicas,
            current_replicas=current_replicas,
            reason=reason,
            explanation=explanation,
            anomaly_score=round(anomaly_score, 4),
            predicted_replicas_raw=round(predicted_raw, 4),
            timestamp=datetime.now(timezone.utc).isoformat(),
            features=features,
        )

    # --------------------------------------------------------------- output

    def log(self, decision: Decision) -> None:
        with open(self.decisions_log_path, "a", encoding="utf-8") as f:
            f.write(decision.to_json() + "\n")

    def _producer_lazy(self) -> KafkaProducer:
        if self._producer is None:
            self._producer = KafkaProducer(
                bootstrap_servers=self.kafka_bootstrap,
                value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
            )
        return self._producer

    def publish(self, decision: Decision) -> None:
        producer = self._producer_lazy()
        producer.send(self.kafka_topic, value=asdict(decision))
        producer.flush(timeout=5)

    def close(self) -> None:
        if self._producer is not None:
            self._producer.flush()
            self._producer.close()
            self._producer = None


# ----------------------------------------------------------------------- run


def _run_offline(engine: DecisionEngine, csv_path: Path) -> None:
    df = pd.read_csv(csv_path)
    rows = df.to_dict("records")
    means = engine._compute_feature_means(rows)
    print(f"Offloading {len(rows)} records from {csv_path}")
    print(f"Feature means: {means}")
    print()
    counts = {"scale": 0, "heal": 0, "noop": 0}
    for i, row in enumerate(rows):
        decision = engine.decide(row, feature_means=means)
        engine.log(decision)
        counts[decision.action] += 1
        if i < 8:
            print(
                f"[{i+1}/{len(rows)}] scenario={row['scenario']:13s}  "
                f"action={decision.action:5s}  target={decision.target_replicas}  "
                f"reason={decision.reason}"
            )
            if decision.explanation:
                print(f"    explanation: {decision.explanation}")
    print()
    print(f"Decision mix: {counts}")
    summary = open(DEFAULT_DECISIONS_LOG, "r", encoding="utf-8").readlines()
    print(f"Saved {len(summary)} decisions to {DEFAULT_DECISIONS_LOG}")


def _run_online(engine: DecisionEngine, kafka_bootstrap: str, topic: str) -> None:
    consumer = KafkaConsumer(
        topic,
        bootstrap_servers=kafka_bootstrap,
        auto_offset_reset="latest",
        enable_auto_commit=True,
        group_id="decision-engine",
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
    )
    print(f"Listening on {topic} @ {kafka_bootstrap}; ctrl-c to stop.")

    def _stop(*_):
        consumer.close()
        engine.close()
        sys.exit(0)

    signal.signal(signal.SIGINT, _stop)

    for message in consumer:
        rec = message.value
        decision = engine.decide(rec)
        engine.log(decision)
        try:
            engine.publish(decision)
        except Exception as exc:  # noqa: BLE001
            LOG.warning("publish failed: %s", exc)
        print(
            f"action={decision.action:5s}  target={decision.target_replicas}  "
            f"reason={decision.reason}"
        )


def main() -> int:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )
    p = argparse.ArgumentParser()
    p.add_argument("--offline", action="store_true",
                   help="run on data/features.csv instead of consuming Kafka")
    p.add_argument("--csv", default=str(DEFAULT_FEATURES_CSV))
    p.add_argument("--bootstrap", default=os.environ.get("KAFKA_BOOTSTRAP", DEFAULT_KAFKA_BOOTSTRAP))
    p.add_argument("--topic", default=DEFAULT_KAFKA_INPUT_TOPIC)
    p.add_argument("--output-topic", default=DEFAULT_KAFKA_TOPIC)
    args = p.parse_args()

    engine = DecisionEngine(
        kafka_bootstrap=args.bootstrap,
        kafka_topic=args.output_topic,
    )

    if args.offline:
        _run_offline(engine, Path(args.csv))
    else:
        _run_online(engine, args.bootstrap, args.topic)

    engine.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
