# Do Norms Generalize? — the rules-in-force model across all jurisdictions

Status: design v1 (task 0010). Question: does the Norm concept sketched in
the story-generation analysis generalize across the existing jurisdictions?
Short answer: **yes, with two adjustments and one extension**, all forced by
the task-0009 taxonomy.

## 1. The sketch under scrutiny

From `story-generation.md` (task 0007):

```yaml
norm:
  rule_form: open_access
  resource: northern_banks
  property: access_right
  beneficiaries: [city-a fishers, city-b fishers]
  source: custom            # custom | statute
```

Probe each field against the three paradigms (resource / conduct-status /
political-burden):

## 2. Adjustment 1 — `resource` is not universal; `object` is

Only resource-paradigm norms are *about* a thing that can be depleted or
occupied. But every jurisdiction's norms are about **something**:

| paradigm | the norm's object | object_type |
|---|---|---|
| resource | northern banks, a berth, an estate | `resource` |
| conduct-status | lending, coinage, citizenship acquisition, an offense category | `conduct`, `status`, `flow` |
| political-burden | the defense burden, the tariff regime, a treaty obligation | `burden`, `relationship` |

So the field becomes a typed reference:

```yaml
object:
  kind: northern_banks      # what it is
  type: resource            # resource | conduct | status | flow | burden | relationship
```

This mirrors exactly the `holding_object_types` declared per paradigm in
`ontology/paradigms.yaml` — a norm's object type must be one its paradigm
admits, and the loader can validate that.

## 3. Adjustment 2 — `beneficiaries` conflates two roles

In resource norms the interesting party is *who may use*. In conduct norms
the interesting party is *who is bound*; the beneficiary is diffuse (the
public, the city, creditors' counterparties). These are different roles and
both are needed:

```yaml
subjects: [creditors]        # who is bound by the rule
beneficiaries: [debtors]     # who gains from it (may be a collective: [the city])
```

Either may be empty: `usury_cap` has subjects and beneficiaries; a criminal
prohibition has subjects (everyone) and a collective beneficiary (the
city); `open_access` has beneficiaries (the fishers of A and B) and no
meaningful subjects.

## 4. Extension — more than two sources of normativity

`custom | statute` covers the phase-1 arc, but the jurisdictions expose two
more sources, and all four map onto LegalObjects:

| source | arises from | LegalObject |
|---|---|---|
| `custom` | long usage; the foundational seed | — (unwritten) |
| `statute` | enactment through the bill flow | Act, Amendment |
| `treaty` | inter-polity agreement | Treaty |
| `charter` | a grant to a specific holder (exemptions, toll farms, entails) | Order, Declaration |

Each non-custom source carries a reference to the LegalObject that created
it (`source_ref: ACT-0017`), which is what makes write-back after enactment
mechanical rather than narrative.

## 5. The generalized Norm

```yaml
norm:
  id: N-0001
  rule_form: open_access              # from the jurisdiction's rule_forms
  object: {kind: northern_banks, type: resource}
  aspect: access_right                # was "property"; the governed aspect
  subjects: []                        # who is bound
  beneficiaries: [city-a fishers, city-b fishers]
  source: custom                      # custom | statute | treaty | charter
  source_ref: null                    # LegalObject id when not custom
  status: in_force                    # in_force | superseded | repealed
```

## 6. Instantiation across paradigms (proof by example)

**resource (fisheries)** — as the sketch: `open_access` over
northern_banks/access_right, beneficiaries both cities' fishers, custom.

**conduct-status (contract)** — `usury_cap` over `lending` (conduct),
aspect `rate`; subjects: creditors; beneficiaries: debtors; custom.

**conduct-status (citizenship)** — `jus_soli` over
`citizenship-acquisition` (status); subjects: newcomers; beneficiaries:
newcomers' children; statute (`source_ref` the Civic Enrollment Act).

**political-burden (military-defense)** — `levy_by_population` over
`defense-burden` (burden); subjects: the nine cities; beneficiaries: the
federation; treaty.

**political-burden (foreign-relations)** — `most_favored_nation` over
`tariff-regime` (relationship); subjects: federation and the neighbor;
treaty with `source_ref`.

**edge (river-water)** — the spatial externality: norms over `watercourse`
need a *scope* (`aspect: flow` at `diversion_point: the_great_weir`) so that
upstream and downstream norms can coexist and conflict. `aspect` absorbs
this; no model change, but task 0012's signatures must carry location.

## 7. Lifecycle: how norms evolve with the machinery

| legal act | effect on norms |
|---|---|
| enactment of an act | a new norm enters (`source: statute`, `source_ref` the act), or an existing norm's source flips custom → statute |
| amendment enacted | norm's `source_ref` updated; rule_form unchanged unless the amendment changes it (then: old norm `superseded`, new norm `in_force` — the `supersedes` LegalRelation made concrete) |
| repeal enacted | norm `status: repealed`. Open legal question the model must honor: **does the custom revive?** Proposal: yes by default in phase-1 fiction (repeal restores the status quo ante) unless the repealing act says otherwise — a nice scenario generator hook |
| constitutional decision | norm `superseded` by the deciding norm |

The director's write-back after each ratified bill is therefore mechanical:
find norms on the act's object/aspect, apply the row, record it in the
journal.

## 8. Relation to holdings

A Holding is **norm-dependent**: it cites the norm it exists under (`under:
N-0001`). When a norm is superseded or repealed, its holdings are not
deleted — they are *re-pointed* or become *contested* (which is itself a
dispute seed: "the right I held under the old rule — does it survive the
new one?"). Vested-rights conflicts fall out of the model for free.

## 9. Verdict

Norms generalize to all fifteen jurisdictions, with:

1. `resource` → typed `object` (validated against paradigm);
2. `beneficiaries` → `subjects` + `beneficiaries`;
3. `source` extended to `custom | statute | treaty | charter` with
   `source_ref`.

Nothing in the model is resource-specific anymore, and nothing is
jurisdiction-specific either — the fifteen files differ only in *data*.
