# 0056: performance and scale tests (cities and actors)

- **created:** 2026-09-13T17:12:46Z
- **type:** [tests]
- **depends-on:** 0053, 0049
- **status:** done

## Description

How does the apparatus scale? Today every sim is 9 cities / 63 persons
and demos are seconds; the federation should hold at **20 cities** and
**hundreds of actors** without the machinery becoming the bottleneck.

Define and measure:

- **scale dimensions:** cities (2 → 20), actors (a dozen → hundreds),
  corpus size (files/history), concurrent sims on one host;
- **metrics:** `provision up` wall time; per-story `sim drive` time
  (phase I and phase II); per-tick API call counts; git history/pack
  size; platform DB size; disk/volume growth; transition duration; one
  CI pipeline duration; journal/matters size;
- **harness:** a way to generate larger worlds (`world genesis` variant
  or a test-only generator), K stories per configuration, deterministic
  seeds, and a metrics table/trend line;
- **budgets:** absolute thresholds for "usable" plus regression budgets
  (e.g. provisioning must not grow worse than x% per doubling) — decide
  what a failure means for CI (nightly vs per-commit tags);
- **known pressure points to watch:** per-user token minting (one API
  call/actor), per-city fork/clone work, the proxy hairpin for
  in-network fetches, gitea/gogs bootstrap waits, woodpecker's SQLite
  under many repos.

Deliverable: a repeatable harness + a report in `docs/design/` (or a
task annex) with the numbers and the conclusions; fixes folded into
this task or split out.

## Progress log

- **2026-09-13 — harness landed, baseline measured, one bug found and
  fixed.** `build_world(seed, cities, legislators_per_city,
  delegates_per_city)` + `polis world genesis --cities N` (the canonical
  world is byte-identical by default; the name pool grew to 24 names —
  appended, never reordered), and `tests/performance_test.py` (worlds,
  per-size provisioning/drive timing, record/git-pack sizes, restore).
  Baseline (seed 42, 1 story): 9/64 → provision 9.8 s; 15/106 → 12.8 s;
  20/141 → 15.7 s; 20/281 → 25.7 s; drive flat at ~1.2 s/story.
  Conclusions and proposed budgets in `docs/design/performance.md`;
  documented in `docs/testing.md`.
- **Bug found by the actor-heavy point (folded in):** provisioning
  hardcoded the Keeper as `e.vexley`; at non-canonical rosters the actual
  `federal-archivist` occupant lost archive write and the Keeper's push
  failed (HTTP 403). Provisioning now resolves the occupant from the
  civil registry. Verified: 20 cities/281 persons enacts 1/1 after the
  fix.

## Completion

- **finished:** 2026-09-13T20:56:25Z
- **commit:** bc34c5c
