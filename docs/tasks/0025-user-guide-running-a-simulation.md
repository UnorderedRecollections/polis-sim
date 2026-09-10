# 0025: User guide — running a simulation

- **created:** 2026-09-09T21:00:00Z
- **type:** [simulation]
- **depends-on:** 0024
- **status:** done

## Description

Structured user-facing documentation of the full simulation lifecycle,
from requirements to a driven sim: requirements (podman, uv, secrets),
infrastructure bring-up, world genesis, legal-data authoring and
validation, provisioning, run bootstrap (`sim new --situation`), driving
(`sim drive/tick/stories/present`), and teardown (+ nuke). Every command
verified against the actual CLI. Deliverable: `docs/running-a-simulation.md`,
linked from AGENTS.md.

## Completion

- **finished:** 2026-09-09T21:20:00Z
- **commit:** (pending — user commits)

Delivered `docs/running-a-simulation.md`: the full lifecycle in nine steps
(requirements → infra → world genesis → legal seed authoring/validation →
provision → `sim new` bootstrap → drive → observe → teardown/nuke), a
moving-parts reference table, and a troubleshooting section. Every command
verified live against the CLI (`world events candidates`, `world legal
validate`, `sim runtime`, provisioning, drive). Linked from AGENTS.md.
