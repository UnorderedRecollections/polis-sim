# 0032: Sim destroy + list — controlled removal

- **created:** 2026-09-10T15:00:00Z
- **type:** [infrastructure]
- **depends-on:** 0027, 0029
- **status:** done

## Description

`rm -rf data/sims/<sim>` is uncontrolled: it can leave containers,
networks, repos and users behind, and stale sim dirs without a valid
inventory can't be torn down at all. Porcelain:

- `polis provision list` — every sim known on this host: sim dir
  presence, inventory validity, live containers, epoch/record summary;
- `polis provision destroy [<sim>] --yes` — full controlled removal,
  tolerant of partial state: best-effort API cleanup (repos/users) if
  the sim's gogs is reachable, containers matched by NAME PATTERN (not
  just the inventory — inventories go stale: `<sim>-postgres`,
  `<sim>-gogs`, `polis-operator-<sim>`, `polis-city-*-<sim>`), the
  network `<sim>-net`, and finally the sim dir itself.

Defaults the sim id to POLIS_PROVISIONED_SIM.

## Completion

- **finished:** 2026-09-10T15:20:00Z
- **commit:** (pending — user commits)

`polis provision list` (all sims: dir presence, container counts,
journal sizes) and `polis provision destroy [<sim>] --yes` (best-effort
API cleanup → containers matched by name pattern → network → sim dir;
tolerant of missing inventory/dir). Verified: a live sim destroyed; an
orphan container (no sim dir) listed and destroyed cleanly. User guide
§9 updated (`list` as the cleanup starting point; `destroy` as the
controlled rm -rf).
