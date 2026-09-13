# polis — Git as a Legal-Political System

> **Git is the historical/constitutive layer** — it records what the law is
> and how the current state came to exist.
> **A GitHub-like platform (gogs/gitea + CI) is the normative/institutional
> layer** — it determines how changes are proposed, evaluated, authorized and
> incorporated.

**polis** simulates a fictional federation — *the Concord of the Nine Cities* —
whose legislative life runs on real local infrastructure. Every legal act is a
real git operation; every institution is a real account, office and permission;
the fiction and the machinery are the same object seen twice.

![Screenshot](docs/images/concord-map.png)

The core idea: [docs/isomorphism/synopsis.md](docs/isomorphism/synopsis.md).

## The three stores (no database, deliberately)

| store | what it is | where |
|---|---|---|
| **git history** | the legal archive — what the law *is* | the platform repos |
| **`data/world/*.json`** | the civil registry — who exists | `world.json` + city slices |
| **`data/world/matters.json`** | the political state — petitions (PET-####), bills (ACT-####) and their procedural record | the matter store |

Recording an event ≠ enforcing a procedure: the constitution is enforced by
people; jurisdiction checks run in the archivists' own tooling, never in the
platform. See [docs/flows/README.md](docs/flows/README.md).

## The two phases

- **Phase 1 — customary**: petitions/bills are matter-store entries; the
  Keeper incorporates locally (git merge + push). The platform is a mere
  mechanical archive host.
- **Phase 2 — codified**: the same command surface, but petitions are real
  issues, bills real PRs, and the **Mechanical Magistrate** (woodpecker CI)
  checks every proposal's form. The transition is itself legislation —
  three ratified acts (CODEOWNERS, branch protection, `.woodpecker.yml`)
  authored in [`data/world/legal/transition/`](data/world/legal/transition).

## Quick start

```bash
# prerequisites: a container runtime (podman or docker, auto-detected); uv
uv run polis world genesis                 # once: the 9 cities, 63 persons, offices
uv run polis world legal validate          # the legal seed

uv run polis provision up my-sim-01 --platform gitea
export POLIS_PROVISIONED_SIM=my-sim-01
uv run polis sim new --situation data/world/legal/norms/fisheries.yaml

uv run polis sim drive --steps 2           # phase 1: customary proceedings
uv run polis sim transition                # the three acts → phase 2 + CI erected
uv run polis sim drive --steps 2           # phase 2: real issues/PRs, CI checks

uv run polis sim present                   # narrated journal replay
uv run polis provision destroy my-sim-01 --yes
```

Full walkthrough: [docs/running-a-simulation.md](docs/running-a-simulation.md).
Phase-2 recipes and a CI demo (defective acts fail, corrected acts pass):
[tests/transition-demo.sh](tests/transition-demo.sh).

## Tooling

- `polis` CLI (typer): domain (`world city person office assign`), legislative
  (`docket bill archive`), simulation (`sim`), component
  (`gogs gitea woodpecker health provision`). Every legislative command builds
  a **Plan** (machinery step + legal meaning) and accepts `--isomorphism` to
  render it instead of executing.
- Infrastructure: podman or docker (auto-detected, `POLIS_RUNTIME`
  overrides), fronted by one proxy — `localhost:10800` → `/gogs`,
  `/gitea`, `/ci` — see [docs/services/](docs/services/).
- The **director** drives stories; the **phase transition** is one story;
  the **Mechanical Magistrate's CI** runs `polis formal-check …`.

## Documentation

| topic | document |
|---|---|
| the isomorphism | [docs/isomorphism/synopsis.md](docs/isomorphism/synopsis.md) |
| user guide | [docs/running-a-simulation.md](docs/running-a-simulation.md) |
| the legal flows | [docs/flows/README.md](docs/flows/README.md) |
| roadmap & status | [docs/design/roadmap.md](docs/design/roadmap.md) |
| simulator design | [docs/design/simulator.md](docs/design/simulator.md), [docs/design/director.md](docs/design/director.md) |
| story data model | [docs/design/story-data-model.md](docs/design/story-data-model.md) |
| per-service docs | [docs/services/](docs/services/) |
| background notes | [docs/notes/](docs/notes/) |

## Development

- Always `uv` (`uv sync`, `uv run …`) — never pip.
- Verify: `scripts/infra/smoke.sh`, `uv run polis health`,
  `tests/e2e-gogs.sh`, `tests/transition-demo.sh`, `uv run behave features/`.
- Tasks live in [docs/tasks/](docs/tasks/) (one file before work starts, one
  commit per task). Platform quirks learned the hard way are recorded in
  [AGENTS.md](AGENTS.md).
