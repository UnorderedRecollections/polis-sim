# The Simulator — overall design

Status: design v1 (task 0001). Audience: the operators of the simulation and
readers of the article. Terminology per `docs/isomorphism/`.

## 0. Requirements

1. **Replay, step by step, from a log-like structure (file).**
2. **Interaction with the per-city containers** (`polis-city-*`).
3. A **legal story generator** that produces use cases — petitions, bills,
   amendments, conflicts — as simulation material.
4. **Python Behave (BDD)** as the foundation, with a pre-built library of
   objects and steps, so scenarios are human-readable for a non-technical
   audience.

## 1. The central idea

A simulation run is a **scenario executed against the federation**, leaving
its trace in the three stores:

- git history (legal time),
- `matters.json` (institutional time),
- `world.json` (civil registry — mostly static during a run).

To make runs replayable and presentable we add a fourth, run-scoped record:

> **The journal** — an append-only log of everything the engine *did*,
> written as it happens, sufficient to (a) re-execute the run deterministically
> and (b) re-present it step by step without touching any infrastructure.

Behave sits on top as the **authoring and presentation format**: a `.feature`
file is simultaneously the script the engine executes, the human-readable
story a non-technical reader can follow, and — via the journal — the index
into what actually happened.

```
            ┌────────────────────────────────────────────┐
            │              presentation layer            │
            │   .feature files  ·  step-through viewer   │
            ├────────────────────────────────────────────┤
            │              engine (polis.sim)            │
            │  journal · executors · story generator     │
            │  · behave step library                     │
            ├──────────────┬───────────────┬─────────────┤
            │ git history  │ matters.json  │ world.json  │
            │ (legal time) │(institutional)│  (registry) │
            └──────────────┴───────────────┴─────────────┘
```

## 2. Components (`polis/sim/`)

### 2.1 `journal.py` — the replay log (requirement 1)

Append-only JSONL, one file per run: `data/sims/<run-id>/journal.jsonl`.
Each line one event:

```json
{
  "seq": 41,
  "ts": "2026-09-08T16:58:01Z",
  "kind": "action",                  // scenario | action | observation | anchor
  "actor": "m.grimsbane",
  "city": "cogswich",
  "action": "bill.introduce",
  "params": {"bill": "bill/harbour-dues-act", "title": "Harbour Dues Act",
             "answering": "PET-0001"},
  "result": {"matter": "ACT-0001", "pushed": true},
  "anchors": {"main": "c97a692…", "branch": "0dec4a8…", "matters_seq": 12}
}
```

- `anchors` capture the resulting state (git heads, matter id) so replay can
  *verify* rather than blindly redo.
- `observation` events record assertions ("main contains harbour-dues-act.md"),
  making the journal self-auditing.
- The journal is written by the **executor**, never by hand — same discipline
  as `status:` flips in documents.

Two replay modes:

- **`sim replay --verify <run-id>`** — re-execute the journal against fresh
  infrastructure (clean repos/matters), asserting each anchor matches. This is
  the determinism proof: same scenario ⇒ same legal history.
- **`sim present <run-id> [--step]`** — render the journal as a narrated
  walkthrough (rich panels: the legal act, its machinery, the resulting
  anchors) with zero infrastructure contact. This is the audience-facing
  "movie" of the simulation.

Relation to the two clocks: journal `seq` is *simulation time*; it references
legal time (git anchors) and institutional time (matter events) but replaces
neither.

### 2.2 `executors.py` — where actions run (requirement 2)

One interface, three implementations, chosen per run:

```python
class Executor(Protocol):
    def run(self, actor: str, city: str, action: str, **params) -> dict: ...
```

- **`OperatorExecutor`** (exists today): loads the chamber operator-side from
  `world.json` + slices. Used now; also the reference implementation for
  `--verify` replay.
- **`ContainerExecutor`**: `podman exec polis-city-<id> polis …` inside city
  containers, which hold only their slice (citizens, local offices) — the
  federated view stays outside. This is the narrative-correct mode: citizens
  act from *their* polity. Depends on the city image (task for later:
  `polis-city` image = python + git + polis package + slice at
  `/etc/polis/city.json`).
- **`HttpExecutor`** (later): the same actions over the FastAPI service, when
  the city node grows one (see `docs/todo/simulation-service-requirements.md`).

The executor is also the **journal writer** and the injection point for
`--isomorphism` rendering, so every action — however executed — produces the
same Plan objects we already have. No new legal logic anywhere: the sim layer
orchestrates `polis.legislation` functions, it never re-implements them.

### 2.3 `storygen.py` — the legal story generator (requirement 3)

Seeded, deterministic generator of simulation *material* from the world
state. It does not execute anything; it emits scenario ingredients:

- **grievances** (petition seeds): domain-shaped problems ("the harbour dues
  burden small vessels") tied to a city and a legal domain;
- **bills**: an act/amendment/repeal answering a grievance, with title,
  target jurisdiction, proposer drawn from the city's legislators;
- **conflict seeds**: the interesting cases — two cities drafting
  incompatible statutes in the same domain (→ merge conflict = conflict of
  laws), an ultra-vires ratification attempt (→ refusal), a repeal after
  enactment, a codification after a messy debate;
- **casting**: which persons take which roles, respecting agency separation
  and jurisdiction (a bill touching `taxation/` must be ratified by the
  Keeper, not a city archivist).

Determinism: `storygen(seed)` ⇒ same scenario every time — which is what
makes `--verify` replay possible. Output is a **`.feature` file** plus a
small casting/manifest JSON, written to `data/sims/<run-id>/`.

### 2.4 `bdd/` — the Behave layer (requirement 4)

```
features/                 # authored + generated .feature files
  steps/
    world_steps.py        # Given a federation … / persons and offices
    docket_steps.py       # petitions
    bill_steps.py         # drafting → ratification
    archive_steps.py      # obtain/promulgate/repeal…
  environment.py          # run context: world, executor, journal, cleanup
```

Step vocabulary mirrors the legal language already in the CLI, e.g.:

```gherkin
Given the federation is at phase 1
  and "m.grimsbane" of "cogswich" has obtained the archive

Scenario: A municipal act is enacted through the full procedure
  When "m.grimsbane" files the petition "The harbour dues are unjust"
  Then the docket contains "PET-0001"
  When he drafts the bill "Harbour Dues Act" as an act for "municipal/cogswich"
   and introduces it answering "PET-0001"
   and "e.vexley" scrutinizes it with verdict "approve"
   and "e.vexley" ratifies it
  Then the corpus on "main" contains "municipal/cogswich/harbour-dues-act.md"
   and its status is "enacted"
   and the matter "ACT-0001" is recorded as ratified
```

Design rules for the step library:

- Steps call **executors + assertion helpers over the three stores** (git log
  contents, matters.json, world.json) — never raw API calls.
- Step text stays legal-institutional ("files the petition", "ratifies"),
  with machinery confined to `Then`-level observable facts where the audience
  wants the isomorphism ("its status is enacted", "the genealogy shows a
  merge").
- Failed assertions leave the journal and stores for post-mortem — runs are
  reproducible, so debugging is `replay --verify`.

## 3. Data flow of a run

1. `polis sim new --seed 42 --story harbour-dues` → storygen emits
   `data/sims/<run-id>/feature + casting.json`.
2. `polis sim run <run-id> [--executor operator|container]` → behave executes
   the feature through the step library; the executor journals every action
   with anchors.
3. `polis sim present <run-id>` → narrated step-through from the journal.
4. `polis sim replay --verify <run-id>` → re-execution against fresh infra
   with anchor assertions.

## 4. Phasing / tasks this spawns

| # | Task | Type |
|---|---|---|
| — | `polis/sim/journal.py` + executor interface + `OperatorExecutor`, `sim run/present/replay` (operator mode, behave) | [simulation] |
| — | step library v1 (world/docket/bill) + one hand-written feature reproducing the e2e flow as BDD | [simulation] |
| — | `storygen` v1: grievances+bills+casting for the 9 cities, seeded | [simulation] |
| — | conflict seeds (merge conflict, ultra-vires, repeal flows) | [simulation] |
| — | `polis-city` image + `ContainerExecutor` | [infrastructure] |
| — | archive/constitutional steps (promulgate, repeal, phase-2 erection) | [simulation] |

Dependencies: the container executor needs the city image; storygen needs the
step library; everything needs the journal. `matters.py` stays the only
political-state access point (per the design debt note).

## 5. Deliberate constraints (carried over)

- **No new legal logic in the sim layer** — it orchestrates
  `polis.legislation`; the isomorphism stays in the Plans.
- **The journal is written by machinery**, never edited by hand.
- **Determinism is a feature**: seeds for storygen, anchors in the journal,
  `--verify` as the test of both.
- **Behave is authoring + presentation**, not a second engine: the engine is
  the executor + legislation layer; Gherkin describes, the engine does.
