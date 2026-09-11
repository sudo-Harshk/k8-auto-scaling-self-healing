export const metrics = {
  // From evidence-freeze.md (single source of truth for paper claims)
  implementationDays: 18,
  tlaDistinctStates: 273702,
  tlaGeneratedStates: 2486782,
  compositionDistinctStates: 53,
  mlOnlyDistinctStates: 93,
  tlaTimeSeconds: 107, // 01m47s
  shieldClamp12of28: 12,
  shieldStressTotal: 28,
  shieldClampRatio: 42.9, // percent
  offlineReplayRows: 285,
  p95RangeFactor: 48, // 290ms to 14,000ms
  unitTestsTotal: 53,
  n10Trials: 10,
  n10OpCells: 4 * 3 * 10, // 4 operators * 3 scenarios * 10 trials = 120
  paperPages: 5,
  paperReferences: 20,
  n3RowsMlBroken: 9,
  n3ErrorRate: 100.0,
  anomalyThreshold: 0.484,
  anomalyThresholdExact: 0.4837573385518591,
  replicaMaeV2: 0.007,
  v2ReplicaRangeMin: 290,
  v2ReplicaRangeMax: 14000,
  v2AnomalyPct: 1.2,
  githubUrl: 'https://github.com/sudo-Harshk/k8-auto-scaling-self-healing',
}

export const headlineStats = [
  {
    value: '273,702',
    label: 'TLC-verified reachable states in the safety shield',
    accent: 'primary' as const,
  },
  {
    value: '53',
    label: 'Reachable states when ML is composed with the shield (vs 93 without it)',
    accent: 'accent' as const,
  },
  {
    value: '42.9%',
    label: 'Of 28 malicious ML proposals clamped by the shield (12 of 28)',
    accent: 'primary' as const,
  },
  {
    value: '53/53',
    label: 'Unit tests passing; 5 invariants + 1 liveness verified offline',
    accent: 'accent' as const,
  },
]

export const tlaSnippet = `---- MODULE SafetyShield ----
EXTENDS Naturals, Integers, Sequences, TLC

CONSTANTS
  MinReplicas,          \\* = 1
  MaxReplicas,          \\* = 10
  MaxScaleStep,         \\* = 2
  CooldownTicks         \\* = 6 (60s @ 10s tick)

VARIABLES replicas, pendingTarget, lastActionClock, clock

vars == <<replicas, pendingTarget, lastActionClock, clock>>

SafetyInvariant ==
  /\\\\ replicas >= MinReplicas
  /\\\\ replicas <= MaxReplicas

BoundedStep == \\A delta \\in {-MaxScaleStep, MaxScaleStep} :
  replicas + delta \\in MinReplicas..MaxReplicas

CooldownElapsed == (clock - lastActionClock) % 11 >= CooldownTicks
\\\\* the modulo fixes cyclic-clock wrap-around (silent disable bug)
====`

export const mlOnlyCounterexampleSnippet = `State 4 (depth 4 from init)
  replicas    = 11      \\* violates MlSafetyMaxReplicas = 10
  pending     = NULL
  clock       = 4
  lastAction  = 0       \\* cooldow 0'd out (modulo 5)

Trace: init -> scale_up -> scale_up -> scale_up -> scale_up
       \\-> replicas goes 6 -> 7 -> 8 -> 9 -> 10 -> 11 (out of bounds)

Without the safety shield, the ML controller scales
beyond the cluster's hard ceiling. Same ML +
SHIELD path: 53 states, 0 violations.`

export const auditSnippet = `$ python scripts/_phase5_audit.py

  Reading docs/paper/main.tex     ............ 84 numeric literals
  Reading evidence-freeze.md      ............ (canonical)

  SOURCED   : 56   (every cited number traces to EF)
  UNSOURCED : 0    (zero fabricated paper claims)

  Audit PASSED (exit code 0).`
