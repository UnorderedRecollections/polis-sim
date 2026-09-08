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
    events/paradigms/norm-kinds), `norms/*.yaml` (seed norms — **snapshot
    principle: seed and evolved state share one format/loader**), `moves.yaml`,
    `templates/*.yaml`. Loaders: `polis/sim/legaldata.py`, `polis/sim/ontology.py`,
    `polis/sim/norms.py`; rationale: `docs/design/story-data-model.md`.
- `.state/` — container persistent data (gogs/gitea/woodpecker/postgres),
  gitignored. All other runtime state under `data/` is gitignored except
  `data/world/legal/` (source YAML).
- `docker/` — per-component Dockerfiles + `docker-compose.yml` (project `polis`,
  network `gogs-local`).
- `scripts/infra/` — `env.sh` (shared), per-service build/run scripts
  (`postgres.sh gogs.sh gitea.sh woodpecker.sh`), `compose-up/down.sh`,
  `smoke.sh` (per-container smoke tests incl. API-key validity).
- `docs/` — `isomorphism/` (concepts), `design/` (simulator design + legal
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
- woodpecker server :10890 + agent — CI (the Mechanical Magistrate), OAuth against gitea.
- City containers `polis-city-*` not built yet.
- Secrets: `.env` (`GOGS_API_KEY GITEA_API_KEY WOODPECKER_API_KEY
  WOODPECKER_GITEA_CLIENT/SECRET POSTGRES_PASSWORD`). Resolution order in
  `polis/config.py`: `POLIS_*_TOKEN` env > process env > `.env`.
- Endpoints overridable via `POLIS_*` env vars.

## Key conventions

- **Every legislative operation builds a `Plan`** (machinery step + legal meaning);
  every such CLI command exposes `--isomorphism` to render instead of execute.
  Stated in `polis/legislation/__init__.py`; keep it.
- Agency separation: `political` persons (legislators/delegates) may not hold
  juridical offices; enforced in `cli/assign.py`.
- Federation `phase`: 1 = gogs (customary), 2 = gitea+CI (codified). Stored in world.json.
- `Chamber` (legislation/chamber.py) resolves actor/remotes/platform; two modes:
  container (`POLIS_CITY_CONFIG` or `/etc/polis/city.json`) vs operator
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

## Platform facts learned the hard way (verified by probing)

- **This gogs build has NO pulls API at all**; issues API works. Phase-1
  petitions/bills are **matter-store entries**; ratify/consolidate always
  incorporate locally (`git merge [--squash] FETCH_HEAD` + push) and close the
  matter with the order entered into the record. Phase 2 (gitea) uses real PRs
  — same command surface, dispatch on `chamber.platform`.
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
  (subsystem checks), `tests/e2e-gogs.sh` (full live flow: `e2e`-prefixed
  users/repo, throwaway `POLIS_MATTERS_FILE`, matter-status and
  status-lifecycle assertions, negative jurisdiction test, cleanup trap).
  **Both passing.**
