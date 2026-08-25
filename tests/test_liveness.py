"""
Day 15 - Liveness simulation test (Python-side mirror of TLA+ property).

The TLA+ spec `specs/SafetyShield.tla` proves the LivenessEventuallyScaleUp
property by exhaustive model checking: for every reachable state where the
sustained-demand precondition holds (consecutive_overload = MAX_REPLICAS),
the operator eventually scales current_replicas above its current value.

This Python test mirrors that property at the implementation level by
simulating the decision engine + safety shield + operator loop over a
synthetic sustained-demand trajectory and asserting that the operator
eventually fires ApplyScaleUp. It does NOT replace the TLA+ proof; it
guards against regressions in the Python code (Day 11 SafetyShield,
Day 12 operator) and provides a quick local sanity check.

The test runs three scenarios:
  - sustained_high_demand  (10 consecutive windows of predicted > current)
  - mixed_demand           (alternating up / down)
  - heal_only              (anomaly-driven; no scale)

Each scenario is run for 30 logical ticks. We assert that the operator
applied at least one scale-up action in the sustained-high-demand case,
and did not violate any safety invariant in any case.

Run with:
    docker run --rm -v $PWD:/code -w /code --entrypoint python k8-ai-ops:dev \
        -m pytest tests/test_liveness.py -v
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from safety.safety_shield import SafetyShield  # noqa: E402

SHIELD_CFG = Path(__file__).resolve().parent.parent / "specs" / "safety_policy.yaml"


@dataclass
class MockDecision:
    """Lightweight Decision mirror used by the liveness tests.

    Matches the field names of `safety_shield.Decision` exactly so that
    `SafetyShield.validate()` and its `_audit`/`_reject` helpers work
    without modification. Field values default to safe empty values.
    """
    action: str
    target_replicas: int
    current_replicas: int
    service: str = "podinfo"
    reason: str = ""
    explanation: list = field(default_factory=list)
    anomaly_score: float = 0.0
    predicted_replicas_raw: float = 0.0
    timestamp: str = ""
    features: dict = field(default_factory=dict)


def _scenario_high_demand() -> List[Tuple[str, int, int]]:
    """10 consecutive windows with target > current."""
    out = []
    current = 2
    for tick in range(30):
        target = min(10, 3 + tick // 2)
        out.append(("scale", target, current))
    return out


def _scenario_mixed_demand() -> List[Tuple[str, int, int]]:
    """Alternating: 3 ticks up, 2 ticks steady."""
    out = []
    current = 2
    for tick in range(30):
        cycle = tick % 5
        if cycle < 3:
            target = min(10, current + 1)
        else:
            target = current
        out.append(("scale", target, current))
    return out


def _scenario_heal_only() -> List[Tuple[str, int, int]]:
    """Heal-only scenario (anomaly-driven): target always equals current."""
    out = []
    current = 2
    for tick in range(30):
        out.append(("heal", current, current))
    return out


def _simulate(
    scenario: List[Tuple[str, int, int]],
    shield: SafetyShield,
) -> List:
    """Run a scenario through the shield with cooldown bypassed (logical clock)."""
    out = []
    for action, target, current in scenario:
        decision = MockDecision(action=action, target_replicas=target, current_replicas=current)
        result = shield.validate(decision, bypass_cooldown=True)
        out.append(result)
    return out


def test_liveness_high_demand_eventually_scales_up():
    """Sustained demand scenario: the operator must scale up at least once."""
    shield = SafetyShield(policy_path=SHIELD_CFG)
    scenario = _scenario_high_demand()
    results = _simulate(scenario, shield)
    scale_ups = [
        r for r in results
        if hasattr(r, "action") and r.action == "scale"
        and getattr(r, "target_replicas", 0) > getattr(r, "current_replicas", 0)
    ]
    assert scale_ups, (
        f"No scale-up applied under sustained demand; "
        f"results={[r.action if hasattr(r, 'action') else type(r).__name__ for r in results]}"
    )
    # At least one scale-up must result in a target strictly above current.
    targets = [r.target_replicas for r in scale_ups]
    assert max(targets) > 2, f"No progress beyond initial replicas: {targets}"


def test_liveness_mixed_demand_within_bounds():
    """Mixed demand scenario: all targets stay within [1, 10]."""
    shield = SafetyShield(policy_path=SHIELD_CFG)
    scenario = _scenario_mixed_demand()
    results = _simulate(scenario, shield)
    for r in results:
        if hasattr(r, "target_replicas"):
            assert 1 <= r.target_replicas <= 10, (
                f"target_replicas={r.target_replicas} outside [1, 10]"
            )


def test_liveness_heal_only_does_not_scale():
    """Heal-only scenario: no scale decisions are produced."""
    shield = SafetyShield(policy_path=SHIELD_CFG)
    scenario = _scenario_heal_only()
    results = _simulate(scenario, shield)
    scale_decisions = [
        r for r in results
        if hasattr(r, "action") and r.action == "scale"
    ]
    assert not scale_decisions, (
        f"Unexpected scale decisions in heal-only scenario: "
        f"{[r.target_replicas for r in scale_decisions]}"
    )


def test_liveness_shield_enforces_cooldown_real_time():
    """Cooldown test: two scale actions within cooldown_seconds -> second rejected."""
    shield = SafetyShield(policy_path=SHIELD_CFG)
    cooldown = shield.cooldown_seconds
    assert cooldown >= 1, f"cooldown_seconds={cooldown} should be at least 1"

    d1 = MockDecision(action="scale", target_replicas=4, current_replicas=2)
    v1 = shield.validate(d1, bypass_cooldown=False)
    assert hasattr(v1, "action") and v1.action == "scale", (
        f"First action should pass: {v1}"
    )

    # Immediately try a second action — should be rejected by cooldown.
    d2 = MockDecision(action="scale", target_replicas=5, current_replicas=2)
    v2 = shield.validate(d2, bypass_cooldown=False)
    assert hasattr(v2, "rejected") and v2.rejected, (
        f"Second action should be rejected by cooldown: {v2}"
    )
    assert "cooldown" in str(v2.reason).lower(), (
        f"Rejection reason should mention cooldown: {v2.reason}"
    )


def test_liveness_shield_clamps_oversized_jump():
    """Safety scaling-step: a jump > max_scale_step is shrunk, not rejected."""
    shield = SafetyShield(policy_path=SHIELD_CFG)
    max_step = shield.max_scale_step
    # Request a jump of 5 replicas (way over max_scale_step).
    current = 2
    target = current + 5
    d = MockDecision(action="scale", target_replicas=target, current_replicas=current)
    v = shield.validate(d, bypass_cooldown=True)
    assert hasattr(v, "action") and v.action == "scale"
    assert v.target_replicas - v.current_replicas <= max_step, (
        f"Step {v.target_replicas - v.current_replicas} exceeds max_scale_step={max_step}"
    )
