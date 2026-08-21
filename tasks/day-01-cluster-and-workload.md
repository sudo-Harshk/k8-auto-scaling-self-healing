# Day 1 — Cluster & Workload Deployment

## Task
Set up a local Kubernetes cluster and deploy the podinfo microservice benchmark.

## Aim
Have a running multi-service application that can be scaled and broken during the project.

## Requirements

- Docker (laptop: Docker Desktop with WSL2 backend on Windows; canonical from Day 4: Azure VM with Docker CE)
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

---

## Execution Notes (2026-08-16)

### Initial build (laptop, Docker Desktop + WSL2)
- kind cluster created with the single-node control-plane config
  (`ops/kind/kind-cluster.yaml`); `kindest/node:v1.30.0` pinned because the
  kind default `v1.36.1` kubelet refuses to run on cgroup v1. See
  `tasks/AMENDMENTS.md` (2026-08-16).
- Single-node cluster (not the plan's 1+2 workers) because Docker Desktop's
  WSL2 VM is capped at ~3.6 GB RAM; a 3-node cluster failed during
  bootstrapping. Single-node is fine because kind does not taint control
  planes by default. See `tasks/AMENDMENTS.md` (2026-08-16).
- Podinfo deployed via `ops/manifests/podinfo.yaml` in the `podinfo` namespace;
  2 replicas (visible scaling target).
- Workload swap from the plan's Sock Shop to podinfo (see `tasks/AMENDMENTS.md`
  2026-08-16): podinfo is ~30 MB RAM vs ~1.1 GB for the slim Sock Shop
  subset, ships active `/metrics` + `/fault_injection/enable`, and is the
  CNCF/Flux/Flagger benchmark — better for the thesis.

### Migration to Azure VM (canonical from Day 4)
After Day 3, the canonical environment moved to Azure `Standard_D4as_v5`
(4 vCPU AMD / 16 GB RAM), Ubuntu 24.04 LTS, cgroup v2. The podinfo
manifests replayed unchanged on the new cluster. See
`tasks/AMENDMENTS.md` (2026-08-18) for the full migration rationale.

### Live state at audit (2026-08-21)
```
NAME                       READY   STATUS    RESTARTS      AGE
podinfo-7c97f86c99-js8tb   1/1     Running   1 (67m ago)   2d11h
podinfo-7c97f86c99-wj6nw   1/1     Running   1 (67m ago)   2d11h
```
Both pods `1/1 Running` on the VM cluster.
