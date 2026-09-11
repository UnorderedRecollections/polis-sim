# 0040: headless dev-rig gitea bootstrap (no installer, credentials from .env)

- **created:** 2026-09-11T01:30:00Z
- **type:** [infrastructure]
- **depends-on:** 0037
- **status:** done

## Description

The shared dev-rig gitea was set up once by hand through its first-run
web installer (admin `agros`, a personal email — stored in the gitea DB
volume, not in config). Repo-side, the username leaks into
`WOODPECKER_ADMIN` (woodpecker.sh + docker-compose.yml) and service docs;
the email also appears in historical session notes. Fix:

- `scripts/infra/gitea.sh`: headless bootstrap — run the container with
  `GITEA__security__INSTALL_LOCK=true` and create the admin with the
  `gitea admin user create --access-token` CLI (as the git user; same
  pattern as the sim bring-up in task 0037), taking username/password/
  email from `.env` (`GITEA_ADMIN_USERNAME`, `GITEA_ADMIN_PASSWORD`,
  `GITEA_ADMIN_EMAIL`); write the minted full-scope token into `.env`
  as `GITEA_API_KEY`.
- `WOODPECKER_ADMIN` reads `GITEA_ADMIN_USERNAME` from `.env` in
  `scripts/infra/woodpecker.sh` and `docker/docker-compose.yml`.
- `.env.example`: document the three new vars.
- Docs: services/gitea.md (no manual installer step), services/woodpecker.md.
- Decide with the user: whether to wipe `.state/gitea` (fresh instance)
  and whether to scrub the personal email from
  `docs/notes/session-ses_f88c.md`.

Decisions taken (user, 2026-09-11): wipe `.state/gitea` and re-bootstrap;
scrub the personal email/name from the session notes. Neutral identity:
`operator` / `operator@concord.invalid` / generated password in `.env`.
Compose's gitea service gained `INSTALL_LOCK` too (gitea.sh performs the
admin bootstrap; compose alone leaves an admin-less gitea — documented).

## Completion

- **finished:** 2026-09-11T02:20:00Z
- **commit:** 9d8ea66
