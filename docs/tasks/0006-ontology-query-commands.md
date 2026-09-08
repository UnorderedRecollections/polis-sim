# 0006: Ontology query commands (`polis world …`)

- **created:** 2026-09-08T18:10:00Z
- **type:** [simulation]
- **depends-on:** 0005
- **status:** in-progress

## Description

Full query surface over the data-driven ontology, so agents and other tools
can interrogate the legal DSL **irrespective of the underlying storage**
(YAML today, a database later — the CLI is the stable interface):

- `polis world jurisdictions inspect <slug> <component>` — one component of
  a jurisdiction (`actors`, `resources`, `activities`, `properties`,
  `rule-forms`, `disputes`);
- `polis world actors list` — every registered actor kind (core +
  jurisdiction-registered at load time) with parent/label/flags;
- `polis world actors show <kind>` — one actor kind with its derivation chain;
- `polis world legal-objects list` — all legal object kinds (implemented
  flags + notes);
- `polis world procedural-events list` — all procedural events with their
  matter-store mappings;
- `polis world relations list` — the thirteen legal relations (for
  completeness).

Requires `parent` recorded on dynamically built types in
`polis/sim/ontology.py`.

## Completion

<!-- filled in when the task is done:
- **finished:**
- **commit:**
-->
