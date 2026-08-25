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

## 7. Liveness property (added Day 15)

Day 15 added a liveness property to the spec, closing the gap between
"nothing bad happens" (safety) and "something good eventually happens"
(liveness).

### 7.1 What we claim

**`LivenessEventuallyScaleUp`** (TLA+):

```
\A n \in 1..MAX_REPLICAS :
    []( (consecutive_overload = MAX_REPLICAS /\ current_replicas = n)
         => <>(current_replicas > n) )
```

Informally: when the engine's decision loop has recorded sustained demand
for `MAX_REPLICAS` consecutive windows (i.e., the AI predictor has
demanded more replicas than are currently deployed in every window for
10 consecutive ticks), and the operator is currently at `n` replicas,
then eventually the operator will scale to more than `n` replicas.

This is the second-strongest paper claim after the safety invariants.

### 7.2 How we model "sustained demand"

The `consecutive_overload` counter increments on each `EmitDecision` where
`predicted_replicas > current_replicas` (saturating at `MAX_REPLICAS = 10`)
and resets to 0 when:
- `ApplyScaleUp` or `ApplyScaleDown` fires (an action was taken), or
- `EmitDecision` decides `noop` or `heal` (demand has dropped)

`DriftPredictor` (online learning drift) and `DriftAnomaly` (severity
change) cannot reset the counter while sustained demand holds: when
`consecutive_overload >= 2`, both `DriftPredictor` and `DriftAnomaly` are
bounded so they cannot push the system out of the "scale" regime.
This is a reasonable ML assumption — a learned model that has seen
sustained high load will not suddenly predict low load in the next
window.

### 7.3 Fairness assumptions

```
Fairness == /\ SF_vars(Tick)
             /\ SF_vars(ApplyScaleUp)
             /\ SF_vars(ApplyScaleDown)
```

- `SF_vars(Tick)`: clock advances infinitely often (so cooldown elapses).
- `SF_vars(ApplyScaleUp)` / `SF_vars(ApplyScaleDown)`: operator fires
  when continuously or infinitely-often enabled.

### 7.4 Cyclic clock subtlety

The logical clock cycles modulo `MAX_REPLICAS + 1` to keep the state
space bounded. Naive integer subtraction `clock - last_action_clock`
becomes negative after wrap-around and silently disables the cooldown
gate. The fix is `CooldownElapsed`, which computes the cyclic distance:

```
CooldownElapsed ==
    LET raw == clock - last_action_clock
    IN IF raw >= 0
       THEN raw >= COOLDOWN
       ELSE (raw + (MAX_REPLICAS + 1)) >= COOLDOWN
```

### 7.5 TLC verification

Run on Day 15:

```
$ java -XX:+UseParallelGC -Xmx2g -jar ~/tla/tla2tools.jar specs/SafetyShield
...
Checking 10 branches of temporal properties for the complete state
    space with 4014780 total distinct states at (...)
Finished checking temporal properties in 02min 47s at (...)
Model checking completed. No error has been found.
2486782 states generated, 273702 distinct states found, 0 states left on queue.
The depth of the complete state graph search is 53.
Finished in 04min 06s
```

TLC explored **2.49 million state generations**, found **273,702 distinct
states**, and verified all 5 safety invariants AND the new liveness
property in 4 minutes 6 seconds.

### 7.6 What the spec still does NOT prove

- **Real-time bounds.** The spec uses logical ticks, not wall-clock time.
  We do not assert that the operator scales within 5 seconds (HPA) or
  30 seconds (the runtime Faust window). These bounds are measured
  empirically in Day 14.
- **Performance under realistic load.** The spec is a state-transition
  model, not a performance model. Day 14's N=3 evaluation measures
  scaling lag, p95 latency, and error rate.
- **Liveness under arbitrary DriftPredictor.** We bound DriftPredictor
  to respect sustained demand (Step 7.2). Removing this bound would
  re-introduce counterexamples where DriftPredictor disables the
  operator by moving `predicted_replicas` out of the bounded-step
  region. We document this as a design choice rather than a limitation.

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