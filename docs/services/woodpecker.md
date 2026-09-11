# Woodpecker CI — the Mechanical Magistrate's engine room

## Why it exists

CI is the federation's **automatic formal-legality machinery** (synopsis §9):
it checks mechanically enforceable rules (form, references, invariants) while
humans decide substantive law. Dormant in phase 1, erected in phase 2 — the
checklist it will enforce is specified in `docs/notes/families-of-legal-documents.md` §6,
and the pipeline that runs it is authored as the Mechanical Magistracy Act's
Schedule 1 (`data/world/legal/transition/woodpecker.yml`).

Two containers: `woodpecker-server` (coordinator, OAuth against gitea) and
`woodpecker-agent` (runs pipeline steps as sibling containers).

## Start locally

```sh
scripts/infra/postgres.sh && scripts/infra/gitea.sh   # dependencies
scripts/infra/woodpecker.sh                            # server + agent
scripts/infra/compose-up.sh                            # or the whole stack
```

- UI: <http://localhost:10890> (log in via gitea OAuth)
- Data: `.state/woodpecker/{server,agent}` · Builds:
  `docker/woodpecker/`, `docker/woodpecker-agent/`

## API key

`WOODPECKER_API_KEY` in `.env`. Obtain: log into the woodpecker UI → user
menu → **Settings → API token**.

Server-side OAuth credentials (`WOODPECKER_GITEA_CLIENT` /
`WOODPECKER_GITEA_SECRET`) come from a gitea OAuth2 application — see
`docs/services/gitea.md`.

Verify: `scripts/infra/smoke.sh woodpecker`.

## Notes / quirks

- API base is `/api` (**unversioned**), Bearer auth.
- Admin: `WOODPECKER_ADMIN=${GITEA_ADMIN_USERNAME}` (from `.env`) makes the
  gitea admin user a woodpecker admin on first login; an existing account
  can be flipped in
  `.state/woodpecker/server/woodpecker.sqlite` (`users.admin`).
- The agent on podman-machine (macOS) needs three non-obvious settings
  (already in `scripts/infra/woodpecker.sh` and the compose file):
  - mount the **VM-internal** rootless socket
    `/run/user/501/podman/podman.sock` — the host-forwarded socket can't be
    mounted (virtiofs can't mount sockets);
  - `--user 0:0` — container root maps to the VM's `core` user, the socket
    owner;
  - `--security-opt label=disable` — the CoreOS VM's SELinux otherwise denies
    socket access even with matching uids.
- `WOODPECKER_GRPC_SECRET` is not pinned; the server regenerates one per
  restart (harmless here, pin it if agents ever run elsewhere).
