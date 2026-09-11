# Provisioning — a stable, reproducible environment for a sim instance

Status: design draft v1 (task 0020). The existing `polis gogs users/orgs/repos`
commands are plumbing (thin API wrappers); `polis provision` is the
**porcelain**: the higher-level wrapper that assembles *everything* a sim
instance needs, idempotently, and records what it made so it can be torn down.

## 1. The simulation instance id

Every provisioned sim gets a human-readable id, e.g. `harbour-01`,
`founding-era-03`. **All** resources carry it:

| resource | naming |
|---|---|
| gogs org (the federal archive) | `<sim>-archive` |
| gogs repo (common law) | `<sim>-archive/common-law` |
| gogs city orgs | `<sim>-<city>` (e.g. `harbour-01-cogswich`) |
| gogs city repos | `<sim>-<city>/common-law` (fork of the archive repo) |
| gogs users | `<sim>-<username>` (e.g. `harbour-01-m.grimsbane`) |
| city containers | `polis-city-<city>-<sim>` (e.g. `polis-city-cogswich-harbour-01`) |
| provision inventory | `data/sims/<sim>/provision.json` |

Consequences: many sims coexist on one gogs; **cleanup is a prefix match**;
nothing named without the id is ever touched. The id also feeds the journal
run id (`data/sims/<sim>/`), so runtime state and infra state share one
namespace.

## 2. What provisioning does (phases)

### Phase 0 — preflight

`scripts/infra/smoke.sh`-equivalent checks: podman network up, gogs
reachable, `GOGS_API_KEY` valid and admin, world.json generated, git on
host. Fail fast with the exact remedy.

### Phase 1 — platform namespace (gogs)

1. **Users**: one per person in world.json, named `<sim>-<username>`,
   password from `credentials.password`; capture a token per user and write
   it back into `world.json` as `credentials.api_tokens["gogs@<sim>"]`
   (keyed by sim — several sims' tokens coexist; never a shared token).
   Idempotent: existing users are reused, tokens only created if absent.
2. **Archive**: org `<sim>-archive`; repo `common-law` (`auto_init: false`);
   the **founding corpus commit** (constitution + domain layout + CODEOWNERS
   placeholder? — no: phase 1, constitution + domain dirs only) by the
   Keeper's namespaced account.
3. **City archives**: org `<sim>-<city>` + repo as a **fork** of the archive
   repo (the fork relationship is the genealogy; phase 2 needs it for
   cross-repo petitions). Collaborators: the city's citizens (write), its
   local archivist (write/maintain); everyone else read.
4. **Slice remotes**: city slices for this sim get remotes pointing at the
   namespaced URLs (`http://gogs:3000/<sim>-<city>/common-law.git` origin,
   `…/<sim>-archive/common-law.git` upstream). Stored per-sim (slices under
   `data/sims/<sim>/cities/`), so the world registry stays sim-neutral.

### Phase 2 — city containers (optional in v1)

5. **Image** `polis-city` (from `docker/polis-city/Dockerfile`): python +
   git + the polis package + the city's slice at `/etc/polis/city.json`
   (`POLIS_CITY_CONFIG` is already the chamber's container-mode hook).
6. **Run** one per city: `polis-city-<city>-<sim>` on `gogs-local`, with the
   sim's slice mounted. Verify: container can reach gogs, clone origin, and
   resolve its citizens.
   (Optional because the OperatorExecutor needs no containers; required for
   the narrative-correct ContainerExecutor.)

### Phase 3 — inventory + registration

7. Write `data/sims/<sim>/provision.json`: id, created-at, every resource
   created (org/repo/user/container names), the admin's own notes. This is
   the teardown manifest.

## 3. Command surface

```
polis provision up <sim-id> [--platform gogs|gitea] [--with-city-containers] [--force]
polis provision status <sim-id>        # what exists vs. the inventory
polis provision teardown <sim-id> [--yes]   # delete exactly the inventory
polis sim stop|start|delete <sim-id>         # lifecycle (post-director, §3a)
polis sim export|import <sim-id>             # portability (post-director, §3a)
```

- **Idempotent**: `up` reconciles (create missing, skip existing, never
  duplicate); `--force` re-provisions tokens.
- **Teardown is exact**: deletes only what the inventory lists — users
  (`DELETE /admin/users/<sim>-*`), repos, orgs (gogs has no org-delete
  route: orgs are documented as teardown-exempt, or removed via DB note in
  services docs), containers (`podman rm -f`), and the sim dir optionally.
- **Platform abstraction (task 0037 — landed)**: `--platform` selects the
  product (`gogs` default, `gitea` since 0037). Phase is a procedure, not
  a product: either product hosts phase 1 (matter-store proceedings, local
  incorporation); `federation.phase` never follows the product. The
  inventory records `platform`; secrets carry per-platform keys
  (`gogs_port`/`gitea_port`, `*_url_external/internal`); slices carry
  `federation.platform` and tokens keyed by product; `status`/`teardown`
  dispatch through `sim_platform_client(sim)`. Product quirks live in the
  clients and the per-platform bring-up (provision.py), nowhere else.

## 3a. Sim lifecycle (added; after the director works)

Beyond up/teardown, a sim instance is a manageable, portable object:

```
polis sim stop <sim-id>     # stop its city containers (platform objects persist)
polis sim start <sim-id>    # start them again
polis sim delete <sim-id>   # teardown + remove data/sims/<sim> entirely
polis sim export <sim-id>   # -> <sim-id>.polis.tar.gz
polis sim import <file>     # -> a ready-to-run sim instance
```

**Export format** (a tarball someone else can import and run): one archive
containing—

- `provision.json` (the inventory, so import can re-materialize infra);
- the journal (`journal.jsonl`) and situation snapshot(s);
- the per-sim city slices;
- **the git bundle(s)** of the archive repo and each city repo
  (`git bundle create <repo>.bundle --all`) — the complete legal history,
  platform-independent;
- a `manifest.json` (format version, sim id, created-at, world/seed
  references).

**Import** on another machine: reads the manifest, re-provisions via
`provision up` (new host, same namespace), pushes the bundles into the
fresh repos, restores slices and journal — the imported sim is runnable and
`present`-able immediately. Import refuses on id collision unless
`--rename <new-id>` (namespace remap of all objects — the id-prefixing
makes this mechanical).

Prerequisite note: export/import depends on the runtime/journal being
settled (post-director), which is why it's scheduled after it.

## 4. Infra dependencies

| dependency | used for |
|---|---|
| podman + network `gogs-local` | containers |
| gogs running + admin `GOGS_API_KEY` | all platform objects |
| `world.json` (genesis done) | persons, passwords, cities, federation fields |
| git on host | founding corpus commit, forks' seed |
| `docker/polis-city/Dockerfile` | city image (phase 2) |
| `.env` | secrets |
| per-sim slices under `data/sims/<sim>/cities/` | chamber container/operator modes |

## 5. Explicitly out of scope (v1)

- gitea/woodpecker provisioning (phase-2 transition task);
- branch protection / CODEOWNERS (enacted as bills in the fiction);
- LLM content provisioning (petition prose etc.);
- multi-platform token refresh/rotation.

## 6. Implementation shape (for the follow-up task)

`polis/provision.py` (or `polis/sim/provision.py`) as the orchestrator;
`polis/cli/provision.py` thin CLI. Reuses `clients/gogs.py` (porcelain),
`store.py` (slices), `clients/podman.py`. Everything recorded in
`provision.json`; teardown consumes it. Demo: `tests/provision-demo.sh` —
up → status → clone as a namespaced citizen → teardown → prefix check that
nothing remains.
