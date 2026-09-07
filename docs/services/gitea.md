# Gitea — the phase-2 platform

## Why it exists

Gitea is the **codified machinery**: issues/PRs (petitions), reviews
(scrutiny), branch protection (constitutional entrenchment), CODEOWNERS
(jurisdiction), status checks (the Mechanical Magistrate's findings).

The federation migrates here narratively: the phase-2 transition is itself
enacted through phase-1 machinery — CODEOWNERS, branch protection and
`.woodpecker.yml` land as ratified bills.

## Start locally

```sh
scripts/infra/postgres.sh      # dependency first
scripts/infra/gitea.sh
scripts/infra/compose-up.sh    # or the whole stack
```

- HTTP: <http://localhost:3001> · SSH: `localhost:2222`
- Data: `data/services/gitea` · Image build: `docker/gitea/`
- DB: database `gitea` on the shared postgres container.

## API key

`GITEA_API_KEY` in `.env` — must be **full scope** (the original limited
token was replaced during bring-up).

- UI: **Settings → Applications → Generate New Token**, check all scopes.

Verify: `scripts/infra/smoke.sh gitea` (also checks admin access).

## Notes

- First-run: the installer appears on first visit; create the admin user
  (`agros`) matching `WOODPECKER_ADMIN` in the woodpecker service config.
- Woodpecker OAuth application (needed by the CI server): **Settings →
  Applications → Add OAuth2 Application**, redirect URI
  `http://localhost:10890/authorize`; copy client id/secret into
  `WOODPECKER_GITEA_CLIENT` / `WOODPECKER_GITEA_SECRET` in `.env`.
