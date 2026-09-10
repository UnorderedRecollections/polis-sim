# Story Data Model — the legal-design YAML

Status: design v1 (task 0003). Data in `data/world/legal/` (YAML, readable by
non-technical people); validated loader in `polis/sim/legaldata.py`.

## Jurisdiction files (`jurisdictions/<slug>.yaml`)

One per jurisdiction (all fifteen). Schema:

| key | meaning |
|---|---|
| `jurisdiction` | slug — must equal the filename |
| `name` | display name |
| `corpus_dir` | backing directory in the corpus, or `null` (not yet enacted) |
| `resources` | concrete resources stories can be about (`northern_banks`) |
| `actors` | jurisdiction actor kinds (core kinds like `citizen`, or jurisdiction-specific ones deriving from `JurisdictionalActor`) |
| `activities` | what actors **do** with the resource — domain verbs (`fish`, `graze`) |
| `resource_properties` | aspects of the resource that rules attach to (`season`, `access_right`) |
| `rule_forms` | the rule shapes that can be enacted or contested (`quota`, `exclusive_access`) |
| `disputes` | typical dispute shapes (`overfishing`, `boundary`) |

### Changes from the initial sketch, and why

1. **`actions` → `activities`.** The sketch mixed domain verbs (`fish`) with
   rule-making acts (`prohibit`, `license`). Those are different layers:
   "the fisher fishes" is story; "the city prohibits" is a legal move that
   becomes a bill. Domain verbs stay in the jurisdiction file; legal moves
   stay centralized in `moves.yaml`.
2. **Added `resource_properties` + `rule_forms`** (from the task-0002
   conflict grammar). A generatable conflict needs: *two incompatible
   `rule_forms` over the same `resource_property` of the same `resource`*.
   The sketch's `constraints` were really rule dimensions; `rule_forms` is
   the enactable vocabulary.
3. **Added `corpus_dir`.** Generated bills must be drafted somewhere;
   `corpus_dir` keeps story generation consistent with the path-based
   jurisdiction enforced by `bill ratify`. `null` = the jurisdiction has no
   enacted corpus yet (its acts would be constitutional moments — new
   directories entering the corpus).

## Legal moves (`moves.yaml`)

Story primitives: what an actor can **do in the legal process**, phrased
institutionally (`file_petition`, `introduce_act`, `ratify`, `promulgate`…).
Each maps onto the simulation's command surface; the git/platform steps
underneath are machinery, not moves. `merge` and `revert` are therefore not
moves — they're the machinery of `ratify` and `repeal` — and are kept only
as an annotated `machinery_aliases` table so the layers never blur in
scenarios.

## Story templates (`templates/*.yaml`)

A template is a **story grammar**: participant *roles* (`claimant`,
`respondent`, `resource`) and a `sequence` of story blocks. Instantiation =
binding nouns from a jurisdiction file:

```
template:  resource_dispute   (sequence: establish_traditional_use →
           introduce_competing_claim → file_petition → assign_jurisdiction →
           propose_legislation → jurisdictional_review → amendment →
           constitutional_review → approval → enactment)
binding:   claimant=brasshaven, respondent=gloamingate,
           resource=western_commons (from land-commons.yaml)
story:     "Brasshaven has traditionally grazed cattle in the Western
           Commons. Gloamingate begins charging access fees. A citizen
           petitions the Federation…"
```

Same grammar, different nouns and legal objects — this is what makes the
story generator data-driven rather than a pile of string templates.

A second grammar exists: `phase_transition` (three acts carrying the
codified-machinery instruments through the customary procedure — see
`data/world/legal/transition/`). Its participants are offices and cities
rather than resource parties; the acts it introduces are authored legal
texts, not template fills.

## Recorded for later: `world.enact(...)` — story block as transaction

The simulation should not poke git stepwise; each **story block** should be
a transaction: `enact(actor, move, **params)` collects the Plan set for one
legal act and applies it as **one journal entry** (with before/after
anchors). This is the natural seam between the DSL and the executor layer
(`docs/design/simulator.md` §2.2) — to be designed when the executor lands.
