# 0056: performance and scale tests (cities and actors)

- **created:** 2026-09-13T17:12:46Z
- **type:** [tests]
- **depends-on:** 0053, 0049
- **status:** open

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

## Completion

<!-- filled in when the task is done:
- **finished:**
- **commit:**
-->
