# 0023: The director — design document

- **created:** 2026-09-09T13:30:00Z
- **type:** [simulation]
- **depends-on:** 0019, 0021
- **status:** done

## Description

Design the director: the component that drives the simulation forward
(situation → candidates → selection → story instantiation → execution via
`runtime.enact` → write-back → next tick). The document must cover what is
needed and the implementation options for each decision:

- story model (free-form vs template-driven vs hybrid);
- selection policy (seeded RNG vs priority vs scripted queue);
- casting rules (jurisdictional parties → world persons; jurists; ratifiers);
- remedy selection (which rule_form the bill proposes);
- the clock (tick granularity, story state machine, persistence);
- executor mechanics for provisioned sims (host-side chamber from sim
  slices);
- v1 scope, CLI surface, demo test plan.

Deliverable: `docs/design/director.md`.

## Completion

- **finished:** 2026-09-09T14:30:00Z
- **commit:** 4e443a5

Delivered `docs/design/director.md`: the drive loop; six decisions —
hybrid story model; **per-party** selection policies (seeded/priority/
scripted/interactive, queues appendable while running, journal-recorded
so replay stays deterministic); constituency+rotation casting;
remedy derived from incompatibilities; one story per drive step with
`stories.json` state; and the **containerized operator** executor
(`polis-operator-<sim>` on gogs-local, `/sim` volume with per-sim
matters/journal/stories/slices, host CLI as proxy) — revised per review
to run the operator inside the network instead of host-side chamber
host-swapping.
