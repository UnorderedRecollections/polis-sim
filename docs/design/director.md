# The Director — design document

Status: design v1 (task 0023). The director drives the simulation forward.
Everything it needs already exists; this document is the six decisions that
remain, with options for each.

## 0. The loop

```
┌─────────────── one drive step ─────────────────┐
│  situation (norms+holdings, per-run)           │
│     → charged candidates (events.py)           │
│     → SELECT one (policy, seeded)              │
│     → INSTANTIATE a story (template + casting  │
│        + remedy)                               │
│     → EXECUTE story blocks via runtime.enact() │
│     → WRITE-BACK (norms, holdings, journal)    │
└────────────────────────────────────────────────┘
            repeat N times → a simulation epoch
```

## 1. What exists (inputs)

| input | where | role |
|---|---|---|
| charged candidates | `polis/sim/events.py` | the story seeds (actor, harmed, norms in question) |
| story templates | `data/world/legal/templates/` | procedural shape (resource_dispute: 10 blocks) |
| casting data | `world.json` persons/offices | who can sign, review, ratify |
| remedy vocabulary | `rule_forms` + `incompatibilities` | what the bill should propose |
| execution | `runtime.enact()` | one story block = one journal entry |
| anchors | journal | proof + later `--verify` replay |
| provisioned world | `polis provision` | the namespaced gogs world to drive in |

## 2. Decision 1 — story model

**Options:**
- **(a) free-form**: the director improvises move sequences from friction
  alone. Maximum variety; impossible to keep procedurally literate (which
  reviews happen in which order?) and hard to narrate.
- **(b) template-driven**: fixed sequences from `templates/*.yaml`, nouns
  bound from the candidate. Literate and presentable; mechanical if used
  alone.
- **(c) hybrid (chosen)**: the template gives the procedural *shape*; the
  charged candidate gives the *conflict*; director rules map one onto the
  other. resource_dispute's 10 blocks cover the petition-to-enactment arc;
  later templates (constitutional challenge, repeal cycle) cover other arcs.

## 3. Decision 2 — selection policy (per-party, not per-run)

**Options:**
- **seeded RNG** over the charged candidates (deterministic given the run
  seed — required for `--verify` replay);
- **priority rules**: max friction, jurisdiction rotation, "least recently
  legislated" — deterministic but less varied;
- **scripted queue**: a user-authored scenario file of forced beats —
  full authorial control, still deterministic.

**Chosen:** pluggable `Selector` with the three implementations above —
but bound **per party (city)**, not per run. The drive step has two levels:

```
global scheduler: which party acts next?   (round-robin | seeded)
party selector:   what does THAT party do? (its own policy)
```

Policies live in a per-sim map (`data/sims/<run>/policies.yaml`):

```yaml
default: seeded
cogswich: priority
thornwick: scripted        # reads its queue, see below
brasshaven: interactive    # explicit user control
```

This is what makes the future modes possible without redesign:

- **mixed epochs**: some cities seeded, some rule-driven, in one run;
- **user-controlled cities**: a `scripted` party consumes a *queue file*
  (`data/sims/<run>/queues/<city>.yaml`) that the user appends to **while
  the sim runs** — the director blocks (or skips, per policy flags) when a
  controlled party's queue is empty; an `interactive` policy prompts at
  drive time;
- **external scenario sources**: anything that can write the queue file is
  a scenario source — an editor, a generator, an LLM through the MCP
  boundary. The director doesn't care who writes, only that the queue is
  valid (validated like every other YAML).

Determinism note: scripted/interactive inputs are *journal-recorded as
scenario events*, so `--verify` replay reproduces even user-driven runs —
replay consumes the journal, not the live queue.

## 4. Decision 3 — casting (party → person)

The jurisdiction actors (`fisher of cogswich`) have no platform accounts;
the world's persons act *for* them:

| story role | casting rule |
|---|---|
| petitioner / bill proposer | a **citizen-legislator of the harmed party's city** ("on behalf of the fishers of Brasshaven") — the constituency channel |
| jurisdictional reviewer | the domain expert **iff** the jurisdiction has a `corpus_dir` (`expert-<domain>`); otherwise **skipped with a record** ("no federal expert exists for fisheries — its acts are municipal in form") |
| constitutional reviewer | a Council jurist, **seat rotation** (seat 1 → 2 → 3 per story) |
| ratifier | the **Keeper** (cross-city law); a **local archivist** if the bill touches only `municipal/<his-city>/**` |
| respondent's voice (debate) | a legislator of the *acting* party's city |

**Chosen:** pool + rotation, deterministic via the run seed; every cast
recorded in the story state (auditable, replayable).

## 5. Decision 4 — remedy selection (what the bill proposes)

**Options:**
- **(a) random** from the jurisdiction's `rule_forms`;
- **(b) derived from incompatibilities (chosen)**: the harmed party wants
  the rule form that is *incompatible with the norm hurting them* — the
  incompatibility table literally lists the candidates (e.g. hurt by
  `open_access`? the remedy is `quota`/`exclusive_access`/`licensing`). The
  legal question is then guaranteed real;
- **(c) scripted** (the scenario file dictates the remedy).

**Chosen:** (b), with (c) able to override; seeded pick among the
incompatible forms. If none exist, fall back to (a) among `tension` pairs.

The bill's text is generated from the document template (`act.md`) with a
title derived from remedy+resource ("Northern Banks Quota Act"). LLM prose
is a later refinement of exactly this step only.

## 6. Decision 5 — the clock and the story state machine

**Options:**
- **one whole story per drive step** (atomic, simple, presentable);
- **one block per tick** (finer, allows interleaving stories — and
  *racing* bills, which is where merge conflicts come from).

**Chosen:** **one whole story per drive step** in v1; the story is executed
block by block internally, journaled per block, and anchored by a `story`
journal entry linking its beats. Interleaving (two active stories racing
for the same corpus path → a real merge conflict = conflict of laws) is
the v2 reason to go finer — noted, deferred, not compromised away.

**State:** `data/sims/<run>/stories.json` — mutable story records (id,
template, bindings, cast, status, produced matter/branch/commits). The
journal stays append-only; stories.json is the resumable state. Both live
in the run dir (export format unchanged).

## 7. The executor question, explained (must be solved for v1)

**What a Chamber is**: the working context of one legislative act — actor,
token, remotes, repo_dir, and *how to reach the platform from here*. It has
two modes, and the modes differ in exactly one thing: **where "here" is**.

| | container mode | operator mode |
|---|---|---|
| entered via | `POLIS_CITY_CONFIG` or `/etc/polis/city.json` | `--city` on the host |
| remotes used as-is | `http://gogs:3000/…` (works **inside** the podman network) | — |
| host-swap? | no | `gogs:3000` → `localhost:10880` (because `gogs` doesn't resolve on the host) |

**The mismatch in a provisioned sim.** The runtime today builds chambers
from *world* slices (`world/cities/*.json`). But a provisioned sim has:

- persons on gogs as **`<sim>-<username>`** — the world slices don't know
  these accounts; the sim's per-person tokens live in the **sim slices**;
- sim slices at `data/sims/<sim>/cities/*.json` whose remotes are
  in-network URLs (`http://gogs:3000/<sim>-cogswich/common-law.git`).

If the director (running on the host) loads a sim slice through the usual
path (`POLIS_CITY_CONFIG`), the chamber enters **container mode** — no
host-swap — and tries to reach `http://gogs:3000` from the host, which
fails. If instead we use `--city`, we get the host-swap but the **wrong
slice** (world slice: no sim remotes, no sim tokens).

**Chosen (revised after review): the operator runs in a container too.**

Instead of host-swap gymnastics, put the operator **inside the network**:

```
┌─ gogs-local (podman network) ─────────────────────────────┐
│  gogs   polis-operator-<sim>   polis-city-<c1>-<sim>  …   │
│              │ mounts                                     │
│              │  /sim      = data/sims/<sim>/  (rw)        │
│              │  /legal    = data/world/legal/ (ro)        │
└──────────────┼────────────────────────────────────────────┘
               │ host CLI proxies platform-touching actions:
               │   podman exec polis-operator-<sim> polis …
          data/sims/<sim>/ (host can read: present, status)
```

The operator container (`polis-operator-<sim>`, same `polis-city` image,
sim id carried like every other resource) holds:

- the sim's slices at `POLIS_CITY_CONFIG` — **container mode, no
  host-swap, ever** (it can reach `gogs:3000` because it *is* in the
  network);
- the mounted sim volume `/sim` containing `matters.json` (per-sim
  institutional time — the companion issue disappears with it), the
  journal, `stories.json`, the situation, and a git workdir for clones.

The host-side `polis` CLI splits cleanly in two:

- **reads**: `sim present`, `sim list`, `provision status` — pure file
  reads on `data/sims/`, no container contact;
- **acts**: `sim drive/tick`, `provision up/teardown` — proxy into the
  operator container (`podman exec`), or run the director itself inside it.

Consequences, all favorable: the host-swap becomes irrelevant to the sim
(it survives only for host-side ad-hoc testing, e.g. the e2e scripts);
city containers and the operator see the *same* network and the *same*
mounted sim state; `sim stop/start` has a natural meaning (operator +
city containers); and ContainerExecutor later is not a new mode, just
"exec into a different container of the same architecture".

## 8. V1 scope and CLI

```
polis sim drive <run> --steps N [--selector seeded] [--seed 42]
polis sim tick <run>                    # = drive --steps 1
polis sim stories <run>                 # story records with status
```

A drive step executes the §0 loop. After N steps:

- N stories journaled end-to-end (petition → … → enactment);
- the situation shows N norm transitions (supersessions/enactments);
- matters hold the procedural record; git holds the legal history;
- `polis sim present <run>` narrates it all, infra-free.

**Demo test** (`tests/director-demo.sh`): `provision up dir-demo-01` →
`sim new dir-demo-01 --situation fisheries-seed` → `sim drive --steps 2` →
assert: 2 matters ratified, 2 norm transitions in the situation, journal
anchors chain (each story's main_before == previous main_after), git log
on the archive shows 2 enactment merges → `teardown` + `nuke` orgs.

## 9. Deferred options (explicitly not v1)

- interleaved stories / racing bills (finer clock — §6);
- LLM-generated bill text and debate contributions (§5 seam);
- ContainerExecutor driving (needs nothing new conceptually — §7);
- multi-jurisdiction epochs and cross-jurisdiction frictions (needs the
  qualified object kinds from docs/todo);
- director as a long-running service (it stays a CLI-driven stepper;
  `sim drive` *is* the scheduler).

## 10. What could invalidate this

- if casting can't find a person for a role (a city with no free
  legislator), the story must skip with a record — v1 accepts skips as
  first-class outcomes (a failed story is still a true story);
- determinism relies on *all* randomness going through the run's seeded
  RNG (selector, casting rotation, remedy pick) — the journal records the
  seed at drive start.
