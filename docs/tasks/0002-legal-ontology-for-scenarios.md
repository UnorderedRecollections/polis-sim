# 0002: Legal ontology (legal DSL) for scenarios

- **created:** 2026-09-08T17:05:00Z
- **type:** [simulation]
- **depends-on:** 0001
- **status:** done

## Description

Define the reusable legal ontology underlying the scenario/story layer:

- **Actor** taxonomy (Person → Citizen → Legislator/Delegate/Jurist/
  Archivist/Federal Archivist; collectives: City, Federation, Council,
  Committee; an intermediary **JurisdictionalActor** from which every
  jurisdiction-specific actor kind derives).
- **LegalObject** taxonomy (Constitution, Act, Amendment, Regulation, Treaty,
  Ordinance, Repeal, Petition, Judgment, Order, Declaration).
- **LegalRelationship** verbs (authorizes, prohibits, requires, permits,
  establishes, amends, repeals, supersedes, incorporates, delegates,
  ratifies, recognizes, exempts).
- **ProceduralEvent** vocabulary (petition filed … act repealed), aligned
  with the matter store's event strings.
- **Jurisdictions** (the 15 agreed areas of law) each with a **conflict
  grammar** (resource, actors, resource_properties, possible_rules) — fully
  worked for Fisheries, stubbed-but-structured for the rest.

Deliverables: `docs/design/legal-ontology.md` (the concepts + mapping onto
the existing polis models) and `polis/sim/ontology.py` (the importable DSL
used by storygen and the Behave step library).

## Completion

- **finished:** 2026-09-10T21:48:57Z
- **commit:** 5103692
