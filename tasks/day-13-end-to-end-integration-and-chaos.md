# Day 13 — End-to-End Integration & Chaos Testing

## Task
Wire all components together and test auto-scaling under load and auto-healing under injected faults.

## Aim
Prove the complete pipeline works as designed.

## Requirements

- All components from Days 1–12 running
- LitmusChaos installed in the cluster (fallback: podinfo's built-in `/fault_injection/enable` endpoint, which makes a single replica return HTTP 500 on application endpoints while probes stay healthy — RAM-light alternative to LitmusChaos)
- Locust load generator
- Grafana and Prometheus dashboards open

## Steps

1. **Start the full pipeline**
   - Ensure Prometheus, Kafka, Faust processor, decision engine, Safety Shield, and operator are all running.
   - Confirm producer is sending metrics to Kafka.

2. **Run a Locust spike test**
   - Ramp users quickly to create load on podinfo.
   - Watch Grafana for CPU and request rate increases.
   - Verify the operator scales up the podinfo deployment.

3. **Run a steady high-load test**
   - Hold 50–100 users for 10 minutes.
   - Verify replicas stabilize at a higher count.
   - Verify SLOs are maintained.

4. **Inject a fault**
   - Either run a LitmusChaos `pod-delete` or `CPU-hog` experiment on a podinfo replica, or POST to `/fault_injection/enable` on a single replica to make it return HTTP 500 (probes stay healthy, so the pod stays in the endpoints set while the error rate climbs).
   - Verify anomaly detection flags the issue.
   - Verify the operator heals the service (restarts/deletes the sick pod).

5. **Capture evidence**
   - Take Grafana screenshots.
   - Save operator logs.
   - Save decision logs.
   - Record a short demo if possible.

6. **Fix any broken links**
   - If a component fails, debug and reconnect it.

## Outcome

- A working end-to-end demo of auto-scaling and auto-healing.
- Grafana screenshots and logs proving the system responded correctly.
- A list of any issues found and fixed.

## Verification

Run:

```bash
kubectl get deployments -n podinfo
kubectl logs -f <operator-pod>
```

Expected result: deployment replicas change during load; pods are recreated during chaos.
