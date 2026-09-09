# 0023: The director — design document

- **created:** 2026-09-09T13:30:00Z
- **type:** [simulation]
- **depends-on:** 0019, 0021
- **status:** in-progress

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

<!-- filled in when the task is done:
- **finished:**
- **commit:**
-->
