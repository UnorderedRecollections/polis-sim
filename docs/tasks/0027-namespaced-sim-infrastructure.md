# 0027: Namespaced infrastructure per sim

- **created:** 2026-09-09T22:00:00Z
- **type:** [infrastructure]
- **depends-on:** 0026
- **status:** done

## Description

Today `provision up` assumes the shared dev infra (containers `gogs`,
`postgres-gogs`, network `gogs-local`). A sim must instead be fully
self-contained so it can coexist with the dev rig and other sims:

- network `<sim>-net`; containers `<sim>-postgres`, `<sim>-gogs`
  (host port allocated and recorded in the inventory), plus the existing
  `polis-operator-<sim>` on that network;
- headless gogs bootstrap: POST /install (postgres backend), admin user,
  admin API token — per-sim secrets recorded in the sim dir
  (never world.json);
- `provision up/status/teardown` manage the whole set; slices keep
  in-network URLs (`http://<sim>-gogs:3000` — constant regardless of
  host port);
- the shared dev rig stays as-is for e2e tests; e2e/demo scripts keep
  working unchanged.

Open design points: port allocation strategy; whether city containers
join the sim network (yes); how `polis health`-style checks address a
sim's gogs (per-sim URL from the inventory).

## Completion

- **finished:** 2026-09-10T08:00:00Z
- **commit:** (pending — user commits)

Delivered: every sim is fully self-contained.

- `_up_platform()`: network `<sim>-net`; `<sim>-postgres` (pg_isready gate
  — gogs crashes FATAL on connect refusal); `<sim>-gogs` with a written
  app.ini (`INSTALL_LOCK`, postgres backend, `DEFAULT_BRANCH=main`),
  headless admin via `gogs admin create-user` (`operator` — `admin` is a
  reserved username; retried — web answers before the schema migrates),
  admin token, host port from `_free_port(11880+)`; secrets in
  `data/sims/<sim>/secrets.json`; re-`up --force` reuses existing
  credentials/volume (token reuse; duplicate-name suffixing for users).
- `GogsClient(base_url=…)`; `sim_gogs_client(sim)` used by up/status/
  teardown; slices/remotes use `http://<sim>-gogs:3000`; operator and city
  containers join `<sim>-net`; teardown removes containers + network.
- `_founding_repo()`: the founding corpus committed ONCE and pushed to all
  repos — the Keeper's enactment pushes to upstream were non-fast-forward
  because each repo had its own founding commit.
- Demo/test fixes: director-demo reads the sim's port from secrets.json;
  provision-demo slice-token source + `set -e`-safe idempotency step.

Verified: `tests/provision-demo.sh`, `tests/director-demo.sh`,
`tests/sim-runtime-demo.sh`, `tests/e2e-gogs.sh`, `scripts/infra/smoke.sh`
all passing; a sim now coexists with the shared dev rig untouched.
