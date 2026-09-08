# Jurisdiction Requirements — a taxonomy across all fifteen

Status: analysis v1 (task 0009). Question: which data-model concepts does
each jurisdiction actually need — and in particular, does the concept of
**holdings** apply to all?

## 1. The finding: three paradigms, not one

Reading the fifteen jurisdictions against the story-generation model
(norms, holdings, activity signatures, incompatibilities), they fall into
three paradigms:

### R — Resource jurisdictions

Norms govern a **contestable resource**; holdings are control/use of it;
activity impacts are physical (depletes, blocks, pollutes, occupies);
incompatibilities are natural and concrete.

fisheries · harbor-navigation · river-water · land-commons ·
environment-resource · inheritance (the estate as resource) ·
roads-carriage (infrastructure as resource)

### C — Conduct/status jurisdictions

Norms govern **acts and statuses**, not things. There is nothing to deplete;
"facts on the ground" are statuses, rights and relationships, not control
of a resource. Impacts are normative (prohibits, requires, penalizes,
confers status).

criminal · citizenship · contract · taxation · currency-weights

### P — Political/burden jurisdictions

Norms allocate **burdens and govern relations between polities**. The
actors are mostly *collectives* (cities, the federation, neighboring
states), not persons; "resources" are burden-shares, command rights, border
arrangements.

military-defense · foreign-relations

## 2. Do holdings apply to all? — Only if generalized

As *control/use of a resource*, holdings apply only to paradigm R. But a
natural generalization covers the rest:

> **A Holding is a durable legal fact linking an actor to an object under a
> norm.** The object's `object_type` varies: `resource` (paradigm R),
> `status`, `right`, or `relationship` (paradigm C and P).

| object_type | paradigm | examples |
|---|---|---|
| `resource` | R | A's fishers fish the northern banks under open_access |
| `status` | C | X holds the freedom of Cogswich under naturalization_by_residence; the accused holds sanctuary |
| `right` | C/P | the guild holds an exemption charter; Thornwick holds a toll farm |
| `relationship` | C/P | creditor–debtor bond on the rolls; a treaty obligation between the federation and a neighbor |

So: **keep Holding, but parameterized by `object_type`.** Jurisdictions
where "holding" means nothing concrete (none, in fact — every paradigm has
durable legal facts of some kind) simply don't use the `resource` type.
This answers the open question: the user's instinct was right that raw
resource-holdings don't generalize — but the underlying notion (a
*standing legal fact* that an event can disturb) does, and that is all the
event-synthesis engine needs.

## 3. The per-jurisdiction requirements matrix

| Jurisdiction | Paradigm | Holdings (sense) | Facts on the ground (seed) | Natural incompatibilities |
|---|---|---|---|---|
| fisheries | R | fishing rights over grounds | who fishes where, customary access | open_access ⊥ exclusive_access, ⊥ licensing |
| harbor-navigation | R | berthing/pilotage rights | dues schedule, pilots' custom | open_port ⊥ harbor_dues; free pilotage ⊥ compulsory_pilotage |
| river-water | R | diversion rights (flow externality!) | upstream diversions, mill rights | prior_appropriation ⊥ riparian_sharing |
| land-commons | R | grazing stints, tenure | customary stints, enclosures | open_commons ⊥ enclosure_grant |
| environment-resource | R | extraction leases | current workings, leases | sustained_yield ⊥ free extraction |
| inheritance | R (estate) | heir positions, entails | current entails, wills on the rolls | primogeniture ⊥ partible_inheritance; testamentary_freedom ⊥ forced_share |
| roads-carriage | R (infra) | toll farms, maintenance duties | toll gates and who farms them | free_passage ⊥ toll_by_weight |
| trade-markets | R/C mixed | stalls, licenses (resource-like) | guild's market custom, current tariffs | free_entry ⊥ guild_monopoly |
| taxation | C | exemption charters (right) | levy schedule, exemptions granted | uniform_levy ⊥ exemption_charter |
| currency-weights | C | exchange-office licenses (right) | the current standard, fineness | fixed_standard ⊥ free_coinage |
| citizenship | C | statuses (freedom, guest) | freedom rolls, guest registers | jus_soli ⊥ jus_sanguinis; open naturalization ⊥ freedom_by_purchase |
| criminal | C | sanctuary, outlawry (status) | watch rolls, pending cases | city_venue ⊥ federal_venue; punishment ⊥ composition |
| contract | C | bonds (relationship) | bond rolls, guild arbitration custom | usury_cap ⊥ free interest; guild_arbitration ⊥ court enforcement |
| military-defense | P | exemptions, command rights | muster rolls, fortification state | levy_by_population ⊥ levy_by_wealth; federal_command ⊥ city_command |
| foreign-relations | P | treaty rights (relationship) | treaties in force, border posts | open_border ⊥ treaty_boundary; most_favored_nation ⊥ exclusivity |

Notes on the odd cases:

- **river-water** is the only jurisdiction where impact propagates
  *spatially* (upstream act → downstream harm). Its activity signatures
  will need a direction/externality field (see task 0012).
- **trade-markets** is genuinely mixed: stalls behave like resources;
  weights/measures are conduct norms. Expect it to exercise both paths.
- **foreign-relations** is the only jurisdiction whose typical actors are
  *collectives*; event synthesis there casts cities/the federation, not
  persons — the casting rules must tolerate that.

## 4. Consequences for the data model

1. **Holding** gains `object_type: resource | status | right | relationship`
   (task 0008's situation store inherits this).
2. **Norms are universal** (every jurisdiction has rules in force); their
   *object* varies the same way — confirmed subject-by-subject in task 0010.
3. **Activity signatures** must admit normative impacts (prohibits,
   penalizes, confers-status), not only physical ones (task 0012).
4. **Incompatibilities** are natural everywhere — no jurisdiction lacks
   contestable rule pairs (task 0013 has material in all fifteen).
5. No jurisdiction is forced into the fisheries shape; paradigm tags
   (`R | C | P`, or `R/C` mixed) should be added to each jurisdiction YAML
   so the generator knows which machinery to use.
