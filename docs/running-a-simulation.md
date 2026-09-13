# Running a simulation — user guide

The complete lifecycle, from an empty machine to a federation legislating
on its own. Every command below is real and tested.

The one-sentence version:

```
container runtime up → uv sync → world genesis → legal validate
→ provision up → sim new --situation … → sim drive --steps N → sim present
→ provision teardown → rm -rf data/sims/<sim>
```

---

## 1. Requirements

| requirement | what for |
|---|---|
| **a container runtime** — podman (machine started) or docker | everything (each sim gets its own postgres + gogs + operator); auto-detected, `POLIS_RUNTIME` overrides |
| **uv** | the Python package manager — *never* pip or ad-hoc venvs |
| **git** | the legal archive is git history |

Install the project (from the repo root):

```bash
uv sync                 # resolves uv.lock into .venv
uv run polis --help     # everything runs through uv
```

No secrets or prior infrastructure are needed: each sim provisions its own
platform (§5). `.env` is only consulted for `POSTGRES_PASSWORD` (defaults
to `gogs`).

## 2. (Development only) the shared dev rig

> **You do NOT need this to run a simulation.** Skip to §3.

`scripts/infra/compose-up.sh` brings up the *shared dev rig* — hardcoded
container names (`gogs`, `postgres-gogs`, network `gogs-local`) used by
the e2e tests and platform development. It is a one-time bring-up:
re-running it while the rig is up collides on container names. Sims never
touch this rig (§5), and the rig never touches sims.

```bash
scripts/infra/compose-up.sh     # once, for e2e/platform work
scripts/infra/smoke.sh          # rig healthy, API keys valid
uv run polis health             # subsystem checks from the CLI's side
```

The test suites themselves — the fast behave stories, the slow gitea
suites (phase I → transition → phase II) and the demo scripts — are
documented in `docs/testing.md`.

## 3. Generate the world (once, ever — it is shared)

```bash
uv run polis world genesis            # 9 cities, 63 persons, all offices
uv run polis world genesis --force    # regenerate from scratch (destroys the old one)
```

This writes `data/world/world.json` + `data/world/cities/*.json` — the
civil registry: who exists, who holds which office (the Keeper of the
Federal Rolls, the Council jurists, the local archivists, the domain
experts), every person's credentials.

> **The world is NOT per-sim.** There is one federation, and every sim is
> an *epoch* played out over the same registry — sims share the citizens
> and offices (they get their own platform accounts at provisioning).
> "A world already exists" is the normal, correct state of affairs;
> `--force` is for starting the *fiction* over, not for starting a sim.

## 4. Author and validate the legal seed

The simulation's subject matter lives in `data/world/legal/` (tracked in
git — this is story *source*, not runtime state):

```
jurisdictions/*.yaml   the 15 jurisdictions (actors, activities, rule
                       forms, incompatibilities, resources)
norms/*.yaml           the seed situation per jurisdiction: norms in
                       force + holdings (one format for seed AND evolved
                       state — the snapshot principle)
ontology/*.yaml        actor/object/relation/event kinds
resources/<j>/*.yaml   concrete resources
transition/*.md        the phase-2 transition corpus: three acts +
                       their instruments (CODEOWNERS, branch-protection,
                       woodpecker.yml) — content only, enacted later
templates/*.yaml       story grammars (resource_dispute, phase_transition)
```

Phase 1 is explicit from the founding: every sim's founding commit
contains `constitution/02-customary-machinery.md` (Article 3 — the
customary machinery), and `world.json` carries `federation.phase: 1`.
The phase-2 transition is *legislation*, not configuration: the acts
authored in `transition/` enter the corpus through the ordinary
phase-1 procedure (story template `phase_transition`); the machinery
takes effect when they are ratified.

Validate before anything runs:

```bash
uv run polis world legal validate     # the whole seed, cross-checked
uv run polis world legal audit        # the new-jurisdiction checklist
```

Browse what the seed implies:

```bash
uv run polis world events candidates --jurisdiction fisheries
```

Charged candidates are the story seeds: who acts, whose holding is
harmed, which norms are in question.

## 5. Provision the sim

One command assembles a complete, namespaced world on the platform:

```bash
uv run polis provision up my-sim-01
```

A sim is **fully self-contained** — nothing touches your other containers:

- **its own platform**: network `my-sim-01-net`, containers
  `my-sim-01-postgres`, `my-sim-01-gogs` and `my-sim-01-proxy` — a caddy
  **front proxy** is the sim's only published port (persisted as
  `proxy_port`), routing `/gogs`, `/gitea`, `/ci` to the services
  (task 0042). Headless bootstrap: schema, admin, API token;
- **users** `my-sim-01-<username>` (64) with per-sim API tokens;
- **orgs + repos** `my-sim-01-archive` and `my-sim-01-<city>` (10 ×
  `common-law`), each seeded with the same founding commit;
- **slices** `data/sims/my-sim-01/cities/*.json` (remotes + tokens);
- the **operator container** `polis-operator-my-sim-01` — on the sim's
  network, the sim dir mounted at `/sim`, the world read-only at
  `/polis-data/world`. This is where legislation physically happens.

Per-sim secrets (admin credentials, token, ports) live in
`data/sims/my-sim-01/secrets.json` — never in world.json. Re-running
`up --force` reconciles against the existing platform (credentials
preserved).

Check it:

```bash
uv run polis provision status my-sim-01
```

The platform's canonical URL is
`http://host.containers.internal:<proxy_port>/…` (gitea/gogs render their
links with it). In-network containers resolve that name natively; for
your **host browser** run `scripts/infra/hosts.sh add` once (sudo) — or
use the `localhost:<proxy_port>/gogs|gitea|ci` form, which the proxy also
serves.

### Addressing the sim with the generic commands

By default the generic commands (`polis health`, `polis gogs …`) address
the shared dev rig. Point them at your sim instead:

```bash
export POLIS_PROVISIONED_SIM=my-sim-01
uv run polis health        # checks my-sim-01-gogs/-postgres/-net/operator
uv run polis gogs --help   # API calls go to the sim's gogs as its admin
```

Resolution order: explicit `POLIS_*` overrides > the sim's `secrets.json`
> process env/.env > built-in defaults. Unset the variable to return to
the dev-rig context. (Gitea/woodpecker checks report n/a in a sim
context — phase-1 sims run gogs only.)

Optional: `--with-city-containers` also starts the nine city nodes
(citizens acting from inside their own city).

## 6. Bootstrap the run

Provisioning builds the *world machinery*; this step chooses *what the
sim will legislate about*. The run **is** the sim (same id, same
directory), so with the context var set no id is needed:

```bash
export POLIS_PROVISIONED_SIM=my-sim-01
uv run polis sim new --situation data/world/legal/norms/fisheries.yaml \
  --seed fixed-seed-1          # optional; generated and recorded otherwise
```

This copies the seed situation in as `situation.yaml` and writes
`run.json` (jurisdiction + seed — the determinism anchor: every random
choice derives from it). Skipping this step is why `sim tick` says
"no run.json".

**Starting from more than one seed, or changing the situation later:**
`situation.yaml` is a plain file in the same format as the seeds (the
snapshot principle — seed and evolved state share one format/loader), and
the director re-reads it on every drive call. So:

- any YAML in that format works as `--situation` — including another
  run's evolved `data/sims/<other>/situation.yaml` (an epoch transplant);
- you can merge several seeds by hand into one file (concatenate `norms:`
  and `holdings:`, keeping ids unique) and edit `jurisdiction` in
  `run.json` accordingly;
- you can edit `situation.yaml` between ticks — grant a holding, repeal a
  norm by fiat — and the next story inherits your intervention.

Caveat: v1's director generates candidates for the *one* jurisdiction in
`run.json`; multi-jurisdiction epochs are deferred design.

## 7. Drive

```bash
uv run polis sim drive --steps 3         # run id defaults to POLIS_PROVISIONED_SIM
uv run polis sim tick                    # one story
```

**How many steps?** As many as you want the epoch to contain — a step is
one story, not a unit of difficulty. There is no "right" number; watch
`sim stories` / `sim present` and stop when the epoch tells you what you
wanted to know. If the situation runs out of grievances (no charged
candidates), the director records a `skipped` story and stops on its
own — the situation is settled. Repeated remedies are not an error: the
second Quota Act is enacted as "… (No. 2)".

**After pulling code changes:** the operator container runs the packaged
code from the `polis-city` image. Rebuild the image and refresh the
container or sims keep running the old code:

```bash
podman build -t polis-city:latest -f docker/polis-city/Dockerfile .   # or docker build
uv run polis provision up --force    # recreates the operator container
```

Each step drives **one whole story** end to end, inside the operator
container (the host CLI proxies via the runtime's `exec`):

- the situation yields charged candidates (frictions);
- the seeded selector picks one;
- casting: a citizen-legislator of the harmed party's city petitions on
  their behalf; a Council jurist reviews constitutionally (seat
  rotation); a domain expert reviews iff the jurisdiction has a federal
  corpus — fisheries doesn't, and the record says so;
- the remedy comes from the contested norm's **incompatibilities** (hurt
  by open access? the bill proposes quota / exclusive access / licensing);
- petition → bill → reviews → the Keeper ratifies → the situation is
  written back (old norm superseded, new statute in force).

Three stores move in lockstep: **git history** (the legal archive),
**matters.json** (the political record, per sim), **the journal**
(`journal.jsonl`, the run's replay log) — plus `stories.json`, the story
state.

## 8. Watch what happened

```bash
uv run polis sim present                   # narrated step-through
uv run polis sim present --last 10
uv run polis sim stories                   # story records: status, cast
uv run polis sim runtime                   # journal size, norms in force
uv run polis docket list                   # all petitions (the sim's, in sim context)
uv run polis docket list --city brasshaven # one city's petitions
```

All four are pure file reads — no infrastructure contact. A failed story
is recorded with its error; it is a true story, not a crash.

### Epochs: archiving the record and starting fresh

The record (journal, situation, stories, matters) is what `present`
narrates; it survives teardown by design. Manage it as porcelain:

```bash
uv run polis sim fresh --yes     # archive the current record to
                                 # epochs/<timestamp>/ and clear it —
                                 # the next `sim new` starts a FRESH epoch
uv run polis sim epochs          # list saved epochs (entries, span)
uv run polis sim present --epoch <name>   # narrate a saved epoch
```

`sim fresh` touches only the record: the machinery (platform, slices,
secrets) is untouched — and the **legal archive's git history does not
roll back** (your next epoch may enact "… (No. 3)" acts on a corpus that
remembers the previous ones; institutional time — PET/ACT numbering —
restarts). For a blank legal slate, `teardown` + `rm -rf` the sim dir.

The legal truth is in git itself:

```bash
# <proxy_port> is in data/sims/my-sim-01/secrets.json (proxy_port)
git clone http://localhost:<proxy_port>/gogs/my-sim-01-archive/common-law.git
git -C common-law log --oneline     # the enactment merges
```

## 9. Stop, resume, delete

```bash
uv run polis provision list            # every sim on this host (dirs, containers,
                                       # journal sizes) — start cleanup here

uv run polis provision stop          # pause: containers stopped, EVERYTHING kept
uv run polis provision start         # resume (postgres → gogs → the rest, in order)

uv run polis provision teardown --yes   # delete the MACHINERY: repos, users,
                                        # containers, network. The sim dir
                                        # (journal, situation, stories, secrets,
                                        # volumes) stays — the epoch survives.

uv run polis provision destroy --yes    # delete EVERYTHING, controlled:
                                        # best-effort API cleanup, all containers
                                        # (matched by NAME, tolerant of stale
                                        # inventories), the network, the sim dir
```

(sim id omitted above: it defaults to `POLIS_PROVISIONED_SIM`.)

`destroy` is the controlled `rm -rf`: it also cleans up *orphans* —
containers/networks whose sim dir is already gone (which is what manual
`rm -rf` leaves behind). After a teardown, `provision up` (no `--force`)
rebuilds the machinery over the surviving sim dir and the epoch resumes.

After a teardown, `provision up` (no `--force` needed) rebuilds the
machinery over the surviving sim dir — the journal and situation resume
where they left off. `--force` is only for re-provisioning a *running*
sim.

Since the whole platform is per-sim, orgs/users/tokens die with the sim's
gogs — no DB surgery needed. (`polis nuke gogs orgs <prefix>` remains for
the *shared dev rig* only, where the gogs API has no org-delete route.)

`polis world cleanup` removes stale per-sim credentials from world.json
(leftovers from pre-0026 provisioning).

Or skip teardown entirely and keep `data/sims/my-sim-01/` — it is the
complete, portable record of the epoch (journal, situation, stories,
matters).

---

## Reference: the moving parts

| piece | where | nature |
|---|---|---|
| legal source | `data/world/legal/` | tracked in git; you author it |
| civil registry | `data/world/world.json`, `cities/` | genesis output |
| sim dir | `data/sims/<id>/` | everything one run produces |
| the archive | gogs repos `<sim>-*/common-law` | the law itself, as git history |
| operator | container `polis-operator-<sim>` | where legislation happens |
| platform quirks | `docs/services/gogs.md` | read before debugging gogs |

## Troubleshooting

- `polis provision status <sim>` first — most sim failures are dead sim
  containers. (`polis health` / `smoke.sh` check the shared dev rig, which
  sims don't use.)
- "no operator container running" during `sim drive` → the sim was not
  provisioned (or was torn down); `--local` exists for development only.
- A story fails with `ultra vires` → the bill's paths escaped the
  ratifier's jurisdiction; only the Keeper ratifies cross-city law.
- Determinism: same seed + same seed situation ⇒ same stories. The seed
  is in `data/sims/<id>/run.json`.
