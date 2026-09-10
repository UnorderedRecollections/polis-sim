# 0004: `polis world` legal-data inspection commands

- **created:** 2026-09-08T17:40:00Z
- **type:** [simulation]
- **depends-on:** 0003
- **status:** done

## Description

CLI inspection of the legal-design YAML from task 0003:

- `polis world jurisdictions list` — table of all fifteen (slug, name,
  corpus dir, counts);
- `polis world jurisdictions show <slug>` — full detail of one jurisdiction
  (resources, actors, activities, properties, rule forms, disputes);
- `polis world moves list` — the legal moves with their command-surface
  mapping and the machinery aliases;
- `polis world templates list` / `polis world templates show <story_type>` —
  story grammars with participants and sequence.

Read-only; data via `polis/sim/legaldata.py`.

## Completion

- **finished:** 2026-09-10T21:48:57Z
- **commit:** 5103692
