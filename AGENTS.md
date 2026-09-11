# AGENTS.md

## What this is

Implementation companion to an article arguing an isomorphism: **Git = the
historical/legal-record layer of a legal order; a GitHub-like platform = the
constitutional/institutional apparatus governing how the corpus may change.**
`docs/isomorphism/synopsis.md` is the conceptual skeleton (§1–§21, cited from
code comments) — read it before design decisions; `docs/isomorphism/` expands
each theme.

The project simulates a fictional federation ("The Concord of the Nine
Cities") whose legislative life runs on real local infrastructure.

## Layout

- `polis/` — Python package, "operator's tool". CLI entry: `polis = polis.cli.main:app`.
  - `models.py`, `genesis.py`, `names.py`, `store.py` — domain model (World/City/Person/Office),
    deterministic founding-population generator, persistence.
  - `matters.py` — the matter store (pending petitions/bills + procedural record).
  - `cli/` — typer commands. Domain: `world city person office assign`;
    legislative: `docket bill archive`; component: `gogs gitea woodpecker citynode health`.
  - `clients/` — httpx wrappers for gogs/gitea/woodpecker APIs + podman CLI wrapper.
  - `legislation/` — the legislative engine: plan, chamber, gitcmd, docket, bill,
    archive, documents (+ `templates/*.md` — act/amendment/repeal scaffolds).
- `data/` — all mutable state:
  - `world/` — `world.json` (9 cities, 63 persons, offices) + `cities/*.json` slices
    + `matters.json`. Regenerate world with `polis world genesis --force`.
  - `world/legal/` — the legal-design YAML (story data, **tracked in git**):
    `jurisdictions/*.yaml` (15), `ontology/*.yaml` (actors/objects/relations/
    events/paradigms/norm-kinds),     `norms/*.yaml` (seed situation documents: norms + holdings per
    jurisdiction — **snapshot principle: seed and evolved state share one
    format/loader**; validate the whole seed with `polis world legal validate`),
    `resources/<jurisdiction>/*.yaml` (concrete resources — files are the
    source of truth; jurisdiction `resources:` list is a cross-checked index),
    `transition/` (the phase-2 transition corpus: three acts + their
    instruments CODEOWNERS/branch-protection/woodpecker.yml — authored
    content only, task 0036; machinery effect is task 0038),
    `moves.yaml`, `templates/*.yaml`. Loaders: `polis/sim/legaldata.py`,
    `polis/sim/ontology.py`, `polis/sim/norms.py`, `polis/sim/resources.py`;
    event synthesis: `polis/sim/events.py` (friction derivation, charged
    candidates — `polis world events candidates --jurisdiction <slug>`);
    extensibility audit: `polis/sim/extensibility.py` (`polis world legal
    audit [slug]` — the new-jurisdiction checklist as code);
    runtime: `polis/sim/journal.py` (append-only JSONL with anchors,
    `data/sims/<run>/`), `polis/sim/runtime.py` (**enact() transaction facade
    — one call = one legal act = one journal entry; the sim never touches git
    stepwise**; situation write-back on ratify/repeal), CLI `polis sim
    new|list|present|runtime`; demo: `tests/sim-runtime-demo.sh` (**passing**);
    rationale: `docs/design/story-data-model.md`.
- `.state/` — container persistent data (gogs/gitea/woodpecker/postgres),
  gitignored. All other runtime state under `data/` is gitignored except
  `data/world/legal/` (source YAML).
- `docker/` — per-component Dockerfiles + `docker-compose.yml` (project `polis`,
  network `gogs-local`).
- `scripts/infra/` — `env.sh` (shared), per-service build/run scripts
  (`postgres.sh gogs.sh gitea.sh woodpecker.sh`), `compose-up/down.sh`,
  `smoke.sh` (per-container smoke tests incl. API-key validity).
- `docs/` — `running-a-simulation.md` (**the user guide**: requirements →
  infra → genesis → legal seed → provision → drive → teardown),
  `flows/` (**the legal flows**, master + petitions/legislation/archive/
  simulation, with mermaid graphs — read after the guide),
  `isomorphism/` (concepts), `design/` (simulator design + legal
  ontology), `services/` (per-service: why, start, API keys, quirks),
  `notes/` (background docs), `tasks/` (task files, see Task workflow),
  `todo/` (design debts).
- `tests/e2e-gogs.sh` — full live legislative flow against gogs (see below).
- `.env` — secrets (NEVER commit; template in `.env.example`).

## Infrastructure (podman, network `gogs-local`)

- postgres-gogs — shared DB (databases `gogs` + `gitea`), internal only.
- gogs :10880 — phase-1 platform ("customary machinery"; merely a mechanical
  archive in the fiction — no petitions/reviews/approvals).
- gitea :3001 — phase-2 platform ("codified machinery"; postgres-backed).
  Since 0037 it also hosts phase-1 sims: `provision up --platform gitea`
  (phase is a procedure, not a product — the federation stays in phase 1
  with matter-store proceedings on either product).
- woodpecker server :10890 + agent — CI (the Mechanical Magistrate), OAuth against gitea.
- City containers `polis-city-*` not built yet.
- Secrets: `.env` (`GOGS_API_KEY GITEA_API_KEY WOODPECKER_API_KEY
  WOODPECKER_GITEA_CLIENT/SECRET POSTGRES_PASSWORD`). Resolution order in
  `polis/config.py`: `POLIS_*_TOKEN` env > process env > `.env`.
- Endpoints overridable via `POLIS_*` env vars.
- **`POLIS_PROVISIONED_SIM=<sim>`** switches the generic commands (health,
  gogs …) from the shared dev rig to one provisioned sim: endpoints/secrets
  come from `data/sims/<sim>/secrets.json` (resolution: `POLIS_*` override
  > sim secrets > env/.env > defaults); container/network names become
  `<sim>-<platform>`, `<sim>-postgres`, `<sim>-net`, `polis-operator-<sim>`
  (platform = the provisioned product, `gogs` default). Health checks the
  sim's platform: gogs checks for gogs sims, gitea checks for gitea sims,
  the other suite reports n/a; woodpecker stays n/a (phase 2).
  `sim new/drive/tick/stories/present/runtime` default their run id to it.

## Key conventions

- **Every legislative operation builds a `Plan`** (machinery step + legal meaning);
  every such CLI command exposes `--isomorphism` to render instead of execute.
  Stated in `polis/legislation/__init__.py`; keep it.
- Agency separation: `political` persons (legislators/delegates) may not hold
  juridical offices; enforced in `cli/assign.py`.
- Federation `phase`: 1 = customary, 2 = codified (gitea+CI). Stored in world.json.
  **Phase is a procedure, not a product** (task 0037): either platform
  product can host phase 1; `federation.phase` never follows the product.
- `Chamber` (legislation/chamber.py) resolves actor/remotes/product/phase:
  `platform` = the provisioned product (from the slice's `federation.platform`,
  fallback phase-derived) and selects client/URL/token; `phase` (1|2) is the
  procedure — bill/docket dispatch on `phase == 2`, never on product. Two
  modes: container (`POLIS_CITY_CONFIG` or `/etc/polis/city.json`) vs operator
  (`--city`, host-swapped URLs). Testing hooks: `POLIS_PLATFORM_TOKEN`,
  `POLIS_ORIGIN_URL`, `POLIS_UPSTREAM_URL`, `POLIS_REPO_DIR`, `POLIS_MATTERS_FILE`.

## The three stores (ontology — settled)

- **git history** = the legal archive (what the law is; the platforms are merely
  its mechanical hosts with NO institutional concepts in the fiction).
- **`data/world/world.json` + `cities/*.json`** = the civil registry (who exists).
- **`data/world/matters.json`** = the political state: pending petitions (PET-####)
  and bills (ACT-####) with their procedural event record. Matters live in the
  **institutions and people**, not in the platform. **Recording an event ≠
  enforcing a procedure** — the constitution is enforced by people; jurisdiction
  checks run in the archivists' own tooling, never in the archive host.

## Recovered design decisions (from docs/notes/session-ses_f88c.md)

- **No database, deliberately**: world JSON = civil registry, git history = legal
  archive, matters JSON = political state. A DB of legal events would break the
  isomorphism.
- **Corpus layout encodes jurisdiction by path**: `constitution/` (council),
  domain dirs (`taxation/ maritime/ criminal/ commerce/ civic/ succession/`),
  `municipal/<city>/`.
- The Keeper of the Federal Rolls' credentials stay with the **orchestrator/
  operator**; city containers must never hold federal merge power.
- Phase-2 transition is enacted through phase-1 machinery: CODEOWNERS, branch
  protection and `.woodpecker.yml` land as three ratified bills.
- Agreed vocabulary: `docket file/list/show/comment/dismiss`;
  `bill draft/amend/introduce/debate/scrutinize/ratify/consolidate/reject/withdraw`;
  `archive obtain/receive/lodge/promulgate/repeal/transplant/reconstruct/replace-history`.

## Provisioning (porcelain)

- **The director** (`polis/sim/director.py`, design `docs/design/director.md`):
  `polis sim drive <run> --steps N` (== `tick` with 1) drives N whole stories
  end-to-end — situation → charged candidates → seeded selection
  (`Random(f"{seed}:{story-n}")`, seed in `run.json`) → casting (constituency
  petitioner, expert iff `corpus_dir`, council-seat rotation, Keeper ratifies)
  → remedy from incompatibilities → `runtime.enact()` per block →
  `stories.json` + `story` journal anchor. **Run id == sim id** (one dir under
  `data/sims/<id>/`: provision.json, cities/, journal, situation, run.json,
  stories.json, matters.json). Host-side `sim drive` proxies into the
  **operator container** (`polis-operator-<sim>`, always created by
  `provision up`: sim dir at `/sim` rw, whole `data/world` at
  `/polis-data/world` ro, env `POLIS_DATA_DIR POLIS_SIM_DIR=/sim
  POLIS_MATTERS_FILE=/sim/matters.json`); `--local` runs in-process.
  Demo: `tests/director-demo.sh` (**passing**).
- **Facts the director relies on**: the Keeper's `federal-archivist` office
  never enters city slices — container-mode chambers must be told of it
  explicitly (director appends it); ratify fetches the bill branch from the
  chamber's **origin**, so the Keeper's chamber origin is pointed at the
  petitioner's repo; `archive.obtain` establishes local `main` from
  `origin/main` (API-created repos have HEAD → nonexistent master); runtime
  anchors read `main`, not HEAD; journal `run_dir()` honors `POLIS_SIM_DIR`.
- `polis provision up <sim-id> [--platform gogs|gitea] [--with-city-containers]
  [--force]` provisions a **fully self-contained** sim instance: network
  `<sim>-net`, containers `<sim>-postgres` + `<sim>-gogs` or `<sim>-gitea`
  (headless bootstrap — `operator` admin user + token; gogs via app.ini
  (`DEFAULT_BRANCH=main`) + its CLI, gitea via `GITEA__*` env config +
  `gitea admin user create --access-token`; host port from
  `_free_port(11880+)`), users `<sim>-<username>` with per-sim tokens, orgs
  `<sim>-archive`/`<sim>-<city>` + `common-law` repos + **one shared founding
  commit** (`_founding_repo` — all repos must share history or the Keeper's
  enactment pushes are non-fast-forward), per-sim slices (carrying
  `federation.platform` = the product; tokens keyed by product), inventory
  `provision.json` (records `platform`). Secrets in `data/sims/<sim>/secrets.json`
  (**never world.json** — provisioning must not mutate the civil registry;
  `polis world cleanup` removes legacy `gogs@<sim>` residue). Slices/remotes
  use the in-network URL `http://<sim>-<platform>:3000`; the host port is for
  the operator CLI only. `status`/`teardown`/`destroy` use
  `sim_platform_client(sim)`; teardown removes containers+network, the
  platform volumes die with the sim dir (`rm -rf data/sims/<sim>`).
  Re-`up --force` reuses existing secrets/volume. Demos:
  `tests/provision-demo.sh` + `tests/provision-demo-gitea.sh` (**passing**).
- `polis nuke gogs orgs <prefix> --yes` (DB cascade) is for the **shared dev
  rig** only — per-sim gogs instances need no surgery.
- City containers: `docker/polis-city/Dockerfile` (build context = project
  root), run as `polis-city-<city>-<sim>` with the sim slice at
  `/etc/polis/city.json` and legal data mounted read-only via
  `POLIS_DATA_DIR` (config.py honors it). Verified: citizens act from inside
  their city container. Demo: `tests/provision-demo.sh` (**passing**).

## Platform facts learned the hard way (verified by probing)

- **`admin` is a reserved gogs username** — the sim's provisioning admin is
  `operator`; gogs web answers HTTP before its DB schema is migrated
  (retry `create-user`); postgres must be `pg_isready` before gogs starts
  (gogs crashes FATAL on connect refusal, no retry).
- **gogs usernames cap at 35 chars** — sim ids cap at 13 (`<sim>-<username>`
  must fit; enforced in `_validate_sim_id`).
- **This gogs build has NO pulls API at all**; issues API works. Phase-1
  petitions/bills are **matter-store entries**; ratify/consolidate always
  incorporate locally (`git merge [--squash] FETCH_HEAD` + push) and close the
  matter with the order entered into the record. Phase 2 (gitea) uses real PRs
  — same command surface, dispatch on `chamber.phase == 2` (task 0037), not
  on the product.
- **Gitea facts (v1.27, task 0037)**: token creation needs `scopes:["all"]`
  in the body when the caller authenticates with basic auth; token names are
  unique per user (re-runs use suffixed names, like gogs); org repos go
  through `POST /orgs/<org>/repos` (the admin-users route covers users only);
  an org with repos refuses deletion (delete repos first); the `gitea admin`
  CLI refuses root — run it `-u git` with `HOME=/data/git GITEA_WORK_DIR=/data/gitea`;
  `--access-token` prints the token on the last stdout line; the sim's
  postgres serves db `gitea` (created at provision time — `CREATE DATABASE`
  must be retried: `pg_isready` turns true during the entrypoint's temp
  bootstrap phase).
- **Also missing: forks API and token-delete route.** City repos are plain
  repos seeded by pushing the founding corpus (no fork relationship in
  phase 1); per-user tokens get suffixed names on re-runs (teardown deletes
  users, taking tokens with them). Org repos need explicit collaborator grants
  (org membership ≠ write).
- Gogs repo creation with `auto_init: true` fails; use `auto_init: false` and
  push a seed commit.
- Rich `Panel` takes `title_align`, not `title_justify`.
- In ratify/consolidate, `git fetch <url> <branch>` updates only `FETCH_HEAD` —
  always fetch `main` **before** the bill branch, or the merge is a silent no-op.

## Design decisions (document families + templates)

- Notes doc `docs/notes/families-of-legal-documents.md` reviewed; its
  "city = branch" row and YAML sketch are **superseded** (synopsis: a city is
  not a branch; stores are JSON).
- Templates are **files**: `polis/legislation/templates/{act,amendment,repeal}.md`
  (`{title}`/`{target}` placeholders; package-data in pyproject.toml).
  `bill draft --kind … --into <jurisdictional dir> [--target] [--answering]`
  scaffolds with `status: draft`.
- The `status:` field is written **only by the machinery**: `proposed` at
  `bill introduce`, `enacted` at ratification. Enactment is **one archival
  act** (merge `--no-commit` + flip + single merge commit), so
  `archive repeal <merge> --mainline 1` undoes the enactment whole.
- Repeal exists twice, deliberately: `archive repeal` (Keeper's exceptional
  correction) and repeal-as-bill (`bill draft --kind repeal`).
- The Mechanical Magistrate's phase-2 CI spec = the checklist in
  `docs/notes/families-of-legal-documents.md` §6.

## Roadmap

`docs/design/roadmap.md` — agreed direction (2026-09-10), tasks 0034–0039:
BDD driving (behave, the UX surface), situation generation, phase-1 made
explicit + the transition corpus, platform abstraction (phase = procedure,
not product; gitea can host phase 1), phase-transition machinery (ratified
acts flip the federation to phase 2), LLM integration (provider boundary,
journal provenance, MCP later).

## Design debts (docs/todo/)

- `simulation-service-requirements.md` — matter ops resolve actors through
  Chamber (a git/platform context); a future simulation service needs
  Chamber-independent identity, event-sourced proceedings, stepping/replay
  over the two clocks (git = legal time, matter events = institutional time).
- `docket-refactoring-for-phase-ii.md` — the platform dispatch in docket/bill
  must become a proceedings-backend interface at the phase-II transition;
  dual id schemes (PET-#### vs issue numbers) and divergent state models
  noted; phase-2 institutional mapping is an open decision.

## Task workflow (mandatory)

Every task gets a description file **before work starts**:
`docs/tasks/NNNN-snake-case-task-title.md` (NNNN = next sequential number,
zero-padded; template: `docs/tasks/0000-task-template.md`). Metadata:

- **created:** ISO-8601 timestamp
- **type:** one of `[simulation]`, `[infrastructure]`, `[tests]`,
  `[refactoring]`, `[bugfix]`
- **depends-on:** task numbers of prerequisites, if any
- **status:** open → in-progress → done

When the task is complete:

1. Commit the changes (this workflow is the standing authorization for
  task-scoped commits; one task = one commit, message referencing the task
  number, e.g. `task 0007: scaffold treaty template`).
2. Fill the task file's **Completion** section: `**finished:**` timestamp and
  `**commit:**` the commit's treeish; set status to `done`; commit that
  update too (may be amended into the task commit).

## Dev

- **Always use uv for development and testing** — never pip, python -m venv,
  or ad-hoc installs. `uv lock` resolves `pyproject.toml` into `uv.lock`
  (committed); `uv sync` creates/updates `.venv`; add/remove dependencies
  with `uv add` / `uv remove`. Run everything through uv: `uv run polis …`,
  `uv run python …` (or activate `.venv`). Deps: typer, httpx, pydantic, rich.
- Verify: `scripts/infra/smoke.sh` (containers + API keys), `polis health`
  (subsystem checks), `tests/e2e-gogs.sh` (full live flow), `uv run behave
  features/` (BDD stories — the user-facing surface: throwaway sim per
  scenario; `polis/sim/scenario.py` is the Gherkin→beats model, one
  binding for tests now and the live-sim queue (0034b) next).
  **All passing.**
