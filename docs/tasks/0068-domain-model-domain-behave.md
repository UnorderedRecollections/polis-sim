# 0068: domain-model domain in Behave (0045c)

- **created:** 2026-09-14T10:01:36Z
- **type:** [tests]
- **depends-on:** 0066
- **status:** done

## Description

Port the cross-jurisdiction suite (task 0054,
`tests/jurisdictions_test.py`) to Behave scenarios tagged `@domain`, so
the domain-model workflow runs it like every other domain.

- the python suite generates a situation per jurisdiction, seeds a run
  on one shared sim and drives one whole story (15 stories) — the
  Behave version can use a scenario per jurisdiction (a generated
  Scenario Outline) or one scenario looping; keep one shared sim, not
  per-scenario provisioning.
- Tag the container-based scenarios `@domain @slow`; the domain-model
  workflow grows to include them (`--tags @domain`) once they are
  runner-ready on docker; until then they remain opt-in locally, exactly
  like the gitea suites.
- Keep the seeds (41/7) and per-jurisdiction pass/fail reporting;
  failures stay reproducible.
- Retire `tests/jurisdictions_test.py`/`tests/jurisdictions.sh` once the
  feature covers it (adjust `tests/all.sh`, `docs/testing.md`).
- Acceptance: the ported suite is green via behave (same 15/15, seeds
  41/7), reproducible, and wired into the domain-model workflow when the
  runner can take it.

## Progress log

- **2026-09-14 — ported to Behave.** `features/jurisdictions.feature`
  (@domain @containers @slow @shared-sim) is a 15-row scenario outline —
  one whole director story per jurisdiction with behave's per-row
  pass/fail; `features/steps/jurisdiction_steps.py` generates/validates
  the situation, seeds the run (`-D seed=`, default 41) and asserts
  enactment + a recorded ratification. The shared-sim machinery in
  `features/environment.py` became per-domain (`bdd-infra`,
  `bdd-domain`), so domain and infrastructure suites can share one behave
  invocation. `tests/jurisdictions_test.py`/`jurisdictions.sh` retired;
  `tests/all.sh`, `docs/testing.md` and AGENTS.md updated; the
  domain-model workflow now runs `--tags @domain` (containers included —
  the docker run is the runner verification).

## Completion

- **finished:** 2026-09-14T12:50:39Z
- **commit:** 0cb6794 (PR #22)
