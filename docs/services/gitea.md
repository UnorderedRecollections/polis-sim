# Gitea — the phase-2 platform

## Why it exists

Gitea is the **codified machinery**: issues/PRs (petitions), reviews
(scrutiny), branch protection (constitutional entrenchment), CODEOWNERS
(jurisdiction), status checks (the Mechanical Magistrate's findings).

The federation migrates here narratively: the phase-2 transition is itself
enacted through phase-1 machinery — CODEOWNERS, branch protection and
`.woodpecker.yml` land as ratified bills. The three acts and their
instruments are authored in `data/world/legal/transition/` (the
`phase_transition` story template carries them into the corpus).

Since the platform abstraction (task 0037), gitea can also **host phase 1**:
`polis provision up <sim> --platform gitea` stands a sim's own gitea up
while the federation remains in phase 1 — matter-store petitions, local
incorporation, no PRs. Phase is a procedure, not a product.

## Start locally

```sh
scripts/infra/postgres.sh      # dependency first
scripts/infra/gitea.sh         # headless: builds, runs, bootstraps the admin
scripts/infra/compose-up.sh    # or the whole stack (then run gitea.sh once for the admin)
```

- HTTP: <http://localhost:3001> · SSH: `localhost:2222`
- Data: `.state/gitea` · Image build: `docker/gitea/`
- DB: database `gitea` on the shared postgres container.

## Admin identity (headless, task 0040)

There is **no web installer** — `gitea.sh` bootstraps the admin from
`.env` (`GITEA_ADMIN_USERNAME` / `GITEA_ADMIN_PASSWORD` /
`GITEA_ADMIN_EMAIL`) with the `gitea admin user create` CLI, and mints a
full-scope API token straight into `.env` as `GITEA_API_KEY`. Use a
neutral, project-owned identity (e.g. `operator`), never a personal
account. To re-bootstrap from scratch: stop the container, delete
`.state/gitea`, re-run `gitea.sh`.

## API key

`GITEA_API_KEY` in `.env` — auto-minted (full scope) by `gitea.sh`; the
web UI route also works: **Settings → Applications → Generate New Token**,
check all scopes.

Verify: `scripts/infra/smoke.sh gitea` (also checks admin access).

## Notes

- Woodpecker OAuth application (needed by the CI server): **Settings →
  Applications → Add OAuth2 Application**, redirect URI
  `http://localhost:10890/authorize`; copy client id/secret into
  `WOODPECKER_GITEA_CLIENT` / `WOODPECKER_GITEA_SECRET` in `.env`.
