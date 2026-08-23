"""Unit tests for src.kopf_operator.actuator.

Tests the operator logic that does NOT require a live Kubernetes cluster:
  - decision_from_kafka() payload parsing
  - record_action() audit log writing
  - _extract_mods() safety-modification parser

The actual K8s API calls (patch Deployment, delete pod) are exercised in
the integration smoke test on the VM, not in unit tests (would need a
mock kubernetes client).

Run:
    docker run --rm --entrypoint python -v $PWD:/code -w /code k8-ai-ops:dev \\
        -m pytest tests/test_actuator.py -v
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.kopf_operator.actuator import (  # noqa: E402
    OperatorAction,
    decision_from_kafka,
    record_action,
    _extract_mods,
)


# ===========================================================================
# decision_from_kafka: payload parsing
# ===========================================================================

def test_decision_from_kafka_minimal_payload():
    raw = {"action": "scale", "target_replicas": 4, "current_replicas": 2}
    d = decision_from_kafka(raw)
    assert d.action == "scale"
    assert d.target_replicas == 4
    assert d.current_replicas == 2
    assert d.service == "podinfo"  # default


def test_decision_from_kafka_full_payload():
    raw = {
        "service": "podinfo",
        "action": "heal",
        "target_replicas": 2,
        "current_replicas": 2,
        "reason": "anomaly",
        "explanation": [{"feature": "x", "delta": 1.0}],
        "anomaly_score": 0.5,
        "predicted_replicas_raw": 2.0,
        "timestamp": "2026-08-23T00:00:00+00:00",
        "features": {"target_pod": "podinfo-x"},
    }
    d = decision_from_kafka(raw)
    assert d.action == "heal"
    assert d.explanation == [{"feature": "x", "delta": 1.0}]
    assert d.features == {"target_pod": "podinfo-x"}


def test_decision_from_kafka_defaults_for_missing_fields():
    """If the message is sparse, the parser fills defaults rather than crashing."""
    raw = {"action": "noop"}
    d = decision_from_kafka(raw)
    assert d.action == "noop"
    assert d.target_replicas == 0
    assert d.current_replicas == 0
    assert d.service == "podinfo"


# ===========================================================================
# record_action: audit log writing
# ===========================================================================

def test_record_action_writes_one_json_line(tmp_path):
    audit = tmp_path / "operator_actions.log"
    action = OperatorAction(
        timestamp="2026-08-23T14:07:22.473441+00:00",
        service="podinfo",
        action="scale",
        target_replicas=4,
        current_replicas_before=2,
        current_replicas_after=4,
        applied=True,
        rejected_reason=None,
        safety_modifications=[],
        api_call="patch_namespaced_deployment",
        pod_name=None,
    )
    record_action(audit, action)
    lines = audit.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["action"] == "scale"
    assert record["applied"] is True
    assert record["target_replicas"] == 4


def test_record_action_appends_multiple(tmp_path):
    """Calling record_action twice writes two lines, not overwrites."""
    audit = tmp_path / "operator_actions.log"
    for i in range(3):
        action = OperatorAction(
            timestamp=f"2026-08-23T14:07:{i:02d}.000+00:00",
            service="podinfo",
            action="noop",
            target_replicas=2,
            current_replicas_before=2,
            current_replicas_after=2,
            applied=False,
            rejected_reason=None,
            safety_modifications=[],
            api_call="none",
            pod_name=None,
        )
        record_action(audit, action)
    lines = audit.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) == 3


# ===========================================================================
# _extract_mods: safety-modification parser
# ===========================================================================

def test_extract_mods_present():
    reason = "predictor says 15 | safety_mods=['shrink_step(15->4)']"
    mods = _extract_mods(reason)
    assert mods == ["['shrink_step(15->4)']"]


def test_extract_mods_absent():
    reason = "no change | safety_pass"
    mods = _extract_mods(reason)
    assert mods == []


def test_extract_mods_empty():
    reason = "scale up | safety_mods=[]"
    mods = _extract_mods(reason)
    # _extract_mods is forgiving; we just check it doesn't crash
    assert isinstance(mods, list)