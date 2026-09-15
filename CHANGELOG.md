# Changelog

All notable changes to this project are documented here. Versions follow
loose [semver](https://semver.org/). The format is based on
[Keep a Changelog](https://keepachangelog.com/).

## [v1.0.1] - 2026-09-15

### Fixed
- `make build-image` now builds with `ops/docker/` as the build context
  (`Makefile`) instead of the repo root, so the Dockerfile's
  `COPY requirements.txt /app/requirements.txt` resolves to
  `ops/docker/requirements.txt`. Previously a fresh bootstrap failed with
  `COPY requirements.txt /app/requirements.txt: not found` until the file
  was manually copied to the repo root.
- `bootstrap.sh` now installs `make` during pre-flight, so step [6/6]
  (`make build-image`) no longer fails with `make: command not found` on a
  clean Ubuntu 24.04 / WSL2 box.

### Changed
- `ops/docker/Dockerfile` and `scripts/build_image.sh` wording unchanged;
  `scripts/build_image.sh` already used the `ops/docker/` context, so both
  build entry points are now consistent.

## [v1.0-handover] - 2026-09-11

### Added
- `LICENSE` (MIT) — permissive license for the project
- `HANDOVER.md` — first-day guide for receiving the project
- `CONTRIBUTING.md` — development workflow and PR checklist
- `CHANGELOG.md` (this file)
- Git tag `v1.0-handover` pointing at the final handover commit

### Changed
- Personal email replaced with `[YOUR_EMAIL]` placeholder across
  11 files: `bootstrap.sh`, `RUN_DEMO.md`, `evidence-freeze.md`,
  `README.md`, `tasks/THESIS.md`, `scripts/demo/quick.sh`,
  `scripts/build_deck.py`, `docs/paper/main.tex`,
  `landing-page/src/components/Footer.tsx`, and this changelog.
- `defense_deck.pdf` rebuilt with placeholder email
- `docs/paper/main.pdf` rebuilt with placeholder email

### Security
- Email attribute removed from public artifacts; recipient does a
  one-time find-and-replace on first day.

## [Phase 6] - 2026-09-06

### Added
- `docs/paper/main.pdf` (5pp IEEE conference, 20 refs) — final paper
- `defense_deck.pdf` (20 slides) — M.Tech defense deck
- `landing-page/` (Vite + React + Tailwind) — public site

## [Phase 5] - 2026-09-06

### Added
- `scripts/_phase5_audit.py` — claim-to-evidence audit. Locks every
  numeric in `main.tex` to `evidence-freeze.md`. Result: **56 sourced,
  0 unsourced**.

## [Day 19] - 2026-09-01

### Added
- `bootstrap.sh` (221 lines, idempotent) — one-command installer for
  fresh Ubuntu 24.04 / WSL2 systems
- `RUN_DEMO.md` (196 lines) — viva cheat-sheet
- `scripts/demo/quick.sh` (90 lines) — 2-min highlight run
- `Makefile` targets: `bootstrap`, `demo-quick`

## [Day 18] - 2026-08-31

### Added
- `workload-v2` (DB-backed Flask + SQLite) deployed alongside podinfo
- v2 replica predictor (MAE 0.007)
- v2 anomaly detector (threshold 0.484)
- v2 dataset (`data/features_v2.csv`, 285 rows)

## [Day 15] - 2026-08-25

### Changed
- N=3 evaluation confirms AI failure mode (9/9 runs, 100% error rate)
- This is the motivating finding for the safety shield

## [Phase 0 - Freeze] - 2026-08-20

### Added
- `evidence-freeze.md` — single source of truth for all paper claims
- Threshold 0.4837573385518591 locked
- 273,702 TLC state count locked

## Earlier phases (pre-freeze)

### Day 1-7
- Initial operator skeleton
- TLA+ spec (`SafetyShield.tla`) first version
- Kafka + Prometheus stack on kind

### Day 8-14
- River HTR + Half-Space-Trees integration
- 53 unit tests added
- Cooldown gate implemented
- 5 invariants + 1 liveness property formalized

---

## Versioning notes

- v1.0-handover is the **last commit by the original author**. Subsequent
  versions are owned by the recipient.
- v1.x is the line of "demoable + audited" releases.
- Breaking changes to the audit script's contract (e.g. changing
  `SOURCED=56` to a different number) require a major version bump
  and a CHANGELOG entry explaining why.
