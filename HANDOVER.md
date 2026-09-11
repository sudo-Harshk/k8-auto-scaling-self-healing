# HANDOVER — Receiving the SHIELD-AI Project

> Read this once. It is the shortest path from "new laptop" to "running demo".

## What you are receiving

A working M.Tech project: a Kubernetes operator that combines online ML
(River HTR + Half-Space-Trees anomaly detector) with a TLA+-verified
safety shield. TLA+ TLC explored **273,702** reachable states and found
**zero** safety violations. **53/53** unit tests pass. Every paper claim
traces to `evidence-freeze.md` (audit script confirms **56 sourced, 0
unsourced**).

This is the final `v1.0-handover` release. Tagged commit on `main`.

---

## Prerequisites (verify these BEFORE running the installer)

| Check | How to verify |
|---|---|
| Windows 11 with WSL2 enabled | `wsl --status` in PowerShell |
| Ubuntu 24.04 LTS in WSL2 | Microsoft Store: "Ubuntu 24.04" |
| 16 GB RAM (8 GB works but tight) | Task Manager → Performance → Memory |
| Outbound HTTPS allowed | Try `curl -fsSL https://github.com` |
| sudo rights in Ubuntu shell | `sudo -v` (should not ask a password) |

If you are NOT on Windows + WSL2, see "Alternative environments" below.

---

## Install (one command, ~15-20 min)

Open **Ubuntu 24.04** from the Start menu (or type `wsl` in PowerShell),
then run:

```bash
curl -fsSL https://raw.githubusercontent.com/sudo-Harshk/k8-auto-scaling-self-healing/main/bootstrap.sh | bash
```

When the script says **"Bootstrap complete!"**:

- **WSL2 users**: open a **new** terminal, then run `wsl --shutdown` ONCE
  so systemd starts docker on the next boot.
- **Native Linux users**: log out and back in (or run `newgrp docker`).

---

## Verify install (10 checks, ~2 min)

In a fresh terminal, run each of these. Every one should succeed.

```bash
docker run hello-world             # 1. docker daemon + group membership
kubectl version --client --short   # 2. kubectl 1.30.x
kind version                       # 3. kind 0.23.x
helm version --short               # 4. helm 3.x
java -version 2>&1 | head -1       # 5. OpenJDK 17
ls /tmp/tla2tools.jar              # 6. (TLC is bundled in repo, OK if missing here)

cd ~/k8-auto-scaling-self-healing  # 7. the repo is here
docker image inspect k8-ai-ops:dev >/dev/null  # 8. Python image pre-built
kind get clusters                  # 9. (empty is fine; bootstrap doesn't auto-create)

python3 scripts/_phase5_audit.py | grep -E "SOURCED|UNSOURCED"
# 10. expect: SOURCED=56, UNSOURCED=0
```

If any check fails, see "Troubleshooting" below.

---

## Daily demo commands

After `bootstrap.sh` adds aliases to `~/.bashrc`, these work in any new shell:

| Command | What it does | Time |
|---|---|---|
| `demo-help` | Print the cheat-sheet (`RUN_DEMO.md`) | instant |
| `demo-quick` | 2-min highlight run (TLC traces + paper + audit logs + stats) | 2 min |
| `demo` | Full 15-min live demo (12-step golden run on a fresh kind cluster) | 15 min |
| `demo-reset` | Wipe kind cluster + rebuild image from scratch | 5 min |
| `tlac` | Re-run just the TLA+ composition theorem (TLC only) | 4 min |
| `paper` | Build + open the IEEE paper PDF | 30 s |

If a command is "not found", run `source ~/.bashrc` once.

---

## Recommended first-week plan

| Day | Action | Time |
|---|---|---|
| **Day 0** | Run the install, then run the 10 verify checks | 20 min |
| **Day 1** | Run `demo-quick` to see all 8 evidence sections print out | 2 min |
| **Day 2** | Run `demo` end-to-end on a fresh cluster; read the audit log | 20 min |
| **Day 3** | Open `docs/VIVA_GAUNTLET.md` (20 viva questions) and `evidence-freeze.md` | 30 min |
| **Day 4** | Read `docs/paper/main.pdf` (5 pages); trace every number back to evidence-freeze | 45 min |
| **Day 5** | Re-run the audit: `python3 scripts/_phase5_audit.py`. Expect 57/0 | 1 min |
| **Day 6** | Run `pytest` from the repo root. Expect 53/53 | 1 min |
| **Day 7** | Open the landing page locally: `cd landing-page && npm install && npm run dev` | 5 min |

---

## Repo layout (top-level)

```
k8-auto-scaling-self-healing/
├── LICENSE                 # MIT
├── HANDOVER.md             # this file
├── CONTRIBUTING.md         # dev workflow
├── CHANGELOG.md            # version history
├── README.md               # full pipeline + 7-step verify
├── RUN_DEMO.md             # viva cheat-sheet
├── GOLDEN_RUN.md           # 12-step golden run
├── bootstrap.sh            # one-command installer
├── evidence-freeze.md      # SINGLE SOURCE OF TRUTH for paper claims
├── Makefile                # demo, build-image, tla, paper, deck, ...
├── conftest.py             # pytest config
├── locustfile.py           # traffic for the 12-step demo
├── data/                   # models, training data, replays
├── docs/                   # paper, thesis, defense deck, viva prep
├── landing-page/           # React + Vite + Tailwind public site
├── logs/                   # audit logs (operator_actions, safety_audit, decisions)
├── ops/                    # kind cluster, Kafka, Prometheus, workload manifests
├── results_N10/            # N=10 deterministic evaluation
├── scripts/                # demo, eval, audit, bootstrap helpers
├── specs/                  # TLA+ SafetyShield.tla, ML_Composition.tla, configs
├── src/                    # Python: kafka, streaming, decision, kopf_operator, ...
├── tasks/                  # THESIS.md, AMENDMENTS.md, milestones
└── tests/                  # 53 pytest cases
```

---

## Development workflow (after the viva)

1. **Never edit a paper number without also updating `evidence-freeze.md`.**
   The audit script (`scripts/_phase5_audit.py`) cross-checks every number
   in `docs/paper/main.tex` against `evidence-freeze.md`. If they diverge,
   the script reports `UNSOURCED > 0` and the build is broken.

2. **Branch for new work.** Keep `main` deployable. Use `feature/...` or
   `fix/...` branches. The handover tag is `v1.0-handover`.

3. **Run tests + audit before every commit.**
   ```bash
   pytest                    # expect 53 passed
   python3 scripts/_phase5_audit.py   # expect SOURCED=56, UNSOURCED=0
   ```

4. **TLC re-runs are slow but deterministic.** A full SafetyShield.tla run
   takes ~4 min; the composition spec takes ~1 s. The pre-recorded traces
   in `specs/tlc_run_*.txt` are the canonical evidence.

5. **Update `CHANGELOG.md`** for every user-visible change.

See `CONTRIBUTING.md` for the full contribution guide.

---

## Customization points

| File | What you can change safely |
|---|---|
| `specs/safety_policy.yaml` | Cooldown seconds, max scale step, min/max replicas |
| `specs/SafetyShield.cfg` | TLC constants (MinReplicas, MaxReplicas, MaxScaleStep, CooldownTicks) |
| `src/decision/decision_engine.py` | ML thresholds, model paths, anomaly detector |
| `data/*.pkl` | Re-train models (`scripts/retrain_canonical.sh`) |
| `Makefile` | Add new operators, scenarios, or demo targets |

**Do not** edit `evidence-freeze.md` without also re-running the audit and
updating `docs/paper/main.tex` consistently.

---

## Known limitations

- **N=10 evaluation is deterministic** (σ = 0 throughout). The paper
  documents this in Threats §1.3. Wilcoxon p and Cohen's d are not
  informative; we report them for completeness.
- **The kind cluster runs on Docker-in-Docker.** It is not a production
  cluster and is not safe to expose externally.
- **The TLA+ specs are simplified abstractions** of the real Python
  controller. They are sufficient to prove the invariants hold; they are
  not a 1:1 implementation.
- **Single-developer project.** No CI, no PR review process. See
  `CONTRIBUTING.md` for the minimum bar.

---

## Troubleshooting (5 escalation paths)

| Symptom | First try | Then try | Then try |
|---|---|---|---|
| `docker: permission denied` | `newgrp docker` | Log out and back in | Reboot WSL: `wsl --shutdown` |
| `kubectl: command not found` | `source ~/.bashrc` | Re-open terminal | Re-run `bash bootstrap.sh` |
| `kind: cluster not found` | `demo` (creates + runs) | `make kind-up` | `demo-reset` |
| Pipeline containers crash-loop | `pkill -f "kubectl.*port-forward"` then re-run | `demo-reset` | See "Advanced recovery" below |
| Demo totally broken | `demo-quick` (no cluster needed) | Open `docs/paper/main.pdf` | See "Advanced recovery" below |

### Advanced recovery (last resort)

```bash
cd ~/k8-auto-scaling-self-healing
git fetch --tags
git checkout v1.0-handover
bash bootstrap.sh          # re-runs idempotently
demo-quick                 # 2-min verify
```

If even this fails, the **paper claims are still true** because they are
reproducible from the committed `evidence-freeze.md` and `specs/tlc_run_*.txt`
files. Open `docs/paper/main.pdf` and walk the examiner through the
sections verbally.

---

## Alternative environments

This repo targets **Windows 11 + WSL2 + Ubuntu 24.04**. It also works on:

- **Native Ubuntu 24.04** (bare metal, dual-boot, or cloud VM): same
  `bootstrap.sh`. Skip the WSL branch (the script auto-detects and skips
  `systemd=true` configuration if not on WSL).
- **macOS**: needs minor bootstrap changes (`brew` instead of `apt`,
  OrbStack / Colima instead of Docker Desktop). Not officially supported
  in `v1.0-handover`; see `CONTRIBUTING.md` for how to add a Mac branch.

---

## Contact

For questions about the project, contact the original author at the
email in the repo header (replace `[YOUR_EMAIL]` in this file with the
maintainer's actual address).

For bugs, open an issue at
`https://github.com/sudo-Harshk/k8-auto-scaling-self-healing/issues`.

---

## Author

Written as part of an M.Tech project handoff. See `LICENSE` (MIT) and
`evidence-freeze.md` for the chain of custody on every claim in the
attached paper.
