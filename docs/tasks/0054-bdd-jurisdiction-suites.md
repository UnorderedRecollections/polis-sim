# 0054: BDD jurisdiction suites — one scenario per jurisdiction

- **created:** 2026-09-13T17:12:46Z
- **type:** [tests]
- **depends-on:** 0053
- **status:** open

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

## Completion

<!-- filled in when the task is done:
- **finished:**
- **commit:**
-->
