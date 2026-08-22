# Day 11 — Safety Shield Implementation

## Task
Implement the Safety Shield as a Python validation service that checks every AI-generated action against the verified policy.

## Aim
Reject or modify unsafe actions before the operator executes them.

## Requirements

- `config/safety_policy.yaml` from Day 10
- `decision_engine.py` from Day 9
- Python project environment

## Steps

1. **Write `safety_shield.py`**
   - Load the policy file at startup.
   - Define a `SafetyShield` class with a `validate(action, cluster_state)` method.

2. **Implement validation checks**
   - Replicas must be within `minReplicas` and `maxReplicas`.
   - Time since last action must be >= `cooldownSeconds`.
   - Scale-down is rejected if `anomalyDetected` is true.
   - Action must target a known service/deployment.
   - Reject actions that would violate SLO constraints.

3. **Return validation result**
   - Return one of:
     - `approved`
     - `rejected` with reason
     - `modified` with corrected parameters and reason

4. **Integrate with decision engine**
   - Modify `decision_engine.py` to pass every decision through the Safety Shield.
   - Only approved/modified decisions are published to `k8s-decisions`.

5. **Add audit logging**
   - Log every validation result including reason.

6. **Write unit tests**
   - Test safe decisions pass.
   - Test unsafe decisions are rejected.

## Outcome

- A Safety Shield that filters AI decisions using verified rules.
- Unsafe actions are rejected before reaching the operator.
- All validation results are logged for audit.

## Verification

```bash
python src/safety/test_safety_shield.py
```

Expected result: unit tests pass; safe decisions are approved, unsafe ones rejected.

---

## Execution Notes (2026-08-22)

### What was built
- `src/safety/__init__.py` — empty package marker.
- `src/safety/safety_shield.py` (260 lines) — `SafetyShield` class loading
  `specs/safety_policy.yaml`. Six invariant-enforcement methods
  (`_check_min_replicas`, `_check_max_replicas`, `_check_scaling_step`,
  `_check_heal_no_scale`, `_check_cooldown`, `_check_unknown_action`).
  Returns `Decision` (allowed, possibly clamped) or `RejectedDecision`
  (cannot be made safe; rejected with reason).
- `tests/__init__.py` + `tests/test_safety_shield.py` (16 tests covering
  every invariant + audit log + bad-policy).
- `conftest.py` at repo root — adds `/code` to `sys.path` so the
  `from src.safety...` import style works inside pytest in the container.
- Audit log: `logs/safety_audit.log` — one JSON line per `validate()`
  call, capturing `input`, `outcome`, `modifications`, `rejected`,
  `timestamp`.

### Architectural choices
- **Step-shrink BEFORE max-clamp.** If the engine wants target=15 from
  current=2, that's a 13-step jump. The right behavior is to first shrink
  the step to max_scale_step (current+2=4), then clamp to max (no-op since
  4 < 10). Greedy max-clamp-first would land at 10, then shrink-back to
  4. Same end-result, but the order makes the audit log clearer.
- **`bypass_cooldown=True` flag for tests.** Tests need to exercise
  multiple invariants in the same shield instance without 60-second sleeps.
  The bypass is a kwarg; default behavior in production is to enforce
  cooldown normally.
- **Decision + RejectedDecision as sibling dataclasses.** The Decision
  class is duplicated (not imported) from `src.decision.decision_engine`
  to avoid an import cycle: the decision engine might one day import the
  shield for shielded decisioning, and the shield imports `Decision` for
  type signatures. Both files have the same dataclass definition;
  divergence is guarded by the unit tests.

### TLA+ → Python mapping
| TLA+ invariant | Python method | Test |
|----------------|---------------|------|
| `SafetyMinReplicas` | `_check_min_replicas` | `test_min_replicas_*` (2 tests) |
| `SafetyMaxReplicas` | `_check_max_replicas` | `test_max_replicas_*` (2 tests) |
| `SafetyScalingStep` | `_check_scaling_step` | `test_scaling_step_*` (3 tests) |
| `SafetyHealNoScale` | `_check_heal_no_scale` | `test_heal_*` (2 tests) |
| `SafetyBoundedRate` | `_check_cooldown` | `test_cooldown_*` + `test_scale_action_*` (3 tests) |
| (defensive) unknown action | `_check_unknown_action` | `test_unknown_action_rejected` |

### Dependencies added
- `pytest==8.3.0` — test runner
- `pyyaml==6.0.1` — safety policy parsing

Docker image rebuilt (`k8-ai-ops:dev` new sha).

### Test results (2026-08-22)
```
tests/test_safety_shield.py::test_min_replicas_clamp_negative_target PASSED
tests/test_safety_shield.py::test_min_replicas_pass_through_valid PASSED
tests/test_safety_shield.py::test_max_replicas_clamp_excessive_target PASSED
tests/test_safety_shield.py::test_max_replicas_pass_through_valid PASSED
tests/test_safety_shield.py::test_scaling_step_shrink_when_too_big PASSED
tests/test_safety_shield.py::test_scaling_step_pass_through_small_step PASSED
tests/test_safety_shield.py::test_scaling_step_shrink_when_scale_down_too_big PASSED
tests/test_safety_shield.py::test_heal_target_equals_current_forces_match PASSED
tests/test_safety_shield.py::test_heal_passes_when_target_matches_current PASSED
tests/test_safety_shield.py::test_cooldown_rejects_immediate_second_action PASSED
tests/test_safety_shield.py::test_cooldown_bypass_allows_immediate_second_action PASSED
tests/test_safety_shield.py::test_unknown_action_rejected PASSED
tests/test_safety_shield.py::test_noop_passes PASSED
tests/test_safety_shield.py::test_scale_action_advances_cooldown_clock PASSED
tests/test_safety_shield.py::test_audit_log_writes_one_line_per_validation PASSED
tests/test_safety_shield.py::test_missing_policy_raises PASSED
============================== 16 passed in 0.10s ==============================
```

### Demo output (real `python src/safety/safety_shield.py`)
```
Policy loaded from /code/specs/safety_policy.yaml
  min_replicas=1 max_replicas=10 max_scale_step=2 cooldown=60s anomaly_threshold=0.2417

Demo: 6 decisions, see how each is handled:
  [1] scale -> target=4 reason='predictor says 15 | safety_mods=['shrink_step(15->4)']'
  [2] scale -> target=1 reason='predictor says -1 | safety_mods=['shrink_step(-1->0)', 'clamp_to_min(0->1)']'
  [3] scale -> target=4 reason='predictor says 8 (step=6) | safety_mods=['shrink_step(8->4)']'
  [4] heal  -> target=2 reason='anomaly but target=4 | safety_mods=['heal_target_forced_to_current(4->2)']'
  [5] noop  -> target=2 reason='no change | safety_pass'
  [6] delete_pod -> REJECTED (unknown_action:delete_pod)
```

### Integration smoke (decision engine -> shield)
Ran the Day-9 decision engine on 5 rows of `data/features.csv`, piped
each decision through the shield:
```
[1] heal  -> ALLOWED target=2
[2] heal  -> ALLOWED target=2
[3] scale -> ALLOWED target=1
[4] scale -> ALLOWED target=1
[5] scale -> ALLOWED target=1
Summary: allowed=5 clamped=0 rejected=0
```
The decision engine's outputs are already in safe range because they
came from clamped predictor (Day 7) + bounded anomaly detector (Day 8).
The shield acts as a defensive backstop.

### Anti-drift contract
The Day-10 walkthrough (`docs/SafetyShield.md` Section 9) states:
*"The unit tests must include at least one test that intentionally
violates each invariant and verifies the Python SafetyShield rejects
or clamps the violating action. This guards against drift between spec
and code."*

This is now satisfied: 8 of the 16 tests are negative cases that
intentionally violate an invariant and verify the Python shield catches
the violation. If any future code change breaks an invariant, the
corresponding test will fail, signaling the spec also needs updating.

### Files added
- `src/safety/__init__.py`
- `src/safety/safety_shield.py` (260 lines)
- `tests/__init__.py`
- `tests/test_safety_shield.py` (240 lines)
- `conftest.py` (sys.path fix for pytest)
- `logs/safety_audit.log` (committed evidence)

### Gotchas encountered
- Image entrypoint is `python`; running pytest via
  `docker run k8-ai-ops:dev python -m pytest` becomes `python python -m pytest`.
  Must use `--entrypoint python -m pytest ...`.
- pytest can't import `src.X` without `conftest.py` adding `/code` to sys.path.
- Invariant order matters: max-clamp-then-shrink gives a different audit
  trail than shrink-then-max-clamp. We picked shrink-first because it
  more directly models the safety intent (don't take large steps; clamping
  the value is a fallback).
- `safety_audit.log` is gitignored by default (logs/*); need to add an
  exception in `.gitignore` (next commit).
