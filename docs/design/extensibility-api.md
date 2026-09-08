# Extensibility — adding actors/jurisdictions, an LLM-facing API

Status: design v1 (task 0014). Questions: what does adding a new actor kind
or a new jurisdiction take, now that the whole stack exists — and can we
expose that as an API an LLM can use to *iterate toward a valid definition*?

## 1. The new-jurisdiction checklist

Everything the sim needs from a jurisdiction, in dependency order — each
step machine-checkable (this is what `polis world legal audit` verifies):

| # | step | artifact | checks |
|---|---|---|---|
| 1 | declare the jurisdiction | `jurisdictions/<slug>.yaml` | slug == filename; `paradigms` reference `ontology/paradigms.yaml` |
| 2 | define its cast | `actors:` | core kinds resolve; new kinds auto-register as `JurisdictionalActor` subclasses |
| 3 | define its grammar | `resource_properties:`, `rule_forms:`, `disputes:` | non-empty; rule_forms referenced later must exist here |
| 4 | write activity signatures | `activities:` | every `impact` admitted by the paradigm's `impact_kinds` |
| 5 | declare incompatibilities | `incompatibilities:` | both rule_forms exist; kind ∈ strict\|tension |
| 6 | ground its resources | `resources/<slug>/*.yaml` | resource-paradigm only; index ↔ files bidirectional; property keys declared |
| 7 | seed its norms | `norms/<slug>.yaml` | ≥1 norm; rule_forms known; object types paradigm-admitted; resource objects exist |
| 8 | seed its holdings | `holdings:` | ≥1; `under:` an existing norm; activity known; holder resolvable |
| 9 | seed consistency | — | no active **strict** conflicts in the seed |
| 10 | corpus backing (optional) | `corpus_dir:` | if set: the directory is or will be in the corpus; note the casting/power implications |

Step 10 has a fiction consequence worth stating: a jurisdiction gaining a
`corpus_dir` it never had is a **constitutional moment** — its first act
creates the directory, and the office holding jurisdiction over it (a new
`expert-<domain>` in `world.json` if it's a *federal* domain) must exist or
be created by the same constitutional process. Municipal-only jurisdictions
need nothing but the city's archivist.

## 2. The new-actor checklist

Much smaller, because of the on-demand registration:

- **Jurisdiction-specific kinds** (`harbor-master`, `fisher`, …): *nothing to
  do*. First use in `actors:`, `activities.actors:`, or a holding
  auto-registers them as subclasses of `ActorJurisdictional`. The checklist
  is: use them consistently (one spelling — slugs are identity).
- **Core kinds** (a new kind of officer or collective): an entry in
  `ontology/actors.yaml` with `kind`, `parent`, `label`, and
  `abstract`/`collective` flags as appropriate; parents before children.
  Then, if the kind should *act* in the world (hold offices, sign
  petitions), map it onto the world model: a role in
  `POLITICAL_ROLES`-style data or an office power in `world.json` — the
  ontology says what it *is*, the world says what it *can do*.

## 3. The LLM-facing API (MCP surface)

The design principle from task 0007 stands: the LLM proposes, the code
disposes. Concretely:

**Read tools** (all backed by the existing query layer):
`list_ontology_categories` / `query_ontology(category)` ·
`list_jurisdictions` / `query_jurisdiction(slug)` ·
`query_situation(jurisdiction)` (norms + holdings) ·
`query_candidates(jurisdiction)` (charged event candidates) ·
`query_checklist(kind: jurisdiction|actor)` — *this document, as data*.

**Write tools** (validated; never write directly):
- `propose_jurisdiction(definition)` — validate the complete definition
  against the §1 checklist *without installing it*: schema, paradigm
  coherence, signatures, incompatibilities, resource files, seed. Returns
  `{accepted: bool, problems: [...]}` — the same machine-readable strings
  the validators already emit, so the model can fix and resubmit.
- `propose_actor(definition)` — the §2 checks.
- `propose_story_element(candidate)` — (from 0007) validate a proposed
  event/story against the situation and ontology.

**Iteration contract**: every rejection includes *what is missing or
inconsistent*, never just "invalid". An LLM (or a human) can therefore loop
`propose → problems → revise → propose` until `accepted`, and only then
does the artifact land in `data/world/legal/` — landing itself is a
deliberate operator act (a commit), not an API call.

## 4. Why this shape

- **Everything the API checks already exists** as loaders/validators from
  tasks 0003–0018; the API is a *composition* of validators, not new logic.
- The checklist doubles as documentation and as test: `legal audit` runs
  the same steps against installed jurisdictions.
- The LLM never touches the situation, the matters, or git — it speaks
  definitions and story elements; the engine speaks law.

## 5. Rollout

1. This document.
2. Follow-up (implemented with it): `polis/sim/extensibility.py` —
   `audit_jurisdiction(slug)` composing the existing validators per §1, and
   `polis world legal audit <slug>` printing the checklist with
   ok/problem per step. `propose_*` MCP tools wrap the same audit when the
   MCP server is built.
