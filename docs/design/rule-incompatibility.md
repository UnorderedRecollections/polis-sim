# Rule Incompatibility — design document

Status: design v1 (task 0013). Dispute generation needs to know *which
rule_forms cannot coexist over the same object+aspect*. This is the last
missing piece between event candidates (0012/0018) and the legal question a
dispute poses.

## 1. The shape of the relation

```yaml
incompatibilities:
  - between: [open_access, exclusive_access]
    over: access_right        # optional aspect scope; absent = any shared aspect
    kind: strict              # strict | tension
    note: free entry and exclusion cannot both govern access
```

Three decisions, argued:

1. **Symmetric pairs, aspect-scoped optionally.** Incompatibility is
   symmetric by nature (if A excludes B, B excludes A). Scoping by aspect
   matters: `quota` and `open_access` are incompatible *over access* but a
   quota over *catch size* coexists fine with open access over entry. When
   `over:` is absent, the pair is incompatible over **any shared aspect**.
2. **Two degrees, not three.** `strict` (cannot both be in force — one must
   supersede or be repealed) and `tension` (can coexist, but their
   coexistence generates friction and eventually demands clarification).
   A third degree considered — *hierarchical override* (treaty beats custom
   automatically) — was rejected: it is not an incompatibility at all, it is
   the **resolution rule**, and it already lives in the source hierarchy
   (statute/treaty/charter > custom, per the lifecycle in
   norms-generalization §7). Resolution is machinery; incompatibility is
   data.
3. **Declared, not derived.** Deriving pairs from rule-form semantics
   (antonymy like open_X ⊥ exclusive_Y) is fragile and opaque to the
   non-technical audience editing YAML. Everything stays data-driven:
   declared per jurisdiction, cross-validated against its `rule_forms`.

## 2. Where incompatibility fires

### a) Pre-enactment (the legislative path)

A bill proposes rule M over (object, aspect) while norm N is in force and
(N, M) is incompatible. This is what **constitutional/expert review is
for**: scrutiny should flag it, and the act must then either

- **supersede** N explicitly (the act names what it replaces — the
  `supersedes` LegalRelation, and ratification writes the supersession back
  via `NormSet.supersede`), or
- be rejected/withdrawn.

A bill that would silently create a strict conflict is defective; the
Magistrate's phase-2 CI checklist will include exactly this check
("does it conflict with existing legislation?").

### b) Post-enactment (the resolution path)

Two norms in force over the same object+aspect with a strict
incompatibility between them — arising legitimately, e.g. a city enacted M
locally while N holds federally. Now there is an **active conflict of
laws**: a petition asks which stands; the Council (or the competent
authority) decides; the order is entered into the record and the losing
norm is superseded or repealed. `NormSet.conflicts()` (already stubbed in
0015) is the detector for this state; in a healthy situation it returns
empty, and a run should *assert* that after every ratification.

### c) In event synthesis (the story path)

A charged candidate (0018) whose implied rule M — the rule the acting party
would want — is incompatible with the in-force N is a **dispute seed**: the
actor petitions for M, the harmed party defends N, the legal question is
"N or M over this aspect?"

## 3. The incompatibility → legal question mapping

| context | detector | procedural path | write-back |
|---|---|---|---|
| bill proposes incompatible M | review step (CI in phase 2) | request-changes, or explicit supersession in the act | `supersede` at ratification |
| two norms in force, strict conflict | `NormSet.conflicts()` | petition → Council decision → order entered | `supersede` / `repeal` the loser |
| charged event candidate | friction + in-force check | grievance → petition → competing bills | whichever act is ratified |

In all three, the *legal question* is the same shape: **"which rule form
governs this object+aspect?"** — and the record preserves the question, the
deliberation, and the answer.

## 4. Worked incompatibilities (all fifteen)

| jurisdiction | strict | tension |
|---|---|---|
| fisheries | open_access ⊥ exclusive_access; open_access ⊥ territorial_boundary | open_access ∼ quota; open_access ∼ licensing |
| harbor-navigation | open_port ⊥ priority_berthing | open_port ∼ harbor_dues; compulsory_pilotage ∼ tonnage_exemption |
| river-water | prior_appropriation ⊥ riparian_sharing | minimum_flow ∼ diversion_permit |
| land-commons | open_commons ⊥ enclosure_grant | stinting ∼ open_commons |
| environment-resource | sustained_yield ⊥ extraction_lease | closed_season ∼ extraction_lease |
| inheritance | primogeniture ⊥ partible_inheritance; testamentary_freedom ⊥ forced_share | primogeniture ∼ forced_share |
| roads-carriage | free_passage ⊥ toll_by_weight | bridge_monopoly ∼ free_passage |
| trade-markets | free_entry ⊥ guild_monopoly | standard_weights ∼ guild_monopoly |
| taxation | uniform_levy ⊥ retaliatory_tariff | uniform_levy ∼ exemption_charter |
| currency-weights | fixed_standard ⊥ free_coinage | legal_tender ∼ free_coinage |
| citizenship | naturalization_by_residence ⊥ guest_status | jus_soli ∼ jus_sanguinis |
| criminal | city_venue ⊥ federal_venue | proportional_penalty ∼ composition_instead_of_punishment |
| contract | usury_cap ⊥ debtor_prison_abolished | guild_arbitration ∼ specific_performance |
| military-defense | levy_by_population ⊥ levy_by_wealth; federal_command ⊥ city_command | substitution_by_payment ∼ levy_by_population |
| foreign-relations | open_border ⊥ treaty_boundary | most_favored_nation ∼ neutral_zone |

(⊥ = strict, ∼ = tension.) Note how the tensions are the subtler story
material: a charter exempting some merchants from a uniform levy is
*stable friction* — exactly the kind that produces petitions without
crisis.

## 5. Rollout

1. This schema (agreement).
2. Follow-up: `incompatibilities:` in all fifteen jurisdiction YAMLs (the
   table above), loader field + cross-validation (both rule_forms exist),
   `NormSet.conflicts()` wired to the real relation, `legal validate`
   extended, `jurisdictions inspect <slug> incompatibilities`.
