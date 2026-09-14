# 0069: functional domain in Behave — one suite per subcommand (0045d)

- **created:** 2026-09-14T10:01:36Z
- **type:** [tests]
- **depends-on:** 0066
- **status:** open

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

## Completion

<!-- filled in when the task is done:
- **finished:**
- **commit:**
-->
