# 0067: infrastructure domain in Behave (0045b)

- **created:** 2026-09-14T10:01:36Z
- **type:** [infrastructure]
- **depends-on:** 0066
- **status:** review

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

## Progress log

- **2026-09-14 — ported to Behave.** `features/infrastructure.feature`
  gained the container-free missing-world fail-fast scenario;
  `features/infrastructure-failures.feature` (@infrastructure
  @containers @shared-sim) ports the rest — baseline/status, stopped
  platform, taken proxy port, deleted repository, missing operator —
  with `features/steps/failure_steps.py` and a shared-sim mode in
  `features/environment.py` (provisioned once, destroyed in `after_all`).
  `tests/failures_test.py`/`failures.sh` retired; `tests/all.sh`,
  `docs/testing.md`, AGENTS.md and the infrastructure workflow updated
  (the workflow now runs `--tags @infrastructure`, so CI exercises the
  port on the runner's docker — the live docker verification).

- **2026-09-14 — the CI docker run surfaced two real portability bugs**
  (both fixed here): (1) readiness polled `/gogs` without the trailing
  slash, which caddy's catch-all answered with a 302 before gogs was up —
  the readiness check now uses `/gogs/`; (2) bind-mounted sim data dirs
  belong to the host uid (1001 on CI runners) while the images run as
  their own user (gogs/gitea: 1000), so `mkdir /data/git` failed —
  provisioning now `chmod 0777`s the sim data directories (`_relax_dir`,
  chmod not chown, no privileges needed; harmless for throwaway data).
  Diagnostics: failing shared-sim provisioning dumps the sim containers'
  logs from `features/environment.py`.

## Completion

<!-- filled in when the task is done (after the PR is approved and merged):
- **finished:**
- **commit:**
-->
