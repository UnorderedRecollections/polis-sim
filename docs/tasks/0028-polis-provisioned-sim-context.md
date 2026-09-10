# 0028: POLIS_PROVISIONED_SIM — address a sim with the generic commands

- **created:** 2026-09-10T09:00:00Z
- **type:** [infrastructure]
- **depends-on:** 0027
- **status:** done

## Description

After `provision up my-sim-01`, generic commands (`polis health`,
`polis gogs …`) still address the shared dev rig. Add a context switch:
`POLIS_PROVISIONED_SIM=<sim>` makes config resolve endpoints, secrets,
container names and network from `data/sims/<sim>/secrets.json`:

- resolution order: `POLIS_*` explicit override > sim secrets > process
  env/.env > built-in defaults;
- `GOGS_URL` → sim's external gogs URL; `gogs_token()` → sim admin token;
  `POSTGRES_CONTAINER` → `<sim>-postgres`; `PODMAN_NETWORK` → `<sim>-net`;
- `polis health` in sim context checks the sim's containers + API token
  (gitea/woodpecker are not part of a phase-1 sim — report them as n/a,
  not as failures).

Document in `docs/running-a-simulation.md`.

## Completion

- **finished:** 2026-09-10T09:45:00Z
- **commit:** (pending — user commits)

`POLIS_PROVISIONED_SIM` implemented in `polis/config.py` (resolution:
`POLIS_*` override > sim `secrets.json` > env/.env > defaults) covering
`GOGS_URL`, `gogs_token()` (sim admin token outranks the rig's .env key in
sim context), `PODMAN_NETWORK`, `POSTGRES_CONTAINER`. Health adapted:
gogs/postgres/citynode container names follow the sim, gitea/woodpecker
report n/a instead of failing, the operator container is checked, and the
full report prints the active context. Verified live against a running
user sim (`my-sim-01`): authenticated as `operator`, all checks green.
Documented in `docs/running-a-simulation.md` §5 and AGENTS.md.
