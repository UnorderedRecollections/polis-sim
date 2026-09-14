# 0053: BDD integration — phase I → transition → phase II (base case)

- **created:** 2026-09-13T17:12:46Z
- **type:** [tests]
- **depends-on:** 0034, 0038, 0041, 0042
- **status:** done

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

## Progress log

- **2026-09-13 — implemented and verified.** Platform-parameterized
  provisioning (`BeatContext.platform`; `-D platform=gitea` or an
  `@gitea` tag), the explicit transition beat `b_codify` (transition +
  host-side CI erection), phase-2 expectations (petition is an issue,
  bill is a PR, PR merged, CI verdict with polling), `b_jurist_approves`,
  phase/corpus/CI-erected expectations; `Runtime.file_petition` anchors
  platform issue numbers; `features/environment.py` snapshots/restores
  `world.json`; new `features/phase-transition.feature`; `behave.ini`
  excludes `@slow` by default; `tests/bdd-phase2.sh` runs phase I on
  gitea plus the full arc. Problems met and fixed on the way:
  - **Host-derived URLs.** gitea derives clone/webhook URLs from the
    request Host; host-side clients reach the proxy as `localhost`, so
    the webhook payload pointed the CI clone at `localhost:<P>` —
    unreachable from a step container. Fixed by forcing the canonical
    Host upstream in both Caddyfiles (`header_up Host`). Verified:
    gitea reports canonical clone URLs and the CI clones successfully.
  - **Vacuous checks.** The CI clone is shallow and has no mainline ref,
    so `_changed_docs` diffed `main` against itself — every check saw
    "no documents changed" and every act passed. The transition demo's
    defective-act assertion had been passing only because the clone
    itself failed. Fixed: the pipeline's first command fetches
    `$CI_COMMIT_TARGET_BRANCH` (`--unshallow`) before the checks.
    Verified: the defective act fails on `missing proposer`; the
    corrected act passes; the BDD approval assertion is now meaningful.
- **Verified:** `tests/bdd-phase2.sh` (phase I on gitea + phase I →
  transition → phase II) green; default `uv run behave features/` green
  and fast (the slow scenario skipped); `tests/transition-demo.sh`
  green; `world.json` restored to phase 1 after the scenario.

## Completion

- **finished:** 2026-09-13T18:11:49Z
- **commit:** 4cdd5d7
