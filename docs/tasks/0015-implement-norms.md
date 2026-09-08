# 0015: Implement norms (rules in force)

- **created:** 2026-09-09T08:10:00Z
- **type:** [simulation]
- **depends-on:** 0010
- **status:** in-progress

## Description

Implement the Norm model from `docs/design/norms-generalization.md`:

- `data/world/legal/ontology/norm_kinds.yaml` — sources (custom/statute/
  treaty/charter + which require `source_ref`) and object types.
- `data/world/legal/norms/<jurisdiction>.yaml` — foundational seed norms
  (fisheries + a representative set).
- `polis/sim/norms.py` — pydantic models, validating loader, and pure
  lifecycle operations (enact / supersede / repeal with custom revival /
  in_force queries / contested holdings; incompatibility hook for 0013).
- CLI: `polis world norms list [--jurisdiction] [--in-force]`,
  `polis world norms show <id>`.
- tests.

**Snapshot principle (user decision):** norm sets are always YAML — seed
and evolved state share one format and one loader; the engine is agnostic
about whether a file is a bootstrap seed or a snapshot. Evolution =
load → apply operations → save; a snapshot of the simulation is a valid
bootstrapping point for another run.

## Completion

<!-- filled in when the task is done:
- **finished:**
- **commit:**
-->
