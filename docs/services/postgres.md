# Postgres — shared backing store

## Why it exists

Pure plumbing: one postgres container holds both platform databases,
`gogs` and `gitea`. It has no role in the fiction — part of the material
substrate (synopsis §19).

## Start locally

```sh
scripts/infra/postgres.sh      # or scripts/infra/compose-up.sh
```

- Internal only (no published ports); the platforms reach it at
  `postgres-gogs:5432` on the `gogs-local` network.
- Data: `.state/postgres` (85 MB; seeded from the original external
  directory, which can now be removed).
- Credentials: user `gogs`, password from `POSTGRES_PASSWORD` in `.env`.

## API key

None — the smoke test verifies with `pg_isready` and a `SELECT 1` per
database: `scripts/infra/smoke.sh postgres`.

## Notes

- The container name `postgres-gogs` is historical (it originally backed only
  gogs); both platforms use it now. Kept for compatibility with the polis CLI
  health checks (`POLIS_POSTGRES_CONTAINER` overrides).
