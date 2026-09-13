# Scenarios vs tests — driving the simulation is not testing it

Status: design (2026-09-13, from the 0053/0057 discussion; refines
roadmap §1 "one binding, two drivers"). The insight: **driving the
simulation with BDD and testing the software with BDD are different use
cases** that happen to share a syntax. Mixing them in one vocabulary,
one feature tree and one runner is a design gap — the long-term UI
surface (TUI/Web) is meant for the first use case, while `features/` and
`tests/all.sh` serve the second.

## 1. The two use cases

| | testing the software | driving the simulation |
|---|---|---|
| audience | developers, CI | non-technical users (future TUI/Web) |
| lifecycle | throwaway sim per scenario, provisioned and destroyed | a *running* sim; the scenario is queued and serviced incrementally |
| input | `features/*.feature` (developer-authored) | user-authored scenarios, submitted via `sim submit`/UI |
| execution | synchronous (behave); one process owns the run | asynchronous; one action beat per drive step, director stories interleaved |
| expectations | assertions: fail the suite | goals/observations: what should the simulation show? |
| failure | the test fails, cleanup runs | pause the scenario, the sim goes on (`sim resume`) |
| determinism | seeded, reproducible | replayable journal; the sim evolves |
| identity | fixtures (`_Cast`, sim slices) | the world's persons and offices; eventually authenticated users |
| entrypoint | `uv run behave`, `tests/all.sh` | `polis sim submit|scenarios|resume`, future UI |

What they legitimately share is the **action core**: `runtime.enact()`,
the legislation plans, the scenario parser/model, and the user-facing
actions. "One binding, two drivers" survives at the action level — not
at the vocabulary, tree or runner level.

## 2. Where the coupling hurts today

- `polis/sim/beats.py` is one flat table mixing four kinds of beats:
  - user actions: petition/draft/ratify, scrutinize;
  - test setup: `a provisioned sim seeded from …`;
  - oracles: `the archive main contains …`, `norm … is superseded`,
    `the Mechanical Magistrate approves …`, `the petition is a real issue`;
  - one hybrid: `the federation codifies its machinery` performs a legal
    act *and* erects the CI (infrastructure).
- `features/environment.py` (provision/destroy, `world.json` snapshot,
  platform selection) is pure test harness, sitting beside the parser.
- `queue.py` accepts every binding, special-cases the provision beat at
  submission, and gives expectations a third semantic ("check that pauses
  the scenario") that is neither assertion nor goal.
- `features/phase-transition.feature` looks like user content but is a
  developer test with infra oracles.
- Actor casting (`_Cast`) and Chamber resolution are director/test
  assumptions baked into the driving path.

## 3. Target layering

```
            action core            runtime.enact + legislation plans +
       (one implementation)        user-facing action bindings
              ^            ^
   scenario driving layer      test harness
   parser, scoped vocabulary,  behave, throwaway sims,
   queue, service API, UI      setup/oracle beats, CI wiring
```

Rules:

- the driving layer must not import behave, `provision`, or the test
  environment;
- the harness may use the action core and the parser; it must not depend
  on the queue's scheduler (or only through an explicit adapter);
- action implementations exist once.

## 4. The vocabulary split

- `Binding` gains `scope: user | test` (and later `requires_phase`,
  `requires_office` for authoring help).
- The rule: **`test`** beats are harness setup and operator-machinery
  introspection — the provisioned-sim precondition and the CI's
  existence; **`user`** beats are the legal actions *and* the in-world
  outcomes a scenario author states as goals (petition answered, norm
  superseded, archive/corpus contents, platform issue/PR/merge, the
  Magistrate's verdicts, the federation's phase). The catalog a UI
  renders therefore shows actions and goals, never provisioning.
- `polis sim submit`/`validate` accepts only `user` beats; behave may
  execute all (`test` beats are the harness's).
- The CI erection moves out of `b_codify` into the **driver** (the test
  harness now; the host command/service later) — a machinery effect, not
  a scenario beat; `b_codify` stays a legal act.
- A machine-readable catalog (`polis sim steps [--scope user] [--json]`)
  is generated from the table: the UI authoring surface and the docs both
  consume it.

## 5. Trees, runners, docs

- `features/` — software tests only (behave, `tests/all.sh`, `@slow`).
- `scenarios/` — tracked example/user scenarios, no test tags, meant for
  `sim submit` and for the UI's library.
- docs split: `docs/testing.md` (developers) and a scenario-authoring
  guide for users; AGENTS.md points at both.

## 6. Live semantics to decide (in 0060)

- expectations as goals: wait-until with a time bound, or pause on
  failure? cancellation? what does `scenarios` show?
- pacing: one action per drive step (today), or ticks/instants?
- identity: who acts when a scenario names "the fishers" without a user
  session — the world's casting rules, later the authenticated user.
- determinism/replay: journal replay, seeded selections.

## 7. Service and UI horizon

- identity: Chamber-independent actors are already a design debt
  (`docs/todo/simulation-service-requirements.md`); auth is task 0052.
- state: event-sourced scenario state, stepping/replay over the two
  clocks (git = legal time, matter/scenario events = institutional time).
- API: submit/list/resume/cancel + streamed status; the operator
  container is the natural home for the service (roadmap §1's horizon).
- the catalog feeds authoring UIs; the session/lifecycle feeds status UIs.

## 8. What not to do

- don't fork action implementations per driver;
- don't let the driving layer depend on fixtures or provisioning;
- don't keep hybrid beats;
- don't let a test assertion masquerade as a user goal.

## 9. Work items

- **0059** — vocabulary scope + catalog (this note's §4);
- **0060** — scenario tree, authoring contract + guide, driver tests
  (§5, §6);
- **0061** — the scenario service: identity, event-sourcing, replay,
  long-running wrapper (absorbs `simulation-service-requirements`);
- **0062** — TUI for authoring and live interaction;
- **0063** — Web UI for authoring, live status and presentation.
