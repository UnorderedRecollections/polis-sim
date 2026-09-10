# 0005: Data-driven ontology (farm hardcoded DSL out to YAML)

- **created:** 2026-09-08T17:55:00Z
- **type:** [refactoring]
- **depends-on:** 0003, 0004
- **status:** done

## Description

Replace the hardcoded registries in `polis/sim/ontology.py` with YAML under
`data/world/legal/ontology/` — one file per category:

- `actors.yaml` — `Actor` base + kinds with **explicit `parent:` properties**;
  the loader dynamically creates subtypes (`ActorPerson`, `ActorCitizen`, …)
  as a real Python class hierarchy.
- `legal_objects.yaml` — `LegalObject` kinds with metadata (`implemented`,
  notes).
- `legal_relations.yaml` — the thirteen relation verbs.
- `procedural_events.yaml` — events with their matter-store mappings.
- Jurisdictions: concrete objects built at load time by a **factory** over
  `data/world/legal/jurisdictions/*.yaml` metadata (task 0003 files stay
  authoritative).

Unknown actor kinds (e.g. `harbor-master`) register on demand as subclasses
of `ActorJurisdictional`. API surface preserved: `is_actor_a`,
`JURISDICTIONS`, `MATTER_EVENT_MAP`.

## Completion

- **finished:** 2026-09-10T21:48:57Z
- **commit:** cfe8049
