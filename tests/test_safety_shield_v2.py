"""Anti-drift tests for the v2 policy (specs/safety_policy_v2.yaml).

Each test mirrors one invariant / action property of specs/SafetyShieldV2.tla.
"""
from pathlib import Path

import pytest

from src.safety.safety_shield import Decision, RejectedDecision, SafetyShield

POLICY = Path(__file__).resolve().parents[1] / "specs" / "safety_policy_v2.yaml"


@pytest.fixture
def shield(tmp_path):
    return SafetyShield(policy_path=POLICY, audit_log_path=tmp_path / "a.log")


def D(action, target, current):
    return Decision(service="podinfo", action=action, target_replicas=target,
                    current_replicas=current, reason="t")


def test_min_clamp(shield):             # SafetyMinReplicas
    assert shield.validate(D("scale", 0, 3), bypass_cooldown=True).target_replicas == 2


def test_max_clamp(shield):             # SafetyMaxReplicas
    assert shield.validate(D("scale", 99, 18), bypass_cooldown=True).target_replicas == 20


@pytest.mark.parametrize("cur,want", [(2, 6), (4, 8), (6, 12), (12, 20)])
def test_up_step_is_max_4_or_100pct(shield, cur, want):   # SafetyScalingStep (up)
    assert shield.validate(D("scale", 99, cur), bypass_cooldown=True).target_replicas == want


def test_down_step_is_2(shield):        # SafetyScalingStep (down)
    assert shield.validate(D("scale", 2, 15), bypass_cooldown=True).target_replicas == 13


def test_heal_keeps_replicas(shield):   # SafetyHealNoScale
    assert shield.validate(D("heal", 9, 4), bypass_cooldown=True).target_replicas == 4


def test_unknown_action_rejected(shield):
    assert isinstance(shield.validate(D("delete_pod", 2, 2)), RejectedDecision)


def test_noop_never_throttled_and_never_restarts_cooldown(shield):
    assert not isinstance(shield.validate(D("scale", 4, 2)), RejectedDecision)
    shield._last_action_time -= 20             # 20 s later
    for _ in range(5):
        assert not isinstance(shield.validate(D("noop", 4, 4)), RejectedDecision)
    # noop did not restart the timer: an up-scale 20 s after the last action passes
    assert not isinstance(shield.validate(D("scale", 8, 4)), RejectedDecision)


def test_up_cooldown_15s(shield):       # SafetyBoundedRate (up)
    assert not isinstance(shield.validate(D("scale", 4, 2)), RejectedDecision)
    assert isinstance(shield.validate(D("scale", 8, 4)), RejectedDecision)
    shield._last_action_time -= 16
    assert not isinstance(shield.validate(D("scale", 8, 4)), RejectedDecision)


def test_down_cooldown_60s(shield):     # SafetyBoundedRate (down)
    assert not isinstance(shield.validate(D("scale", 8, 4)), RejectedDecision)
    shield._last_action_time -= 30
    assert isinstance(shield.validate(D("scale", 6, 8)), RejectedDecision)
    shield._last_action_time -= 31
    assert not isinstance(shield.validate(D("scale", 6, 8)), RejectedDecision)
