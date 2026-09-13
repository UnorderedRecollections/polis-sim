# Performance and scale — the harness and the baseline

Status: harness landed, baseline measured (task 0056, 2026-09-13). The
full sweep and the CI budgets are the remaining policy decision (task
0049 owns the CI thresholds).

## 1. What this measures

The federation should hold at **20 cities** and **hundreds of actors**.
`tests/performance_test.py` builds worlds of a given size
(`build_world(seed, cities=N, legislators_per_city, delegates_per_city)` /
`polis world genesis --cities N`), provisions one sim per size, drives
director stories, and records:

| metric | how |
|---|---|
| provisioning wall time | around `provision.up` |
| drive time per story | around `director.drive` |
| roster / repos / users | the generated world + `provision.json` |
| journal / matters size | by bytes after the stories |
| archive git pack | the working clone's `.git` bytes |

The canonical world is snapshotted and restored around every run. Run it
with `uv run python tests/performance_test.py --cities 9,15,20` (see
`docs/testing.md`).

**Not yet instrumented:** API call counts per tick, transition + CI
durations (phase 2), platform DB size, concurrent sims, and disk growth
beyond the git pack.

## 2. Baseline (seed 42, 1 story, fisheries, macOS podman machine)

| cities | persons | provision s | drive s/story | enacted | git pack B |
|---|---|---|---|---|---|
| 9 | 64 | 9.8 | 1.2 | 1/1 | 38,815 |
| 15 | 106 | 12.8 | 1.2 | 1/1 | 40,972 |
| 20 | 141 | 15.7 | 1.2 | 1/1 | 42,729 |
| 20 | 281 | 25.7 | 1.2 | 1/1 | 42,782 |

## 3. Conclusions

- **Provisioning is the cost driver and scales with the roster** — about
  **0.07–0.09 s per actor** (per-user account + token minting, one API
  call each): 0.75 s/city at the canonical roster, ~26 s at 281 actors.
  Linear, no cliff: token minting, not the platform, dominates.
- **Drive time is flat** (~1.2 s/story from 64 to 281 persons, 9 to 20
  cities): the director picks from the situation, not the roster size.
- **The archive pack grows by ~1.7 KB per city** at this act volume —
  history size is act-driven, not roster-driven.
- **The 20-city/281-actor point found a real bug**, now fixed:
  provisioning hardcoded the Keeper as `e.vexley`; at non-canonical
  rosters the actual `federal-archivist` office holder lost write on the
  archive and the Keeper's push failed with HTTP 403. Provisioning now
  resolves the occupant from the civil registry (`provision.py`).

## 4. Budgets (proposed)

- provisioning ≤ **0.15 s/actor** and ≤ **60 s at 281 actors**;
- drive ≤ **5 s per story**;
- a **>25% regression** against the recorded baseline at the same size is
  a failure.
- CI meaning: sizes 9 and 20 with one story are cheap enough to run in a
  nightly/slow job; the actor-heavy point (281) stays opt-in. The CI
  tasks (0045/0049) decide where this lands; until then the harness is a
  manual/slow suite.

## 5. Next steps

- transition + CI timings on a gitea sim (phase 2) — the remaining
  unmeasured arc;
- per-tick API call counts (wrap the clients) and platform DB size;
- concurrent sims on one host;
- beyond 20 cities: the name pool (24 names) and per-same-host resource
  limits become the constraint.
