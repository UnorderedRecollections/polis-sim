# 0055: BDD infra failure tests (failure modes decided first)

- **created:** 2026-09-13T17:12:46Z
- **type:** [tests]
- **depends-on:** 0053
- **status:** done

## Description

What happens when the machinery itself fails? Today: mostly "the demo
explodes and a human reads the traceback". Build a failure-injection
suite over the BDD integration (0053) so the apparatus's behavior under
infrastructure failures is specified and tested.

**Decision gate — do this first.** Failure modes and the expected
behavior are NOT decided yet; agree them before writing any test (in
this task's description, or better a short `docs/design/failure-modes.md`).
At minimum decide, for each candidate:

- **candidates:** postgres down/unready; gogs/gitea failing to start,
  crash-looping or unreachable mid-provision; the front proxy misrouting
  or its upstream gone (502s); a port conflict on `proxy_port`; the
  woodpecker server or agent down; webhook delivery failing (the forge
  cannot reach `/ci`); a broken/missing OAuth application or secret; a
  revoked/expired API token; a corrupted/locked `world.json` or
  `matters.json`; a half-provisioned sim (leftovers);
- **expected behavior per failure:** fail fast with a specific remedy?
  retry with backoff (which failures)? partial rollback or keep the
  partial state for inspection? what does `provision status`/`polis
  health` report? does an infra failure enter the legal record (the
  journal/matter store) at all — or only the operator's logs (the
  three-stores ontology says the legal record is for legal acts);
- **injection points:** container stop/kill, container that cannot
  start, API 4xx/5xx, network partition (proxy/forge), timing races.

Prefer the mock forge (task 0047) and CI runner (task 0048) once they
exist — they make injection fast and deterministic; until then,
container-level failure + scripted API faults are enough. Coordinate
with task 0049 (comprehensive integration tests), which covers the
happy-path matrix and idempotency.

Deliverables: the failure-mode decision note; failure scenarios/tags in
behave; any fixes the expected behaviors imply (or separate `[bugfix]`
tasks when they are not small); docs updates where behavior is
user-visible.

## Progress log

- **2026-09-13 — decision gate prepared; tests not started (by design).**
  `docs/design/failure-modes.md` drafted: principles (record integrity,
  fail-fast-with-remedy, idempotent recovery, no silent half-state), 15
  candidate failures with proposed behavior and injection points, and
  seven decisions requested in §5 (recommended defaults marked). The
  suite will be written once those are agreed; implementation notes:
  a `tests/failures.sh` matrix reusing the mock forge (0047)/runner
  (0048) when they land, asserting non-zero exits with remedies, record
  integrity and idempotent recovery. Any behavior fixes the decided
  tests require become separate `[bugfix]` tasks.

- **2026-09-14 — decisions approved; implemented and verified.**
  `tests/failures.sh` (+ `tests/failures_test.py`, 15 checks) implements
  the agreed provisioning/deployment cases; three behavior fixes folded
  in: `provision.up` fails fast on an empty world (no half-provisioned
  sim), `_up_proxy` refuses a taken persisted port naming it, and
  `provision.status` reports an unreachable platform instead of
  tracebacking. Verified 15/15; docs updated (`failure-modes.md` §5
  decisions + §7 implementation, `docs/testing.md`). PR for review.

## Completion

- **finished:** 2026-09-14T09:49:09Z
- **commit:** 23546b4 (merge of PR #30)
