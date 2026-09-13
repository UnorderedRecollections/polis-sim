# 0051: Documentation — delivery pipeline and law-in-effect stack

- **created:** 2026-09-10T22:00:00Z
- **type:** [simulation]
- **depends-on:** none
- **status:** done

## Description

Capture the theoretical detour (2026-09-10): CI is the normative layer,
but CD — *delivery* — decomposes in the legal order into ratify →
promulgate → receive → apply; and law in force ≠ law in effect requires
the L0–L5 stack (text → legal state → action → compliance → enforcement
→ behavior), mapped against what the sim already has (activity
signatures, the legitimacy predicate, conduct jurisdictions, holdings)
and what it lacks (world state, act events, violation consequences,
dispositions).

Deliverables:
- `docs/isomorphism/law-in-effect.md` — the concept document;
- `docs/design/enforcement-arc.md` — the implementation design (world
  variables, act events in the journal, violation→accusation→trial
  template, dispositions, how it grounds the director's candidates);
- roadmap entries 0043+ for the enforcement arc and the post-ratification
  delivery arc (promulgation cadence + reception tracking).

## Completion

- **finished:** 2026-09-10T22:15:00Z
- **commit:** e3caf4f (renumbered to 0051 on 2026-09-13 — the 0040 slot
  collided with the headless dev-rig gitea bootstrap task)

Delivered: `docs/isomorphism/law-in-effect.md` (the delivery pipeline —
ratify → promulgate → receive → apply, with the software/legal/sim
mapping — and the L0–L5 stack: text, legal state, action, compliance,
enforcement, behavior; what exists vs what's missing) and
`docs/design/enforcement-arc.md` (world-state.yaml, ambient act events
with compliance tags, violation channels — prosecution template +
evidenced grievances, dispositions, minimal intrusions). Roadmap
addendum added; implementation tasks filed as 0043 (enforcement arc)
and 0044 (delivery arc) — renumbered after a numbering collision with
concurrently created 0041/0042.
