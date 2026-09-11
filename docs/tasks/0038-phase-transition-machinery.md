# 0038: phase transition machinery

- **created:** 2026-09-10T18:00:00Z
- **type:** [infrastructure]
- **depends-on:** 0036, 0037
- **status:** done

## Description

When the transition acts are ratified: flip federation phase to 2 via ordinary channels, per-sim gitea+woodpecker with OAuth, Mechanical Magistrate CI active, docket/bill dispatch switches to real PRs (same command surface).

See docs/design/roadmap.md for context and ordering.

Decisions taken (user, 2026-09-11): execution path = explicit
`polis sim transition <run>`; the phase flip is recorded by the runtime
in the ratification transaction (situation + registry + slices); the
proceedings record truly moves into the platform in phase 2 (matters
serve phase 1); the Mechanical Magistrate's CI is deferred to 0038b.

## Completion

- **finished:** 2026-09-11T09:20:00Z
- **commit:** (main)
