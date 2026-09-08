# The Legal Ontology — the simulation's legal DSL

Status: design v1 (task 0002), data-driven since task 0005: every category is
YAML in `data/world/legal/ontology/` (`actors.yaml`, `legal_objects.yaml`,
`legal_relations.yaml`, `procedural_events.yaml`); `polis/sim/ontology.py`
defines the base classes (`Actor`, `LegalObject`, `LegalRelation`,
`ProceduralEvent`) and parses the YAML at load time, dynamically creating
subtypes (`ActorPerson`, `ActorCitizen`, …) with the YAML's explicit
`parent:` property as the real Python inheritance chain. Jurisdiction
objects are built by `jurisdiction_factory` over
`data/world/legal/jurisdictions/*.yaml`. Consumed by the story generator
and the Behave step library.

The ontology has four pillars — **Actor**, **LegalObject**,
**LegalRelationship**, **ProceduralEvent** — plus a registry of
**Jurisdictions**, each carrying a *conflict grammar* for the story
generator.

## 1. Actor

### 1.1 Hierarchy

```
Actor
├── Person                          (individual; exists somewhere)
│   ├── Citizen                     (political existence in a city)
│   │   ├── Legislator              (proposes; political agency)
│   │   └── Delegate                (represents the city federally)
│   ├── Jurist                      (constitutional scrutiny)
│   ├── Archivist                   (maintains an archive)
│   │   └── Federal Archivist       (the Keeper of the Federal Rolls)
│   └── JurisdictionalActor         (INTERMEDIARY — never instantiated)
│       ├── harbor-master           \
│       ├── fisher                   |  jurisdiction-specific kinds,
│       ├── merchant, farmer, …      |  registered by each Jurisdiction
│       └── treasurer, magistrate,… /
├── City                            (collective)
├── Federation                      (collective)
├── Council                         (collective)
└── Committee                       (collective)
```

`is_actor_a(kind, ancestor)` walks the derivation chain; unknown kinds are
treated as jurisdiction-specific (deriving from `JurisdictionalActor`).

### 1.2 Mapping onto the existing world model

| Ontology | `polis` model |
|---|---|
| Citizen | `Person(member_of=city)` |
| Legislator / Delegate | `roles` = `citizen-legislator` / `local-delegate` (`agency=political`) |
| Jurist / Archivist / Federal Archivist | `Person(agency=juridical)` + the offices they `occupy` |
| City / Federation / Council / Committee | `City`, `Federation`, office `body` values (`constitutional-council`, …) |
| JurisdictionalActor kinds | story-layer roles; not persons in `world.json` unless a scenario needs accounts for them |

The separation rule survives: a person who is a Legislator/Delegate
(political agency) may not also be a Jurist/Archivist (juridical office).

## 2. LegalObject

`constitution · act · amendment · regulation · treaty · ordinance · repeal ·
petition · judgment · order · declaration`

- **Already produced by the machinery**: `act`, `amendment`, `repeal`
  (document templates), `petition` (matter store). Marked in code as
  `IMPLEMENTED_OBJECT_TYPES`.
- **Reserved for later**: `constitution` (the founding document of
  `constitution/`), `treaty` (inter-city or external; needs the
  `treaty.md` template), `regulation`/`ordinance` (secondary legislation),
  `judgment`/`order`/`declaration` (juridical outputs — an Order is what an
  archivist "enters into the record" at ratification).

## 3. LegalRelationship

`authorizes · prohibits · requires · permits · establishes · amends ·
repeals · supersedes · incorporates · delegates · ratifies · recognizes ·
exempts`

Used to state facts about the legal order in scenarios and to generate
conflicts:

- object→object: *ACT-0017 **amends** the Harbour Dues Act; the Reform Act
  **supersedes** the old schedule.*
- object→actor/actor→object: *the Council **ratifies** the act; the act
  **exempts** small vessels; the charter **authorizes** the guild.*
- constitutional readings: *the constitution **prohibits** enclosure of the
  commons; the treaty **requires** two cities' approval.*

The story generator pairs these with jurisdiction rules: a conflict is
typically *rule A* (permits X) vs *rule B* (prohibits X) over the same
resource property.

## 4. ProceduralEvent

`petition filed · proposal introduced · matter referred · jurisdiction
assigned · hearing held · objection raised · amendment proposed · review
completed · vote held · act approved · act rejected · act enacted ·
act repealed`

Canonical names for institutional time. The matter store already records a
subset; `MATTER_EVENT_MAP` in code is the alignment:

| ProceduralEvent | matters.json event string |
|---|---|
| petition filed | `filed` |
| hearing held | `heard` |
| proposal introduced | `introduced` |
| review completed | `scrutinized` (+ `: approved` / `: changes requested`) |
| act enacted | `enacted` |
| act rejected | `rejected` |

Events without a current mapping (`matter referred`, `jurisdiction assigned`,
`vote held`, `act approved`, `objection raised`, `amendment proposed`) are
the vocabulary for richer proceedings later — the matter store accepts them
today (free-form event strings), the DSL gives them names.

## 5. Jurisdictions and conflict grammars

Fifteen jurisdictions; **not all are implemented** — they exist so scenarios
can be detailed later. Those with a `corpus_dir` are backed by the corpus
today:

| Jurisdiction | corpus dir | Typical matters | Typical actors |
|---|---|---|---|
| Harbor & Navigation | `maritime/` | ports, shipping, pilots | harbor master, merchants, shipowners |
| Fisheries | — | grounds, seasons, quotas | fishers, coastal cities |
| River & Water | — | irrigation, canals | farmers, cities |
| Trade & Markets | `commerce/` | tariffs, weights, licenses | merchants, guilds |
| Land & Commons | — | grazing, forests, tenure | farmers, villages |
| Taxation | `taxation/` | customs, levies, exemptions | treasurers, merchants |
| Roads & Carriage | — | roads, bridges, tolls | cities, carriers |
| Currency & Weights | — | coinage, standards | treasury, merchants |
| Citizenship | `civic/` | residence, naturalization | citizens, cities |
| Criminal Law | `criminal/` | offenses, penalties | courts, magistrates |
| Contract Law | — | debts, sale, partnership | merchants |
| Inheritance | `succession/` | succession, estates | families, courts |
| Environmental/Resource | — | forests, extraction | cities, resource users |
| Military/Defense | — | levies, fortifications | cities, federation |
| Foreign Relations | — | treaties, borders | federation, neighbors |

### 5.1 The conflict grammar

Each jurisdiction declares the raw material for generating disputes:

```yaml
resource:             # what the dispute is over
actors:               # who is disputing (jurisdiction-specific actor kinds)
resource_properties:  # which aspects of the resource matter
possible_rules:       # rules that could cause or settle the dispute
```

Worked example — **Fisheries**:

```yaml
resource: fishery
actors:
  - City A fishers
  - City B fishers
resource_properties: [location, season, species, access_right]
possible_rules:
  - open_access
  - exclusive_access
  - quota
  - seasonal_closure
  - licensing
  - territorial_boundary
  - conservation_requirement
```

A generated conflict: *City A enacts `exclusive_access` over the fishery's
`location`; City B's custom is `open_access`; the same `access_right` is
governed by incompatible rules → petition to the federation → competing
bills → a merge conflict or a Council decision.* All fifteen grammars are
registered in `polis/sim/ontology.py` (`JURISDICTIONS`), fisheries first.

## 6. How the pieces compose in a scenario

```
Jurisdiction (grammar)  →  conflict seed
LegalObject             →  what gets drafted (act/amendment/repeal)
Actor                   →  who files / debates / scrutinizes / ratifies
LegalRelationship       →  what the documents assert about each other
ProceduralEvent         →  what the matter record shows afterwards
```

That is the whole DSL: Behave steps phrase sentences over these five
vocabularies, the story generator instantiates them, the machinery executes
them, and the journal records which instances actually happened.
