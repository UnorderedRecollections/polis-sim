# Running the tests

Status: current (2026-09-13, task 0057). Two layers: **behave** Gherkin
suites (throwaway sims, the fast feedback loop) and **demo scripts**
(bash, real containers, the integration surface). Everything runs on the
local container runtime — podman (default) or docker — and nothing talks
to a remote host.

## Prerequisites

- `uv sync` — behave is a dev dependency.
- A running container runtime: podman (machine started,
  `podman machine start`) or docker. Auto-detected (`podman` first, then
  `docker`); override with `POLIS_RUNTIME=podman|docker`.
- First run pulls/builds the images (`polis/postgres`, `polis/gogs`,
  `polis/gitea`, `polis/caddy`, `polis/woodpecker-*`, `polis-city`) — a
  few minutes on a cold machine.
- **`POLIS_PROVISIONED_SIM` must be unset** for the suites; they set it
  per scenario themselves.
- The sim suites need **no `.env`**; only the dev-rig scripts do (see
  below).
- Optional: `scripts/infra/hosts.sh add` (sudo) so the *host browser*
  resolves `host.containers.internal` and can open canonical links; the
  tests themselves work without it.

## 1. The fast behave suite

```bash
uv run behave features/                      # ~10 s
uv run behave features/northern-banks.feature
```

One throwaway sim per scenario (provisioned and destroyed by
`features/environment.py`; a gogs sim unless the scenario says
otherwise). `behave.ini` sets `tags = not @slow`, so the fast suite is
exactly what runs by default.

**Platform parameterization** (task 0053): the same scenario text can be
backed by either product.

```bash
uv run behave features/northern-banks.feature -D platform=gitea
```

Tags:

| tag | meaning |
|---|---|
| `@phase1` | phase I procedures (valid on either product) |
| `@phase2` | exercises the codified machinery (requires gitea) |
| `@gitea` | the scenario requires the gitea backing |
| `@slow` | provisions/transitions/CI — excluded from the default run |

## 2. The slow gitea suites (phase I → transition → phase II)

```bash
tests/bdd-phase2.sh                          # both suites, ~45 s
```

or directly:

```bash
uv run behave features/northern-banks.feature -D platform=gitea
uv run behave features/phase-transition.feature --tags @slow
```

> **Trap:** `uv run behave features/phase-transition.feature` *without*
> `--tags @slow` reports `1 skipped` and every step shows `# None` — that
> is the `behave.ini` default excluding the slow suite, not a broken
> scenario.

### Cross-jurisdiction suite (task 0054)

```bash
tests/jurisdictions.sh              # seed 41
tests/jurisdictions.sh --seed 7
```

One provisioned sim, one whole director story per jurisdiction (15):
each situation is generated from the jurisdiction's own data
(`polis/sim/situations.py`), validated, seeded into a fresh run, and
driven to enactment; the summary lists per-jurisdiction pass/fail with
the story's error. Takes minutes (drives 15 stories); seeds 41 and 7
both pass 15/15. Cross-jurisdiction cases (e.g. river-water ↔ fisheries)
are not reachable by a single-jurisdiction run — see
`docs/todo/runtime-and-cross-jurisdiction-resources.md`.

### Performance / scale harness (task 0056)

```bash
uv run python tests/performance_test.py --cities 9,15,20
uv run python tests/performance_test.py --cities 20 \
    --legislators-per-city 8 --delegates-per-city 4
```

Builds scaled worlds, provisions one sim per size, drives stories, and
prints a metrics table (provisioning/drive times, record and git-pack
sizes). The canonical world is restored afterwards; take minutes and
opt-in. Baseline and conclusions: `docs/design/performance.md`.

### Deployment failure suite (task 0055)

```bash
tests/failures.sh
```

Provisions one sim and injects local deployment failures (unknown
runtime, missing world, platform down, taken proxy port, deleted
resources, missing operator), asserting fail-fast-with-remedy, no bare
traceback, inspectable state and idempotent recovery (~2 min). The
agreed taxonomy and behaviors: `docs/design/failure-modes.md`.

The transition scenario flips `federation.phase` in `world.json` (the
civil registry); `features/environment.py` snapshots and restores it
around every scenario, so a normal run leaves the world in phase 1. If a
run is killed hard, check and reset:

```bash
uv run python -c "from polis import store; print(store.load_world().federation.phase)"
uv run python -c "from polis import store; w = store.load_world(); w.federation.phase = 1; store.save_world(w)"
```

## 3. Demo scripts (bash, real containers)

Each provisions its own namespaced sim and destroys it afterwards.

| script | what it proves | needs |
|---|---|---|
| `tests/provision-demo.sh` | gogs provisioning: proxy path, city clone, slices, status, teardown | a runtime |
| `tests/provision-demo-gitea.sh` | gitea provisioning, phase stays 1 | a runtime |
| `tests/director-demo.sh` | director drives two stories through the operator container | a runtime; sources `.env` (may be empty) |
| `tests/scenarios-demo.sh` | a user scenario from `scenarios/` submitted and serviced to completion | a runtime |
| `tests/transition-demo.sh` | transition + CI verdicts (defective fails, corrected passes) | a runtime |
| `tests/sim-runtime-demo.sh` | the `enact()` facade end to end | dev rig up + `.env` (`GOGS_API_KEY`) |
| `tests/e2e-gogs.sh` | the full live legislative flow | dev rig up + `.env` (`GOGS_API_KEY`) |

Run with `bash tests/<script>.sh`. The dev-rig scripts assume the stack is
up (`scripts/infra/compose-up.sh` or the per-service scripts) and its gogs
admin token is in `.env`; everything else is self-contained.

## 4. Dev-rig checks

```bash
scripts/infra/smoke.sh        # containers up + API keys valid (needs .env)
uv run polis health           # subsystem checks (dev rig, or the sim named by POLIS_PROVISIONED_SIM)
```

## 5. One command — the full verification

```bash
tests/all.sh              # everything below, cheapest first
tests/all.sh --dev-rig    # also the dev-rig checks (required, not skipped)
```

`tests/all.sh` runs the fast suite, the slow gitea suites and the
self-contained demos in order; the dev-rig checks (smoke, sim-runtime,
e2e) run when the shared rig answers, or are **required** with
`--dev-rig`. It continues past failures and exits non-zero with a summary
naming what failed. This is the command the CI tasks (0045/0049) should
call.

## 6. Troubleshooting

- **Everything skipped, `# None` step locations** → a `@slow` suite;
  pass `--tags @slow` or use `tests/bdd-phase2.sh`.
- **`.env: No such file or directory`** → a demo sourced `.env`; for
  sim-only demos an empty file (`touch .env`) is enough, for the dev rig
  copy `.env.example` and fill it in.
- **`'host.containers.internal' does not resolve on this host`** → the
  expected warning; run `scripts/infra/hosts.sh add` (sudo) only for
  browser links.
- **`the federation already operates in phase 2`** → `world.json` was
  left flipped by a hard-killed transition scenario; reset it (section 2).
- **Leftover sims/containers** → `uv run polis provision list`, then
  `uv run polis provision destroy <sim> --yes` (or `teardown` to keep the
  record).

## See also

- `docs/simulation-scenarios.md` — the author-facing guide to driving a
  running sim (the other side of the BDD split).
- `docs/design/proxy.md` — why every sim's one HTTP entrypoint is
  `localhost:<proxy_port>` and how the canonical URLs work.
- `docs/tasks/0053-*.md`, `0054`–`0056` — the BDD work this document
  serves: transition base case, jurisdiction suites, failure injection,
  performance.
