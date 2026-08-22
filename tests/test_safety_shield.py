"""Unit tests for src.safety.safety_shield.

Anti-drift contract from Day 10: every TLA+ invariant has a Python unit test
that (a) verifies positive cases pass through unchanged, and (b) intentionally
violates the invariant to verify the Python class catches the violation.

If any of these tests ever fail after a code change, the spec and code have
drifted and the TLA+ spec needs to be updated and re-verified by TLC.

Run (inside the shared Docker image — pytest is in requirements.txt):

    docker run --rm -v $PWD:/code -w /code k8-ai-ops:dev \
        python -m pytest tests/test_safety_shield.py -v
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

# Add /code to sys.path (same convention as src/models tests).
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.safety.safety_shield import (  # noqa: E402
    Decision,
    RejectedDecision,
    SafetyShield,
)


@pytest.fixture
def shield(tmp_path):
    """Fresh SafetyShield per test, with audit log in tmp_path."""
    audit = tmp_path / "safety_audit.log"
    return SafetyShield(audit_log_path=audit)


# ===========================================================================
# INVARIANT 1: SafetyMinReplicas (current_replicas >= 1)
# ===========================================================================

def test_min_replicas_clamp_negative_target(shield):
    """Intentional violation: target = -1 should be clamped to min_replicas."""
    d = Decision("podinfo", "scale", target_replicas=-1, current_replicas=2, reason="buggy engine")
    safe = shield.validate(d, bypass_cooldown=True)
    assert isinstance(safe, Decision)
    assert safe.target_replicas == shield.min_replicas


def test_min_replicas_pass_through_valid(shield):
    d = Decision("podinfo", "scale", target_replicas=1, current_replicas=2, reason="scale down to min")
    safe = shield.validate(d, bypass_cooldown=True)
    assert isinstance(safe, Decision)
    assert safe.target_replicas == 1


# ===========================================================================
# INVARIANT 2: SafetyMaxReplicas (current_replicas <= MAX_REPLICAS)
# ===========================================================================

def test_max_replicas_clamp_excessive_target(shield):
    """Intentional violation: target = max+5 should be clamped to max_replicas.

    Note: current=8 so the step to max (10) is exactly max_scale_step (2).
    Step-shrink passes through; only the max clamp fires.
    """
    d = Decision("podinfo", "scale", target_replicas=shield.max_replicas + 5, current_replicas=8, reason="predictor overshoot")
    safe = shield.validate(d, bypass_cooldown=True)
    assert isinstance(safe, Decision)
    assert safe.target_replicas == shield.max_replicas


def test_max_replicas_pass_through_valid(shield):
    """Valid: target exactly at max, current close enough that step is in range."""
    d = Decision("podinfo", "scale", target_replicas=shield.max_replicas, current_replicas=shield.max_replicas - 2, reason="scale to max")
    safe = shield.validate(d, bypass_cooldown=True)
    assert isinstance(safe, Decision)
    assert safe.target_replicas == shield.max_replicas


# ===========================================================================
# INVARIANT 3: SafetyScalingStep (|new - old| <= max_scale_step)
# ===========================================================================

def test_scaling_step_shrink_when_too_big(shield):
    """Intentional violation: target = 8 with current = 2 -> step = 6, shrink to max_scale_step."""
    d = Decision("podinfo", "scale", target_replicas=8, current_replicas=2, reason="predictor says 8")
    safe = shield.validate(d, bypass_cooldown=True)
    assert isinstance(safe, Decision)
    assert safe.target_replicas == 2 + shield.max_scale_step


def test_scaling_step_pass_through_small_step(shield):
    d = Decision("podinfo", "scale", target_replicas=4, current_replicas=2, reason="predictor says 4")
    safe = shield.validate(d, bypass_cooldown=True)
    assert isinstance(safe, Decision)
    assert safe.target_replicas == 4


def test_scaling_step_shrink_when_scale_down_too_big(shield):
    """Shrink must preserve direction (scale-down)."""
    d = Decision("podinfo", "scale", target_replicas=1, current_replicas=9, reason="predictor says 1")
    safe = shield.validate(d, bypass_cooldown=True)
    assert isinstance(safe, Decision)
    # target=1, current=9, delta=-8, shrink to current - max_scale_step = 9 - 2 = 7
    assert safe.target_replicas == 9 - shield.max_scale_step


# ===========================================================================
# INVARIANT 4: SafetyHealNoScale (heal => target == current)
# ===========================================================================

def test_heal_target_equals_current_forces_match(shield):
    """Intentional violation: heal action with target != current must be corrected."""
    d = Decision("podinfo", "heal", target_replicas=4, current_replicas=2, reason="anomaly + scale conflict")
    safe = shield.validate(d, bypass_cooldown=True)
    assert isinstance(safe, Decision)
    assert safe.target_replicas == 2  # forced to current


def test_heal_passes_when_target_matches_current(shield):
    d = Decision("podinfo", "heal", target_replicas=2, current_replicas=2, reason="anomaly")
    safe = shield.validate(d, bypass_cooldown=True)
    assert isinstance(safe, Decision)
    assert safe.target_replicas == 2


# ===========================================================================
# INVARIANT 5: SafetyBoundedRate (cooldown enforced)
# ===========================================================================

def test_cooldown_rejects_immediate_second_action(shield):
    d1 = Decision("podinfo", "scale", target_replicas=3, current_replicas=2, reason="first action")
    safe1 = shield.validate(d1)
    assert isinstance(safe1, Decision)

    d2 = Decision("podinfo", "scale", target_replicas=4, current_replicas=3, reason="second action right away")
    result = shield.validate(d2)
    assert isinstance(result, RejectedDecision)
    assert "cooldown_active" in result.reason


def test_cooldown_bypass_allows_immediate_second_action(shield):
    d1 = Decision("podinfo", "scale", target_replicas=3, current_replicas=2, reason="first action")
    safe1 = shield.validate(d1, bypass_cooldown=True)
    assert isinstance(safe1, Decision)

    d2 = Decision("podinfo", "scale", target_replicas=4, current_replicas=3, reason="second action")
    safe2 = shield.validate(d2, bypass_cooldown=True)
    assert isinstance(safe2, Decision)


# ===========================================================================
# UNKNOWN ACTION: defensive reject
# ===========================================================================

def test_unknown_action_rejected(shield):
    d = Decision("podinfo", "delete_pod", target_replicas=2, current_replicas=2, reason="rogue action")
    result = shield.validate(d, bypass_cooldown=True)
    assert isinstance(result, RejectedDecision)
    assert "unknown_action" in result.reason


# ===========================================================================
# NOOP: always passes (no scaling, no heal, no cooldown trigger)
# ===========================================================================

def test_noop_passes(shield):
    d = Decision("podinfo", "noop", target_replicas=2, current_replicas=2, reason="no change")
    safe = shield.validate(d)
    assert isinstance(safe, Decision)
    assert safe.target_replicas == 2


# ===========================================================================
# COMBINED: scale-down to floor must NOT trigger cooldown's last_action_time
# (noop also doesn't, but cooldown only triggers after a real action)
# ===========================================================================

def test_scale_action_advances_cooldown_clock(shield):
    """After a scale action, cooldown must be active (default 60s)."""
    d1 = Decision("podinfo", "scale", target_replicas=3, current_replicas=2, reason="scale")
    shield.validate(d1)

    # Immediately retry the same action -> cooldown must reject.
    d2 = Decision("podinfo", "scale", target_replicas=4, current_replicas=3, reason="retry")
    result = shield.validate(d2)
    assert isinstance(result, RejectedDecision)


# ===========================================================================
# AUDIT LOG: every validation produces one JSON line
# ===========================================================================

def test_audit_log_writes_one_line_per_validation(shield):
    d1 = Decision("podinfo", "scale", target_replicas=3, current_replicas=2, reason="ok")
    d2 = Decision("podinfo", "delete_pod", target_replicas=2, current_replicas=2, reason="rogue")
    shield.validate(d1, bypass_cooldown=True)
    shield.validate(d2, bypass_cooldown=True)

    lines = shield.audit_log_path.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) == 2
    record1 = json.loads(lines[0])
    record2 = json.loads(lines[1])
    assert record1["rejected"] is False
    assert record2["rejected"] is True


# ===========================================================================
# POLICY LOADING: bad policy -> ValueError
# ===========================================================================

def test_missing_policy_raises(tmp_path):
    bad = tmp_path / "bad.yaml"
    bad.write_text("not_a_safety_shield: true\n", encoding="utf-8")
    with pytest.raises(ValueError, match="missing 'safety_shield'"):
        SafetyShield(policy_path=bad)