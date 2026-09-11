# v1.0-handover — Project Handover Release

**Release date:** 2026-09-11
**Tag:** `v1.0-handover` (pinned at commit `70ad8ea`)
**License:** MIT
**Status:** ✅ Stable — recommended state for new recipients

---

## TL;DR

This is the final commit by the original author (`sudo-Harshk`). The repository is ready for handover. A new recipient can install everything on a fresh Windows 11 + WSL2 Ubuntu 24.04 machine in 30–45 minutes using a single command.

**Install:**
```bash
curl -fsSL https://raw.githubusercontent.com/sudo-Harshk/k8-auto-scaling-self-healing/main/bootstrap.sh | bash
```

**Verify (2 min):**
```bash
demo-quick
```
Expect: `SOURCED=56, UNSOURCED=0`

---

## What this release contains

### New files (handover package)
- **`LICENSE`** — MIT license, copyright 2026 sudo-Harshk
- **`HANDOVER.md`** (10 sections, 270 lines) — comprehensive day-0 receiving guide
- **`RECIPIENT_SETUP.md`** (9 steps, 416 lines) — clean step-by-step setup from zero
- **`PROJECT_EXPLAINED.md`** (10 sections, 618 lines) — what every component is, does, contributes
- **`CONTRIBUTING.md`** (85 lines) — development workflow and PR checklist
- **`CHANGELOG.md`** (95 lines) — version history

### Changed files (paper-closure + email placeholder)
- 8 file edits replacing personal email `harshk1744@gmail.com` with `[YOUR_EMAIL]` placeholder
- 1 LaTeX fix: escape underscore in `[YOUR_EMAIL]`
- 20 references to `SOURCED=57` updated to `SOURCED=56` (the `1744` digit sequence in the email was a counted literal)
- `docs/paper/main.pdf` rebuilt (5 pages, 253 KB)
- Landing page rebuilt (`landing-page/dist`, 0 TS errors, 0 warnings)

### The locked contracts

| Contract | Value | How to verify |
|---|---|---|
| Paper claims audit | **SOURCED=56, UNSOURCED=0** | `python3 scripts/_phase5_audit.py` |
| Unit tests | **53/53 passing** | `pytest` |
| TLA+ safety shield | **273,702 states, 0 violations** | `make tla` |
| TLA+ composition | **53 states, 0 violations** | `make tla-composition` |
| ML-only counterexample | **93 states, depth 4, MlSafetyMinReplicas violated** | `make tla` (separate config) |
| Shield stress audit | **12 of 28 = 42.9%** | `head -28 logs/safety_audit.log` |
| N=10 evaluation | **4 operators × 3 scenarios × 10 trials = 120 runs, σ=0** | `cat results_N10/stats_report.md` |

---

## What's NOT in this release (deliberately)

- No production deployment (single-node kind cluster, deterministic N=10)
- No CI/CD pipeline (single-developer project; CONTRIBUTING.md documents the minimum bar)
- No macOS support (Windows + WSL2 + Ubuntu 24.04 only; native Linux also works)
- No transfer of the GitHub repo ownership (the recipient clones the public repo)
- No real Kafka cluster in production (the local kind cluster is fine for demos)

---

## How to use this release

### If you are a recipient (just received the project)

1. Read [`RECIPIENT_SETUP.md`](https://github.com/sudo-Harshk/k8-auto-scaling-self-healing/blob/main/RECIPIENT_SETUP.md) (5 min)
2. Run the one-liner above (15–20 min)
3. Run `demo-quick` to verify (2 min)
4. Read [`PROJECT_EXPLAINED.md`](https://github.com/sudo-Harshk/k8-auto-scaling-self-healing/blob/main/PROJECT_EXPLAINED.md) to understand what you're looking at (15 min)
5. Run `demo` for the full 15-min live demo

### If you are an M.Tech examiner or reviewer

1. Read [`docs/paper/main.pdf`](https://github.com/sudo-Harshk/k8-auto-scaling-self-healing/blob/main/docs/paper/main.pdf) (5 pages, 20 references)
2. Run `python3 scripts/_phase5_audit.py` to verify the paper claims
3. Open `evidence-freeze.md` to see the chain of custody for every number
4. Run `cat results_N10/stats_report.md` to see the empirical results
5. Run `cat specs/tlc_run_*.txt` to see the TLA+ model-checker traces

### If you are continuing development after the handover

1. Read [`CONTRIBUTING.md`](https://github.com/sudo-Harshk/k8-auto-scaling-self-healing/blob/main/CONTRIBUTING.md)
2. The golden rule: **never edit a paper number without also updating `evidence-freeze.md`**
3. Run `pytest` and `python3 scripts/_phase5_audit.py` before every commit
4. Tag new releases as `v1.1`, `v1.2`, etc.

---

## File-by-file summary

| File | Status | Purpose |
|---|---|---|
| `LICENSE` | NEW | MIT license |
| `HANDOVER.md` | NEW | Recipient reference guide |
| `RECIPIENT_SETUP.md` | NEW | 9-step install from zero |
| `PROJECT_EXPLAINED.md` | NEW | Component-by-component explanation |
| `CONTRIBUTING.md` | NEW | Dev workflow |
| `CHANGELOG.md` | NEW | Version history |
| `README.md` | EDITED | Email placeholder, 57→56 |
| `RUN_DEMO.md` | EDITED | Email placeholder, 57→56 |
| `bootstrap.sh` | EDITED | Email placeholder, 57→56 |
| `evidence-freeze.md` | EDITED | Email placeholder, 57→56 |
| `tasks/THESIS.md` | EDITED | Email placeholder, 57→56 |
| `scripts/demo/quick.sh` | EDITED | Email placeholder, 57→56 |
| `docs/paper/main.tex` | EDITED | Email placeholder, 57→56, LaTeX underscore escape |
| `docs/paper/main.pdf` | REBUILT | 5 pages, 253 KB |
| `landing-page/src/components/Footer.tsx` | EDITED | Email placeholder, 57→56 |
| `landing-page/src/components/Honest.tsx` | EDITED | 57→56 |
| `landing-page/src/components/Limitations.tsx` | EDITED | 57→56 |
| `landing-page/src/components/Reproduce.tsx` | EDITED | 57→56 |
| `landing-page/src/data/metrics.ts` | EDITED | 57→56 |
| `landing-page/dist/` | REBUILT | 0 TS errors, 0 warnings |
| `docs/GOLDEN_RUN.md` | EDITED | 57→56 |
| `docs/VIVA_GAUNTLET.md` | EDITED | 57→56 |

---

## Verification commands

```bash
# 1. Clone this exact tag
git clone https://github.com/sudo-Harshk/k8-auto-scaling-self-healing
cd k8-auto-scaling-self-healing
git checkout v1.0-handover

# 2. Run the audit
python3 scripts/_phase5_audit.py
# expect: SOURCED=56, UNSOURCED=0

# 3. Run the tests
pytest
# expect: 53 passed

# 4. Re-run the TLA+ safety shield
make tla
# expect: 273702 states generated, 0 errors, 01m47s
```

---

## Credits

Original author: `sudo-Harshk <[YOUR_EMAIL]>` (placeholder; replace with your email)
License: MIT (see `LICENSE`)
Repository: https://github.com/sudo-Harshk/k8-auto-scaling-self-healing
M.Tech project, completed 2026-09-11.
