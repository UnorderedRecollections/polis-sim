# Activity Signatures — design document

Status: design v1 (task 0012). Activity signatures are the engine of event
synthesis: they say *who can do what to which object, with what effect* —
so the director can compute *who is harmed by it* and thereby why a story
starts.

## 1. The core design decision: impact declared, friction derived

A signature could declare what it disrupts (`friction: [open_access
holdings]`), but that duplicates knowledge the situation already has, and
it rots as the situation evolves. Instead:

> A signature declares only the **impact** of the activity. **Friction is
> derived** by the engine, at event time, from the current norms and
> holdings — the same signature produces different frictions (or none) as
> the legal situation changes.

This keeps signatures small, timeless data, and makes the whole causality
of the simulation live in one place: the situation.

## 2. Schema

Activities in jurisdiction YAML upgrade from bare verbs to objects (a bare
string stays valid — it is a signature with only a verb):

```yaml
activities:
  - verb: fish
    actors: [fisher]            # actor kinds that may perform it
    target: resource            # resource | object | norm  (what it binds)
    affects: [stock]            # aspects of the target it touches
    impact: depletes            # an impact kind of the jurisdiction's paradigm
    preconditions:              # optional, declarative
      norm_in_force: open_access
      holding_required: true    # actor must hold something over the target
    direction: null             # river-water only: upstream → downstream
```

Field rules:

- `verb` must appear in the jurisdiction's (legacy) activity list — the
  string list remains the vocabulary, the objects add structure.
- `impact` must be one of the `impact_kinds` the jurisdiction's **paradigm**
  declares (`paradigms.yaml`) — the paradigm contract is enforced here.
- `affects` names aspects (the same vocabulary as norm `aspect:` and
  resource `properties:`) — this is what lets the engine join activities
  onto norms and holdings.

## 3. From signatures to event candidates

The director computes event candidates against the current situation:

```
for each activity signature s, actor A of kind k, object R in the situation:
    1. k ∈ s.actors and s.preconditions hold            → candidate (A, s, R)
    2. friction = derive(s.impact, R, situation):
         find parties B ≠ A whose holding over (R, aspect ∈ s.affects)
         is harmed by s.impact (table below)
    3. friction ≠ ∅  →  the candidate is *charged*:
         (A acts) + (B is harmed) + (the norm over R/affects may be contested)
```

**Friction derivation table** (who is harmed by each impact kind):

| impact | harmed party |
|---|---|
| depletes | actors holding use-rights over the same resource |
| blocks / occupies | actors whose holdings require access / right-of-way |
| pollutes | actors whose holdings depend on quality |
| enriches | — (no friction) |
| prohibits | actors whose current conduct/holding is of that kind |
| requires / burdens / obliges | the subjects who must now pay or act |
| penalizes | actors engaged in the penalized conduct |
| confers-status | existing holders of the status (dilution) |
| allocates | whoever receives the smaller share |

A charged candidate is a **story seed**: actor, action, victim, and —
through the norms over the affected aspect — the legal question. The
director picks among charged candidates (seeded random or by story
pressure), not among arbitrary events.

## 4. Impact write-back

Two layers, kept strictly apart:

1. **Physical/normative impact of the event itself** (the trigger): applied
   to the situation when the event executes — resource properties change
   (stock reduced, access blocked), the harmed holding is marked
   *pressured*, and a **grievance candidate** is attached to the harmed
   party. Raw events never change norms.
2. **The legal response** (the story): the grievance becomes a petition
   (matter), the petition a bill, the bill a norm change — through the
   already-implemented write-back on ratification (`enact` / `supersede` /
   `repeal` in `norms.py`).

Law is the only thing that changes norms; events only change facts. That
separation is what keeps the isomorphism honest when the simulation is
driving itself.

### 4.1 What enactment does to friction (the runtime loop)

The friction table gives *raw* harm; the situation decides whether it is
*charged*:

```
raw harm  = friction_table[impact](who else uses this object/aspect)
charged   = raw harm NOT legitimately allocated by a norm in force
```

When a remedying law is enacted (say a `quota` over the banks):

- activity **within** the quota → harm is allocated by law → friction ∅
  (the fix works; no grievance);
- activity **beyond** the quota → harm is not allocated → friction returns,
  now *against the norm itself* (an enforcement story, not a petition for
  new rules);
- supersession, repeal-with-custom-revival, and intensity-constraining
  rule forms (`quota`, `licensing`) are the machinery that changes which
  acts charge friction — no "opposite effect" rows are needed in the table;
- and the remedy creates friction of its own: the newly excluded or capped
  party is harmed *by the law* → their grievance → the next story.

Laws relocate friction; they never delete it. That is what keeps the
simulation producing stories: every enactment settles one legal question
and poses the next.

## 5. Worked example A — resource paradigm (fisheries)

Signature: `fish / actors: [fisher] / target: resource / affects: [stock] /
impact: depletes`.

Situation: N-0001 open_access over northern_banks; holdings H-0001
(Cogswich fishers) and H-0002 (Brasshaven fishers), both `fish` under
N-0001.

Candidate: Cogswich's fishers intensify fishing (`fish`, northern_banks).
Friction: H-0002 is harmed (shared stock depleted). Charged: A = Cogswich
fishers, B = Brasshaven fishers, aspect = stock/access_right, norm in
question = open_access.

Story: Brasshaven's fishers petition the federation → a bill proposing
`quota` (or `exclusive_access`) over northern_banks → reviews → enactment →
norm write-back. If the enacted rule is `exclusive_access`,
incompatibility with open_access is exactly the dispute material of 0013.

## 6. Worked example B — conduct paradigm (contract)

Signature: `enforce_bond / actors: [creditor] / target: object /
affects: [rate, security] / impact: penalizes`.

Situation: N-0051 `usury_cap` over `lending` (conduct), aspect `rate`;
holding H-0051 (a creditor's bond on the rolls).

Candidate: the creditor enforces a bond *above the cap*. Friction: the
debtor is harmed (penalized), and the enforcement *tests the norm* — is the
cap binding on old bonds? Charged: A = creditor, B = debtor, norm in
question = usury_cap.

Story: the debtor petitions → competing readings of the cap → an amendment
clarifying (or a repeal of the cap) → norm write-back: `usury_cap`
superseded by a clarified rule, or repealed — and the holding H-0051
becomes **contested** (does the old bond survive the new rule?).

No resource was depleted in example B: the "harm" is normative, and the
model handles both through the same machinery.

## 7. The river-water edge: direction

River-water is the one jurisdiction where impact **propagates spatially**:
an upstream diversion harms downstream holders even though they hold over a
different stretch. Its signatures carry `direction: upstream` /
`downstream`, and friction derivation walks the watercourse in that
direction rather than matching the same object. One optional field, no
model change — but the engine needs the watercourse's ordering of
resources (headwaters → the_great_weir → irrigation_cuts), which belongs
in the river-water resource files' properties.

## 8. Rollout and back-compat

1. This schema (agreement).
2. Follow-up task: upgrade `activities:` in the seeded jurisdiction YAMLs
   to signatures (bare verbs stay valid), extend the loader model
   (`ActivitySignature` with string coercion), implement friction
   derivation + charged-candidate computation in `polis/sim/events.py`.
3. The director (clock, selection) consumes `polis/sim/events.py` when the
   executor lands.
