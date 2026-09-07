# Gogs — the phase-1 platform

## Why it exists

In the fiction, gogs is **merely the mechanical host of the legal archive**:
it stores git refs and serves them over HTTP/SSH. It has *no* institutional
concepts — no petitions, proceedings, reviews or approvals. Those live in the
institutions and people (the matter store, `data/world/matters.json`).

This is deliberate: phase 1 of the simulation is the **customary era** of the
federation. The constitution is enforced by people; the platform only records.

## Start locally

```sh
scripts/infra/gogs.sh          # build + run alone (podman)
scripts/infra/compose-up.sh    # or the whole stack via compose
```

- HTTP: <http://localhost:10880> · SSH: `localhost:10022`
- Data: `data/services/gogs` · Image build: `docker/gogs/`

## API key

`GOGS_API_KEY` in `.env`. Obtain:

- UI: user avatar → **Settings → Applications → Generate New Token**, or
- API: `curl -u <user>:<pass> -H "Content-Type: application/json" \
  -X POST http://localhost:10880/api/v1/users/<user>/tokens -d '{"name":"polis"}'`

Verify: `scripts/infra/smoke.sh gogs`.

## Notes / quirks (verified by probing)

- This "next" build answers most of the gitea-shaped v1 API, but **has no
  pulls API at all** (list/create/merge all 404). Phase-1 bills therefore
  never touch PR machinery; ratification is local `git merge` + push.
- Repo creation with `auto_init: true` fails ("Something went wrong") — create
  with `auto_init: false` and push a seed commit.
- Some GET admin routes 404 while the matching POST/DELETE routes work; user
  listing goes through `/api/v1/users/search`.
- No org-deletion route; orgs are created via
  `POST /api/v1/admin/users/{owner}/orgs`.
- First-run setup (once, via UI): create the admin user, then generate a token.
