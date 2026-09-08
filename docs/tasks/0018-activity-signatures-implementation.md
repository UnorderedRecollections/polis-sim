# 0018: Activity signatures — implementation

- **created:** 2026-09-09T09:50:00Z
- **type:** [simulation]
- **depends-on:** 0012, 0008
- **status:** in-progress

## Description

Implement `docs/design/activity-signatures.md`:

- upgrade `activities:` to signatures in the seeded jurisdiction YAMLs
  (fisheries, harbor-navigation, land-commons, river-water, contract,
  taxation — covering all three paradigms; bare verbs stay valid elsewhere);
- `ActivitySignature` model with string coercion in the loader;
- `polis/sim/events.py` — friction derivation (raw harm table per impact
  kind) + charged-candidate computation (with the §4.1 legitimacy hook:
  harm allocated by an in-force norm is not charged);
- CLI: `polis world events candidates --jurisdiction <slug>` to inspect
  charged candidates against the seed;
- tests.

## Completion

<!-- filled in when the task is done:
- **finished:**
- **commit:**
-->
