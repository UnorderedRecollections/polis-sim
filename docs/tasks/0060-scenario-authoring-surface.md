# 0060: the scenario authoring surface (tree, contract, guide, driver tests)

- **created:** 2026-09-13T19:00:00Z
- **type:** [simulation]
- **depends-on:** 0059
- **status:** in-progress

## Description

`docs/design/scenarios-vs-tests.md` §5–§6. With the vocabulary scoped
(0059), give the *driving* use case its own home and contract, and stop
relying on the test harness to verify the driver.

- **Tree split.** Software tests stay in `features/`; add `scenarios/`
  (tracked) for user scenarios — examples that are meant to be read and
  submitted (`polis sim submit`), not run by behave: no test tags, no
  infrastructure oracles.
- **Authoring contract.** Write it down for authors (and for the future
  UIs): the user beat grammar (scope `user`), how actors/cities/resources
  are named, phase constraints (what a phase-1 vs phase-2 scenario may
  do), and what an expectation *means* — goal vs assertion, wait-until
  bounds, and the failure policy (pause, resume, cancel). Tie the
  grammar to the 0059 catalog (`polis sim steps`).
- **Guide.** `docs/simulation-scenarios.md` (author-facing): the
  contract, worked examples from `scenarios/`, and the
  `submit`/`scenarios`/`resume` lifecycle; `docs/testing.md` keeps
  pointing at the developer side.
- **Driver tests.** The queue gets its own tests, independent of behave:
  submit/validate (rejecting test-scoped beats), setup beats at
  submission, one action beat per service step, expectation handling,
  pause/resume, done, and that a failing beat never crashes the sim.
  Run them from `tests/all.sh` (no containers where possible).

Acceptance: an example scenario from `scenarios/` drives a provisioned
sim via `submit` → `drive` → done; a test-scoped beat is rejected with
an explanatory message; the queue's own tests run in the full
verification; the authoring guide is written.

## Progress log

- **2026-09-13 — implemented and verified.** `scenarios/` (tracked) added
  with a README and two examples — `northern-banks-quota.feature`
  (phase I) and `codified-procedure.feature` (phase II, review +
  Magistrate check). `docs/simulation-scenarios.md` is the authoring
  contract: lifecycle, keyword timing (Given = at submission, one action
  per drive step, goals evaluated as reached), naming (casting, corpus
  dirs, norm ids, rule forms), phase-constraint table, failure/resume
  semantics, the rejected test vocabulary, and the UI horizon; linked
  from `docs/flows/simulation.md`, `docs/testing.md` and AGENTS.md.
  Driver tests added: `tests/queue_driver_test.py` (15 checks, stub
  `execute_beat`, no containers) covers submit/Given timing, one action
  per service, goals passed as reached, pause with the reason, "the sim
  goes on" while one scenario is paused, resume retrying, done, and the
  journal scoreboard; wired into `tests/all.sh`. Acceptance demo
  `tests/scenarios-demo.sh` provisions a sim, submits
  `scenarios/northern-banks-quota.feature`, drives three steps and
  asserts every beat executed/passed and the scenario `done` — also in
  `tests/all.sh`. Noted for 0061: the `codify` beat performs the legal
  transition but the **CI erection is the driver's** — the service must
  perform machinery effects for user-submitted transitions.
- **Verified:** `tests/queue_driver_test.py`, `tests/scenarios-demo.sh`,
  fast behave, `tests/bdd-phase2.sh`, full `tests/all.sh`.

## Completion

<!-- filled in when the task is done:
- **finished:**
- **commit:**
-->
