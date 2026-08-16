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
