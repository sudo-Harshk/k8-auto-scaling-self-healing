"""Unit tests for src.decision.decision_engine.

These tests exist to close the **Day-9 gap**: the DecisionEngine's Kafka
consumer mode (`_run_online`) was committed without being exercised
end-to-end. Day-13 E2E integration exposed two bugs that offline tests
didn't catch:

  1. **Field-name mismatch.** Faust emits `cpu_cores_avg`,
     `memory_bytes_avg`, `request_rate_per_s_avg`, etc. (Day-5 metric
     naming). The Day-6 dataset uses `cpu_percent`, `memory_percent`,
     `request_rate`, etc. The offline test ran on the CSV directly and
     never hit the Faust-format path.
  2. **Hour/day-of-week not derived from timestamp.** The CSV had
     `hour_of_day` and `day_of_week` columns populated by the feature
     builder; the Kafka consumer path had no equivalent.

These tests pin both behaviors. If a future change to either Faust's
METRIC_KEYS or to `_featurise()` breaks the contract, these tests fail.

Run (in container with /code mounted):
    docker run --rm --entrypoint python -v $PWD:/code -w /code \\
        k8-ai-ops:dev -m pytest tests/test_decision_engine.py -v
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.decision.decision_engine import DecisionEngine  # noqa: E402


@pytest.fixture
def engine(tmp_path):
    """DecisionEngine pointed at the project's real models, with a tmp audit log."""
    audit = tmp_path / "decisions.log"
    return DecisionEngine(decisions_log_path=audit)


def _faust_record(
    *,
    timestamp: str = "2026-08-21T14:30:00+00:00",
    cpu_cores: float = 0.005,
    memory_bytes: float = 120_000_000,
    request_rate: float = 5.0,
    error_rate: float = 0.0,
    p95_latency: float = 4.75,
    current_replicas: int = 2,
    available_replicas: int = 2,
) -> dict:
    """Construct a Faust k8s-features record with the standard Day-5 names."""
    return {
        "timestamp": timestamp,
        "service": "podinfo",
        "window_s": 30,
        "samples": 3,
        "cpu_cores_avg": cpu_cores,
        "memory_bytes_avg": memory_bytes,
        "request_rate_per_s_avg": request_rate,
        "error_rate_per_s_avg": error_rate,
        "current_replicas_avg": current_replicas,
        "available_replicas_avg": available_replicas,
        "p95_latency_ms_avg": p95_latency,
    }


# ===========================================================================
# Field-name translation (Day-9 bug #1)
# ===========================================================================

def test_featurise_translates_faust_cpu_cores_to_percent(engine):
    """cpu_cores_avg (absolute cores) -> cpu_percent (% of pod limit)."""
    rec = _faust_record(cpu_cores=0.05, current_replicas=2)
    feats = engine._featurise(rec)
    # Pod limit = 0.1 cores * 2 replicas = 0.2 cores.
    # cpu_percent = 0.05 / 0.2 * 100 = 25.0
    assert feats["cpu_percent"] == pytest.approx(25.0)


def test_featurise_translates_faust_memory_bytes_to_percent(engine):
    """memory_bytes_avg (absolute bytes) -> memory_percent (% of pod limit)."""
    rec = _faust_record(memory_bytes=128 * 1024 * 1024, current_replicas=1)
    feats = engine._featurise(rec)
    # Pod limit = 128Mi * 1 replica = 128Mi. So 100%.
    assert feats["memory_percent"] == pytest.approx(100.0)


def test_featurise_keeps_request_rate_as_is(engine):
    """request_rate_per_s_avg passes through unchanged (already absolute)."""
    rec = _faust_record(request_rate=42.5)
    feats = engine._featurise(rec)
    assert feats["request_rate"] == 42.5


def test_featurise_handles_missing_faust_fields_gracefully(engine):
    """A sparse Faust record defaults features to 0.0 without crashing."""
    rec = {"timestamp": "2026-08-21T14:30:00+00:00", "service": "podinfo"}
    feats = engine._featurise(rec)
    # Metric-bearing features default to 0.0 when Faust didn't emit them.
    # hour_of_day and day_of_week are derived from the timestamp and are non-zero.
    for k in (
        "cpu_percent", "memory_percent", "request_rate",
        "p95_latency_ms", "error_rate", "current_replicas",
    ):
        assert feats[k] == 0.0, f"{k} should be 0.0 for sparse record, got {feats[k]}"
    # The timestamp IS present in this record, so hour/day are derived correctly.
    assert feats["hour_of_day"] == 14
    assert feats["day_of_week"] == 4


# ===========================================================================
# Hour / day-of-week derivation (Day-9 bug #2)
# ===========================================================================

def test_featurise_computes_hour_of_day_from_timestamp(engine):
    rec = _faust_record(timestamp="2026-08-21T14:30:00+00:00")
    feats = engine._featurise(rec)
    assert feats["hour_of_day"] == 14


def test_featurise_computes_day_of_week_from_timestamp(engine):
    """2026-08-21 is a Friday (weekday=4)."""
    rec = _faust_record(timestamp="2026-08-21T14:30:00+00:00")
    feats = engine._featurise(rec)
    assert feats["day_of_week"] == 4


def test_featurise_handles_malformed_timestamp(engine):
    """A bad timestamp -> 0.0 for hour/day, no crash."""
    rec = _faust_record(timestamp="not-a-timestamp")
    feats = engine._featurise(rec)
    assert feats["hour_of_day"] == 0.0
    assert feats["day_of_week"] == 0.0


def test_featurise_handles_missing_timestamp(engine):
    """A missing timestamp -> 0.0 for hour/day, no crash."""
    rec = {"cpu_cores_avg": 0.01, "memory_bytes_avg": 100_000_000,
           "request_rate_per_s_avg": 1.0, "current_replicas_avg": 2}
    feats = engine._featurise(rec)
    assert feats["hour_of_day"] == 0.0
    assert feats["day_of_week"] == 0.0


# ===========================================================================
# End-to-end Faust-record -> Decision
# ===========================================================================

def test_decide_with_realistic_faust_record_produces_valid_decision(engine):
    """Full integration: Faust record -> decide() -> Decision populated correctly."""
    rec = _faust_record(request_rate=10.0, current_replicas=2)
    decision = engine.decide(rec, feature_means={"cpu_percent": 1.0})
    assert decision.features["request_rate"] == 10.0
    assert decision.features["cpu_percent"] > 0
    assert decision.features["hour_of_day"] in range(0, 24)
    assert decision.features["day_of_week"] in range(0, 7)
    assert decision.action in {"scale", "heal", "noop"}
    assert decision.target_replicas >= 1
    assert decision.timestamp != ""
    # Anomaly score is always populated.
    assert 0.0 <= decision.anomaly_score <= 1.0
    # predicted_replicas_raw is always populated.
    assert isinstance(decision.predicted_replicas_raw, float)


def test_decide_publishes_audit_record(engine):
    """Every decide() + log() writes one JSON line to the audit log."""
    rec = _faust_record()
    decision = engine.decide(rec)
    engine.log(decision)
    contents = engine.decisions_log_path.read_text(encoding="utf-8")
    lines = contents.strip().split("\n")
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert "features" in record
    assert "action" in record
    assert "target_replicas" in record


# ===========================================================================
# Anti-regression guard: same input twice -> same key features
# ===========================================================================

def test_featurise_is_deterministic(engine):
    """The same Faust record must produce the same feature dict (no randomness)."""
    rec = _faust_record(request_rate=10.0)
    feats1 = engine._featurise(rec)
    feats2 = engine._featurise(rec)
    assert feats1 == feats2