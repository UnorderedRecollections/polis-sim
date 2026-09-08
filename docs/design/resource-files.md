# Resource Files — design document

Status: design v1 (task 0011). Question: what should a per-resource YAML
file look like, where does it live, and how does it relate to what already
exists (jurisdiction `resources:` lists, norms, the story engine)?

## 1. What a resource file is for

The jurisdiction YAMLs name resources (`northern_banks`) but say nothing
about them. Stories need more: the resource's *current properties* (the
things rules and events attach to), and narrative metadata for realization.
So a resource file answers three consumers:

1. **the situation seed** — norms and holdings reference a concrete object
   with concrete property values;
2. **event synthesis** — activity signatures target resources and read their
   properties (a `seasonal_closure` story needs the resource's `season`);
3. **realization (prose/LLM)** — names, places, flavor that make the same
   story grammar read differently each time.

Scope: files exist only for objects of `type: resource` (the R paradigm and
the resource half of mixed jurisdictions). Conduct/status/burden objects
are abstract categories — they are declared in norms directly and get no
files.

## 2. Schema

One file per resource, in `data/world/legal/resources/<jurisdiction>/<kind>.yaml`:

```yaml
resource: northern_banks          # slug — must equal the filename
jurisdiction: fisheries           # owner jurisdiction (cross-checked)
label: The Northern Banks         # human name for prose

object_type: resource             # always "resource" in these files

properties:                       # current values, one entry per property
  location: the northern waters   #   declared in the jurisdiction YAML
  season: [spring, autumn]
  species: [herring, cod]
  access_right: open

customary_use:                    # free-form facts on the ground (seed text)
  - fishers of cogswich and brasshaven have fished here since before the Concord

narrative: >-                     # realization metadata (optional, for prose/LLM)
  Cold, treacherous banks; the richest herring grounds of the Nine Cities.
```

Validation rules (loader-enforced):

1. `resource` == filename slug; `jurisdiction` exists and lists the resource.
2. Every key in `properties:` is declared in the jurisdiction's
   `resource_properties:` (no invention); not every declared property must
   be set (some only become meaningful through stories).
3. `object_type` is always `resource`.

## 3. Relation to the jurisdiction `resources:` list

**Single source of truth: the files.** The jurisdiction YAML's
`resources:` list becomes an *index* and the loader cross-checks the two in
both directions:

- every slug in `resources:` has a file → otherwise the index names a
  resource that doesn't exist;
- every file's slug appears in `resources:` → otherwise a resource exists
  that its jurisdiction doesn't claim.

Drift is then impossible at load time (same discipline as
slug↔filename and paradigm cross-validation). Norm validation tightens
accordingly: `object.kind` for resource-typed norms is checked against the
resource *files*, not just the index.

## 4. How resources participate

| consumer | use |
|---|---|
| **seed (0008)** | norms and holdings reference `resource:<kind>`; `customary_use` lines become seed facts / Given-steps |
| **events (0012)** | activity signatures bind to a resource and read `properties` (a closure story needs `season`; a quota story needs `stock`-like values) |
| **disputes (0013)** | an incompatibility over property P *of this resource* is the legal question; the resource is the dispute's object |
| **realization** | `label`, `customary_use`, `narrative` feed prose/Gherkin: "the Northern Banks", not `northern_banks` |
| **snapshots** | same principle as norms: resource state (properties as they evolve) shares the file format, so a snapshot includes evolved resources unchanged in kind |

## 5. Worked example (fisheries)

`data/world/legal/resources/fisheries/northern_banks.yaml` (as in §2) +
existing `norms/fisheries.yaml` N-0001 (`open_access` over
`northern_banks/access_right`) gives the seed for your Gherkin example:

```
Given City A controls the Northern Harbor        ← holding over a resource file
And fishing in the Northern Banks is traditionally open to City A and City B
                                                  ← norm N-0001 + customary_use
```

## 6. Rollout

1. This schema (agreement).
2. Follow-up task: files for the resources of the seeded jurisdictions
   (fisheries, harbor-navigation, land-commons, taxation has none —
   conduct-status), loader (`polis/sim/resources.py`) + cross-validation,
   CLI `polis world resources list/show`.
3. Remaining jurisdictions' resources as their seeds are written (0008).
