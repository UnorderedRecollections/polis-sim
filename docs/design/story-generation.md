# Story Generation — what is missing, and how to close it

Status: analysis v1 (task 0007). Question posed: what does the data model /
ontology still lack so we can initialize a jurisdiction, synthesize events
that play out in it, and generate disputes — and can that be pure code or
does it need an LLM (with MCP)?

## 1. What we have vs. what is missing

| Need | Have | Missing |
|---|---|---|
| Vocabulary of the legal world | ontology YAML: actors, objects, relations, events; jurisdiction data (resources, actors, activities, properties, rule_forms, disputes) | — |
| A place to start from | world registry (cities, persons, offices) | **the legal situation**: which rules are *in force* over which resources, held by whom, by custom or by statute |
| Events that drive the sim | activities per jurisdiction (verbs) | **why an event happens**: actor interests, activity impacts, a clock/director |
| Disputes | dispute shapes per jurisdiction (names only) | **rule incompatibility**: which rule_forms cannot coexist over the same property; the *legal question* a dispute poses |
| Executing the story | the whole machinery (docket/bill/archive, matters, git) | **binding**: story roles → actual persons; story state machine (where in the template we are) |
| Human-readable output | document templates, Gherkin goal | **realization**: plausible prose, particulars, variety |

Four concrete gaps. Each gets a proposed model below.

## 2. Gap 1 — the legal situation: rules in force and holdings

The ontology knows rule *forms*; nothing represents a **rule in force**.

```yaml
# a Norm — a rule actually governing a resource property
norm:
  rule_form: open_access
  resource: northern_banks
  property: access_right
  beneficiaries: [city-a fishers, city-b fishers]
  source: custom            # custom | statute (statute → a LegalObject id)
```

And the facts on the ground:

```yaml
# a Holding — who controls/uses what under which norm
holding:
  actor: city-a fishers
  resource: northern_banks
  activity: fish
  under: <norm id>
```

**Initializing a jurisdiction** = emitting a set of norms and holdings for
its resources ("City A controls the Northern Harbor", "fishing in the
Northern Banks is traditionally open to A and B"). These are *social facts*:
not enacted law (git), not pending matters, not the civil registry. They
belong to the **run state** — a fourth, run-scoped store
(`data/sims/<run>/situation.json`, seeded by the scenario, mutated by
enactments: when a bill is ratified, the corresponding norm's source flips
from `custom` to the enacted act, or the norm is replaced). This keeps the
three-stores ontology clean: situation state is scenario data, not a new
system of record.

## 3. Gap 2 — why events happen: interests, impacts, a director

An event in a story is never random; it is an actor pursuing an interest
against a friction. Two data additions:

**Activity signatures** (upgrade `activities` in jurisdiction YAML from
strings to objects):

```yaml
activities:
  - verb: fish
    actors: [fisher]
    affects: [stock, access_right]
    impact: depletes          # depletes | blocks | pollutes | enriches | burdens
```

**Actor interests** (small, per jurisdiction actor kind):

```yaml
actors:
  - kind: fisher
    interests: [maximize_catch, secure_access]
```

Then an *event candidate* = (actor, activity, resource) such that the
activity's impact on some property conflicts with another actor's holding
or interest under the current norms. The **director** (the sim's scheduler)
walks the clock, evaluates candidates against open stories, and picks the
next event. Deterministic: same seed, same situation ⇒ same event stream.

## 4. Gap 3 — generating disputes: incompatibility and the legal question

A dispute, mechanically, is:

1. **a triggering event** — actor A does an activity affecting property P
   (from §3);
2. **a grievance** — actor B is harmed (B has a holding or interest over P);
3. **a legal question** — which rule_form should govern P? The dispute is
   generatable iff we know **which rule_forms are incompatible over the same
   property**.

That relation does not exist yet. Proposed: a per-jurisdiction
`incompatibilities` list (pairs of rule_forms that cannot both hold over one
property):

```yaml
incompatibilities:
  - [open_access, exclusive_access]
  - [open_access, licensing]
  - [free_entry, guild_monopoly]
```

With it, dispute generation is a pure-code search: current norm N over P +
triggering event implying rule M, where (N, M) incompatible ⇒ legal question
"should P be governed by N or M?" → petition → competing bills.

**So: code or LLM?** The *skeleton* — parties, resource, property,
incompatible rules, procedural path, casting — must be **pure code**:
determinism and `--verify` replay depend on it, and it is exactly the part
an LLM would hallucinate wrong (invalid actors, impossible rules, wrong
jurisdiction). Where an LLM earns its place is **realization**: petition
prose, bill titles and article text, debate contributions, variety across
runs — and optionally *proposing* new event candidates that the code then
**validates** against the situation and the ontology before admitting.

Proposed contract (LLM optional; pure-code mode always available):

- **MCP tools (read)**: query ontology kinds, jurisdiction data, the run's
  situation (norms, holdings), open matters.
- **MCP tools (write)**: `propose_story_element(candidate)` — validated in
  code (actors exist? rules incompatible? jurisdiction correct? casting
  legal?) and either admitted to the event stream or rejected with reasons.
- The LLM never touches git, matters, or the situation directly; it speaks
  story elements, the engine speaks law.

This keeps the LLM where it is strong (plausibility of particulars) and the
code where correctness lives (structure, determinism, execution).

## 5. Gap 4 — binding and the story state machine

Two small pieces:

- **Casting**: template roles (`claimant`, `respondent`, `petitioner`,
  reviewing jurist, ratifying archivist) bind to actual persons, respecting
  agency separation and jurisdiction powers (a `taxation/` bill can only be
  ratified by the Keeper; the Fisheries Jurist is the domain expert's
  jurisdictional face). The binder answers: *who can play this role?* from
  `world.json` + offices.
- **Story state machine**: each instantiated story tracks its position in
  the template sequence, its bindings, and its produced artifacts (matter
  ids, branch names, commit hashes — cross-referenced with the journal).
  Templates gain optional `trigger` (which situation condition starts the
  story) and `outcomes` (how it may end: enactment, rejection, dismissal),
  so the director knows when a story is done and its consequences should be
  written back to the situation.

## 6. A worked end-to-end trace (fisheries)

1. **Initialize**: norms = {northern_banks/access_right: open_access, custom,
   beneficiaries A+B fishers}; holdings = {A fishers fish northern_banks}.
2. **Event** (director): pressure — City A enacts locally
   `exclusive_access` over `location`; impact: blocks B's holding.
3. **Dispute** (code): (open_access, exclusive_access) ∈ incompatibilities ⇒
   legal question over `access_right`.
4. **Story** (template `resource_dispute`, cast: claimant=B, respondent=A):
   fisher from B files petition (→ matter PET, event `petition filed`) →
   jurisdiction assigned (fisheries) → B's city drafts an Act regulating
   access (→ `bill draft --kind act --into …`) → Fisheries Jurist approves →
   Constitutional Jurist approves → cities approve → Federal Archivist
   ratifies (→ merge, matter `act enacted`).
5. **Write-back**: the norm's source flips from custom to the enacted act;
   situation updated; journal holds the anchors.
6. **Assertions** (the Gherkin `Then`s): the Act is on `main`; the previous
   rule remains in legal history (the custom is *superseded*, not erased);
   the new rule governs the Northern Banks (situation query).

## 7. Summary of proposed data-model changes

| Addition | Where | Task type |
|---|---|---|
| `Norm` + `Holding` models; run-scoped situation store | `polis/sim/situation.py` + `data/sims/<run>/` | [simulation] |
| Activities as objects (verb, actors, affects, impact); actor interests | `data/world/legal/jurisdictions/*.yaml` | [simulation] |
| `incompatibilities` per jurisdiction | same YAML | [simulation] |
| Template `trigger` / `outcomes` + casting binder | templates + `polis/sim/casting.py` | [simulation] |
| Director (clock, candidate evaluation, story state machine) | `polis/sim/director.py` | [simulation] |
| LLM realization + `propose_story_element` MCP boundary (optional) | later | [simulation] |

Decision: **structure in code, prose optionally from an LLM behind a
validated MCP boundary.** No LLM is required for a working, replayable
simulation.
