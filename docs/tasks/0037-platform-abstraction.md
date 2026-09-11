# 0037: platform abstraction

- **created:** 2026-09-10T18:00:00Z
- **type:** [refactoring]
- **depends-on:** none
- **status:** done

## Description

Phase is a procedure, not a product: Platform interface for provisioning (users/orgs/repos/tokens/container bring-up), GogsPlatform default + GiteaPlatform; provision up --platform gitea runs phase 1 on gitea without PRs; gogs quirks isolated in GogsPlatform. Blocks 0038.

See docs/design/roadmap.md for context and ordering.

Decisions taken (user, 2026-09-10): chamber splits product (platform)
from procedure (phase) — bill/docket dispatch on `phase == 2`; full
sim-context tooling support (health, `polis gitea`, config endpoint
resolution); verify via `tests/provision-demo-gitea.sh`.

## Completion

- **finished:** 2026-09-11T01:10:00Z
- **commit:** (main)
