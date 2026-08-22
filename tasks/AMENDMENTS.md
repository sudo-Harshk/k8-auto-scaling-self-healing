# AMENDMENTS — deviations from the original 14-day plan

This file records every substantive change made to `tasks/day-*.md` during the build, with
timestamp and rationale. The original day docs are edited **in place**; this file is the
human-readable changelog so the thesis and reviewers can trace what was changed and why.

All times IST.

---

## 2026-08-22 — Safety Shield: Python implementation with 16 unit tests, invariant order matters (Day 11)

**What changed**
- `src/safety/safety_shield.py` (260 lines) — `SafetyShield` class
  enforcing all five TLA+ invariants at runtime. Loads
  `specs/safety_policy.yaml`.
- `tests/test_safety_shield.py` (240 lines, 16 tests) — anti-drift
  contract from Day 10: every invariant has a positive test (valid
  action passes) and a negative test (intentional violation is caught).
- `conftest.py` — adds `/code` to sys.path so pytest can import `src.X`.
- `ops/docker/requirements.txt`: added `pytest==8.3.0`, `pyyaml==6.0.1`.
- Docker image rebuilt (`k8-ai-ops:dev` new sha256).
- `logs/safety_audit.log` — JSON audit trail, one line per `validate()`.

**Why (deviation from plan)**

The Day-11 plan listed step 4 as "modify decision_engine.py to pass every
decision through the Safety Shield. Only approved/modified decisions are
published to k8s-decisions." We did **not** wire the shield into the
decision engine yet — instead we provided a clean integration smoke test
(5 decisions through shield, all allowed). The decision engine integration
is deferred to Day 12 (Kopf operator), where the shielded decision is the
input to the operator's reconcile loop. Putting the integration there
avoids a circular import (engine -> shield -> engine).

**Test results:** 16 passed in 0.10s.

**Gotchas (and fixes)**

1. **Image entrypoint is `python`.** Running pytest via
   `docker run k8-ai-ops:dev python -m pytest` becomes
   `python python -m pytest`. Fix: use `--entrypoint python -m pytest`.
2. **pytest can't import `src.X`.** Fix: `conftest.py` at the repo root
   that adds the repo dir to `sys.path`. Same convention as the rest of
   the project.
3. **Invariant order matters.** First implementation applied max-clamp
   before step-shrink. For target=15 from current=2, that gave
   max→10 then shrink→4. Switching to step-shrink first gives
   shrink→4 then max-clamp→no-op. Same end result, but the audit log
   tells a clearer story: the danger is the step, not the absolute
   value. We picked shrink-first.
4. **Test for max-replicas clamp was too aggressive.** Initial test set
   current=2 with target=15. Both step-shrink and max-clamp fire, and
   the result is target=4 (shrunk) not target=10 (clamped). Fix: use
   current=8 so the step to max (10) is exactly max_scale_step (2) and
   only max-clamp fires.

**Test isolation (anti-drift contract)**
Eight of the 16 tests are **negative cases** that intentionally violate
an invariant and verify the Python shield catches the violation. If any
future code change breaks an invariant, the corresponding test will
fail, signaling the spec also needs updating. This is the contract
documented in `docs/SafetyShield.md` Section 9.

---

## 2026-08-22 — TLA+ verified via CLI on the VM, not TLA+ Toolbox on Windows (Day 10)

**What changed**
- `specs/SafetyShield.tla` (217 lines) — TLA+ spec modelling the safety
  layer. PlusCal-shaped algorithm with 7 variables, 8 actions, and 5
  invariants.
- `specs/SafetyShield.cfg` — TLC model checker config.
- `specs/safety_policy.yaml` — Python-readable form of the same rules.
  Day 11's `SafetyShield` class reads this file.
- `docs/SafetyShield.md` — human walkthrough of the spec, invariants,
  state-space analysis, and Day 11 contract.
- VM: installed `default-jre-headless` (OpenJDK 21) and downloaded
  `tla2tools.jar` v2026.08.21 to `~/tla/tla2tools.jar` (~4.5 MB).

**Why**
The plan called for TLA+ Toolbox on the Windows laptop. We picked the
CLI alternative: `java -jar ~/tla/tla2tools.jar`. Reasons:

1. The verification run is fully reproducible on the VM (the laptop only
   holds the source files). Anyone can re-run TLC without an IDE.
2. The CLI is faster to iterate on — no GUI model-creation step.
3. Avoids a 30-min Toolbox install on the laptop.

The CLI outputs the same model-check report (`No error has been found.
N states generated, M distinct.`); the GUI adds a state-space explorer
that we don't need for Day 10.

**TLC verification result (2026-08-22 02:39:07)**

```
264330 distinct states found, 0 states left on queue.
The depth of the complete state graph search is 37.
Finished in 03s
Probability of missed state (fp collision): 3.0E-11
```

All 5 invariants hold on every reachable state.

**Gotchas (and fixes)**
- `EXTENDS Naturals` does not provide the unary `-` operator. Added
  `Integers` to the EXTENDS list.
- `Abs` must be defined before first use; reordered the spec.
- State invariants cannot reference primed variables (`x'`);
  reformulated `SafetyScalingStep` to be a state predicate and
  enforced the |delta| <= 2 bound in the action guards directly.
- TLC's `-config` expects the config file path; the spec is given as a
  separate positional argument (`specs/SafetyShield`, not `.tla`).

**Side effects**
- Day 11's `SafetyShield.validate()` must mirror every rule in
  `safety_policy.yaml`. Drift between spec and code is mitigated by
  unit tests that intentionally violate each invariant.

---

## 2026-08-21 — Decision Engine uses perturbation-based feature importance, not SHAP (Day 9)

**What changed**
- `src/decision/decision_engine.py`: new module. `DecisionEngine` class
  combines the Day-7 replica predictor and Day-8 anomaly detector into
  a single decision rule with publishing to Kafka topic `k8s-decisions`
  and logging to `logs/decisions.log`.
- Offline mode (`--offline`) reads `data/features.csv` and produces one
  decision per row; online mode consumes `k8s-features` from Kafka and
  publishes to `k8s-decisions`.
- Top-2 features are explained via leave-one-out perturbation (replace
  feature with column mean, recompute prediction, take |delta|).

**Why**
The plan listed "shap or River feature importances as fallback". SHAP's
`TreeExplainer` is XGBoost/sklearn-only; SHAP's `KernelExplainer` is
model-agnostic but slow (~seconds per call) and unsuitable for an
online loop. The perturbation approach is also model-agnostic, runs in
milliseconds, and is well-established in the interpretability literature
(Fisher, Rudin, Dominick 2018; "All Models are Wrong but Many are Useful").
The replicated-replica data pipeline produces feature means at every
window, so the column-mean reference is always available.

**No new dependencies.** `shap` and `scikit-learn` were the planned
additions for Day 9 (`requirements.txt` line 27) — neither was added.
The decision engine is pure Python.

**Side effects / gotchas**
- The decision object schema is now locked for Day 12 (Kopf operator).
  See `tasks/day-09-decision-engine-and-shap.md` execution notes.
- Heal action is intentionally scale-neutral: `target_replicas` equals
  `current_replicas`. The operator interprets this as "delete the
  unhealthy pod, don't change replica count".
- Kafka publishing path uses the same `KafkaProducer` class as Day 4
  (kafka-python 2.0.2, `localhost:9094` host-side port-forward).

---

## 2026-08-21 — HalfSpaceTrees `window_size` tuned to 10 for the 33-row dataset (Day 8)

**What changed**
- `src/models/anomaly_detector.py`: `AnomalyDetector.__init__` defaults
  `window_size=10` (River's default is 250) and splits `train_offline` into
  three phases — `learn` (33 normal rows), `score` (normal), `score` (abnormal).

**Why**
River's `HalfSpaceTrees.score_one` returns `0.0` while `self._first_window` is
true. The window only completes after `window_size` `learn_one` calls have
been seen. With the default `window_size=250` and only 33 normal training
rows, the model never reaches its first pivot and every score is 0.0 on the
offline dataset. Setting `window_size=10` makes the first window complete
during training (after 10 `learn_one` calls), so subsequent `score_one`
calls return meaningful values.

**Side effects / gotchas**
- The constructor argument is data-dependent; if the dataset grows, the
  window_size should be reviewed. A future training-set expansion (Day 13+
  capture) is a candidate to revisit this.
- The fix is model-only; the threshold strategy (midpoint of max normal and
  min abnormal) is unchanged.

---

## 2026-08-21 — Anomaly detection rate 55% on the 55-row dataset (Day 8)

**Observation**
On the 22 abnormal rows (`is_anomaly=1`: spike=11 + idle=11), the chosen
threshold (0.2417, midpoint of max normal and min abnormal scores) catches
12 (55%) with 3 false positives (9% of 33 normal rows). The mean abnormal
score is 0.2637 vs mean normal 0.0394 — a **6.7x** separation, which is the
primary paper-citable evidence.

**Why the spike rows are partially missed**
The 33-row training set (`baseline` + `steady_high`) covers request_rates
0.7-25 req/s. HalfSpaceTrees' mass profile extends across this entire range,
so spike rows near the upper edge of steady_high (~30 req/s) are not yet
"outside" the learned mass; only spike rows above the trained envelope flag.
The detector therefore catches **idle** (low-end outlier) reliably but
**spike** only when the load clearly exceeds the high end of training.

**Impact on the project**
- Day 9 (Decision Engine + SHAP): the anomaly score is an input feature,
  not a hard gate. The decision engine can still trigger auto-healing on a
  organic error-rate spike (Day 13 injects via podinfo's
  `/fault_injection/enable`).
- Day 13 (E2E + Chaos): use podinfo's `POST /fault_injection/enable` to
  inject deterministic anomaly events, bypassing the organic-detection
  limitation. The detector will still see the atypical request shape
  and produce a high score.

**Resolution plan — POST-COMPLETION REWORK (user decision, 2026-08-21)**
No code change. The detector is functional and the mean separation is
paper-citable. The 55% rate is a property of the small dataset, not a
bug. Document here so reviewers can trace the limitation and the next
rework path (Day 15+: capture a richer dataset with at least 200 normal
rows spanning a wider request-rate range, then retrain).

---

## 2026-08-20 — River 0.26.0 installed via one-line source patch on Python 3.11 (Day 7)

**What changed**
- `ops/docker/requirements.txt`: `numpy` bumped 1.26.4 → 2.4.6 (river 0.26.0's hard
  floor), `river` added at 0.26.0 (latest stable — 0.24.0 was yanked).
- `ops/docker/Dockerfile`: kept `python:3.11-slim` base, added a 1-line `sed`
  patch after `pip install` that strips the 3.12 typing syntax from
  `river/stream/iter_csv.py`:

```
class DictReader(csv.DictReader["FeatureName"]):   # 3.12-only, breaks on 3.11
        → class DictReader(csv.DictReader):        # works on both, loses only the type hint
```

**Why**
River 0.10.0 through 0.26.0 all ship cp311 wheels whose source uses PEP 695
generic syntax (`csv.DictReader["FeatureName"]`) — a 3.12-only feature. Every
river import path that touches `tree` (HoeffdingAdaptiveTreeRegressor)
transitively loads `iter_csv`, so the whole module is unimportable on 3.11.
Upgrading to 3.12 instead would have broken `kafka-python 2.0.2` (vendored six
broken on 3.12) and Faust's still-unverified 3.12 status. The patch keeps the
existing 3.11 stack intact and removes only the static type hint (no runtime
effect).

**Side effects / gotchas**
- The patch must run AFTER `pip install`; re-ordering breaks the build.
- `from src.models.replica_predictor import ReplicaPredictor` requires
  `PYTHONPATH=/code` or running from the `/code` directory with `src` on the
  path. The container's WORKDIR is `/code` but `sys.path` doesn't include it
  automatically for `from src...` imports.

---

## 2026-08-20 — KNOWN LIMITATION: p95_latency_ms is constant (zero variance) with podinfo

**Observation**
In the Day-6 dataset (`data/features.csv`, 55 rows across 4 load scenarios),
`p95_latency_ms` is **4.75 ms in every single row** — baseline (10 users), spike
(100 users), steady-high (50 users), and idle alike. Zero variance.

**Root cause**
podinfo is a trivial Go HTTP server with **no backend dependencies** — no database,
no external API calls, no queues. It renders responses in microseconds, so even 100
concurrent Locust users cannot push its p95 latency above ~5 ms. The latency feature
simply has nothing to measure. This is a property of the workload, not a pipeline bug
(the `histogram_quantile` query is verified working; it just has nothing to vary).

**Impact on the project**
- Day 7 (replica predictor): River-ML will learn the feature has no predictive power
  and ignore it. Harmless.
- Day 8 (anomaly detector): anomalies are carried by `cpu_percent` and
  `request_rate`, which show strong variance (0.4% → 13.3% and 0.73 → 51.4 req/s
  respectively). No impact.
- Day 9 (SHAP): p95 will report ~zero contribution. An honest but empty explanation
  component.

**Resolution plan — POST-COMPLETION REWORK (user decision, 2026-08-20)**
**Do not fix now.** Proceed through all 14 days with podinfo. After the full project
is complete and verified end-to-end, redo the dataset + evaluation with a realistic
microservice that has backend dependencies (e.g., a service backed by a database or
simulated async processing) so p95 latency varies meaningfully under load. The
pipeline itself (Prometheus → Kafka → Faust → models → operator) is
workload-agnostic, so the rework only swaps the workload manifest and re-runs
Days 3, 6, 13, 14 data capture.

---

## 2026-08-20 — p95 latency added to the metrics pipeline (Day 6)

**What changed**
- `src/metrics/metrics_client.py`: added `p95_latency_ms` to `QUERIES`
  (`histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket{...}[1m]))
  by (le)) * 1000`). NaN results (idle histograms) are mapped to 0.0 so downstream
  JSON/Faust never sees NaN. **Additive only** — the six Day-3 fields are unchanged.
- `src/streaming/stream_processor.py`: `METRIC_KEYS` extended with
  `p95_latency_ms`; accumulation hardened with `float(msg.get(k) or 0.0)` so JSON
  nulls (metrics_client writes None on a Prometheus hiccup) can't poison a window.
- Feature percentages in `feature_builder.py` are computed against podinfo's own
  pod limits (100m CPU / 128Mi per replica), **not** node capacity — node-relative
  percentages on the 4 vCPU / 16 GiB VM would be ~0% and useless as ML features.
- The Day-6 plan's single `feature_builder.py -> features.csv` step is split into
  two scripts: `feature_builder.py` (per-scenario JSONL capture, one fresh Kafka
  consumer group per run so scenarios don't bleed into each other's offsets) and
  `build_dataset.py` (merge + label + target_replicas -> features.csv). A ~40s
  settle gap between scenarios keeps window-boundary bleed to at most one window.

**Why**
- p95 latency is a Day-6 feature-vector column (`p95_latency_ms`) and a useful
  anomaly signal for Day 8; it was missing from the Day-3 locked QUERIES.
- Splitting capture from labeling lets each scenario run unattended with a hard
  timeout and keeps the labeling policy in one reviewable place.

---

## 2026-08-20 — faust-streaming bumped to 0.11.3, aiokafka pinned to 0.10.0 (Day 5)

**What changed**
- `ops/docker/requirements.txt`: `faust-streaming` bumped from 0.10.11 → 0.11.3.
  `aiokafka` explicitly pinned to 0.10.0 (previously unpinned, resolved to 0.14.0).
- `src/streaming/stream_processor.py`: removed `@app.on_shutdown` flush handler
  (decorator signature changed in faust 0.11.x; the handler is unnecessary because
  at least 2 full 30-s windows are emitted during any ≥70-s run).

**Why**
Three blocking incompatibilities in sequence:
1. `faust-streaming==0.10.11` crashes with `ModuleNotFoundError: No module named
   'mode.utils.typing'` on Python 3.11. Bumping to 0.10.24 did not fix it (same
   mode-streaming dependency). Bumping to 0.11.3 resolved the `mode` import chain.
2. `faust-streaming==0.11.3` pulls `aiokafka==0.14.0` by default, which fails with
   `AttributeError: 'MetadataRequest_v1' object has no attribute 'prepare'` when
   talking to Apache Kafka 3.9.x. Pinning `aiokafka==0.10.0` (the minimum allowed
   by faust 0.11.3) fixes the protocol negotiation.
3. Faust's built-in web server binds port 6066; a zombie container from an earlier
   smoke test held the port and crashed the worker with `OSError(98)` on restart.

**Side effects / gotchas**
- Faust 0.11.3 on Python 3.11 works; earlier 0.10.x releases do not.
- `aiokafka` must be pinned — letting pip resolve to 0.14.0 breaks Kafka 3.9.x.
- Faust worker web UI (port 6066) is unused; can be disabled if it becomes noisy.
- Docker data dir (`k8s-stream-processor-data`) should be deleted and recreated when
  changing faust-streaming versions to avoid stale offset/store incompatibilities.

---

## 2026-08-18 — Kafka via official apache/kafka image, not Bitnami chart (Day 4)

**What changed**
- `ops/manifests/kafka.yaml` deploys single-node KRaft Kafka from the official
  `apache/kafka:3.9.1` image (plain Deployment + ClusterIP Service) instead of the
  Bitnami Kafka Helm chart named in the Day-4 plan. Topic `k8s-metrics` (1
  partition, RF 1) per plan.
- Two listeners: `PLAINTEXT` :9092 advertised as `kafka.kafka.svc.cluster.local`
  (in-cluster clients, e.g. Day-5 Faust) and `EXTERNAL` :9094 advertised as
  `localhost` (host-side clients via port-forward).
- Storage ephemeral (`/tmp/kraft-combined-logs` on the container layer); the
  metrics stream is transient and the Day-6 dataset persists to CSV, not Kafka.

**Why**
Bitnami moved its container catalog behind a paid tier (Aug 2025); the official
Apache image is free and KRaft-native. A raw manifest also avoids pulling in
Strimzi/operator machinery for a single dev broker.

**Side effects / gotchas**
- The image only enables KRaft when `KAFKA_PROCESS_ROLES`, `KAFKA_NODE_ID`,
  `KAFKA_CONTROLLER_QUORUM_VOTERS`, `KAFKA_CONTROLLER_LISTENER_NAMES` are set
  explicitly; otherwise it fails demanding `zookeeper.connect`.
- kafka-*.sh tools inside the pod need `env KAFKA_HEAP_OPTS="-Xms128M -Xmx128M"`;
  they inherit the broker's 512M heap env and OOM at the 1Gi pod limit otherwise.

---

## 2026-08-18 — Environment migrated to Azure VM (canonical for Days 4-14)

**What changed**
- Canonical environment moved from the Windows laptop (Docker Desktop/WSL2) to an
  Azure VM: `Standard_D4as_v5` (4 vCPU AMD EPYC x86-64 / 16 GB RAM / 64 GB Standard
  SSD), Ubuntu 24.04 LTS, cgroup v2, Central India. Hardened: SSH-key-only auth,
  ufw (port 22 only), daily auto-shutdown 23:00 IST, budget alerts at $10/$25.
  Repo cloned to `~/k8-auto-scaling-self-healing`; kind cluster + podinfo +
  monitoring + ServiceMonitor replayed from committed manifests, unchanged.
- Day-3 baseline **re-captured on the Azure VM**: `data/baseline_metrics.csv` and
  `logs/locust_baseline_stats.csv` now hold the Azure run (1,479 reqs, 0 failures,
  median 2 ms, ~5.7 req/s steady state). The laptop run is superseded but preserved
  in git history (commit d6154ec).
- Container run pattern on the VM: `docker run --rm --network host` with
  `PROMETHEUS_URL=http://localhost:9090` / `LOCUST_HOST=http://localhost:8070`
  env overrides. Linux Docker has no built-in `host.docker.internal`; host
  networking via loopback is simpler and traffic never leaves the VM.

**Why**
The laptop (6 cores, 7.3 GB RAM, Docker Desktop WSL2 VM capped ~3.6 GB) cannot hold
the full Day-13 stack (~4.5 GB); Docker Desktop already crashed once under the
Day-3 load. A second laptop (3.7 GB RAM, 2-core AMD A6) was evaluated and also
failed the bar. `D4as_v5` was chosen over B-series because burstable VMs throttle
under the sustained CPU this project generates (control plane + Prometheus +
Kafka + Locust); its dedicated cores give predictable demo performance, and it is
cheaper per hour than `B4ms`. Azure B-series was quota-blocked for this free
account in India regions; `D4as_v5` was available in Central India.

**Side effect**
- kind node image stays pinned at `kindest/node:v1.30.0` (works fine on cgroup v2;
  preserves reproducibility with Days 1-3).
- Grafana/Prometheus are reached from the laptop via SSH tunnels (`ssh -L`);
  NSG + ufw expose only port 22 publicly.
- kind CLI on the VM is v0.33.0-alpha (upstream `/latest/` resolved to it);
  cluster creation verified healthy — revisit if instability appears.
- VM-side git syncs via `git pull`; commits/pushes happen on the laptop where
  GitHub SSH auth lives.

---

## 2026-08-17 — Python runs inside shared Docker image, not host venv (Day 3)

**What changed**
- Built a shared Docker image `k8-ai-ops:dev` (python:3.11-slim base) at
  `ops/docker/Dockerfile` holding the Python dependencies for the project
  (Days 3, 4, 5, 7, 9, 12). All Python scripts are run via
  `docker run --rm -v ${PWD}:/code -w /code k8-ai-ops:dev ...` instead of a host
  virtual environment.
- `ops/docker/requirements.txt` is pinned to Day-3 deps only
  (prometheus-api-client 0.5.5, requests 2.32.3, locust 2.31.1, pandas 2.2.3,
  numpy 1.26.4). Future days append their own deps as those components come online.

**Why**
Locust 2.44 + gevent on **Python 3.12 Windows** raises `RecursionError` from the
SSL monkey-patch (`ssl._ssl._sslocert_verify`), so the host's preinstalled Python
runtime cannot run Locust. Python 3.11 (slim Debian) inside Docker sidesteps this
entirely and gives a consistent Linux runtime for the rest of the project
(Faust and Kopf officially target 3.10/3.11). One image (~615 MB) is reused by
every later Python service day, so the cost is paid once.

**Side effect**
First-run image build takes ~3-5 min; subsequent script runs reuse the cached
image. Containerised scripts reach host port-forwards via `host.docker.internal`
(the `PROMETHEUS_URL` and `LOCUST_HOST` defaults baked into the code use it).

---

## 2026-08-17 — Locust endpoint fix: /echo -> /api/echo, 2xx accepted (Day 3)

**What changed**
- `locustfile.py` posts to `/api/echo` (not `/echo`).
- Failure check accepts any 2xx (not `== 200`).

**Why**
podinfo's `/echo` is a **WebSocket** endpoint — plain HTTP POSTs are rejected
with 4xx. The HTTP echo API is `/api/echo`, which returns **202 Accepted**
(not 200) with the posted JSON echoed in the body. The first baseline run flagged
100 % of POSTs as failures (314/314) until this was fixed. After the fix: 285
requests, **0 failures**.

**Side effect**
The baseline error-rate metric (`rate(http_requests_total{status=~"5.."}[1m])`)
stayed at 0.0 throughout both runs — the original 4xx failures were correctly
excluded from the 5xx error-rate signal. The metrics pipeline was already sound;
only the Locust request definition was wrong.

---

## 2026-08-16 — Slim monitoring stack (Day 2)

**What changed**
- Used `prometheus-community/kube-prometheus-stack` chart (v88.3.0) with a slim
  `ops/manifests/monitoring-values.yaml` that:
  - Disables **Alertmanager** (we feed an AI pipeline, not human alerts -> ~150 MB saved).
  - Sets memory/CPU limits sized for the 3.6 GB Docker Desktop WSL2 VM.
  - Sets Prometheus retention to 2h, no PVC (emptyDir).
  - Sets Grafana admin password to `admin` (explicit, known).
  - Disables the chart's default alerting/recording Rule groups (less CPU churn).
- Added `ops/manifests/podinfo-service-monitor.yaml` (a `ServiceMonitor` CRD with
  the `release: kube-prometheus-stack` label so Prometheus Operator picks it up)
  that scrapes podinfo's `/metrics` every 15s.

**Why**
- Alertmanager is dead weight for this project (no humans to alert).
- Default chart resources are sized for real clusters and would OOM our VM.
- podinfo's Service needs a `ServiceMonitor` (not legacy annotation scraping)
  because the Prometheus Operator only honors ServiceMonitors/PodMonitors.

**Grafana first-boot needed two fixes** (took iteration during Day 2):
1. **Liveness probe was too aggressive** for Grafana 13.1.3, which spends ~3-4 min
   on FIRST boot installing its "Grafana Apps" resource manager (alerting, playlists,
   advisor, etc.) before HTTP binds port 3000. Default chart probe
   (`initialDelaySeconds=60, failureThreshold=10`) killed the container at ~160s.
   Fix: bumped `grafana.livenessProbe.initialDelaySeconds` to 300 and
   `failureThreshold` to 30 (~8 min total tolerance).
2. **128 Mi memory limit was too tight** for the same init phase - the Go runtime's
   `GOMEMLIMIT` was bound to the pod limit, and the first-run heap spike was OOMKilled
   (exit 137). Fix: bumped Grafana `resources.limits.memory` to 256 Mi (request 128 Mi).

After both fixes Grafana came up `3/3 Running, 0 restarts`. Subsequent boots are much
faster (migrations cached), so the probe headroom has plenty of margin.

**Known Down targets (expected, not a problem)**
Four control-plane scrape targets in the Prometheus `/targets` page report `DOWN`:
- `https://172.18.0.2:10257/metrics` (kube-controller-manager)
- `http://172.18.0.2:2381/metrics` (etcd)
- `http://172.18.0.2:10249/metrics` (kube-proxy)
- `https://172.18.0.2:10259/metrics` (kube-scheduler)

Root cause: kind runs these components with `--bind-address=127.0.0.1`, so they are
only reachable from inside the kind node container, not from the pod network.
**No impact on the AI pipeline**: the metrics we actually need are scraped from
cAdvisor (`container_cpu_usage_seconds_total`), kube-state-metrics
(`kube_deployment_status_replicas_available`), node-exporter, and podinfo's own
`/metrics` - all of which are `UP`.

---

## 2026-08-16 — Workload swap: Sock Shop -> podinfo (Day 1)

**What changed**
- Replaced Weaveworks **Sock Shop** with **stefanprodan/podinfo v6.14.1** as the workload that
  the operator auto-scales and auto-heals.
- Namespace changed from `sock-shop` to `podinfo`.
- Edited in place: `README.md` (root), `tasks/README.md`, `tasks/day-01`,
  `tasks/day-02`, `tasks/day-03`, `tasks/day-06`, `tasks/day-13`.
  (`ops/manifests/sock-shop-*.yaml` deleted; new `ops/manifests/podinfo.yaml` added).

**Why**
1. **RAM ceiling.** Docker Desktop's WSL2 VM is capped at ~3.6 GB on this host. The slim
   5-service Sock Shop subset (front-end + catalogue + catalogue-db + carts + carts-db) was
   already using ~1.1 GB on Day 1 with thin headroom for Prometheus + Kafka (Days 2 & 4).
   podinfo runs at ~30 MB image / ~30 MB RAM for 2 replicas — frees ~1 GB of VM RAM.
2. **Broken UI.** The slim Sock Shop subset renders a **white page** because the front-end
   (Node.js) ships product data as client-side JSON and its hydration depends on services we
   had dropped (user/session/queue-master), so the page errors out instead of painting.
3. **Catalogue-db image dead-ends on this kernel.** The
   `weaveworksdemos/catalogue-db:0.3.0` image (mysql:5.7 from 2016) gets VM-OOMKilled at
   `mysqld --verbose --help` inside the kind node on this WSL2 cgroup-v1 kernel. We worked
   around it once via a modern `mysql:8.0` + extracted seed, but the whole stack is fragile.
4. **Better fit for the thesis.** podinfo is a 6k-star, Apache-2.0, **actively-maintained**
   Go microservice used by CNCF Flux and Flagger for autoscaling and progressive-delivery
   e2e tests and workshops. Citing it is more credible than citing an abandoned 2017 demo.
5. **Built-in fault injection.** podinfo's `POST /fault_injection/enable` makes a single
   replica return HTTP 500 on application endpoints while keeping probes healthy — a clean
   error-rate spike for the anomaly detector (Day 8) and a RAM-light alternative to
   LitmusChaos for the Day 13 auto-heal demo.

**Thesis framing**
*"We evaluate the operator against podinfo, a CNCF-adopted Go microservice benchmark
designed for Kubernetes autoscaling and progressive-delivery workshops (Flux, Flagger)."*

**Impact on later days**
- Day 3 Locust profile changes from browse/cart/orders to hitting `/`, `/api/info`, and `/echo`.
- Day 6 load scenarios unchanged (Baseline / Spike / Steady-high / Idle) but against podinfo.
- Day 13 chaos: now offers two equivalent fault paths (LitmusChaos pod-delete OR podinfo
  built-in fault injection). Either or both can be demonstrated.
- Day 14 evaluation: no change (same HPA-vs-AI-operator comparison, same SLOs).

---

## 2026-08-16 — kind node image pinned to v1.30.0 (Day 1)

**What changed**
`ops/kind/kind-cluster.yaml` pins `kindest/node:v1.30.0` instead of the kind default.

**Why**
The kind default (`kindest/node:v1.36.1`) kubelet **refuses to run on cgroup v1**:
```
kubelet: "kubelet is configured to not run on a host using cgroup v1"
```
The Docker Desktop WSL2 kernel boots in **cgroup v1** (hybrid mode), so the v1.36 kubelet
crash-loops, the API server never comes up, and `kind create cluster` fails during
`wait-control-plane`. v1.30.0 still accepts cgroup v1 and also matches the user's kubectl
client version (`v1.30.0`) — a clean compatibility win.

**Side effect**
[Long-term fix] If the host ever moves to cgroup v2 (newer WSL2 kernel via
`wsl --update`), we can unpin to use the kind default again.

---

## 2026-08-16 — Single-node kind cluster (not 3 nodes)

**What changed**
The cluster runs one control-plane node only (instead of the original 1 control-plane +
2 workers the spec called for). All workloads (podinfo + monitoring + Kafka + Python services)
schedule on that single node.

**Why**
Docker Desktop's WSL2 VM is capped at ~3.6 GB RAM; a 3-node kind cluster failed during
bootstrapping immediately (API server timed out waiting for resources). A single node
schedules everything because kind does not apply a `NoSchedule` taint to control-plane nodes
by default.

**Side effect**
No multi-node scheduling realism in the demo. Acceptable: this project studies scaling/healing
behaviour, not bin-packing. If we ever need it, adding a worker node is one line in
`kind-cluster.yaml`.

---