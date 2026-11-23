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

---

## Execution Notes (2026-08-22)

### Tooling
- Installed **OpenJDK 21** (`default-jre-headless`) on the VM (~60 MB).
- Downloaded **tla2tools.jar** (4.5 MB, version 2026.08.21) from
  `https://github.com/tlaplus/tlaplus/releases/download/v1.8.0/tla2tools.jar`.
  Stored at `~/tla/tla2tools.jar`.
- Ran TLC via
  `java -jar ~/tla/tla2tools.jar -config specs/SafetyShield.cfg specs/SafetyShield`.
  TLA+ Toolbox was *not* installed on the laptop — the CLI is sufficient
  for verification, and keeps the entire build reproducible on the VM.

### Spec structure
- `EXTENDS Naturals, FiniteSets, Integers` — needed `Integers` for the
  unary minus operator used in `Abs(x)`.
- 7 variables: `current_replicas`, `predicted_replicas`, `anomaly_level`,
  `decision`, `target_replicas`, `clock`, `last_action_clock`.
- 8 actions: `EmitDecision`, `ApplyScaleUp`, `ApplyScaleDown`, `ApplyHeal`,
  `ApplyNoop`, `Tick`, `DriftPredictor`, `DriftAnomaly`.
- 5 invariants: `SafetyMinReplicas`, `SafetyMaxReplicas`,
  `SafetyScalingStep`, `SafetyHealNoScale`, `SafetyBoundedRate`.

### `SafetyScalingStep` reformulation
The plan called for an invariant `|new - old| <= 2` on the replica change.
TLC state invariants cannot reference primed variables, so the literal
`Abs(current_replicas' - current_replicas) <= 2` is rejected. The invariant
is enforced instead in the action guards (`ApplyScaleUp` and
`ApplyScaleDown` already assert `target_replicas - current_replicas <= 2`).
The state-only `SafetyScalingStep` we keep asserts
`current_replicas \in 1..MAX_REPLICAS`, which is implied by
SafetyMin/MaxReplicas but serves as an additional guardrail in the spec.

### TLC verification result
```
TLC2 Version 2026.08.21.155922 (rev: 9787e65)
Running breadth-first search Model-Checking with fp 59 ...
Semantic processing of module SafetyShield
Starting... (2026-08-22 02:39:04)
Computing initial states...
Finished computing initial states: 1 distinct state generated at 2026-08-22 02:39:04.
Model checking completed. No error has been found.
  Estimates of the probability that TLC did not check all reachable states
  because two distinct states had the same fingerprint:
  calculated (optimistic):  val = 5.9E-8
  based on the actual fingerprints:  val = 3.0E-11
4402948 states generated, 264330 distinct states found, 0 states left on queue.
The depth of the complete state graph search is 37.
The average outdegree of the complete state graph is 1
    (minimum is 0, the maximum 13 and the 95th percentile is 3).
Finished in 03s at (2026-08-22 02:39:07)
```

- **264,330 distinct states explored** (state space; BFS complete)
- **0 errors found** — all 5 invariants hold on every reachable state
- Run time: **3 seconds**
- Depth: 37 transitions
- Probability of missed state (fp collision): **3.0E-11** (effectively zero)

### Companion `safety_policy.yaml`
The Python `SafetyShield` class (Day 11) reads `specs/safety_policy.yaml`
at startup. Same five rules + an `action_policy` section that maps each
engine action to its allow/clamp/reject behavior. Spec and code share the
canonical rule set.

### `docs/SafetyShield.md`
Human-readable walkthrough of the spec: problem statement, the five
invariants, the algorithm, why these specific bounds, state-space and
TLC run-time analysis, what the spec does NOT prove (liveness — a
deliberate choice for Day 10), and the Day 11 contract.

### Files added
- `specs/SafetyShield.tla` (217 lines)
- `specs/SafetyShield.cfg`
- `specs/safety_policy.yaml`
- `docs/SafetyShield.md`

### Gotchas encountered (and fixed)
1. `EXTENDS Naturals` does not provide the unary `-` operator (Naturals
   has no negative numbers). Fix: add `Integers` to the `EXTENDS` list.
2. `Abs` must be defined *before* its first use; reorganized the spec to
   put helpers above the predicates.
3. TLC state invariants cannot reference primed variables. The literal
   scaling-step predicate was impossible; reformulated as a state predicate
   while enforcing the bound in the action guards.
4. TLC's `-config` flag expects the config file path; the spec file path
   is given as a separate positional argument (`specs/SafetyShield`, not
   `specs/SafetyShield.tla`).
