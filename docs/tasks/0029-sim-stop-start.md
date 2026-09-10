# 0029: Sim stop/start (pause without teardown)

- **created:** 2026-09-10T10:30:00Z
- **type:** [infrastructure]
- **depends-on:** 0027
- **status:** done

## Description

Lifecycle gap: `provision up` creates, `provision teardown --yes` deletes,
but there is no way to *pause* a sim (free the containers, keep the
volumes, slices, journal and secrets). Add:

- `polis provision stop` — stop the sim's containers (operator, gogs,
  postgres; city containers if any), keep everything else;
- `polis provision start` — start them back in dependency order
  (postgres → pg_isready → gogs → operator/city containers), so gogs
  doesn't hit its connect-refusal FATAL (it has --restart, but order is
  cheaper than crash-loops).

Both default the sim id to POLIS_PROVISIONED_SIM. Delete remains
`provision teardown --yes` + `rm -rf data/sims/<sim>`. Document in
`docs/running-a-simulation.md` §9.

## Completion

- **finished:** 2026-09-10T10:50:00Z
- **commit:** (pending — user commits)

`polis provision stop` / `polis provision start` implemented
(`provision.stop/start`): stop pauses the sim's containers keeping all
state; start resumes in dependency order (postgres first with a
pg_isready gate, then gogs, then the operator/city containers). Sim id
defaults to POLIS_PROVISIONED_SIM like every other command. Verified
live on a running sim: stop → start → `health gogs` green. User guide §9
retitled "Stop, resume, delete" (duplicate paragraphs removed).
