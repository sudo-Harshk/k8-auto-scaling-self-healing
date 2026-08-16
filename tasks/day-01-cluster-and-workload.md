# Day 1 — Cluster & Workload Deployment

## Task
Set up a local Kubernetes cluster and deploy the podinfo microservice benchmark.

## Aim
Have a running multi-service application that can be scaled and broken during the project.

## Requirements

- Docker Desktop (with WSL2 backend on Windows)
- [kind](https://kind.sigs.k8s.io/docs/user/quick-start/)
- kubectl
- Helm 3
- Internet access to pull images

## Steps

1. **Install kind and kubectl**
   - Verify with `kind version` and `kubectl version --client`.

2. **Create a kind cluster**
   - Use a single control-plane node configuration (Docker Desktop WSL2 VM caps RAM at ~3.6 GB; pods schedule on the control-plane because kind does not taint it).

3. **Verify cluster health**
   - Run `kubectl get nodes` and confirm the node is `Ready`.

4. **Deploy podinfo**
   - Apply `ops/manifests/podinfo.yaml` to the `podinfo` namespace.
   - The Deployment runs 2 replicas so scaling is immediately visible.

5. **Verify the deployment**
   - Run `kubectl get pods -n podinfo` and wait until both pods are `Running`.
   - Check the service with `kubectl get svc -n podinfo`.

6. **Access the UI**
   - Use `kubectl -n podinfo port-forward svc/podinfo 8070:9898`.
   - Open `http://localhost:8070` in a browser; the podinfo page loads and the browser tab title shows the serving pod's hostname.
   - To verify both replicas round-robin, run from inside the cluster: `kubectl run curltest --rm -i --restart=Never --image=curlimages/curl --command -- sh -c "for i in 1 2 3 4 5 6; do curl -s http://podinfo.podinfo:9898/api/info; echo; done"`.

## Outcome

- A local kind Kubernetes cluster is running.
- podinfo is deployed with 2 healthy replicas.
- You can access the podinfo UI from your browser.
- `kubectl get pods -n podinfo` shows both pods Ready.

## Verification Command

```bash
kubectl get pods -n podinfo
```

Expected result: 2 pods show `Running` and `READY` columns `1/1`.
