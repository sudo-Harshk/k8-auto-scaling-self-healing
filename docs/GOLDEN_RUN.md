# Golden Run — 12-Step Deterministic Demo

> **Purpose:** one repeatable sequence a reviewer can run on a fresh machine
> and reproduce every claim in the paper. This is the artifact submitted
> alongside `docs/paper/main.pdf`.

## Prereqs

- Docker CE (or Podman + kind-compatible)
- `kind`, `kubectl`, `helm`, `docker compose`
- 8 GB RAM minimum
- Network access (pulls Kafka, Prometheus, workload-v2 images)

## The 12 steps

| # | Action | Command | Verifies |
|---|--------|---------|----------|
| 1 | Create `kind` cluster | `make kind-up` | Single-node K8s cluster `k8-ai` |
| 2 | Build shared image | `make build-image` | `k8-ai-ops:dev` (Python 3.11-slim, River 0.26.0, Faust 0.11.3) |
| 3 | Deploy Kafka (KRaft) | `make deploy-kafka` | Kafka cluster, topics `k8s-metrics`, `k8s-features`, `k8s-decisions` |
| 4 | Deploy Prometheus + Grafana | `make deploy-prometheus` | ServiceMonitor for workload-v2 |
| 5 | Deploy workload-v2 | `make deploy-workload` | 2 healthy replicas, `/metrics` endpoint |
| 6 | Start pipeline via docker compose | `make pipeline-up` | Producer + Faust + Decision + Operator all running |
| 7 | Baseline traffic (5 min) | `make load-baseline` | p95 stable, decisions = `noop` |
| 8 | Burst (5 min, ramp) | `make load-burst` | decisions = `scale` 2 → N (verified via `kubectl get deploy`) |
| 9 | Ramp down | `make load-rampdown` | decisions = `scale` N → 2 |
| 10 | Inject pod fault | `make inject-fault` | decision = `heal` (anomaly_score > 2 × threshold), operator deletes pod, K8s recreates |
| 11 | Rejected-unsafe-action test | `make inject-unsafe` | Decision engine emits `replicas=20`, Shield rejects with audit log line |
| 12 | Export artifacts | `make export-graphs` | Latency/replicas/decisions PNG + CSV in `results_N10/` |

## Quick path

```bash
make tla                  # ~3 s — TLC on SafetyShield.tla
make tla-composition      # ~4 min — TLC on ML_Composition.tla
make paper                # IEEE PDF (pdflatex + bibtex + pdflatex x2)
make demo                 # ~30 min — all 12 steps end-to-end
make eval                 # ~3 h — N=10 deterministic offline replay
make stats                # ~10 s — regenerate results_N10/stats_report.md
```

## What each step proves (for the viva)

1. **`kind-up`** — system is self-contained, no Azure dependency.
2. **`build-image`** — same Python 3.11 env as production, no host pollution.
3. **`deploy-kafka`** — bus is real Kafka, not in-memory mock.
4. **`deploy-prometheus`** — metrics are real Prometheus, not synthetic.
5. **`deploy-workload`** — workload is a real DB-backed Flask microservice with a Prometheus `/metrics` endpoint.
6. **`pipeline-up`** — all four docker-compose services (`shield-ai-producer`, `shield-ai-stream`, `shield-ai-decision`, `shield-ai-actuator`) actually start.
7. **`load-baseline`** — system does nothing when nothing is needed.
8. **`load-burst`** — **autoscaling works** (the P1 fix).
9. **`load-rampdown`** — autoscaling is not a one-way ratchet.
10. **`inject-fault`** — **self-healing works**.
11. **`inject-unsafe`** — **safety shield blocks unsafe ML output** (the strongest contribution).
12. **`export-graphs`** — paper figures are reproducible, not hand-drawn.

## What each step leaves in the repo

| Step | Artefact (committed for verification) |
|------|----------------------------------------|
| 1    | `kind` cluster state (ephemeral, on host) |
| 2    | `k8-ai-ops:dev` Docker image (in kind) |
| 3    | Kafka KRaft cluster + 3 topics |
| 4    | Prometheus + Grafana + ServiceMonitor |
| 5    | `workload-v2-*` Deployments in ns `workload-v2` |
| 6    | 4 docker-compose services running |
| 7-9  | `logs/decisions.log` + `logs/operator_actions.log` |
| 10   | `logs/safety_audit.log:1-28` (28 synthetic entries) |
| 11   | `logs/safety_audit.log` rejection rows |
| 12   | `results_N10/` directory (CSV + JSON) |

## Failure mode handling

- If any step fails, `make demo` halts and prints the failing log.
- `make reset` cleans up to a known state (deletes cluster, images, volumes).
- All run output is captured to `logs/demo_<timestamp>/` for postmortem.

## On the student's Windows machine (WSL2 path)

For a student running the demo locally on a 16 GB Windows laptop
without any pre-installed dev tools:

1. **One PowerShell command (admin):** `wsl --install -d Ubuntu-24.04`
   then reboot.

2. **One bootstrap line inside the WSL Ubuntu shell:**
   ```bash
   curl -fsSL https://raw.githubusercontent.com/sudo-Harshk/k8-auto-scaling-self-healing/main/bootstrap.sh | bash
   ```
   Installs Docker CE + kubectl 1.30 + kind 0.23 + helm 3 +
   OpenJDK 17, clones the repo, pre-builds `k8-ai-ops:dev`, and adds
   demo aliases to `~/.bashrc`. ~15 min, unattended, idempotent.

3. **Pin WSL2 RAM** so the 12-step demo has headroom (in
   `%UserProfile%\.wslconfig`):
   ```ini
   [wsl2]
   memory=11GB
   processors=4
   swap=4GB
   ```
   Then `wsl --shutdown` and reopen Ubuntu.

4. **Demo:**
   ```bash
   demo-help     # print RUN_DEMO.md
   demo-quick    # 2-min highlight (TLC traces + paper + audit + stats)
   demo          # full 30-min 12-step live demo
   demo-reset    # rebuild cluster + image
   ```

5. **Recovery** — if `make demo` mid-step crashes:
   ```bash
   cd ~/k8-auto-scaling-self-healing
   make reset        # wipe kind cluster + image cache
   make bootstrap    # rebuild image, leave cluster up
   ```
   If even that fails, `demo-quick` works without a running cluster
   (uses pre-recorded TLC traces and committed logs).

See `RUN_DEMO.md` for the printable single-page cheat-sheet the
student brings to the viva.

## Exact reproducibility checks

The following commands verify the paper claims from scratch on a fresh
clone:

```bash
# 1. Confirm every number in the paper traces to evidence-freeze.md
python scripts/_phase5_audit.py
#   expected: SOURCED=57, UNSOURCED=0

# 2. Confirm 53/53 unit tests pass on the laptop
pip install kafka-python kubernetes
python -m pytest tests/ -q --tb=line
#   expected: 53 passed

# 3. Confirm TLC safety guards are clean
ssh k8-vm 'cd ~/k8-auto-scaling-self-healing && make tla && make tla-composition'
#   expected: 0 errors, 0 violated invariants

# 4. Rebuild the IEEE paper
ssh k8-vm 'cd ~/k8-auto-scaling-self-healing/docs/paper && pdflatex main && bibtex main && pdflatex main && pdflatex main && pdfinfo main.pdf | grep Pages'
#   expected: Pages: 5

# 5. Regenerate the defense deck
python scripts/build_deck.py --output defense_deck.pdf
#   expected: "Wrote defense_deck.pdf (20 slides)"
```

If any of these fail, the project is not ready for defense.
