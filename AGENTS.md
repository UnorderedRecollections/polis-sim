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
  - `clients/` — httpx wrappers for gogs/gitea/woodpecker APIs + the
    container-runtime boundary (podman/docker).
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
  (`postgres.sh gogs.sh gitea.sh woodpecker.sh`), `proxy.sh` (dev-rig
  front proxy), `hosts.sh` (canonical-host entry), `compose-up/down.sh`,
  `smoke.sh` (per-container smoke tests incl. API-key validity).
- `docs/` — `running-a-simulation.md` (**the user guide**: requirements →
  infra → genesis → legal seed → provision → drive → teardown),
  `testing.md` (**how to run the suites**: fast behave, slow gitea,
  demos, troubleshooting),
  `simulation-scenarios.md` (**the author guide**: driving a running sim
  with user scenarios — the other side of the BDD split),
  `flows/` (**the legal flows**, master + petitions/legislation/archive/
  simulation, with mermaid graphs — read after the guide),
  `isomorphism/` (concepts), `design/` (simulator design + legal
  ontology), `services/` (per-service: why, start, API keys, quirks),
  `notes/` (background docs), `tasks/` (task files, see Task workflow),
  `todo/` (design debts).
- `tests/e2e-gogs.sh` — full live legislative flow against gogs (see below).
- `features/` — the developer BDD tests (behave, `@slow`; docs/testing.md),
  tagged by domain: `@domain`, `@infrastructure`, `@functional` — one CI
  workflow each in `.github/workflows/` (task 0066).
  `scenarios/` — user-authored scenarios for a *running* sim
  (`polis sim submit`; the driving side of the split in
  `docs/design/scenarios-vs-tests.md`; author guide
  `docs/simulation-scenarios.md`). The vocabulary is scoped: `polis sim
  steps [--scope user|test]`; submitted scenarios use user beats only.
- `.env` — secrets (NEVER commit; template in `.env.example`).

## Infrastructure (container runtime: podman or docker; network `gogs-local`)

- postgres-gogs — shared DB (databases `gogs` + `gitea`), internal only.
- proxy :10800 — the dev rig's only HTTP entrypoint (task 0042, caddy):
  routes `/gogs`, `/gitea`, `/ci`; the services publish no HTTP port of
  their own. Canonical base `http://host.containers.internal:10800` —
  containers resolve it natively, the host needs a one-time
  `scripts/infra/hosts.sh add` (sudo) for browser links; `localhost:10800`
  always works. Same scheme per sim (`<sim>-proxy`).
- gogs (internal :3000) — phase-1 platform ("customary machinery"; merely a
  mechanical archive in the fiction — no petitions/reviews/approvals).
- gitea (internal :3000) — phase-2 platform ("codified machinery"; postgres-backed).
  Since 0037 it also hosts phase-1 sims: `provision up --platform gitea`
  (phase is a procedure, not a product — the federation stays in phase 1
  with matter-store proceedings on either product). The dev rig's gitea
  bootstraps **headlessly** (task 0040): `scripts/infra/gitea.sh` takes
  `GITEA_ADMIN_USERNAME/PASSWORD/EMAIL` from `.env` (project-owned,
  neutral identity — never a personal account), creates the admin via the
  gitea CLI and mints `GITEA_API_KEY` into `.env`; `WOODPECKER_ADMIN`
  follows `GITEA_ADMIN_USERNAME`.
- woodpecker server (internal :8000) + agent — CI (the Mechanical
  Magistrate), OAuth against gitea, reached at `/ci`.
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
- Container runtime (task 0043): everything goes through
  `polis/clients/containers.py` (`ContainerRuntime`; auto-detect podman
  first, then docker; `POLIS_RUNTIME` overrides). The quirks live there —
  image/network probes, machine vs daemon state, socket path, the
  woodpecker agent's flags, and the canonical-host alias docker needs
  (auto-inserted on every `run`) — never in provisioning. `scripts/infra/*`
  use `env.sh`'s `rt`/`rt_*` helpers; `tests/runtime-agnosticism.sh` checks
  both paths (docker via a stub CLI). Known gap for 0050: woodpecker's
  docker backend has no per-step `extra_hosts`, so pipeline step
  containers on docker need the canonical-host problem solved there.

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
  `/polis-data/world` **rw since 0038** — the phase transition writes the
  civil registry from inside the operator — env `POLIS_DATA_DIR POLIS_SIM_DIR=/sim
  POLIS_MATTERS_FILE=/sim/matters.json`); `--local` runs in-process.
  Demo: `tests/director-demo.sh` (**passing**).
- **The phase transition** (`polis/sim/transition.py`, task 0038):
  `polis sim transition <run>` (explicit command; proxies like drive)
  plays the `phase_transition` story — petition → the three authored acts
  + instruments from `data/world/legal/transition/` (CODEOWNERS → root,
  branch-protection.md → constitution/, woodpecker.yml → root) introduced
  and ratified through the customary procedure; the THIRD ratification
  flips the federation to phase 2 in the same transaction (situation.yaml
  `federation.phase: 2`, world.json `federation.phase`, the sim's city
  slices — the Keeper's archival act, never a hand edit) → the
  `codified-machinery` edition promulgated. Requires a gitea-hosted sim
  (`provision up --platform gitea`); one-time (a run with an enacted
  phase_transition story refuses). Post-transition the proceedings truly
  move into the platform: issues/PRs (gitea city repos are **forks** —
  cross-repo PRs require the fork relationship; the merge API auto-closes
  PRs, so the order is not PATCH-closed again; container-mode chambers
  derive the API client's base URL from the slice origin).
  Demo: `tests/transition-demo.sh` (**passing**).
- **The Mechanical Magistrate's CI** (`provision.up_woodpecker`, task 0041;
  the rest of roadmap §5): the transition's host wrapper erects the CI
  after the story — per-sim `<sim>-woodpecker-server` + agent (the macOS
  VM quirks: `--user 0:0`, `--security-opt label=disable`, the VM socket),
  an OAuth2 app on the sim's gitea (`POST /user/applications/oauth2`,
  ONE canonical redirect — `<proxy>/ci/authorize`), the Magistrate's FIRST LOGIN scripted
  end-to-end (gitea login form → OAuth grant (`granted=true`; already
  authorized apps redirect straight to the callback) → woodpecker
  `/authorize` → the CSRF token from `/web-config.js` → `POST
  /api/user/token`), the archive repo enabled (Magistrate gets admin
  collaborator rights; `require_approval: "none"` — fork PRs are blocked
  pending approval otherwise), the city forks synced to the codified
  machinery (a PR's pipeline config is read from its HEAD — the fork),
  global secrets `POLIS_GITEA_URL`/`POLIS_GITEA_TOKEN` (the checks'
  context — `WOODPECKER_ENVIRONMENT`'s comma format mangles URLs), and
  the forge webhook (woodpecker registers its own — the canonical
  `WOODPECKER_HOST` is deliverable from the forge as-is; no repoint; gitea
  keeps `security.ALLOWED_HOST_LIST` incl. `host.containers.internal` +
  `webhook.ALLOW_LOCALNETWORK_HOSTS=true` for the private target).
  The pipeline = `data/world/legal/transition/.woodpecker.yml` (woodpecker
  v3 `steps:` list format; the step image is `polis-city:latest`, which
  carries the legal-design data — `POLIS_DATA_DIR` — for the CLI's
  import-time ontology loaders). Its first command fetches the target
  branch (`--unshallow`): the CI clone is shallow and without a mainline
  ref the checks diffed nothing — every act passed vacuously (found live
  in task 0053). The checks: `polis formal-check
  identify|entry-force|references|constitution` (exit non-zero =
  failure; the constitution check requires a jurist's
  `SCRUTINY — APPROVED` comment on the PR — read via the global secrets +
  `CI_REPO_OWNER/CI_REPO_NAME/CI_COMMIT_PULL_REQUEST`). The demo asserts
  both verdicts: a defective act fails, the corrected act passes.
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
  `gitea admin user create --access-token`; the host port comes from the
  **front proxy** — `<sim>-proxy` (caddy) is the only published port,
  `proxy_port` persisted and reused by `--force`; task 0042), users
  `<sim>-<username>` with per-sim tokens, orgs
  `<sim>-archive`/`<sim>-<city>` + `common-law` repos + **one shared founding
  commit** (`_founding_repo` — all repos must share history or the Keeper's
  enactment pushes are non-fast-forward), per-sim slices (carrying
  `federation.platform` = the product; tokens keyed by product), inventory
  `provision.json` (records `platform`). Gitea city repos are **forks** of
  the archive (cross-repo PRs, task 0038); gogs city repos stay plain
  (no forks API). Secrets in `data/sims/<sim>/secrets.json`
  (**never world.json** — provisioning must not mutate the civil registry;
  `polis world cleanup` removes legacy `gogs@<sim>` residue). Slices/remotes
  use the canonical proxy URL
  `http://host.containers.internal:<proxy_port>/<platform>`; config.py
  host-swaps to `localhost:<proxy_port>` for host-side work. `status`/`teardown`/`destroy` use
  `sim_platform_client(sim)`; teardown removes containers+network, the
  platform volumes die with the sim dir (`rm -rf data/sims/<sim>`).
  Re-`up --force` reuses existing secrets/volume. Demos:
  `tests/provision-demo.sh` + `tests/provision-demo-gitea.sh` (**passing**).
- **The front proxy** (task 0042, `docs/design/proxy.md`): per deployment
  (dev rig + per sim) one caddy container is the ONLY host-published
  entrypoint, routing path prefixes `/gogs`, `/gitea`, `/ci` (`/`
  redirects). Prefix semantics differ (spike): gitea/gogs need the prefix
  **stripped** (`handle_path` — their ROOT_URL still carries it so rendered
  links are absolute), woodpecker needs it **kept** (it is part of
  `WOODPECKER_HOST`). Canonical base `host.containers.internal:<P>`;
  containers resolve it natively, the host browser needs a one-time
  `127.0.0.1 host.containers.internal` (`scripts/infra/hosts.sh add`,
  sudo) — provisioning and the CLI use `localhost:<P>`, which caddy binds
  too. The proxy **forces the canonical Host upstream** (`header_up
  Host`), because gitea derives clone/webhook URLs from the request host;
  without it host-side pushes produce `localhost:<P>` clone URLs the CI
  step containers cannot reach (found live in task 0053). Pieces:
  `docker/caddy/{Dockerfile,Caddyfile.template,Caddyfile.dev}`,
  `_up_proxy` in `provision.py`, `scripts/infra/proxy.sh` for the dev rig.
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
- **Gitea facts (webhooks + OAuth, task 0041)**: webhook targets on private
  addresses are DENIED by default (SSRF guard) — set
  `security.ALLOWED_HOST_LIST=host.containers.internal,localhost` +
  `webhook.ALLOW_LOCALNETWORK_HOSTS=true`; clone URLs reported to the forge
  derive from `server.ROOT_URL` — the sim's gitea uses the in-network URL
  (the CI clones from inside the network, never through the mac loopback);
  the OAuth grant form needs `granted=true`; the exchange redirect_uri must
  EXACTLY match the authorize request's. The sim's woodpecker DB persists in
  `platform/<sim>/woodpecker/server` — repo enable is idempotent (409
  "already active" → reuse the lookup).
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

Every task is tracked twice: the local description file is the **source of
truth**, the GitHub issue is its **public mirror** (`gh issue …`). Work is
**reviewed before it lands**: implementation goes on a feature branch and
reaches `main` only through a pull request.

**Local file (before work starts):**
`docs/tasks/NNNN-snake-case-task-title.md` (NNNN = next sequential number,
zero-padded; template: `docs/tasks/0000-task-template.md`). Metadata:

- **created:** ISO-8601 timestamp
- **type:** one of `[simulation]`, `[infrastructure]`, `[tests]`,
  `[refactoring]`, `[bugfix]`
- **depends-on:** task numbers of prerequisites, if any
- **status:** open → in-progress → **review** → done (`review` = the PR is
  open and awaiting approval)

**GitHub issue (the same moment the file lands):** `gh issue create`:

- **title:** the file's `# NNNN: title` line, verbatim (e.g.
  `0039: llm integration`);
- **body:** the task's Description verbatim, ending with
  `Tracked in the repo: [docs/tasks/NNNN-....md](docs/tasks/NNNN-....md)`;
- **label:** `bug` for `[bugfix]`, `documentation` for doc-only tasks,
  `enhancement` otherwise.

**Implementation — feature branch + PR:**

1. Branch from `main`: `task/NNNN-slug` (one task per branch). Commit
   there; this workflow is the standing authorization for task-scoped
   commits; one task = one PR.
2. Open the PR when the work is ready for review:
   `gh pr create --base main` — title `NNNN: <task title>`, body
   summarizing what/why/verification and closing the issue
   (`Closes #<n>`).
3. Move the issue `in-progress` → `review` and comment the PR link:
   `gh issue edit <n> --remove-label in-progress --add-label review`.
   Set the local file's `status:` to `review` (in the branch).

**Review → done:**

4. Only an **approval on GitHub** allows the merge. Merging closes the
   issue (`Closes #<n>`); never mark a task done before that.
5. After the merge: set the local `status: done`, fill the **Completion**
   section (`**finished:**` timestamp, `**commit:**` the merge) and commit
   the bookkeeping directly on `main` — metadata alone needs no review.
6. **Label hygiene:** a closed issue carries **neither `in-progress` nor
   `review`**. `Closes` does not remove labels, so clean them after the
   auto-close (or when closing manually):
   `gh issue edit <n> --remove-label in-progress --remove-label review`.
   Verification: `gh issue list --state closed --label in-progress` and
   `… --label review` are empty. A `done` file never outlives its closed
   issue (and vice versa). No back-fill for tasks already closed.

## Dev

- **Always use uv for development and testing** — never pip, python -m venv,
  or ad-hoc installs. `uv lock` resolves `pyproject.toml` into `uv.lock`
  (committed); `uv sync` creates/updates `.venv`; add/remove dependencies
  with `uv add` / `uv remove`. Run everything through uv: `uv run polis …`,
  `uv run python …` (or activate `.venv`). Deps: typer, httpx, pydantic, rich.
- Verify: `scripts/infra/smoke.sh` (containers + API keys), `polis health`
  (subsystem checks), `tests/e2e-gogs.sh` (full live flow), `uv run behave
  features/` (BDD stories — the fast suite; `behave.ini` excludes `@slow`;
  `polis/sim/scenario.py` is the Gherkin→beats model, one binding for
  tests and the live-sim queue), `tests/bdd-phase2.sh` (the slow gitea
  suites: phase I on gitea + phase I → transition → phase II, task 0053),
  `tests/jurisdictions.sh` (one whole story per jurisdiction, task 0054),
  `uv run behave features/ --tags @infrastructure` (local deployment
  failures: fail-fast, inspectable state, idempotent recovery, task 0067).
  **All passing.** One shot: `tests/all.sh` (`--dev-rig` includes the
  shared-rig checks). Runbook: `docs/testing.md` (tags, prerequisites,
  direct invocations, troubleshooting).
