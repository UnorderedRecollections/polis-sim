# 0060: the scenario authoring surface (tree, contract, guide, driver tests)

- **created:** 2026-09-13T19:00:00Z
- **type:** [simulation]
- **depends-on:** 0059
- **status:** open

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

## Completion

<!-- filled in when the task is done:
- **finished:**
- **commit:**
-->
