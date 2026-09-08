# 0016: Resource files — implementation

- **created:** 2026-09-09T08:45:00Z
- **type:** [simulation]
- **depends-on:** 0011, 0015
- **status:** in-progress

## Description

Implement the resource-file schema from `docs/design/resource-files.md`:

- `data/world/legal/resources/<jurisdiction>/<kind>.yaml` for the seeded
  jurisdictions (fisheries, harbor-navigation, land-commons; taxation has
  none — conduct-status);
- `polis/sim/resources.py` — model + loader with bidirectional
  cross-validation (jurisdiction `resources:` index ↔ files);
- norm validation tightened: resource-typed `object.kind` checked against
  resource files, not just the index;
- CLI: `polis world resources list [--jurisdiction]` and
  `polis world resources show <kind>`.

## Completion

<!-- filled in when the task is done:
- **finished:**
- **commit:**
-->
