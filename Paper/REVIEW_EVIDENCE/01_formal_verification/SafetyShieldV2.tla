---------------------------- MODULE SafetyShieldV2 ----------------------------
(*
 * SHIELD-AI Safety Shield, revised specification (v2, paper revision).
 * Runtime counterpart: src/safety/safety_shield.py + specs/safety_policy_v2.yaml.
 *
 * Changes w.r.t. SafetyShield.tla (v1), addressing review comments:
 *   1. UNTRUSTED ML: the predictor may propose any value in 0..ML_MAX_OUTPUT
 *      (including 0 and values above the maximum). In v1 the predictor was
 *      already constrained to |delta| <= 2, which made the shield trivially safe.
 *   2. The shield function is modelled explicitly, in the same order as the
 *      Python code: StepLimit first, then Clamp to [MIN, MAX].
 *   3. No cyclic clock. Time is a saturating counter `since_last` in
 *      0..COOLDOWN_DOWN; one tick = one decision window (15 s). Hence
 *      COOLDOWN_UP = 1 tick = 15 s and COOLDOWN_DOWN = 4 ticks = 60 s.
 *   4. Asymmetric policy (as in Kubernetes HPA): scale-up step
 *      max(STEP_UP_ABS, current*STEP_UP_PCT/100), scale-down step STEP_DOWN.
 *   5. SafetyScalingStep and SafetyBoundedRate are NON-TRIVIAL: they are stated
 *      over history variables and ALSO as temporal action properties.
 *   Mutation testing (specs/tlc_run_v2_mutants.txt) shows that disabling each
 *   shield rule makes TLC report a violation of the matching invariant.
 *)
EXTENDS Naturals, Integers

CONSTANTS
    MIN_REPLICAS, MAX_REPLICAS,
    STEP_UP_ABS, STEP_UP_PCT, STEP_DOWN,
    COOLDOWN_UP, COOLDOWN_DOWN,
    ANOMALY_THRESHOLD,
    ML_MAX_OUTPUT,      \* largest value the untrusted ML may emit
    OVERLOAD_CAP        \* saturation of the sustained-demand counter

VARIABLES
    current_replicas, predicted_replicas, anomaly_level, decision,
    target_replicas, since_last, consecutive_overload,
    prev_replicas,   \* history: replicas before the last applied action
    gap_at_apply,    \* history: since_last when the last action was applied
    last_applied     \* history: "none" | "up" | "down" | "heal"

vars == <<current_replicas, predicted_replicas, anomaly_level, decision,
          target_replicas, since_last, consecutive_overload,
          prev_replicas, gap_at_apply, last_applied>>

Abs(x) == IF x < 0 THEN -x ELSE x
Min(a, b) == IF a < b THEN a ELSE b
Max(a, b) == IF a > b THEN a ELSE b

\* ---------------- Shield function (mirrors safety_shield.py) ----------------
UpLimit(c) == Max(STEP_UP_ABS, (c * STEP_UP_PCT) \div 100)

StepLimit(t, c) == IF t - c > UpLimit(c) THEN c + UpLimit(c)
                   ELSE IF c - t > STEP_DOWN THEN c - STEP_DOWN ELSE t

Clamp(x) == IF x < MIN_REPLICAS THEN MIN_REPLICAS
            ELSE IF x > MAX_REPLICAS THEN MAX_REPLICAS ELSE x

Shield(p, c) == Clamp(StepLimit(p, c))

TypeOK ==
    /\ current_replicas \in MIN_REPLICAS..MAX_REPLICAS
    /\ predicted_replicas \in 0..ML_MAX_OUTPUT
    /\ anomaly_level \in {0, 1, 2}
    /\ decision \in {"scale", "heal", "noop"}
    /\ target_replicas \in MIN_REPLICAS..MAX_REPLICAS
    /\ since_last \in 0..COOLDOWN_DOWN
    /\ consecutive_overload \in 0..OVERLOAD_CAP
    /\ prev_replicas \in MIN_REPLICAS..MAX_REPLICAS
    /\ gap_at_apply \in 0..COOLDOWN_DOWN
    /\ last_applied \in {"none", "up", "down", "heal"}

Init ==
    /\ current_replicas = MIN_REPLICAS
    /\ predicted_replicas = MIN_REPLICAS
    /\ anomaly_level = 0
    /\ decision = "noop"
    /\ target_replicas = MIN_REPLICAS
    /\ since_last = COOLDOWN_DOWN
    /\ consecutive_overload = 0
    /\ prev_replicas = MIN_REPLICAS
    /\ gap_at_apply = COOLDOWN_DOWN
    /\ last_applied = "none"

\* ---------------- Decision engine + shield ----------------
EmitDecision ==
    LET safe == Shield(predicted_replicas, current_replicas) IN
    /\ IF safe # current_replicas
         THEN /\ decision' = "scale"
              /\ target_replicas' = safe
         ELSE IF anomaly_level >= ANOMALY_THRESHOLD
              THEN /\ decision' = "heal"
                   /\ target_replicas' = current_replicas
              ELSE /\ decision' = "noop"
                   /\ target_replicas' = current_replicas
    /\ consecutive_overload' =
         IF safe > current_replicas
         THEN Min(consecutive_overload + 1, OVERLOAD_CAP) ELSE 0
    /\ UNCHANGED <<current_replicas, predicted_replicas, anomaly_level,
                   since_last, prev_replicas, gap_at_apply, last_applied>>

\* ---------------- Actuator (direction-aware cooldown) ----------------
ApplyScaleUp ==
    /\ decision = "scale"
    /\ target_replicas > current_replicas
    /\ since_last >= COOLDOWN_UP
    /\ current_replicas' = target_replicas
    /\ prev_replicas' = current_replicas
    /\ gap_at_apply' = since_last
    /\ since_last' = 0
    /\ last_applied' = "up"
    /\ decision' = "noop"
    /\ consecutive_overload' = 0
    /\ UNCHANGED <<predicted_replicas, anomaly_level, target_replicas>>

ApplyScaleDown ==
    /\ decision = "scale"
    /\ target_replicas < current_replicas
    /\ since_last >= COOLDOWN_DOWN
    /\ current_replicas' = target_replicas
    /\ prev_replicas' = current_replicas
    /\ gap_at_apply' = since_last
    /\ since_last' = 0
    /\ last_applied' = "down"
    /\ decision' = "noop"
    /\ consecutive_overload' = 0
    /\ UNCHANGED <<predicted_replicas, anomaly_level, target_replicas>>

ApplyHeal ==
    /\ decision = "heal"
    /\ since_last >= COOLDOWN_DOWN
    /\ prev_replicas' = current_replicas
    /\ gap_at_apply' = since_last
    /\ since_last' = 0
    /\ last_applied' = "heal"
    /\ decision' = "noop"
    /\ UNCHANGED <<current_replicas, predicted_replicas, anomaly_level,
                   target_replicas, consecutive_overload>>

\* ---------------- Environment ----------------
Tick ==
    /\ since_last' = Min(since_last + 1, COOLDOWN_DOWN)
    /\ UNCHANGED <<current_replicas, predicted_replicas, anomaly_level, decision,
                   target_replicas, consecutive_overload, prev_replicas,
                   gap_at_apply, last_applied>>

\* Untrusted ML: any output in 0..ML_MAX_OUTPUT. Only restriction = liveness
\* premise: once demand is sustained (overload >= 2), the ML keeps asking for
\* more replicas than are running.
DriftPredictor ==
    /\ predicted_replicas' \in 0..ML_MAX_OUTPUT
    /\ \/ consecutive_overload < 2
       \/ predicted_replicas' > current_replicas
    /\ UNCHANGED <<current_replicas, anomaly_level, decision, target_replicas,
                   since_last, consecutive_overload, prev_replicas,
                   gap_at_apply, last_applied>>

DriftAnomaly ==
    /\ anomaly_level' \in {0, 1, 2}
    /\ UNCHANGED <<current_replicas, predicted_replicas, decision,
                   target_replicas, since_last, consecutive_overload,
                   prev_replicas, gap_at_apply, last_applied>>

Next == \/ EmitDecision \/ ApplyScaleUp \/ ApplyScaleDown \/ ApplyHeal
        \/ Tick \/ DriftPredictor \/ DriftAnomaly

Spec == Init /\ [][Next]_vars
Fairness == /\ SF_vars(Tick) /\ SF_vars(ApplyScaleUp) /\ WF_vars(EmitDecision)
LivenessSpec == Spec /\ Fairness

\* ======================= SAFETY INVARIANTS (state) =======================
SafetyMinReplicas == current_replicas >= MIN_REPLICAS
SafetyMaxReplicas == current_replicas <= MAX_REPLICAS
SafetyScalingStep == /\ current_replicas - prev_replicas <= UpLimit(prev_replicas)
                     /\ prev_replicas - current_replicas <= STEP_DOWN
SafetyHealNoScale == /\ (decision = "heal" => target_replicas = current_replicas)
                     /\ (last_applied = "heal" => current_replicas = prev_replicas)
SafetyBoundedRate == /\ (last_applied = "up"   => gap_at_apply >= COOLDOWN_UP)
                     /\ (last_applied \in {"down", "heal"} => gap_at_apply >= COOLDOWN_DOWN)

\* ======================= SAFETY (action properties) =======================
StepAction == [][ /\ current_replicas' - current_replicas <= UpLimit(current_replicas)
                  /\ current_replicas - current_replicas' <= STEP_DOWN ]_vars
\* Checked on every transition, independently of the history variables.
\* (Heal does not change replicas; its rate bound is SafetyBoundedRate.)
RateAction == [][ /\ (current_replicas' > current_replicas => since_last >= COOLDOWN_UP)
                  /\ (current_replicas' < current_replicas => since_last >= COOLDOWN_DOWN) ]_vars

\* ======================= LIVENESS =======================
LivenessEventuallyScaleUp ==
    \A n \in MIN_REPLICAS..(MAX_REPLICAS - 1) :
        []( (consecutive_overload >= 2 /\ current_replicas = n)
            => <>(current_replicas > n) )
=============================================================================
