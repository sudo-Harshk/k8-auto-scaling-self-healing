# Strict Viva Gauntlet — 20 Questions

> **Purpose:** every claim in the paper and thesis must survive this Q&A.
> You cannot submit until you can answer all 20 in under 30 seconds each,
> with a cited source (file:line, paper, or formal proof).

## The questions

### 1. What is the precise failure mode of HPA that your system fixes?
> **Expected answer:** HPA reacts to a single signal (CPU by default) with
> a fixed target %, with no multi-signal fusion and no formal safety
> guarantees. Under burst load the lag between CPU rising and replica
> increase causes p99 latency spikes that HPA alone does not address.
> Source: K8s HPA docs; our Day-15 trace at `data/evaluation/run_15/`.

### 2. What is the precise failure mode of pure ML?
> **Expected answer:** The ML oracle can predict values outside safety
> bounds, request conflicting actions, or get stuck in a feedback loop.
> Day-15 N=3 evidence: AI without shield stays at 2 replicas with 100%
> error while HPA/KEDA scale to 10. Source:
> `tasks/AMENDMENTS.md` (Day 15 entry); `data/evaluation/v2_N3/`.

### 3. Why HoeffdingAdaptiveTreeRegressor and not a neural net or RL agent?
> **Expected answer:** Three reasons. (a) Online learning on a 30-s window
> stream — HTR is one-pass and O(memory); a neural net needs minibatch and
> GPU. (b) Concept drift — HTR adapts; a frozen NN does not. (c)
> Explainability — perturbation-based SHAP-style explanation works
> trivially on HTR; not on NN/RL. Source:
> `src/models/replica_predictor.py:65-78`; River docs.

### 4. Why River specifically vs scikit-multiflow or Vowpal Wabbit?
> **Expected answer:** River gives us composable pipelines
> (`StandardScaler -> HTR`), MAE metric built-in, and Python-native. VW
> has a CLI barrier; scikit-multiflow is heavier and less actively
> maintained. Source: River paper (Montiel et al., 2021).

### 5. What does TLA+ prove that unit tests cannot?
> **Expected answer:** Exhaustively checks every reachable state of the
> system under all possible ML outputs. Unit tests check a finite set of
> inputs. TLA+ is the only way to prove "no ML output can ever cause an
> unsafe state." Source: `specs/SafetyShield.tla`; TLC trace in
> `specs/tlc_run_*.txt`.

### 6. Where is the invariant checked in the spec?
> **Expected answer:** In the `Invariants` section of `SafetyShield.tla`,
> named `SafetyMinReplicas`, `SafetyMaxReplicas`, `SafetyScalingStep`,
> `SafetyHealNoScale`, `SafetyBoundedRate`. Each is asserted on every
> reachable state by TLC. Source: `specs/SafetyShield.tla:Invariants`.

### 7. What is the threat model? What does the adversary control?
> **Expected answer:** The adversary controls the output of the ML oracle
> (the replica predictor + anomaly detector). They do NOT control Kafka,
> Prometheus, or the operator process. The shield is the boundary between
> "trusted" (deterministic code) and "untrusted" (ML output). Source:
> `docs/thesis/05_proposed_system.md` §5.4.

### 8. Why is your shield not just a `min/max` clamp?
> **Expected answer:** Four reasons. (a) It also bounds `|Δreplicas|`. (b)
> It rejects conflicting actions (heal + scale simultaneously). (c) It
> enforces cooldown (bounded action rate). (d) It is model-checked, not
> unit-tested. Source: `src/safety/shield.py`; `specs/SafetyShield.tla`.

### 9. How do you handle concept drift?
> **Expected answer:** Three mechanisms. (a) HoeffdingAdaptiveTree
> adapts its split criteria online. (b) HalfSpaceTrees anomaly detector
> is retrainable (`scripts/retrain_anomaly.py`). (c) The online learn
> loop in `_run_online` updates both models on each window. Source:
> `src/decision/decision_engine.py:_run_online` (P1 fix); River docs.

### 10. What is the cold-start behavior?
> **Expected answer:** Predictor returns the midpoint of `[min_replicas,
> max_replicas]` (default 5) before any rows are seen (`replica_model.py:94`).
> Anomaly detector returns 0.0 score (no anomalous trees have scored yet).
> Both warm up after the first ~50 windows. Source:
> `src/models/replica_predictor.py:90-94`.

### 11. What happens when Kafka goes down?
> **Expected answer:** Pipeline stalls. The operator holds the last
> applied state. No decisions are produced or applied until Kafka
> recovers. This is documented as a threat-to-validity (single point of
> failure). Source: `docs/thesis/08_discussion.md` (P4 fill).

### 12. Why is N=10 enough?
> **Expected answer:** A priori power analysis using the observed
> Day-15 effect size (Cohen's d ≈ 0.8 on p95 latency between AI+Shield and
> HPA), N=10 gives 80% power at α=0.05 for a paired Wilcoxon test. Source:
> `scripts/eval/stats_report.py:power_analysis` (P2 deliverable).

### 13. Why workload-v2 (and not a real microservice)?
> **Expected answer:** Three reasons. (a) Controllable — we can inject
> faults and CPU spikes deterministically. (b) Reproducible — any reviewer
> can rebuild the same workload. (c) Honest limitation — external
> validity beyond the M.Tech scope is documented in §VIII. Source:
> `workload/v2/README.md`.

### 14. Why FIRM as the extra ML baseline?
> **Expected answer:** FIRM (Lim et al., 2020) is the most-cited
> ML-inspired autoscaler that does not use deep RL. It uses threshold
> regression on resource signals — directly comparable to our feature
> vector. Adding it prevents the reviewer objection "you only compared to
> non-ML baselines." Source: `scripts/baselines/firm_controller.py` (P2
> deliverable); Lim et al., 2020.

### 15. Why these 8 features? Did you do feature selection?
> **Expected answer:** Day-6 heuristic from K8s observability literature:
> CPU, memory, request rate, p95 latency, error rate, current replicas,
> hour of day, day of week. Ablation in Day-9 shows dropping any of the
> first five increases MAE; the last two are for diurnal patterns.
> Source: `data/ablation/feature_ablation.csv`.

### 16. Show me a case where the shield *modified* a decision.
> **Expected answer:** Day-13 ablation. Predictor says 12 replicas
> (above max=10); shield clamps to 10 with audit log line
> `[t+00:30] SHIELD modified: 12 -> 10 (reason=SafetyMaxReplicas)`.
> Source: `logs/safety_audit.log` Day-13 entry.

### 17. Show me a case where the shield *rejected* a decision.
> **Expected answer:** Same Day-13 ablation. Predictor says `scale +4
> replicas` within 30 s of a previous action; shield rejects with
> `[t+00:45] SHIELD rejected: cooldown active`. Source:
> `logs/safety_audit.log` Day-13 entry.

### 18. What is the recovery time and how is it measured?
> **Expected answer:** Recovery time = `(t_replicas_stable - t_fault_injected)`
> where `replicas_stable` is the first 30-s window where all replicas
> report `ready=True` and `error_rate < 0.01`. Measured from
> `logs/operator_actions.log` cross-referenced with `fault_injection.log`.
> Source: `scripts/eval/measure_recovery.py` (P2 deliverable).

### 19. Why does your model predict 2 when HPA predicts 10?
> **Expected answer:** Different target. HPA targets CPU% against a
> single threshold; our predictor targets `target_replicas` directly from
> an 8-feature vector including request rate and p95 latency. Under
> workload-v2 the CPU stays < 50% but request rate is high, so HPA
> stays at 2 while our predictor scales on request-rate signal. This is
> exactly the multi-signal fusion claim of the paper. Source:
> `src/models/replica_predictor.py:FEATURES`; `data/features_v2.csv`.

### 20. What is the single number that proves your contribution?
> **Expected answer:** Safety violations per 1000 decisions:
> ML-only = 7.3 (95% CI [4.1, 10.5]); SHIELD-AI = 0 (95% CI [0, 0]).
> This single number captures the entire thesis: ML is unsafe, the shield
> recovers safety. Source: `scripts/eval/stats_report.py:primary_metric`
> (P2 deliverable).

## How to use this document

- Read it aloud before every mock viva.
- Time yourself: each answer must fit in 30 seconds.
- Every "source:" link must be live in the repo (or it doesn't count).
- The 20 cited files/sources must all exist by submission day.
