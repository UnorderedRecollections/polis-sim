# 0068: domain-model domain in Behave (0045c)

- **created:** 2026-09-14T10:01:36Z
- **type:** [tests]
- **depends-on:** 0066
- **status:** open

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

## Completion

<!-- filled in when the task is done:
- **finished:**
- **commit:**
-->
