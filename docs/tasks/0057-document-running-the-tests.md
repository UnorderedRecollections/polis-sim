# 0057: document how to run the tests (and repair the pre-proxy dev-rig URLs)

- **created:** 2026-09-13T18:18:39Z
- **type:** [tests]
- **depends-on:** 0053
- **status:** done

## Description

There is no single place documenting how to run the test suites. The
knowledge is scattered across the AGENTS.md Dev bullet and the scripts'
header comments, and the `behave.ini` default (`tags = not @slow`) is
easy to walk into: running `uv run behave features/phase-transition.feature`
directly reports the scenario as skipped with `# None` step locations
(no hint that `--tags @slow` is the missing piece).

Deliverables:

- `docs/testing.md`: the suite matrix, prerequisites (podman machine,
  first-run image pulls, when `.env` is needed, the optional
  `scripts/infra/hosts.sh add`), the fast behave suite vs the slow gitea
  suites and how to invoke each directly, tags (`@phase1`, `@gitea`,
  `@slow`, `-D platform=`), expected durations, cleanup semantics
  (throwaway sims; `world.json` snapshot/restore around transition
  scenarios), the dev-rig checks (`smoke.sh`, `polis health`), and a
  troubleshooting section (all-skipped output, stale world phase,
  leftover sims, hosts warning);
- link it from AGENTS.md's Dev section (and the user guide where it
  fits);
- a header comment in `features/phase-transition.feature` with the
  direct invocation — the trap that prompted this task;
- **bugfix while here:** `tests/sim-runtime-demo.sh` and
  `tests/e2e-gogs.sh` still hardcode `http://localhost:10880` — the
  dev-rig gogs port retired by the front proxy (task 0042). They must use
  `http://localhost:10800/gogs` (the proxy path) like everything else.

Acceptance: `docs/testing.md` exists, is linked, and every command in it
has been executed in the form written (the dev-rig-only ones at least
syntax-checked when the rig has no credentials); `bash -n` passes; the
slow-suite invocation from the docs actually runs the scenario.

## Progress log

- **2026-09-13 — implemented.** `docs/testing.md` added (layers, tags,
  platform selection, direct invocations, durations, cleanup,
  troubleshooting) and linked from AGENTS.md (layout + Dev) and
  `docs/running-a-simulation.md` §2. Header comment in
  `features/phase-transition.feature` with the direct `--tags @slow`
  invocation. Repaired the pre-proxy URLs: both dev-rig demos now use
  `http://localhost:10800/gogs` (`tests/sim-runtime-demo.sh` clone URL
  included), and the dead `GOGS` variable in `tests/provision-demo.sh`
  was dropped. Verified: the documented direct slow invocation runs
  16/16 steps; the fast suite still green; `bash -n` clean; no stale
  `10880` references remain.

## Completion

- **finished:** 2026-09-13T18:18:39Z
- **commit:** 4eec1ea
