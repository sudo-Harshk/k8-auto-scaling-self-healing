# SHIELD-AI Viva Demo Guide

> **Print this page. Bring it to the viva.**
> Read it once, then put it on the desk in front of you during the demo.

---

## What you have

| Item | Where it is | What it does |
|---|---|---|
| `k8-auto-scaling-self-healing` repo | `~/k8-auto-scaling-self-healing` | The project (Python + Kafka + TLA+ + K8s manifests) |
| `k8-ai-ops:dev` Docker image | pre-built during bootstrap | Shared Python env (River, Faust, k8s client) |
| `bootstrap.sh` | `~/k8-auto-scaling-self-healing/bootstrap.sh` | The installer you ran on first day |
| `RUN_DEMO.md` | this file | The cheat-sheet you are reading right now |

## Daily commands (set up by bootstrap.sh)

```bash
demo-help     # print this cheat-sheet
demo-quick    # 2-minute highlight run (recommended if time is short)
demo-viva     # 13-minute curated viva demo (for presentation/defense)
demo          # full 30-minute 12-step live demo
demo-reset    # wipe kind cluster + rebuild from scratch (only if demo breaks)
tlac          # just the TLA+ composition theorem (~4 min)
paper         # build + open the IEEE paper PDF
```

After bootstrap, all of these are auto-completed in any new shell.
If a command is "not found", run `source ~/.bashrc`.

---

## 5-minute highlight run (recommended)

Open **Ubuntu 24.04** in your Start menu (or type `wsl` in PowerShell),
then type:

```bash
demo-quick
```

What `demo-quick` does (in order, all pre-recorded or pre-computed):

| Step | What the examiner sees | Source |
|---|---|---|
| 1 | TLA+ safety shield trace | `cat specs/tlc_run_safety_shield.txt` |
| 2 | Composition theorem trace (SHIELD path 53 states, 0 errors) | `cat specs/tlc_run_ml_composition.txt` |
| 3 | ML-only counterexample (proves the shield is necessary) | `cat specs/tlc_run_ml_only_counterexample.txt` |
| 4 | Live audit log (Sep-1 docker-compose run) | `cat logs/operator_actions.log` |
| 5 | Synthetic shield stress audit | `cat logs/safety_audit.log` |
| 6 | N=10 deterministic stats report | `cat results_N10/stats_report.md` |
| 7 | **The strongest single claim:** every number in our paper traces to `evidence-freeze.md` | `python3 scripts/_phase5_audit.py` (expect `SOURCED=56, UNSOURCED=0`) |
| 8 | IEEE paper PDF (5 pages, IEEE conference, 20 refs) | `docs/paper/main.pdf` |

If the examiner asks "show me the formal proof", point to steps 1-3.
If they ask "show me the empirical results", point to steps 4-6.
If they ask "where do the numbers come from", show step 7 — that is the
load-bearing claim that every value in the paper is traceable to a
single source of truth.

---

## 13-minute curated viva demo (`demo-viva`)

Use this for a **live end-to-end walkthrough** that fits in a 15-minute
presentation slot. It demonstrates the actual system running — data flowing,
decisions being made, the safety shield clamping, and self-healing in action.

```bash
make demo-viva
```

The script runs these 10 steps. All are idempotent and have graceful fallbacks.

| Step | What happens | Duration |
|---|---|---|
| 1 | **Pre-flight** — ensure cluster/image/infra/pipeline are all ready | ~30s (cached) |
| 2 | **Pipeline log preview** — 60s of live data flowing (producer → stream → decision → actuator) | ~1 min |
| 3 | **Smoke test** — curl podinfo to verify it responds on localhost:9898 | ~10s |
| 4 | **Live load with decision capture** — 1m baseline + 2m burst + 1m rampdown; prints all captured decisions | **4 min** |
| 5 | **TLC composition theorem** — live TLC (if installed) or pre-recorded trace | ~1 min |
| 6 | **Self-healing** — scale to 0, wait 35s for AI heal decision, restore replicas | ~1.5 min |
| 7 | **Unsafe injection** — prove the shield REJECTS a malicious ML output (replicas=20) | ~30s |
| 8 | **Export figures** — latency/replicas/decisions PNGs + CSVs | ~5s |
| 9 | **Statistical report** — from pre-recorded N=10 comparison CSV | ~5s |
| 10 | **Summary banner** — prints counts observed (decisions / rejections / heals) | instant |

**Total wall-clock: ~10-14 min**

What to look for during step 4 (load phases):
- `shield-ai-decision` log: `action=scale target=N` — ML model prediction
- `shield-ai-actuator` log: `WARNING operator: decision REJECTED by safety shield`
  — proves the TLA+-verified safety shield is actively clamping unsafe actions
- After step 4: replica count from `kubectl get deploy workload-v2`

What to look for during step 5 (TLC):
- `Model checking completed. No error.` — 53 states, 0 violations
- Or the pre-recorded trace if TLC is not installed

What to look for during step 6 (self-healing):
- `action=heal target=N` in the pipeline logs during the 35s wait
- Replica count restores from 0 → 2 after the wait

What to look for during step 7 (unsafe injection):
- `inject_unsafe_decision.py` sends `replicas=20` (beyond MaxReplicas)
- Shield REJECTS with `cooldown_active` or `SafetyMaxReplicas` violation

---

## Full 30-minute 12-step demo (`demo`)

Use this if the examiner specifically asks "show me it running live".

The 12 steps are:

1. `make kind-up` — local Kubernetes cluster (one node, Docker-in-Docker)
2. `make build-image` — builds `k8-ai-ops:dev` (already cached by bootstrap)
3. `make deploy-kafka` — Kafka in KRaft mode, 3 topics pre-created
4. `make deploy-prometheus` — Prometheus + Grafana via kube-prometheus-stack
5. `make deploy-workload` — `workload-v2` Flask + SQLite deployment
6. `make pipeline-up` — docker-compose 4 services (producer, Faust stream, decision engine, actuator)
7. `make load-baseline` — 5 min idle traffic; decisions = `noop`
8. `make load-burst` — 5 min 100 RPS burst; decisions = `scale 2 → 6`
9. `make load-rampdown` — ramp back down; `scale 6 → 2`
10. `make inject-fault` — kill a workload-v2 pod; decision = `heal`; operator recreates
11. `make inject-unsafe` — try `replicas=20`; **Shield rejects with audit log entry**
12. `make export-graphs` — paper figures saved as PNG + CSV

All 12 steps are idempotent. If one fails, fix it and re-run that one
target in isolation.

---

## Recovery

| Symptom | Fix |
|---|---|
| `docker: permission denied` | run `newgrp docker` once (or open a new terminal) |
| `kubectl: command not found` | `source ~/.bashrc` |
| `kind: cluster not found` | `make kind-up` |
| A pipeline step crashed mid-demo | `demo-reset` (wipes cluster, rebuilds image, keeps logs) |
| WSL clock drifted | `wsl --shutdown` then reopen Ubuntu |
| `Cannot connect to Docker daemon` | `sudo service docker start` (older WSL) or `sudo systemctl start docker` (newer WSL with systemd) |

## How to open the paper PDF

```bash
xdg-open ~/k8-auto-scaling-self-healing/docs/paper/main.pdf
```

If `xdg-open` doesn't work (no browser inside WSL), open it in Windows:
```powershell
explorer.exe "$(wsl pwd)\..\k8-auto-scaling-self-healing\docs\paper\main.pdf"
```

Or read the source:
```bash
cat ~/k8-auto-scaling-self-healing/docs/paper/main.tex | head -100
```

## How to show the live audit stream

Open **two** terminals side by side. In one:
```bash
cd ~/k8-auto-scaling-self-healing
tail -f logs/operator_actions.log
```
In the other, trigger a decision:
```bash
make load-burst   # 5 min burst shows continuous shield decisions
```

The examiner sees, line by line, what the safety shield would have
clamped if the ML model proposed an unsafe action.

## How to view the N=10 stats report

```bash
cat ~/k8-auto-scaling-self-healing/results_N10/stats_report.md
```

The report contains a markdown table per (operator, scenario) with
mean and std-dev of `replicas_end` and the violations column. Every row
is **deterministic** (we ran 10 trials per condition and got sigma=0).

For a single JSON view:
```bash
cat ~/k8-auto-scaling-self-healing/results_N10/stats_report.json
```

## Defense deck (20 slides)

The deck is in the repo:
```bash
xdg-open ~/k8-auto-scaling-self-healing/defense_deck.pdf
```

If you need to rebuild it:
```bash
cd ~/k8-auto-scaling-self-healing
python3 scripts/build_deck.py --output defense_deck.pdf
```

## Viva room checklist

- [ ] Ubuntu 24.04 LTS terminal open (or RDP/SSH session)
- [ ] Demonstrator warm-up: `make pipeline-up` + `tail -f logs/operator_actions.log` (10 min)
- [ ] Print copy of this cheat-sheet
- [ ] Print copy of `docs/VIVA_GAUNTLET.md` (the 20 questions)
- [ ] Internet not required once booted (everything is on disk after bootstrap)
- [ ] If port `9090` (Prometheus) or `3000` (Grafana) is needed: run the
  `kubectl -n monitoring port-forward ...` commands from `README.md`

## If something breaks mid-viva

1. Stay calm. The artifacts are committed in the repo (TLC traces,
   audit logs, stats report). Even if the cluster dies, the **paper
   claims** still hold because every number in `docs/paper/main.pdf`
   is reproducible from `evidence-freeze.md`.

2. Run `demo-reset` (rebuilds kind cluster, keeps logs).

3. If `demo-reset` also fails:
   ```bash
   cd ~/k8-auto-scaling-self-healing
   make reset        # wipes cluster + image
   make bootstrap    # rebuilds image, re-creates kind
   ```

4. If even `make reset` fails: lean on `demo-quick` (uses pre-recorded
   traces; doesn't need a running cluster at all).

5. Last resort: open `docs/paper/main.pdf` and walk through the
   sections verbally. The paper is **self-contained evidence** —
   the live demo is icing on the cake, not the cake.

---

## Author

This guide was written by `sudo-Harshk <[YOUR_EMAIL]>` as
part of the SHIELD-AI M.Tech project. See `LICENSE` and
`evidence-freeze.md` for the chain of custody on every claim.
