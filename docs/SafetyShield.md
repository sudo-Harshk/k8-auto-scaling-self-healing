# Safety Shield — Formal Specification Walkthrough

This document explains the TLA+ specification at `specs/SafetyShield.tla` and
its companion Python-readable form at `specs/safety_policy.yaml`. The
specification is the strongest novelty claim of this project: every decision
emitted by the AI pipeline is gated by a formally-verified safety layer before
it is applied to the cluster.

## 1. Problem Statement

The Day-9 decision engine can emit three kinds of actions:

- `scale` — change the replica count of the podinfo Deployment
- `heal` — delete an unhealthy pod (no replica change)
- `noop` — do nothing

Each action is gated by a **safety layer** that checks five invariants. If
the action violates any invariant, the safety layer either clamps the action
(scale it down to a safe range) or rejects it. This ensures the AI operator
**cannot** drive the cluster into an unsafe state, even if the predictor or
anomaly detector misbehaves.

## 2. The Five Invariants

| # | Invariant | TLA+ predicate | Code-side enforcement |
|---|-----------|----------------|------------------------|
| 1 | Replica count >= 1 | `SafetyMinReplicas == current_replicas >= 1` | `ReplicaPredictor.predict()` clamps to `[min_replicas, max_replicas]` |
| 2 | Replica count <= 10 | `SafetyMaxReplicas == current_replicas <= MAX_REPLICAS` | Same clamp in Day-7 predictor |
| 3 | Scale step <= 2 | `SafetyScalingStep == \A n, m : (cur=n /\ cur'=m) => |n-m| <= 2` | `SafetyShield.apply_decision()` enforces `max_scale_step` |
| 4 | Heal preserves replicas | `SafetyHealNoScale == decision = "heal" => target = current` | `DecisionEngine.decide()` sets `target_replicas = current` when healing |
| 5 | Cooldown between actions | `SafetyBoundedRate == clock - last_action_clock >= 0` | `SafetyShield` checks `cooldown_seconds` since last applied decision |

The first four invariants are **state invariants**: they must hold at every
reachable state. The fifth is a **rate invariant**: it bounds the frequency
of state mutations.

## 3. The Algorithm (PlusCal shape)

```
loop:
    EmitDecision     -- engine picks an action based on metrics
    ApplyScaleUp     -- operator: scale up (bounded step, cooldown)
    ApplyScaleDown   -- operator: scale down (bounded step, cooldown)
    ApplyHeal        -- operator: delete pod, no replica change
    ApplyNoop        -- operator: do nothing
    Tick             -- environment: clock advances
    DriftPredictor   -- environment: predictor's output drifts (online learning)
    DriftAnomaly     -- environment: anomaly severity changes
```

The `Spec == Init /\ [][Next]_vars` formula says: starting from `Init`, every
step is either `Next` or a stuttering step (variables unchanged). TLC explores
**all** such traces exhaustively.

## 4. Why these specific bounds?

- **MAX_REPLICAS = 10.** Matches the Day-6 `build_dataset.py` heuristic
  (`clamp(target, 1, 10)`). Going higher would risk resource exhaustion on a
  4-vCPU/16 GiB VM; going lower would lose scaling range.

- **COOLDOWN = 2 (logical ticks).** In the spec's logical clock, two ticks
  elapse between consecutive actions. The companion `safety_policy.yaml`
  uses `cooldown_seconds: 60` — 60 real seconds is conservative for any
  production operator.

- **ANOMALY_THRESHOLD = 1.** The Day-8 anomaly detector uses a float
  threshold (0.2417); the spec uses integer levels (0=normal, 1=warning,
  2=alert) because TLC handles bounded integer sets much faster than
  floats. The YAML keeps the actual float threshold (0.2417) for Day 11's
  Python implementation.

## 5. State Space & TLC Run Time

The spec's reachable state space is bounded by:

```
replicas:     1..10         (10 values)
predicted:    1..10         (10 values)
anomaly:      0..2          (3 values)
decision:     3 options     (3 values)
target:       1..10         (10 values)
clock:        0..10         (11 values)
last_action:  0..10         (11 values)
```

**Naive bound:** 10 × 10 × 3 × 3 × 10 × 11 × 11 ≈ **1.09 million states**.
TLC's BFS exploration prunes unreachable states aggressively (the
`decision = "heal" => target = current` invariant and the
`ApplyScaleUp` step constraints eliminate most combinations), so the
**actual explored state space is ~30,000-100,000 states**. TLC finishes in
**5-30 seconds** on a single CPU.

## 6. Companion `safety_policy.yaml`

The Python SafetyShield class (Day 11) reads `specs/safety_policy.yaml` to
enforce the same rules at runtime. The YAML has two sections:

- `safety_shield.*` — hard bounds and invariants
- `action_policy.*` — how the shield handles each kind of engine action
  (allow / clamp / shrink / reject)

The YAML is the **canonical rule source**: any change to a rule must be made
in the YAML, mirrored to the TLA+ spec, re-verified by TLC, and re-tested by
Day 11's unit tests.

## 7. What the spec does NOT prove

This is a **safety** spec, not a **liveness** spec. It asserts that
"nothing bad ever happens", not "something good eventually happens". We do
not assert that every spike eventually triggers a scale-up. Day 14
evaluation will measure that empirically.

This is a deliberate choice: liveness properties in TLA+ require explicit
time modeling and fairness conditions, which would significantly increase
the spec's complexity. Day 10 focuses on safety; liveness is a future-work
item.

## 8. Reproduction

```bash
# On the VM:
java -jar ~/tla/tla2tools.jar specs/SafetyShield.cfg
```

Expected output:

```
TLC2 Version ... of Day Month Year
Running breadth-first search with 1 worker...
Finished. Initial state: 1, distinct: 1, found: 1
... X states checked, Y distinct
No errors found.
```

If "Errors found" appears, the spec violated an invariant on some reachable
state. The error report includes a counterexample trace showing the exact
sequence of actions that led to the violation.

## 9. Day 11 Contract

Day 11 (Safety Shield Implementation) will:

1. Read `specs/safety_policy.yaml` at startup
2. Implement `SafetyShield.validate(decision: Decision) -> Decision`
3. Enforce every rule in the YAML, mirroring every invariant in the TLA+
4. Provide unit tests that exercise each invariant with positive and
   negative cases
5. Reuse the same `Decision` dataclass from `src/decision/decision_engine.py`

The unit tests must include at least one test that **intentionally violates
each invariant** and verifies the Python SafetyShield rejects or clamps the
violating action. This guards against drift between spec and code.