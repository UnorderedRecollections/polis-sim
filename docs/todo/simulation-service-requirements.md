# TODO: Simulation service requirements

## The mishap

After the phase-1 ontology fix (matters live in the institutions, not in the
platform), `docket`/`bill` operations on the **matter store** still resolve the
actor through `Chamber` (`polis/legislation/chamber.py`). Chamber is a
git/platform working context — remotes, repo_dir, platform client, host-swap —
but matter-store operations need none of that. They use Chamber only to answer
"who is acting, from which city".

That works for now (CLI with `--as`/`--city`), but it couples the political
layer to the archival layer's context object.

## Why it will hurt later

If the simulation becomes a service of its own — e.g. to **render the
simulation state** and **step through it** (advance one event, replay a
session, drive multiple city agents) — then:

- the matter store needs concurrent, transactional access (not load-modify-save
  JSON from CLI processes);
- actor resolution must not require a git working context (a rendering UI or a
  stepper has no `repo_dir`);
- the procedural record (matter events) becomes an **event log** the service
  replays — worth designing `MatterEvent` with that in mind;
- the CLI's `enact(plan)` pattern (execute immediately) needs a service
  equivalent: submit intent → validate → record → execute machinery.

## Requirements to design for

1. **Actor resolution independent of Chamber** — a small identity/context
   object (who, city, offices, powers) usable by both the CLI and a future
   service. Chamber should *consume* it, not be it.
2. **Matter store behind an interface** — today JSON files; later a service or
   DB. Keep `polis/matters.py` as the only access point (it already is).
3. **Event-sourced proceedings** — matter events as the canonical record of the
   political process; state (`status`) derivable by replay.
4. **Stepping/replay** — the service should be able to reconstruct any point in
   the simulation: git gives archival time, matters give political time; the
   service correlates them.
5. Keep the two clocks distinct: **git history = legal time**,
   **matter events = institutional time**. Do not merge them.

Related decisions: no database for now (files are the stores); YAML sketch in
earlier notes superseded by JSON.
