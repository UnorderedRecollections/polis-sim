# 0049: comprehensive integration tests

- **created:** 2026-09-11T16:00:00Z
- **type:** [tests]
- **depends-on:** 0043, 0047
- **status:** open

## Description

A systematic integration suite beyond today's demo scripts, covering
the whole matrix the demos currently sample:

- platforms × phases: gogs-phase-1, gitea-phase-1, gitea-phase-2
  (post-transition), including driven (director) and CLI-driven flows;
- the transition: happy path, retry-after-early-failure,
  retry-refusal-with-leftovers, double-transition refusal, gogs-host
  refusal;
- failure injection: mid-story git failures, platform 4xx/5xx on the
  probed quirks (token scopes, fork PRs, merge auto-close, hook
  delivery, SSRF denials), idempotency of `up --force` and teardown;
- the CI verdicts: defective/corrected acts, constitutional change with
  and without the Council's `SCRUTINY — APPROVED` comment;
- teardown assertions: nothing remains (containers, volumes, networks,
  repos/users) — the volume-prune behavior included;
- deterministic seeds everywhere; time-bounded polling helpers shared
  with the demos (extract the repeated API-poll loops into a test lib).

Runner notes: container-backed cases stay in `tests/*.sh` style; the
pure layers get pytest coverage; the mock forge (task 0047) makes the
matrix fast and failure-injectable.

## Completion

<!-- filled in when the task is done:
- **finished:**
- **commit:**
-->
