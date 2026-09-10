# 0021: Provisioning — implementation

- **created:** 2026-09-09T11:45:00Z
- **type:** [infrastructure]
- **depends-on:** 0020
- **status:** done

## Description

Implement `docs/design/provisioning.md`:

- extend `clients/gogs.py` (create/delete repo, collaborators, per-user
  token creation via basic auth, fork if the build supports it — probe
  first; fallback: plain repo + seed push);
- `polis/provision.py` — the orchestrator: preflight, users with per-sim
  tokens (written back to `world.json` as `api_tokens["gogs@<sim>"]`),
  archive org/repo + founding corpus, city orgs/repos, per-sim slices under
  `data/sims/<sim>/cities/`, `provision.json` inventory;
- `polis/cli/provision.py` — `up [--with-city-containers] [--force]`,
  `status`, `teardown [--yes]`; idempotent;
- `docker/polis-city/Dockerfile` + container phase behind the flag;
- `tests/provision-demo.sh` — up → clone as a namespaced citizen → status →
  teardown → verify nothing remains.

## Completion

- **finished:** 2026-09-10T21:48:57Z
- **commit:** 836a26d
