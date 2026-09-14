# 0069: functional domain in Behave — one suite per subcommand (0045d)

- **created:** 2026-09-14T10:01:36Z
- **type:** [tests]
- **depends-on:** 0066
- **status:** in-progress

## Description

Build out the functional domain: each `polis` subcommand gets its own
Behave feature under `features/`, tagged `@functional` (task 0066 has the
container-free skeleton).

- one `.feature` per command group — `world`, `city`, `person`,
  `office`, `assign`, `docket`, `bill`, `archive`, `sim`, `provision`,
  the component commands (`gogs`, `gitea`, `woodpecker`, `citynode`) and
  `health` — covering the command's contract: success paths, clear
  failures, `--isomorphism` rendering for the legislative commands
  (plans render, nothing executes), and idempotency where it matters;
- container-free scenarios run on an isolated federation (the
  `features/steps/cli_steps.py` pattern) and are what CI runs
  (`@functional and not @slow`); scenarios that need a sim or the
  platforms are tagged `@slow` and join CI when runner-ready;
- the per-subcommand suites are the regression net for the CLI surface;
  interfaces should be exercised through subprocesses (the real CLI), not
  in-process calls, except where a step legitimately inspects state;
- docs: `docs/testing.md` grows the domain table with per-command
  features; `AGENTS.md` verify list stays the one-shot source.

Acceptance: every subcommand has a feature, the fast ones green in
`@functional and not @slow`, the slow ones opt-in and documented.

## Progress log

- **2026-09-14 — built out. Fast (container-free, CI) features:**
  `world`, `city`, `person`, `office`, `assign`, `docket`, `bill`
  (isomorphism renders, nothing executes), `archive` (plans + the
  `--yes` guard), `sim` (runs/journal, clean failures), `provision`
  (fail-fast contracts), `formal-check` (all four checks against a
  throwaway corpus, steps in `formal_check_steps.py`) and `health`
  (`health hosts`). Harness: `cli_steps` now shlex-splits arguments,
  substitutes `{data_dir}`/`{repo_dir}` and runs with a wide `COLUMNS`
  so Rich does not truncate identifiers.
  **Slow (opt-in, `@slow @containers`):** `gogs`, `gitea`, `citynode`,
  `health` in a sim context, and `woodpecker` (full transition — the CI
  is erected only then); `sim_functional_steps.py` runs the CLI against
  the scenario's sim. The functional workflow now selects
  `@functional and not @slow`; the slow set is in `tests/all.sh`.
  First full runs: 59 fast scenarios green (~45 s); the sim-backed
  scenarios green (gogs, gitea, citynode, health); the woodpecker
  scenario exposed task 0075 (the sim's `woodpecker_token` was never
  resolved in a sim context) and passes with it. `nuke` is deliberately
  not covered (dev-rig-only DB surgery, dangerous to exercise).

## Completion

<!-- filled in when the task is done:
- **finished:**
- **commit:**
-->
