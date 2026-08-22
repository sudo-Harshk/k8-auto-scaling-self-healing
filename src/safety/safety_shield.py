"""Day 11 Safety Shield: Python implementation of the TLA+-verified rules.

This class is the runtime enforcement of `specs/safety_policy.yaml`, which is
the canonical rule source shared with the TLA+ spec `specs/SafetyShield.tla`.
Every invariant verified by TLC in Day 10 is enforced here:

    SafetyMinReplicas     -> shield._check_min_replicas
    SafetyMaxReplicas     -> shield._check_max_replicas
    SafetyScalingStep     -> shield._check_scaling_step
    SafetyHealNoScale     -> shield._check_heal_no_scale
    SafetyBoundedRate     -> shield._check_cooldown

Each call to `validate()` either:
    - returns the input Decision (possibly with clamped `target_replicas`)
    - returns a RejectedDecision (cannot be made safe; rejected with reason)

Every validation is logged to `logs/safety_audit.log` for audit. The same
five anti-drift tests in tests/test_safety_shield.py verify each invariant
violation is caught — guard against spec/code drift.

Usage:
    from src.safety.safety_shield import SafetyShield
    shield = SafetyShield()
    safe_decision = shield.validate(engine_decision)
"""
from __future__ import annotations

import json
import logging
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_POLICY = ROOT / "specs" / "safety_policy.yaml"
DEFAULT_AUDIT_LOG = ROOT / "logs" / "safety_audit.log"

LOG = logging.getLogger("safety_shield")

ALLOWED_ACTIONS = {"scale", "heal", "noop"}


@dataclass
class RejectedDecision:
    """A decision that the safety shield refused to pass through."""

    service: str
    rejected_action: str
    current_replicas: int
    reason: str
    timestamp: str

    def to_json(self) -> str:
        return json.dumps(asdict(self), default=str)


@dataclass
class Decision:
    """Mirror of src.decision.decision_engine.Decision (duplicated here to
    avoid an import cycle: safety_shield is imported by the decision engine
    when running shielded, and by tests). The dataclass fields match exactly.
    """

    service: str
    action: str
    target_replicas: int
    current_replicas: int
    reason: str
    explanation: list[dict[str, float]] = field(default_factory=list)
    anomaly_score: float = 0.0
    predicted_replicas_raw: float = 0.0
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    features: dict[str, float] = field(default_factory=dict)

    def to_json(self) -> str:
        return json.dumps(asdict(self), default=str)


class SafetyShield:
    """Runtime enforcement of the TLA+ safety invariants.

    Loads `safety_policy.yaml` at construction; the loaded policy is the
    single source of truth for both this Python class and the TLA+ spec.
    """

    def __init__(
        self,
        policy_path: Path = DEFAULT_POLICY,
        audit_log_path: Path = DEFAULT_AUDIT_LOG,
    ) -> None:
        self.policy_path = Path(policy_path)
        self.audit_log_path = Path(audit_log_path)
        self.policy = self._load_policy()
        self._last_action_time: float = 0.0
        self.audit_log_path.parent.mkdir(parents=True, exist_ok=True)

    # --------------------------------------------------------------- policy

    def _load_policy(self) -> dict[str, Any]:
        with open(self.policy_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if "safety_shield" not in data:
            raise ValueError(f"policy missing 'safety_shield' key: {self.policy_path}")
        return data["safety_shield"]

    @property
    def min_replicas(self) -> int:
        return int(self.policy["min_replicas"])

    @property
    def max_replicas(self) -> int:
        return int(self.policy["max_replicas"])

    @property
    def max_scale_step(self) -> int:
        return int(self.policy["max_scale_step"])

    @property
    def cooldown_seconds(self) -> int:
        return int(self.policy["cooldown_seconds"])

    @property
    def anomaly_threshold(self) -> float:
        return float(self.policy["anomaly_threshold"])

    # --------------------------------------------------------------- invariants

    def _check_min_replicas(
        self, action: str, target: int, current: int
    ) -> tuple[int, list[str]]:
        mods: list[str] = []
        if action == "scale" and target < self.min_replicas:
            mods.append(f"clamp_to_min({target}->{self.min_replicas})")
            return self.min_replicas, mods
        return target, mods

    def _check_max_replicas(
        self, action: str, target: int, current: int
    ) -> tuple[int, list[str]]:
        mods: list[str] = []
        if action == "scale" and target > self.max_replicas:
            mods.append(f"clamp_to_max({target}->{self.max_replicas})")
            return self.max_replicas, mods
        return target, mods

    def _check_scaling_step(
        self, action: str, target: int, current: int
    ) -> tuple[int, list[str]]:
        """Shrink the scaling step to max_scale_step (preserving direction)."""
        mods: list[str] = []
        if action != "scale":
            return target, mods
        delta = target - current
        if abs(delta) <= self.max_scale_step:
            return target, mods
        if delta > 0:
            new_target = current + self.max_scale_step
        else:
            new_target = current - self.max_scale_step
        mods.append(f"shrink_step({target}->{new_target})")
        return new_target, mods

    def _check_heal_no_scale(
        self, action: str, target: int, current: int
    ) -> tuple[int, list[str], str | None]:
        """If heal action somehow has target != current, reject.

        Returns (target, mods, reject_reason).
        """
        mods: list[str] = []
        if action == "heal" and target != current:
            return (
                current,
                [f"heal_target_forced_to_current({target}->{current})"],
                None,
            )
        return target, mods, None

    def _check_unknown_action(self, action: str) -> str | None:
        if action not in ALLOWED_ACTIONS:
            return f"unknown_action:{action}"
        return None

    def _check_cooldown(self) -> str | None:
        """Mirror TLA+ SafetyBoundedRate: enforce cooldown between actions."""
        now = time.time()
        if now - self._last_action_time < self.cooldown_seconds:
            remaining = self.cooldown_seconds - (now - self._last_action_time)
            return f"cooldown_active:{remaining:.1f}s_remaining"
        return None

    # --------------------------------------------------------------- validate

    def validate(
        self, decision: Decision, *, bypass_cooldown: bool = False
    ) -> Decision | RejectedDecision:
        """Apply the safety policy to a decision. Returns either a (possibly
        clamped) Decision, or a RejectedDecision with the rejection reason.

        Args:
            decision: the engine's emitted decision
            bypass_cooldown: when True, skip the cooldown check (used by tests
                to exercise the other invariants without waiting).
        """
        action = decision.action
        target = int(decision.target_replicas)
        current = int(decision.current_replicas)
        mods: list[str] = []

        # Invariant: unknown action -> reject
        reject = self._check_unknown_action(action)
        if reject is not None:
            return self._reject(decision, reject)

        # Invariant: cooldown -> reject (skip when bypass_cooldown)
        if not bypass_cooldown:
            reject = self._check_cooldown()
            if reject is not None:
                return self._reject(decision, reject)

        # Invariant: heal preserves replicas (target == current)
        target, hmods, hreject = self._check_heal_no_scale(action, target, current)
        mods.extend(hmods)
        if hreject is not None:
            return self._reject(decision, hreject)

        # Invariant: scaling step bound (apply BEFORE max clamp so we don't
        # greedily cap to max then shrink back; a 13-step jump from 2 to 15
        # should shrink to 4, not first clamp to 10 then shrink to 4.)
        target, smods = self._check_scaling_step(action, target, current)
        mods.extend(smods)

        # Invariant: min replicas clamp
        target, mmods = self._check_min_replicas(action, target, current)
        mods.extend(mmods)

        # Invariant: max replicas clamp
        target, Mmods = self._check_max_replicas(action, target, current)
        mods.extend(Mmods)

        # All invariants passed (with possible clamps).
        self._last_action_time = time.time() if not bypass_cooldown else self._last_action_time
        safe = Decision(
            service=decision.service,
            action=action,
            target_replicas=target,
            current_replicas=current,
            reason=(
                decision.reason
                + (f" | safety_mods={mods}" if mods else " | safety_pass")
            ),
            explanation=decision.explanation,
            anomaly_score=decision.anomaly_score,
            predicted_replicas_raw=decision.predicted_replicas_raw,
            timestamp=datetime.now(timezone.utc).isoformat(),
            features=decision.features,
        )
        self._audit(decision, safe, mods, rejected=False)
        return safe

    def _reject(self, decision: Decision, reason: str) -> RejectedDecision:
        rejected = RejectedDecision(
            service=decision.service,
            rejected_action=decision.action,
            current_replicas=decision.current_replicas,
            reason=reason,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        self._audit(decision, rejected, mods=[], rejected=True)
        return rejected

    def _audit(
        self,
        original: Decision,
        outcome: Decision | RejectedDecision,
        mods: list[str],
        *,
        rejected: bool,
    ) -> None:
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "input": asdict(original),
            "outcome": asdict(outcome),
            "modifications": mods,
            "rejected": rejected,
        }
        with open(self.audit_log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, default=str) + "\n")


def main() -> int:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )
    shield = SafetyShield()
    print(f"Policy loaded from {DEFAULT_POLICY}")
    print(
        f"  min_replicas={shield.min_replicas} max_replicas={shield.max_replicas} "
        f"max_scale_step={shield.max_scale_step} cooldown={shield.cooldown_seconds}s "
        f"anomaly_threshold={shield.anomaly_threshold}"
    )

    demo = [
        Decision(
            service="podinfo", action="scale",
            target_replicas=15, current_replicas=2,
            reason="predictor says 15",
        ),
        Decision(
            service="podinfo", action="scale",
            target_replicas=-1, current_replicas=2,
            reason="predictor says -1",
        ),
        Decision(
            service="podinfo", action="scale",
            target_replicas=8, current_replicas=2,
            reason="predictor says 8 (step=6)",
        ),
        Decision(
            service="podinfo", action="heal",
            target_replicas=4, current_replicas=2,
            reason="anomaly but target=4",
        ),
        Decision(
            service="podinfo", action="noop",
            target_replicas=2, current_replicas=2,
            reason="no change",
        ),
        Decision(
            service="podinfo", action="delete_pod",
            target_replicas=2, current_replicas=2,
            reason="rogue action",
        ),
    ]
    print("\nDemo: 6 decisions, see how each is handled:")
    for i, dec in enumerate(demo, 1):
        result = shield.validate(dec, bypass_cooldown=True)
        if isinstance(result, RejectedDecision):
            print(f"  [{i}] {dec.action:5s} -> REJECTED ({result.reason})")
        else:
            print(
                f"  [{i}] {dec.action:5s} -> target={result.target_replicas} "
                f"reason='{result.reason}'"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())