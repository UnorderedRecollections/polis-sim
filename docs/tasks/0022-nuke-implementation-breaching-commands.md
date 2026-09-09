# 0022: `polis nuke` — implementation-breaching commands

- **created:** 2026-09-09T13:00:00Z
- **type:** [infrastructure]
- **depends-on:** 0021
- **status:** in-progress

## Description

A `polis nuke` subcommand family for operations that deliberately breach
the implementation boundary (things the platforms don't offer via API).
First command: **org deletion on gogs via direct DB cascade** — the API has
no org-delete route (404 verified), and orgs are rows in `user` (type=1)
with dependents in `org_user`/`team`/`team_repo`/`team_user`.

- `polis nuke gogs orgs <prefix>` — preview what would be deleted;
  with `--yes`, execute the cascade via `podman exec postgres-gogs psql`
  in one transaction: team_repo → team_user → team → org_user → user
  (type=1), matched by `lower_name LIKE '<prefix>%'`.
- Wired into `polis/cli/main.py`; documented as dangerous in
  `docs/services/gogs.md` and AGENTS.md.

## Completion

<!-- filled in when the task is done:
- **finished:**
- **commit:**
-->
