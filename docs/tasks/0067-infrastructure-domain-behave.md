# 0067: infrastructure domain in Behave (0045b)

- **created:** 2026-09-14T10:01:36Z
- **type:** [infrastructure]
- **depends-on:** 0066
- **status:** open

## Description

Port the local deployment failure suite (task 0055,
`tests/failures_test.py`, 15 checks) to Behave scenarios tagged
`@infrastructure`, so the infrastructure workflow runs it like every
other domain (the agreed behaviors are in `docs/design/failure-modes.md`
§5/§7).

- The python suite shares one provisioned sim across cases and mutates
  it (stop a container, hog the port, delete a repo, remove the
  operator) — the Behave version needs a suite-level fixture
  (`before_all`/`after_all` or a steps module owning one sim), not the
  throwaway-per-scenario environment used by the legal features.
- Keep the same assertions: fail fast with a remedy, no bare traceback,
  inspectable state, idempotent recovery.
- Container-based: GitHub runners provide docker (runtime auto-detect);
  this suite does not need woodpecker, so the docker path should hold —
  verify on a docker machine and record the result.
- Once the feature covers everything, retire `tests/failures_test.py`
  (and adjust `tests/all.sh`/`docs/testing.md`).
- Acceptance: the ported suite is green via
  `uv run behave features/ --tags @infrastructure` on podman and docker;
  the infrastructure workflow runs it with no extra runner, no custom
  scripts.

## Completion

<!-- filled in when the task is done:
- **finished:**
- **commit:**
-->
