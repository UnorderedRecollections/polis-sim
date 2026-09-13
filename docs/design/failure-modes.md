# Failure modes and expected behavior (task 0055)

Status: **proposal awaiting decisions** (2026-09-13). The failure tests
are deliberately not written yet: the taxonomy and the expected behavior
below (especially §5) must be agreed first — behavior is a product
decision, not an implementation detail. Nothing here is implemented.

## 1. Why this exists

Today an infrastructure failure erupts as a traceback and the operator
reads it. The apparatus should instead behave predictably: **fail fast
with a specific remedy where it can, degrade where that is honest, and
never silently corrupt the record.** The failure suite will hold that
behavior still.

## 2. Principles

- **The legal record is sacred.** A failed legal act leaves no journal
  entry (the journal is the record of what happened); the failure itself
  is visible in `stories.json`, the scenario scoreboard, or the error —
  never as a half-written act.
- **Machinery failures are the operator's, not the law's.** The story/
  matter state says an act was enacted even if the CI, proxy or a
  container later falls over; the machinery is repaired by machinery
  commands, not by rewriting the record.
- **Fail fast with the remedy.** A blocked operation names what is
  wrong, which container/sim/port, and the command that fixes it.
- **Recovery is idempotent.** `provision up --force`, `up_woodpecker`
  (repo enable is idempotent), `sim resume`, `up --force` port reuse.
- **No silent half-state.** `provision status` / `polis health` are the
  diagnosis surface; partial state stays inspectable.

## 3. Candidate failures → expected behavior (proposal)

| # | failure | proposed behavior | injection |
|---|---|---|---|
| 1 | postgres down/unready before the platform starts | bounded wait (existing `pg_isready` loop), then fail naming `postgres` + `logs` | stop postgres; start the platform first |
| 2 | gogs/gitea crash-loops or restarts mid-bootstrap | bounded retries (existing), then fail naming the container and its last log line | kill during migration; wrong DB password |
| 3 | proxy up, upstream gone (502s) | readiness fails after its timeout; `status`/`health` name the proxy and the upstream | stop the platform container |
| 4 | `proxy_port` conflict at start | **fail** naming the port and the sim (`up --force` currently reuses the persisted port); do not silently move | bind the port, then `up` |
| 5 | token mint race right after bootstrap | already retried (0042): bounded retries, then fail with the last API error | scripted 502 during mint |
| 6 | operator container missing/stopped | `sim drive` proxies if it can, else runs locally with a warning (existing degrade); `health` reports | stop/remove the operator |
| 7 | CI erection fails after a successful transition | **keep the phase flip** (the legal act happened) and make the CI a retryable machinery step: `up_woodpecker` idempotent; the story stays enacted | break the OAuth app/woodpecker start |
| 8 | webhook delivery failing (forge cannot reach `/ci`) | CI verdict polling times out with a clear "no status" outcome; the scenario pauses; `health` gains a webhook/proxy reachability check | stop woodpecker; block the proxy path |
| 9 | OAuth app missing/bad secret | `up_woodpecker` fails with the OAuth step named; remedy: re-run (idempotent) | delete the app; corrupt the client secret |
| 10 | revoked/expired API token | preflight/API call fails `token invalid`; remedy: `provision up --force` (fresh token) — never silently recreate | revoke a token in the platform |
| 11 | `world.json`/`matters.json` corrupted/locked | load fails fast; no auto-repair; snapshot/restore advice | truncate the file |
| 12 | half-provisioned leftovers | `status` lists what is missing; `destroy` is tolerant; `up --force` reconciles | kill provisioning midway |
| 13 | disk/volume exhaustion | container start errors surface; `destroy` prunes orphan volumes (existing) | — (hard to simulate; manual) |
| 14 | mid-story git/API failure inside a plan | the act aborts; **no journal entry**; `stories.json` carries status `failed` + error; the failed attempt stays in the record | mock forge 5xx; kill platform |
| 15 | record files missing (`sim fresh`/epoch edge) | `fresh`/`epochs` fail with the files named; no partial archive | delete a record file |

## 4. Injection points

- container stop/kill, a container that cannot start (bad image/env),
  scripted platform 4xx/5xx, network partition (proxy↔forge),
  timing races around bootstrap;
- prefer the **mock forge** (task 0047) and **CI runner** (0048) once
  they exist: fast, deterministic, and injection-friendly; until then,
  container-level failures + scripted API faults (secrets/env).
- coordinate with task 0049 (comprehensive integration tests) which
  covers the happy-path matrix and idempotency.

## 5. Decisions requested (recommended defaults marked)

1. **CI erection after a successful transition:** keep the phase flip,
   repair the CI with a retry (`up_woodpecker`) — *recommended* — or roll
   the transition back?
2. **Partial plan execution:** failed legal acts leave no journal entry;
   they appear as `failed` in `stories.json` / the scenario scoreboard —
   *recommended* — or should a "failed attempt" observation enter the
   journal?
3. **`proxy_port` conflict on re-up:** fail with the remedy —
   *recommended* — or transparently re-allocate and persist the new port?
4. **Invalid token mid-life:** fail and require `up --force` —
   *recommended* — or auto-mint a fresh token and continue?
5. **Auto-restart policy:** rely on `--restart unless-stopped` —
   *recommended* — or add CLI-level supervision/retry loops?
6. **Diagnosis surface:** extend `polis health` with proxy + webhook
   reachability checks — *recommended* — or keep health as-is?
7. **Where the tests live:** a `tests/failures.sh` matrix keyed by the
   cases above — *recommended* — or behave scenarios tagged `@failure`?

## 6. What the suite will assert (once decided)

- the operation exits non-zero, with a message naming the failure and
  the remedy (no bare traceback);
- the record is intact: no legal act appears for a failed attempt, and
  completed acts remain;
- the state is inspectable (`provision status`, `polis health`,
  `stories.json`) and recovery is idempotent (re-run the failed step).
