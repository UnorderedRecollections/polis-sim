# 0024: Director implementation — sim drive

- **created:** 2026-09-09T14:45:00Z
- **type:** [simulation]
- **depends-on:** 0023, 0021
- **status:** done

## Description

Implement the director per `docs/design/director.md`:

1. **Operator container in provisioning** — `polis provision up` also
   creates `polis-operator-<sim>` (same polis-city image): mounts
   `data/sims/<sim>/` at `/sim` (rw) and `data/world/legal/` at `/legal`
   (ro), `POLIS_DATA_DIR=/legal`; `status` lists it, `teardown` removes
   it.
2. **`polis/sim/director.py`** — the drive loop: charged candidates →
   per-party selector (v1: `seeded` with run seed; policy map
   `policies.yaml` read if present, default seeded) → casting
   (constituency petitioner, domain expert iff corpus_dir else recorded
   skip, council-seat rotation, Keeper/local-archivist ratifier) → remedy
   from incompatibilities → story instantiation from template → execution
   via `runtime.enact()` block by block → `stories.json` state + `story`
   journal anchor.
3. **CLI** — `polis sim drive <run> --steps N`, `sim tick`, `sim stories`.
   Host-side `sim drive` proxies into the operator container
   (`podman exec polis-operator-<sim> polis sim drive … --local`); the
   director executes in-process inside the container (chamber in
   container mode, `POLIS_MATTERS_FILE=/sim/matters.json`, run dir = /sim).
4. **Demo** — `tests/director-demo.sh`: provision → `sim new` →
   `drive --steps 2` → assert 2 ratified matters, 2 norm transitions,
   journal anchors chain, 2 enactment merges in the archive's git log →
   teardown (+ nuke orgs).

## Completion

- **finished:** 2026-09-09T20:30:00Z
- **commit:** (pending — user commits)

Delivered per `docs/design/director.md`:

1. **Operator container** — `provision up` always creates
   `polis-operator-<sim>` (`/sim` rw + `data/world` ro, `POLIS_SIM_DIR=/sim`,
   `POLIS_MATTERS_FILE=/sim/matters.json`); status/teardown cover it via the
   inventory. Image build factored into `_ensure_image()`.
2. **`polis/sim/director.py`** — the drive loop: seeded selection over
   charged candidates (`Random(f"{seed}:{n}")`, run.json), casting
   (constituency legislator rotation, council-jurist rotation, Keeper,
   expert iff `corpus_dir`), remedy from incompatibilities, story execution
   through `runtime.enact()` mapped to the resource_dispute template,
   `stories.json`, `story` journal anchors, failed stories recorded as
   first-class outcomes.
3. **CLI** — `sim drive [--steps N] [--local]` (host proxies via
   `podman exec` into the operator container), `sim tick`, `sim stories`;
   `sim new` gains `--jurisdiction/--seed` (writes `run.json`).
   `journal.run_dir()` honors `POLIS_SIM_DIR`.
4. **Machinery fixes surfaced by the demo**: `archive.obtain` establishes
   local `main` from `origin/main` (API-created repos have HEAD →
   nonexistent master); `_incorporate_locally` passes committer identity to
   merge commands (containers have no global git config); runtime anchors
   read `main` (not HEAD — drafting moves HEAD); the Keeper's
   `federal-archivist` office is appended to his container-mode chamber
   (city slices never carry it) and his origin points at the petitioner's
   repo (ratify fetches the bill branch from origin).

Verified: `tests/director-demo.sh` (provision → 2 stories enacted →
matters, situation write-back, chaining anchors, 2 enactment merges in the
archive's git log → teardown) — **passing**; `tests/sim-runtime-demo.sh`
and `tests/e2e-gogs.sh` still pass (regression).
