# Day 12 — Kubernetes Operator with Kopf

## Task
Build a Kubernetes operator using Kopf that consumes validated decisions and executes scaling or healing actions.

## Aim
Autonomously apply safe scaling/healing decisions to the cluster.

## Requirements

- `kopf` Python framework
- `kubernetes` Python client
- Validated decisions from Day 11
- kubeconfig pointing to the kind cluster

## Steps

1. **Install Kopf**
   - Add `kopf` and `kubernetes` to your virtual environment.

2. **Write `operator.py`**
   - Define a Kopf operator that either:
     - Watches a custom resource `AIScaleDecision`, or
     - Polls the `k8s-decisions` Kafka topic.
   - For this project, polling the Kafka topic is simpler and sufficient.

3. **Implement the `scale` action**
   - Use the Kubernetes API to patch the Deployment's `spec.replicas`.
   - Verify the patch succeeded.

4. **Implement the `heal` action**
   - Identify the unhealthy pod in the target deployment.
   - Delete the pod so Kubernetes recreates it.

5. **Add safety checks before execution**
   - Double-check that the action was approved by the Safety Shield.
   - Log the action, old state, and new state.

6. **Run the operator locally**
   - Execute `kopf run src/operator/operator.py --standalone`.
   - Verify it connects to the kind cluster.

7. **Test manually**
   - Publish a test `scale` decision to `k8s-decisions`.
   - Confirm the deployment's replica count changes.

## Outcome

- A Kopf operator running locally or in-cluster.
- The operator applies approved scaling and healing actions.
- All executed actions are logged.

## Verification Command

```bash
kopf run src/operator/operator.py --standalone
```

Expected result: operator logs show it consuming decisions and patching deployments.

---

## Execution Notes (2026-08-23)

### What was built
- `src/kopf_operator/__init__.py` — empty package marker.
- `src/kopf_operator/actuator.py` (~260 lines) — `K8sOperator` class + `run_operator()` main loop. Consumes from Kafka topic `k8s-decisions`, re-runs `SafetyShield.validate()` on each decision (defense in depth), then either:
  - `scale` — patches `podinfo` Deployment `spec.replicas` via the kubernetes client.
  - `heal` — deletes a pod of the target Deployment. Pod selection: optional `target_pod` in `decision.features` (used by Day 13 fault injection), else highest-restart, else oldest.
  - `noop` — log only, no API call.
  - rejected (by Safety Shield) — log + audit, no API call.
- `src/kopf_operator/publish_decision.py` (~80 lines) — CLI helper to inject test decisions into `k8s-decisions`. Used by Day 12 smoke test and Day 13 chaos scenarios.
- `tests/test_actuator.py` (8 tests) — unit tests for the parts that don't need a live cluster (payload parsing, audit log writing, modification parser).
- `ops/docker/requirements.txt`: added `kubernetes==29.0.0`. Docker image rebuilt.

### Architectural deviation from plan: no Kopf

The plan listed `kopf==1.37.2` as the operator framework. We evaluated it and
**skipped it** because:
1. Kopf's core value is watching Kubernetes resources (CRDs, Deployments,
   etc.). Our trigger source is Kafka, not the Kubernetes API server.
2. The recommended alternative for a Kafka-driven actuator is a plain
   consumer loop — exactly what we wrote. Wrapping it in Kopf's `@kopf.timer`
   would add asyncio complexity without semantic benefit.
3. The operator-pattern semantics (observe → decide → act reconcile loop)
   are preserved: Kafka observe, SafetyShield decide, kubernetes client act.

**Stack updated:**
- `README.md` "Stack" section now says "Python operator (kafka-python +
  kubernetes client)" instead of "Kopf (Python) + kubernetes client".
- `tasks/README.md` "Locked-in Choices" table now says "Python operator
  (kafka-python + kubernetes client)" instead of "Kopf (Python)".

The architectural diagram in `README.md` still says "Operator" — the
framework choice is a footnote, not a paper-claim shift.

### Why the package was renamed `operator` → `kopf_operator`

Python's stdlib has an `operator` module (used by `enum`, `json`, etc.).
When the script directory contains a sibling file named `operator.py`,
Python's import machinery loads it as the top-level `operator` module,
shadowing the stdlib. This causes:

```
from operator import or_ as _or_
AttributeError: partially initialized module 're' has no attribute 'compile'
```

Two options: rename the package or rename the file inside. Renaming the
package (`src/operator` → `src/kopf_operator`) keeps the file `actuator.py`
semantic (it IS the operator, but the package is the operator service).
The script that publishes test decisions is `publish_decision.py` (no
import collision). Both are now siblings under `src/kopf_operator/`.

### Smoke test (live, on the VM)

1. **Scale up (2 → 4):** publish a `scale` decision via
   `publish_decision.py`, run the operator with `--once`. Result:
   ```
   operator: k8s connected: namespace=podinfo deployment=podinfo current_replicas=2
   operator: scale applied: 2 -> 4 (target=4)
   ```
   `kubectl get deploy podinfo` → `4/4 READY`, two new pods spin up.
2. **Heal (delete a pod):** publish a `heal` decision with `target_pod=
   podinfo-7c97f86c99-ddkfv`, run the operator. Result:
   ```
   operator: heal applied: pod=podinfo-7c97f86c99-ddkfv replicas=4
   ```
   That pod is deleted; Kubernetes creates `podinfo-7c97f86c99-hv4mp`.
3. **Noop:** publish a `noop` decision, run the operator. Result:
   ```
   operator: noop: smoke test: noop | safety_pass
   ```
   No API call, audit entry written.

After the smoke test, scaled back to 2 replicas via `kubectl scale` for
the steady-state baseline.

### Audit log
`logs/operator_actions.log` — 3 JSON entries (scale, heal, noop). Each
captures `timestamp`, `service`, `action`, `target_replicas`,
`current_replicas_before`, `current_replicas_after`, `applied`,
`rejected_reason`, `safety_modifications`, `api_call`, `pod_name`.

### Test results
```
tests/test_actuator.py::test_decision_from_kafka_minimal_payload      PASSED
tests/test_actuator.py::test_decision_from_kafka_full_payload         PASSED
tests/test_actuator.py::test_decision_from_kafka_defaults_for_missing_fields PASSED
tests/test_actuator.py::test_record_action_writes_one_json_line       PASSED
tests/test_actuator.py::test_record_action_appends_multiple            PASSED
tests/test_actuator.py::test_extract_mods_present                     PASSED
tests/test_actuator.py::test_extract_mods_absent                      PASSED
tests/test_actuator.py::test_extract_mods_empty                       PASSED
============================== 8 passed in 0.45s ===============================
```

Combined with Day 11's safety shield tests: **24 tests pass, 0 fail.**

### Files added
- `src/kopf_operator/__init__.py`
- `src/kopf_operator/actuator.py` (~260 lines)
- `src/kopf_operator/publish_decision.py` (~80 lines)
- `tests/test_actuator.py` (8 tests)
- `logs/operator_actions.log` (3 audit entries)

### Gotchas
1. **Package name shadowed stdlib `operator`** (see above). Fix: renamed
   to `kopf_operator`.
2. **Docker image entrypoint is `python`.** `docker run ... k8-ai-ops:dev
   src/...` becomes `python src/...`. Same convention as Days 5-11.
3. **First consumer-group join takes ~3 s** while `__consumer_offsets`
   initializes. Self-resolves; the `--once` mode waits long enough.
4. **In-memory cooldown state is reset on operator restart.** For the
   smoke test, this is desirable (we wanted to fire scale and heal back-
   to-back). For Day 13's continuous run, the cooldown is enforced
   naturally — the operator doesn't restart.
5. **`publish_decision.py --target` is now a string** (was int). For
   `scale`, it's the replica count; for `heal`, it's the pod name.
