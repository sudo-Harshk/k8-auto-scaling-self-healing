# Contributing to SHIELD-AI

> The minimum bar for any change to this repo. The project has no CI;
> you are the CI.

## Before you start

1. **Read `HANDOVER.md`** to understand the project shape.
2. **Read `evidence-freeze.md`** to understand which numbers are locked.
3. **Run the baseline checks** and confirm they all pass:
   ```bash
   pytest                                  # 53/53 must pass
   python3 scripts/_phase5_audit.py        # 56 sourced / 0 unsourced
   make tla-composition                    # 53 states, 0 errors
   ```

## The golden rule

> Never edit a paper number without also updating `evidence-freeze.md`.

The audit script (`scripts/_phase5_audit.py`) cross-checks every numeric
literal in `docs/paper/main.tex` against `evidence-freeze.md`. If they
diverge, the script reports `UNSOURCED > 0`. This is a hard failure:
**no commit may land with `UNSOURCED > 0`.**

If your change moves a number:
1. Edit `evidence-freeze.md` first.
2. Edit `docs/paper/main.tex` to match.
3. Re-run the audit; confirm `SOURCED=56, UNSOURCED=0`.
4. Commit both files in the same commit.

## Branching

- `main` is the deployable, demoable branch. **Never commit broken state.**
- For new work, branch from `main`:
  - `feature/<short-name>` for new capabilities
  - `fix/<short-name>` for bug fixes
  - `docs/<short-name>` for documentation-only changes
- For releases, tag from `main`:
  - `v1.0-handover` is the current release tag.
  - Subsequent releases: `v1.1`, `v1.2`, etc. (semver, but loose).

## Before every commit

Run these locally and confirm they pass:

```bash
pytest                                  # 53/53
python3 scripts/_phase5_audit.py        # SOURCED=56, UNSOURCED=0
cd landing-page && npm run build && cd ..    # 0 TS errors, 0 warnings
```

If the change touches the TLA+ specs, also re-run:

```bash
make tla                # ~4 min
make tla-composition    # ~1 s
```

## Commit message style

Use **conventional commits** with a short body. Examples:

```
feat(decision): add cooldown elapsed detection

Currently the cooldown flag flips when (now - last) < cooldown.
Add a unit test that exercises the wrap-around case.
Resolves: #42

tla(safety-shield): add cyclic-clock modulo test

The original spec used (clock - last_action_clock) > CooldownTicks
which silently disables the cooldown when clock wraps. Add a test
that fails without the modulo fix.
```

Types: `feat`, `fix`, `docs`, `refactor`, `test`, `tla`, `chore`.

## Pull request checklist

When you open a PR (or describe a change in chat):

- [ ] `pytest` passes
- [ ] `scripts/_phase5_audit.py` shows `SOURCED=56, UNSOURCED=0`
- [ ] `landing-page` builds cleanly (`npm run build` → 0 errors)
- [ ] If TLA+ changed, `make tla` and `make tla-composition` pass
- [ ] If paper numbers changed, `evidence-freeze.md` and `docs/paper/main.tex` updated together
- [ ] `CHANGELOG.md` updated
- [ ] Commit message uses the conventional format

## Adding new content

### A new operator (e.g. "KEDA v2")

1. Add a new case in `scripts/eval/run_one_trial.py` (look for the
   `if operator == "hpa"` branches).
2. Add the operator name to `Makefile` (`eval` and `demo` targets).
3. Update `evidence-freeze.md` with the new operator's stats.
4. Update `docs/paper/main.tex` if the operator is mentioned in text.
5. Re-run the audit.

### A new scenario (e.g. "burst-then-idle")

1. Add a new `Scenarios` entry in `data/evaluation/run_template.md`.
2. Add a `make load-<scenario>` target in `Makefile`.
3. Update `scripts/eval/run_one_trial.py` to handle the new scenario.
4. Run N=3 and then N=10 trials; record results in `results_N10/`.

### A new safety invariant

1. Edit `specs/SafetyShield.tla` (add the invariant to `vars` and
   `SafetyInvariant`).
2. Edit `specs/SafetyShield.cfg` if you need new constants.
3. Re-run `make tla` (~4 min).
4. Update the `tlaDistinctStates` field in `evidence-freeze.md` if the
   count changed.
5. Update the paper.

## Repository conventions

- Python 3.11+ (the Docker image is `python:3.11-slim`).
- No `requirements.txt` at the repo root; the image bakes deps in via
  the `Dockerfile`.
- TLA+ specs use the `specs/` directory; TLC is invoked with
  `cd specs && java -jar /path/to/tla2tools.jar Foo.tla -config Foo.cfg`.
- Markdown is the source of truth for docs; rebuild PDFs only when needed.

## When in doubt

- Read `evidence-freeze.md` first.
- Read `HANDOVER.md` second.
- Read `docs/VIVA_GAUNTLET.md` third.
- Then read the code.

If something in this guide is wrong, open a PR fixing it. The author
who left the project trusts you to maintain it.
