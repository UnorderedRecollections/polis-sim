# 0053: BDD integration — phase I → transition → phase II (base case)

- **created:** 2026-09-13T17:12:46Z
- **type:** [tests]
- **depends-on:** 0034, 0038, 0041, 0042
- **status:** open

## Description

The transition arc (phase I → transition → phase II) is currently driven
by hand (or by `tests/transition-demo.sh`, a shell demo). Make it a
**BDD integration scenario** so the whole arc is executable, readable and
regression-proof — using the existing one-binding-two-drivers layer
(0034): `polis/sim/beats.py`, `features/steps/`, `features/environment.py`.

Shape:

- **Platform-parameterized scenarios.** Feature tags select the
  implementation per phase: `@gogs` (phase I only — transition requires
  gitea), `@gitea` (phase I on gitea and phase II), later `@rest` (a
  custom polis-native REST API — task 0047). The same scenario text must
  run against each backing; the provision binding and expectations
  dispatch on the tag.
- **The transition is explicit in the feature.** A dedicated beat enacts
  it (`b_codify`: `transition.transition()` + the host-side CI erection
  `provision.up_woodpecker`), with its own expectation beats (phase
  recorded in situation/registry/slices, the three acts and instruments
  in the corpus, the CI enabled). Alternate transition scenarios and
  failure variants become writable later; detailed failure modes are
  task 0055.
- **Phase-2 vocabulary.** New bindings: `b_scrutinize` (the jurist's
  `SCRUTINY — APPROVED` comment — the CI constitution check needs it)
  and phase-2 expectations (petition is a real issue; the bill is a real
  PR; the PR merged and closed; commit status success/failure with
  bounded polling). Existing action beats (`b_petition`, `b_drafts`,
  `b_keeper_ratifies`) should dispatch on `phase == 2` already — verify
  and fix if they do not.
- **Environment.** `features/environment.py` must snapshot/restore
  `world.json` (the transition flips the civil registry globally, as
  `tests/transition-demo.sh` already restores it); the provision binding
  gains the platform (and optionally `--with-city-containers`).
- **Slow suite.** The full arc costs minutes (containers, transition,
  CI runs): tag it (`@phase2`/`@slow`) and keep it out of the default
  `uv run behave features/`; add a runner (`tests/bdd-phase2.sh` or a
  documented `behave --tags`) and document it in `docs/`/AGENTS.md.

Acceptance: one scenario provisions a gitea sim, drives a phase-1 story,
enacts the transition explicitly, and drives a phase-2 story through the
real platform (issue → PR → scrutiny → merge) with the CI verdict
asserted — all through behave; the gogs variant of the phase-1 part also
passes; default `behave features/` stays fast.

Out of scope: per-jurisdiction suites (0054), failure injection (0055),
performance (0056).

## Completion

<!-- filled in when the task is done:
- **finished:**
- **commit:**
-->
