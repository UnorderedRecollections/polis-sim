# 0026: World credential cleanup + stop polluting world.json

- **created:** 2026-09-09T22:00:00Z
- **type:** [infrastructure]
- **depends-on:** 0021
- **status:** done

## Description

world.json accumulates `api_tokens["gogs@<sim>"]` entries from sims that
no longer exist — the civil registry should not carry per-sim machinery
credentials at all (the sim slices under `data/sims/<sim>/cities/` are
the per-sim credential store).

1. `provision up` must stop mutating world.json (tokens go only into the
   sim slices; verify nothing else reads the world.json copies).
2. New command `polis world cleanup` (dry-run by default, `--yes` to
   apply): find every `api_tokens` key of the form `<platform>@<sim>`
   (and any other per-sim residue) on persons in world.json, report, and
   remove.

## Completion

- **finished:** 2026-09-09T22:20:00Z
- **commit:** (pending — user commits)

1. `provision up` no longer mutates world.json — per-sim tokens go only
   into the sim slices (verified nothing read the world.json copies:
   chamber reads plain `gogs` keys from slices; `person show` only
   displays).
2. `polis world cleanup` (dry-run default, `--yes` applies): finds
   `api_tokens` keys containing `@` across all persons, reports per key,
   removes them and re-exports city slices. Verified live: 384 tokens
   across 6 dead sims removed; second run confirms "registry is clean".
