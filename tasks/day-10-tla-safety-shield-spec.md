# Day 10 — TLA+ Safety Shield Specification

## Task
Model the safety rules of the operator in TLA+/PlusCal and verify them with the TLC model checker.

## Aim
Formally prove that the operator will never take unsafe scaling or healing actions.

## Requirements

- TLA+ Toolbox installed locally
- Basic understanding of the actions your operator will perform

## Steps

1. **Define the system state variables**
   - `currentReplicas`
   - `proposedReplicas`
   - `lastActionTime`
   - `sloHealthy`
   - `anomalyDetected`
   - `currentTime`

2. **Write the PlusCal algorithm**
   - Model the operator as a process that receives proposed actions.
   - Include actions: `ScaleUp`, `ScaleDown`, `Heal`, `NoOp`.

3. **Define safety invariants**
   - Minimum and maximum replica limits.
   - Cooldown: no action within `cooldownPeriod` of the last action.
   - No scale-down while `anomalyDetected` is true.
   - No scale-up beyond `maxReplicas`.
   - Healing only when `sloHealthy` is false or anomaly is detected.

4. **Run TLC model checker**
   - Translate PlusCal to TLA+.
   - Run TLC and confirm no invariant violations.

5. **Export rules to a policy file**
   - Create `config/safety_policy.yaml` or `config/safety_policy.json` from the verified invariants.
   - Include values like `minReplicas`, `maxReplicas`, `cooldownSeconds`.

## Outcome

- A TLA+ specification file (`specs/SafetyShield.tla`).
- TLC reports no invariant violations.
- A machine-readable safety policy file (`config/safety_policy.yaml`).

## Verification

Open `specs/SafetyShield.tla` in TLA+ Toolbox, run TLC, and confirm:

```
Model checking completed. No error has been found.
```
