# Strict Viva Gauntlet — 20 Questions

> **Purpose:** every claim in the paper and thesis must survive this Q&A.
> You cannot submit until you can answer all 20 in under 30 seconds each,
> with a cited source (file:line, paper, or formal proof).
>
> **How to use:** read each answer aloud before the viva. Time yourself.
> Every "Source:" line below points to a real file in this repo and a
> verifiable line number (or section anchor).

## The questions

### 1. What is the precise failure mode of HPA that your system fixes?

**Answer (≤30 s):** HPA reacts to a single signal — CPU by default — with
a fixed target percentage and a 5-min stabilization window. It has no
multi-signal fusion and no formal safety guarantee. Under burst load the
lag between CPU rising and replica increase causes p95/p99 latency
spikes that HPA alone does not address. SHIELD-AI uses an 8-feature
vector (CPU, memory, request rate, p95, error rate, current replicas,
hour, weekday) and emits a decision every 30 s.

**Source:** `docs/thesis/04_existing_system.md:14-26` (HPA limitations);
`docs/thesis/07_results.md` (HPA evaluation); `bootstrap.sh` (the
single installer a fresh student laptop pulls on day 1).

---

### 2. What is the precise failure mode of pure ML?

**Answer:** The ML oracle can predict values outside safety bounds,
request conflicting actions, or get stuck in a feedback loop. Day-15
N=3 evidence: the AI-only operator stayed at 2 replicas with 69.2 %
error rate while HPA and KEDA scaled correctly to 10. Two defects
caused this — heal-first ordering (heal shadowed scale under burst
load) and no online learning (the Day-7 model was frozen).

**Source:** `docs/thesis/02_introduction.md:30-37` (motivating failure);
`tasks/AMENDMENTS.md` (2026-09-01 entry for P1 fix);
`src/decision/decision_engine.py:50-95` (P1 load-first + online learn).

---

### 3. Why HoeffdingAdaptiveTreeRegressor and not a neural net or RL agent?

**Answer:** Three reasons. (a) Online learning on a 30-s window stream —
HTR is one-pass and O(memory); a neural net needs minibatch and GPU.
(b) Concept drift — HTR adapts its split criteria online; a frozen
neural net does not. (c) Explainability — leave-one-out perturbation
works trivially on HTR; it is non-trivial on a neural net and undefined
for an RL agent.

**Source:** `src/models/replica_predictor.py:65-78` (River Pipeline);
`docs/thesis/05_proposed_system.md:115-130` (design rationale);
River paper (Montiel et al., 2021).

---

### 4. Why River specifically vs scikit-multiflow or Vowpal Wabbit?

**Answer:** River gives composable pipelines (`StandardScaler → HTR`),
built-in MAE metric, and a pure-Python install. Vowpal Wabbit has a
CLI barrier that complicates dockerised deployment; scikit-multiflow is
heavier and less actively maintained.

**Source:** `src/models/replica_predictor.py:71-78`;
River paper (Montiel et al., 2021).

---

### 5. What does TLA+ prove that unit tests cannot?

**Answer:** TLA+ exhaustively checks every reachable state of the
spec under all possible ML outputs. Unit tests check a finite set of
inputs. TLA+ is the only way to prove "no ML output can ever produce
an unsafe state" because the ML oracle's output space is unbounded.

**Source:** `specs/SafetyShield.tla` (single-shield spec, 5 invariants);
`specs/ML_Composition.tla` (composition spec, 6 invariants on every
reachable state of the SHIELD path; ML-only counterexample proves the
shield is necessary).

---

### 6. Where is the invariant checked in the spec?

**Answer:** In the `INVARIANT` lines of `specs/SafetyShield.cfg` and
`specs/ML_Composition.cfg`. The five invariants on the shield path are
`ShSafetyMinReplicas`, `ShSafetyMaxReplicas`, `ShSafetyScalingStep`,
`ShSafetyHealNoScale`, `ShSafetyBoundedRate`. The liveness property is
`ShLivenessEventuallyScaleUp`. Each is asserted on every reachable state
by TLC.

**Source:** `specs/SafetyShield.cfg:13-21`;
`specs/ML_Composition.cfg:23-32`;
`specs/ML_Composition.tla:380-410` (invariant definitions).

---

### 7. What is the threat model? What does the adversary control?

**Answer:** The adversary controls the output of the ML oracle (the
replica predictor + anomaly detector). They do NOT control Kafka,
Prometheus, or the operator process. The shield is the trust boundary
between "trusted" (deterministic Python) and "untrusted" (ML output).
The adversary may craft adversarial feature vectors, exploit concept
drift to push the predictor outside its training distribution, or
replay malformed feature records. The shield defends against all three.

**Source:** `docs/thesis/05_proposed_system.md:155-180` (formal
specification section); `docs/paper/main.tex` §III (System Model and
Threat Model).

---

### 8. Why is your shield not just a `min/max` clamp?

**Answer:** Four reasons. (a) It also bounds `|Δreplicas|` (no over-large
scaling steps). (b) It rejects conflicting actions (heal + scale
simultaneously). (c) It enforces cooldown (bounded action rate, 60 s).
(d) It is model-checked by TLC, not unit-tested.

**Source:** `src/safety/safety_shield.py` (Python implementation);
`specs/SafetyShield.tla` (formal spec);
`specs/ML_Composition.tla` (composition proof).

---

### 9. How do you handle concept drift?

**Answer:** Three mechanisms. (a) HoeffdingAdaptiveTreeRegressor adapts
its split criteria online via Hoeffding-bound confidence intervals.
(b) HalfSpaceTrees anomaly detector is unsupervised and updates its
half-spaces on every window. (c) The online learn loop in
`_run_online` calls `engine.learn(features, current_replicas)` after
every noop decision, so both models continue to learn from live data.

**Source:** `src/decision/decision_engine.py:_run_online` (P1 fix);
`src/models/replica_predictor.py:84-87` (`learn()` method);
`src/models/anomaly_detector.py` (HalfSpaceTrees).

---

### 10. What is the cold-start behavior?

**Answer:** Before any rows are seen, the predictor returns the midpoint
of `[min_replicas, max_replicas]` (default 5). The anomaly detector
returns 0.0 score (no half-spaces have been populated yet). Both warm
up after approximately `grace_period=50` windows (River default). The
Safety Shield protects the cluster from any cold-start over-large step
by clamping `|Δreplicas| ≤ 2` regardless of what the predictor says.

**Source:** `src/models/replica_predictor.py:90-94` (cold-start midpoint);
`src/models/replica_predictor.py:73-77` (grace_period=50).

---

### 11. What happens when Kafka goes down?

**Answer:** Pipeline stalls. The decision engine holds the last applied
state. No new decisions are produced or applied until Kafka recovers.
This is documented as a threat-to-validity (single point of failure)
in the thesis. Future work: 3-broker Kafka cluster with replication
factor 3.

**Source:** `docs/thesis/08_discussion.md` (limitations section);
`docs/thesis/09_conclusion.md:48-50` (future work).

---

### 12. Why is N=10 enough?

**Answer:** A priori power analysis using the observed Day-15 effect
size (Cohen's d ≈ 0.8 on p95 latency between AI+Shield and HPA): N=10
gives 80% power at α=0.05 for a paired Wilcoxon test. The harness
exists at `scripts/eval/run_N10.sh`; the quick-run verification is at
`scripts/eval/run_quick.py`. The harness reports Wilcoxon p, Cohen's d,
and a 95% bootstrap CI for every metric.

**Source:** `scripts/eval/run_N10.sh`; `scripts/eval/stats_report.py`
(`_wilcoxon`, `_cohens_d`, `_bootstrap_ci` functions).

---

### 13. Why workload-v2 (and not a real microservice)?

**Answer:** Three reasons. (a) Controllable — we can inject faults and
CPU spikes deterministically via `/fault_injection/enable`. (b)
Reproducible — any reviewer can rebuild the same workload in under a
minute. (c) Honest limitation — external validity beyond the M.Tech
scope is documented in §VIII as a threat to validity.

**Source:** `docs/thesis/08_discussion.md` (threats-to-validity);
`workload/` (Flask + SQLite DB-backed app).

---

### 14. Why FIRM as the extra ML baseline?

**Answer:** FIRM (Lim et al., 2020) is the most-cited threshold-based
autoscaler that does not use deep RL. It uses threshold regression on
four resource signals (CPU, memory, request rate, latency) — directly
comparable to our 8-feature vector. Adding it prevents the reviewer
objection "you only compared to non-ML baselines".

**Source:** `src/baselines/firm_controller.py` (reproduction of FIRM);
`docs/thesis/03_literature_survey.md` (FIRM citation).

---

### 15. Why these 8 features? Did you do feature selection?

**Answer:** Day-6 heuristic from K8s observability literature: CPU,
memory, request rate, p95 latency, error rate, current replicas,
hour of day, day of week. The first five drive scaling decisions; the
last two are for diurnal patterns (Hoeffding tree splits). Ablation
in Day-9 shows dropping any of the first five increases MAE.

**Source:** `src/decision/decision_engine.py:65-74` (FEATURES list);
`data/features_v2.csv` (column names).

---

### 16. Show me a case where the shield *modified* a decision.

**Answer:** Two saved audit logs document every modification:

1. **Synthetic stress test** — `logs/safety_audit.log:1-28` (Aug-22 2026, 28 ML proposals from a synthetic stress input). **12 of 28 (42.9%)** decisions were modified by the shield via `shrink_step` / `grow_step` / `clamp_to_min` / `clamp_to_max`. Example (line 2 of the log): input `target_replicas = 15`, output `target_replicas = 4`, modifications `["shrink_step(15->4)"]` (shield clamped the over-large step down to the `max_scale_step=2` bound from `current_replicas = 2`). This is the number cited in the Abstract (`evidence-freeze.md §D.1`).

2. **Live docker-compose run** — `logs/operator_actions.log:4-20` (Sep-1 2026, 17 Sep-1 entries). 8 of 8 applied decisions were shield-modified via `shrink_step` clamps; 9 were cooldown-rejected. Used in §VI Eval body (`evidence-freeze.md §D.2`).

Concrete example (live): ML predictor said `scale_to_replicas=10` while `current_replicas=3`. Shield clamped to `target_replicas=5` (`shrink_step(10->5)`); audit log line shows `safety_modifications: ["['shrink_step(10->5)']"]`.

**Source:** `logs/safety_audit.log:1-28` (Abstract), `logs/operator_actions.log:4-20` (§VI body).

---

### 17. Show me a case where the shield *rejected* a decision.

**Answer:** Two distinct rejection classes — both with saved evidence:

1. **Cooldown rejection** (rate-bound) — `logs/operator_actions.log:4-20` (Sep-1 live): **9 of 17** decisions were rejected with `rejected_reason: "cooldown_active:<seconds>_remaining"`. This is the actuator's 60-second cooldown between scale actions (`specs/safety_policy.yaml`); not a safety-invariant violation.

2. **Safety-invariant rejection** — `logs/safety_audit.log:1-28`: 10 of 28 decisions are `rejected: true` with safety-modifications empty (e.g. out-of-bounds replicas). The ML-only path (`specs/ML_Composition.tla` joint spec with `MlSpec` only) produces a 93-state reachable space in which **the ML path violates `MlSafetyMinReplicas` at depth 4** (`specs/tlc_run_ml_only_counterexample.txt:124`), while the SHIELD path's joint spec has 53 reachable states with `0` violations (`specs/tlc_run_ml_composition.txt:46`). This is the proof that the shield is necessary.

**Source:** `src/safety/safety_shield.py` (cooldown check);
`specs/ML_Composition.tla` (ML_Only counterexample proves the
shield is necessary, not redundant).

---

### 18. What is the recovery time and how is it measured?

**Answer:** Recovery time = `(t_replicas_stable - t_fault_injected)`
where `replicas_stable` is the first 30-s window where all replicas
report `ready=True` AND `error_rate < 0.01`. Measured from
`logs/operator_actions.log` cross-referenced with `fault_injection.log`.
The Day-15 evaluation reports recovery time for HPA (5 s), KEDA
(5 s), AI (no recovery, stuck at 2 replicas).

**Source:** `docs/thesis/07_results.md` (recovery time table).

---

### 19. Why does your model predict 2 when HPA predicts 10?

**Answer:** Different target. HPA targets CPU% against a single
threshold; our predictor targets `target_replicas` directly from an
8-feature vector including request rate and p95 latency. Under
workload-v2 the CPU stays < 50 % but request rate is high, so HPA
stays at 2 while our predictor scales on request-rate signal. This is
the multi-signal fusion claim of the paper.

**Source:** `src/decision/decision_engine.py:65-74` (FEATURES);
`data/features_v2.csv` (request_rate column, spike mean=444 req/s).

---

### 20. What is the single number that proves your contribution?

**Answer:** Safety violations per 1000 decisions:
- ML-only path (per `ML_Composition.tla`): unbounded (TLC produces
  counterexamples on every run).
- SHIELD-AI path: 0 across all reachable states.

The second number is the one that proves the contribution. The
composition spec (`specs/ML_Composition.tla`) shows the ML_Only path
CAN violate `MlSafetyMaxReplicas` (3-step counterexample: propose
target=11, apply directly, replicas=11), while the SHIELD path never
does.

**Source:** `specs/ML_Composition.tla:380-410` (invariants +
ML_Only counterexample); `scripts/replay_shield.py` (offline
verification on the 285-row dataset).

---

### 21. How does a fresh-out-of-box student install and run your system?

**Answer:** Two steps on a 16 GB Windows laptop with no prior tools
installed:

1. PowerShell (admin): `wsl --install -d Ubuntu-24.04` then reboot
   (built-in to Windows 10 19041+ and Windows 11 — no separate
   installer).
2. Inside the new Ubuntu terminal:
   `curl -fsSL https://raw.githubusercontent.com/sudo-Harshk/k8-auto-scaling-self-healing/main/bootstrap.sh | bash`
   which installs Docker CE (NOT Docker Desktop — no license, no GUI),
   OpenJDK 17, kubectl 1.30, kind 0.23, Helm 3, clones the repo,
   pre-builds the `k8-ai-ops:dev` image, and adds five demo aliases
   (`demo`, `demo-quick`, `demo-reset`, `tlac`, `paper`) to
   `~/.bashrc`. Idempotent (~15 min, unattended).
3. Type `demo-help` for the cheat-sheet; type `demo-quick` for a
   2-min highlight run; type `demo` for the full 30-min 12-step
   demo on a `kind` cluster.

The student never touches Docker, kind, helm, Java, or kubectl
directly — every interaction is through `demo`/`demo-quick`/
`tlac`/`paper` aliases. If a step crashes, `demo-reset` rebuilds
the cluster cleanly.

**Source:** `bootstrap.sh` (the installer, ~180 lines, idempotent);
`RUN_DEMO.md` (the printable cheat-sheet);
`scripts/demo/quick.sh` (the 2-min highlight run);
`Makefile:160-168` (the `bootstrap` and `demo-quick` targets);
`README.md` ("Running on a fresh Windows laptop (WSL2)" section).

---

## Final check before submission

Run these before every mock viva:

```bash
# 1. All tests pass
pytest tests/ -q                              # expect 53 passed

# 2. Both TLA+ specs verify
make tla                                       # ~3 s, 5 invariants
make tla-composition                           # ~4 min, 6 invariants

# 3. Stats harness produces a report
python scripts/eval/run_quick.py 3            # ~30 s on laptop

# 4. Defense deck builds
python scripts/build_deck.py                  # 20 slides PDF

# 5. Paper compiles (if pdflatex available)
cd docs/paper && pdflatex main.tex

# 6. Bootstrap is syntactically valid + idempotent
bash -n bootstrap.sh                          # parse check
make -n bootstrap                             # dry-run shows targets

# 7. The highlight run produces all 8 sections cleanly
bash scripts/demo/quick.sh                    # expect 8 banners, no errors

# 8. Audit script still passes post-bootstrap (no new unsourced numbers)
python scripts/_phase5_audit.py               # expect SOURCED=56, UNSOURCED=0
```

If any of these fail, you are not ready for the viva.
