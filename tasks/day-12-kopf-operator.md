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
