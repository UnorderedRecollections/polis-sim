# 0067: infrastructure domain in Behave (0045b)

- **created:** 2026-09-14T10:01:36Z
- **type:** [infrastructure]
- **depends-on:** 0066
- **status:** in-progress

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

- **2026-09-14 — CI blocked; issue rebuilt as #15 after the repository
  recreation.** PR #37 and the original issue were lost when the old
  repository was deleted over the leaked personal email in commit
  metadata; `polis-sim` was recreated from the rewritten local history
  (clean contributors) and the issue mirror rebuilt there (issues
  #1–#18). The docker-backed suite still fails the shared-sim scenarios
  on GitHub runners after the fixes above (gogs uid permissions →
  `_relax_dir`; `/gogs` readiness false positive): the infrastructure
  workflow is **manual-only** (`workflow_dispatch`) until the runner
  issue is understood. The implementation stays on
  `task/0067-infrastructure-behave`; this task is in-progress.

## Completion

<!-- filled in when the task is done (after the PR is approved and merged):
- **finished:**
- **commit:**
-->
