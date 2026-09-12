# Law in force ≠ law in effect — the delivery pipeline and the L0–L5 stack

A theoretical note (2026-09-10) on what CI/CD means for the legal half of
the isomorphism — and what the simulation must therefore contain.

## 1. CI verifies; CD delivers — but delivery decomposes

In software, CI verifies the change and CD puts the artifact into effect
for its users. Merge to main is neither: it produces the artifact.

Legal orders have always known this gap and have vocabulary for every
step. After a bill is **ratified** (the merge — the artifact exists):

| step | legal name | software name | sim primitive |
|---|---|---|---|
| the text joins the authoritative history | enactment | merge | `bill ratify` |
| the law is made public, citable | **promulgation** | release / tag | `archive promulgate`, `archive editions` |
| delayed effect ("enters into force on…") | *vacatio legis* | canary / scheduled rollout | *(not modeled yet)* |
| cities pull the enactment into their own archives | **reception** | **deployment to nodes** | `archive receive` |
| officials apply, courts adjudicate, people conform | **application** | the running system | *people, not machinery* |

A city that has not received is running yesterday's legal order — a
staggered fleet, which is exactly what real federations are. Reception
lag per city is a beautiful, measurable observable.

So enactment alone is not delivery. The delivery pipeline of a legal
order is **ratify → promulgate → receive → apply**, and only the first
step is mechanical. The middle two are git operations the sim already
knows; the last is people — and the sim must measure it through conduct,
not containers.

## 2. The L0–L5 stack — what "in effect" requires

For law to be *in effect*, actors must act, their acts must be checked
against the law, and violations must have consequences:

```
L0  legal text        the archive (git) — what the law says
L1  legal state       the situation (norms + holdings) — what binds whom, now
L2  action layer      actors ACT: the fisher fishes, the authority inspects —
                      and the world changes (stocks deplete, steps crumble)
L3  compliance layer  each act checked against L1: lawful | violation
L4  enforcement layer violations → accusation → trial → sanction
L5  behavior layer    actors adapt: comply, violate, or agitate to change
                      the law back — the post-ratification landscape
```

## 3. What the sim already has

- **The action vocabulary** — activity signatures (`fish`, `inspect`,
  `accuse`, `try`): actors, affects, impacts, preconditions. Today they
  *imagine* action (friction hypotheticals); they are ready to *be* action.
- **The compliance predicate** — the legitimacy hook answers precisely
  "is this harm allocated by a norm in force?" Turned 90°, it is the
  violation check: an act whose harm is not allocated is an **offense**.
- **The enforcement vocabulary** — the conduct paradigms (criminal:
  `accuse`, `arrest`, `try`; `proportional_penalty`,
  `composition_instead_of_punishment`, `outlawry`) were authored for
  exactly this flow and are currently idle.
- **Holdings** — who may do what; a violation is action without, or
  beyond, a holding.

## 4. What the sim lacks (the enforcement arc, task 0043)

1. **World state** — quantities: `northern_banks.stock`, the season.
   A quota means nothing without a stock; a closure without a calendar.
   This is the sim's production environment.
2. **The act as event** — an actor performs an activity at a tick:
   journaled (the journal is already the event log), mutating world
   state, tagged lawful/violation by L3.
3. **Violation consequences** — violations become *accusable facts*;
   the criminal flow (accuse → try → penalty) becomes a story template
   fed by L3 detections, sanctions writing back to the situation
   (`outlawry` is a status norm).
4. **Dispositions** — actors must be *able* to break law, or enforcement
   has no stories: a seeded spectrum (lawful / pragmatic / opportunistic)
   driving action selection under new rules.

## 5. Closing the loop

The full CI/CD loop of a legal order:

> friction (telemetry) → petition (incident) → bill (patch) → scrutiny
> (CI) → ratification (merge) → promulgation (release) → reception
> (deploy) → conduct checked (runtime assertion) → violation handled
> (incident response) → pressure to amend (new incident).

The director's role changes with L2/L3: from *generating* conflicts
(hypothetical frictions) to also *adjudicating* ones the world produced
(actual violations, with evidence). Both kinds of stories are true;
the actual ones carry a case.

And the honesty the isomorphism forces: **git delivers the text;
institutions and people deliver the effect.** The Mechanical Magistrate
can verify forms and the archive can publish, but "the law is live"
means conduct changed — and the sim's production metrics are holdings,
stocks and violations, never containers.
