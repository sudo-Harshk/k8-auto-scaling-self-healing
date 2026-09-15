export const metrics = {
  githubUrl: 'https://github.com/sudo-Harshk/k8-auto-scaling-self-healing',
  tlaDistinctStates: 273702,
  unitTestsTotal: 53,
  evaluationTrials: 10,
  implementationDays: 18,
}

export const headlineStats = [
  {
    value: '273,702',
    label: 'MODEL-CHECKED STATES',
  },
  {
    value: '53 / 53',
    label: 'TESTS PASSING',
  },
  {
    value: '0',
    label: 'SAFETY VIOLATIONS',
  },
  {
    value: '10',
    label: 'EVALUATION TRIALS',
  },
]

export const tlaSnippet = `---- MODULE SafetyShield ----
EXTENDS Naturals, Integers, Sequences, TLC

CONSTANTS
  MinReplicas,          \* = 1
  MaxReplicas,          \* = 10
  MaxScaleStep,         \* = 2
  CooldownTicks         \* = 6 (60s @ 10s tick)

VARIABLES replicas, pendingTarget, lastActionClock, clock

vars == <<replicas, pendingTarget, lastActionClock, clock>>

SafetyInvariant ==
  /\\ replicas >= MinReplicas
  /\\ replicas <= MaxReplicas

BoundedStep == \\A delta \\in {-MaxScaleStep, MaxScaleStep} :
  replicas + delta \\in MinReplicas..MaxReplicas

CooldownElapsed == (clock - lastActionClock) % 11 >= CooldownTicks
\*\* the modulo fixes cyclic-clock wrap-around (silent disable bug)
====`

export const mlOnlyCounterexampleSnippet = `State 4 (depth 4 from init)
  replicas    = 11      \* violates MlSafetyMaxReplicas = 10
  pending     = NULL
  clock       = 4
  lastAction  = 0       \* cooldown 0'd out (modulo 5)

Trace: init -> scale_up -> scale_up -> scale_up -> scale_up
       \\-> replicas goes 6 -> 7 -> 8 -> 9 -> 10 -> 11 (out of bounds)

Without the safety shield, the ML controller scales
beyond the cluster's hard ceiling. Same ML +
SHIELD path: 53 states, 0 violations.`

export const architectureStages = [
  { name: 'Prometheus', description: 'Scrapes metrics every 10s', tech: 'Metrics' },
  { name: 'Kafka', description: 'KRaft bus, streaming pipeline', tech: 'Streaming' },
  { name: 'Feature Aggregation', description: '30s windowed features', tech: 'River' },
  { name: 'Online ML', description: 'HTR + HalfSpaceTrees', tech: 'Learning' },
  { name: 'Anomaly Detection', description: 'Streaming anomaly scoring', tech: 'River' },
  { name: 'Safety Shield', description: 'Formal verification layer', tech: 'TLA+' },
  { name: 'Kubernetes', description: 'Actuator execution', tech: 'Operator' },
]

export const threeLayers = [
  {
    id: 'observe',
    title: 'OBSERVE',
    subtitle: 'Prometheus',
    description: 'See what the cluster is doing.',
    metrics: ['CPU', 'Memory', 'Latency', 'Queue depth', 'Pod health', 'GPU utilization'],
    icon: 'Database',
  },
  {
    id: 'learn',
    title: 'LEARN',
    subtitle: 'Online ML',
    description: 'Understand how workload demand is changing.',
    metrics: ['River', 'Online learning', 'Anomaly detection', 'Streaming features'],
    icon: 'Brain',
  },
  {
    id: 'protect',
    title: 'PROTECT',
    subtitle: 'Safety Shield',
    description: 'Prevent unsafe actions before they reach Kubernetes.',
    metrics: ['TLA+', 'TLC', 'Policy invariants', 'Runtime safety validation'],
    icon: 'Shield',
  },
]

export const safetyInvariants = [
  { name: 'Min Replicas', formula: 'replicas >= 1', desc: 'Replica count never drops below 1' },
  { name: 'Max Replicas', formula: 'replicas <= 10', desc: 'Replica count never exceeds 10' },
  { name: 'Bounded Step', formula: '|new - old| <= 2', desc: 'Single decision changes replicas by at most 2' },
  { name: 'Heal Preserves', formula: 'heal => target = current', desc: 'Heal actions never change replica count' },
  { name: 'Cooldown', formula: '(clock - last) % 11 >= 6', desc: '60s minimum between actions' },
]

export const evaluationSystems = [
  { name: 'Fixed Replicas', color: '#6F6F6F' },
  { name: 'HPA', color: '#A8A8A8' },
  { name: 'ML Only', color: '#A8A8A8' },
  { name: 'SHIELD-AI', color: '#F12525' },
]

export const researchPillars = [
  { name: 'Formal Verification', tech: 'TLA+ / TLC', desc: 'Model-checked safety invariants across 273,702 reachable states' },
  { name: 'Online Learning', tech: 'River', desc: 'Streaming ML models for real-time workload prediction' },
  { name: 'Load Testing', tech: 'Locust', desc: 'Reproducible workload simulation and benchmarking' },
  { name: 'Chaos Testing', tech: 'LitmusChaos', desc: 'Controlled failure injection and recovery validation' },
]

export const selfHealingSteps = [
  { name: 'FAILURE', description: 'Pod crash, memory leak, GPU failure', color: 'accent' },
  { name: 'DETECT', description: 'Anomaly score crosses threshold', color: 'neutral' },
  { name: 'ANALYZE', description: 'Identify root cause and affected resources', color: 'neutral' },
  { name: 'VERIFY', description: 'Safety shield validates heal action', color: 'neutral' },
  { name: 'HEAL', description: 'Execute corrective action', color: 'neutral' },
  { name: 'RECOVER', description: 'System returns to stable state', color: 'neutral' },
]

export const autoscalingSignals = [
  'Request Rate',
  'Queue Depth',
  'Latency',
  'CPU',
  'Memory',
  'GPU',
  'Current Replicas',
]

export const observabilityMetrics = [
  'REQUEST RATE',
  'QUEUE DEPTH',
  'P95 LATENCY',
  'CURRENT REPLICAS',
  'PREDICTED REPLICAS',
  'CPU',
  'GPU',
  'MEMORY',
  'ANOMALY SCORE',
]
