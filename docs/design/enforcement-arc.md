# The enforcement arc — design (task 0043 preview)

Status: design v1, from docs/isomorphism/law-in-effect.md. The middle
layers (L2–L5) that make law *effective* rather than merely *in force*.

## 1. World state (L2's ground)

A new per-run document `data/sims/<run>/world-state.yaml`:

```yaml
variables:
  northern_banks.stock: 1000        # arbitrary units; activities move them
  eastern_shoals.stock: 600
  season: spring                     # for closures / seasonal norms
```

- Seeds from the situation generation (0035) with defaults; hand-editable
  like situation.yaml (same snapshot principle).
- Activities mutate variables per their impact (`depletes`: −amount,
  `enriches`: +…). Amounts seeded like everything else.
- `season` advances every N ticks (the sim's wall clock).

## 2. The act event (L2)

Each drive step, before story work, the director plays **ambient action**:
a seeded sample of parties performs their activities against the world
state. Each act is one journal entry (`kind: action`, `action:
world.act`) with anchors `{variable: before → after}`.

Compliance (L3) is the legitimacy predicate turned 90°: the act's harm
is **allocated** (a norm in force regulates the actor over object+aspect)
→ `lawful`; otherwise → `violation`, recorded with its evidence (the
norms that should have allocated it and didn't).

## 3. Violations feed two channels (L4)

- **Accusable facts**: violations over a conduct paradigm's object become
  candidates for the *criminal* flow: a new story template
  `prosecution` (accuse → (optional arrest) → try → penalty). The
  magistrate is cast; penalties write back to the situation
  (`composition_instead_of_punishment` = a composition norm;
  `outlawry` = a status norm on the offender).
- **Grievance with a case**: violations over a resource become *charged
  candidates with evidence* — the injured party's petition cites the
  actual violation event, not a hypothetical friction. Both candidate
  kinds coexist; the actual ones outrank hypothetical in selection.

## 4. Dispositions (L5)

Every person gets a seeded disposition at provisioning (world registry,
`disposition: lawful|pragmatic|opportunistic` — derived from the genesis
seed, so it's stable):

- **lawful**: acts only when the act is (or would be) lawful; petitions
  when harmed;
- **pragmatic**: complies while stocks/risks are comfortable, violates
  under pressure;
- **opportunistic**: violates when the expected penalty is below the
  expected gain (seeded dice).

Disposition feeds action selection AND petition pressure — a city whose
fishers keep violating the quota is also a city agitating to change it:
the post-ratification landscape as data.

## 5. What changes in existing pieces (minimal intrusions)

- `sim/journal.py`: nothing (act events are ordinary entries).
- `sim/events.py`: gains `actual_candidates(violations)` alongside
  `charged_candidates` (hypotheticals); selection prefers actuals.
- `sim/director.py`: the drive step becomes **ambient action → compliance
  → queue → story**; new template `prosecution` bound to the criminal
  jurisdiction (finally used).
- `sim/situations.py`: seeds `world-state.yaml` alongside situation.yaml.
- Nothing in legislation/ or the platforms changes — enforcement is a
  sim-layer concern; law remains git.

## 6. The delivery arc (task 0044, sibling)

Post-ratification: promulgation cadence (an edition every N enactments —
the epoch gets citable releases) and reception (city archivists
`archive receive` after federal acts; a `reception` anchor per city so
lag is observable). Both are existing machinery the director simply
doesn't call yet — much smaller than 0043.
