# 0054: BDD jurisdiction suites — one scenario per jurisdiction

- **created:** 2026-09-13T17:12:46Z
- **type:** [tests]
- **depends-on:** 0053
- **status:** done

## Description

Every test today legislates in **fisheries**; the other fourteen
jurisdictions are only seed-validated (`polis world legal validate`),
never exercised end to end. Domain-specific runtime errors have surfaced
exactly this way before:

- task 0035 caught live that generated norms bound the resource
  *overseers* instead of the users, so all harm was allocated and the
  situation held no friction — every story was skipped (a bug invisible
  in fisheries-only testing until it wasn't);
- `docs/todo/runtime-and-cross-jurisdiction-resources.md` documents two
  open classes: runtime-created resources (validation checks
  design-time files only) and cross-jurisdiction object references
  (river-water ↔ fisheries is the canonical pair).

Build one suite per jurisdiction (15), each scenario: generate/validate
the situation (`polis world situation new <slug>`), provision, drive at
least one whole story to enactment, and assert the archive/situation
outcome — parameterized by the same bindings and platform tags as 0053
(`@gogs` phase I, `@gitea` including phase II once 0053 lands).

Deliverables:

- one feature per jurisdiction (or one data-driven generator emitting
  them from the jurisdiction index), deterministic seeds;
- a runner that loops the 15 suites and reports per-jurisdiction
  pass/fail (tagged, not part of the default fast behave run);
- a triage list of the domain bugs the suites surface — each becomes a
  fix in this task or a separate `[bugfix]` task, whichever is cleaner;
- a note in the task (and the docs, if conventions emerge) of what each
  jurisdiction needs to exercise honestly (actors, resources,
  paradigms, cross-jurisdiction cases).

Acceptance: all 15 jurisdictions have an executable, passing (or
explicitly bug-tracked) scenario; failures are reproducible with the
recorded seed.

## Progress log

- **2026-09-13 — implemented and verified.** Data-driven suite
  `tests/jurisdictions_test.py` (+ `tests/jurisdictions.sh` runner): one
  provisioned gogs sim; per jurisdiction (15): generate and validate the
  situation from the jurisdiction's own data, clear the record, seed a
  fresh run, drive one whole director story, and assert enactment plus a
  recorded ratification. Per-jurisdiction summary with the story title
  or error; `--seed` for reproducibility. Verified **seeds 41 and 7:
  15/15 enacted both times** — no domain bugs surfaced at these seeds
  (the historical 0035 friction bug stays fixed).
- **Triage / coverage note.** Resource-paradigm and conduct-paradigm
  jurisdictions are both exercised end to end (the generated situations
  cover both branches). The cross-jurisdiction object-reference class in
  `docs/todo/runtime-and-cross-jurisdiction-resources.md`
  (river-water ↔ fisheries) is **not reachable by a single-jurisdiction
  run** — multi-jurisdiction stories remain future work; that TODO
  stands.
- Added to `tests/all.sh` (full verification; ~4 min) and documented in
  `docs/testing.md`/AGENTS.md. Cross-jurisdiction seed sweep (more seeds)
  is cheap: `tests/jurisdictions.sh --seed N`.

## Completion

- **finished:** 2026-09-13T20:43:11Z
- **commit:** c52d6cb
