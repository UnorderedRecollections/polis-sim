# 0070: path-filtered workflow triggering (0045e)

- **created:** 2026-09-14T10:01:36Z
- **type:** [infrastructure]
- **depends-on:** 0066, 0067, 0068, 0069
- **status:** open

## Description

Make PRs run only the test domains whose code changed (agreed direction,
2026-09-14: "map these to source code / scripts such that PRs only
trigger certain tests based on where the code was changed").

- a **mapping table** from changed paths to domains, e.g.:
  - `polis/clients/containers.py`, `polis/provision.py`,
    `scripts/infra/`, `docker/` → **infrastructure** (+ functional, since
    provisioning is the application);
  - `data/world/legal/`, `polis/sim/{legaldata,ontology,norms,resources,
    situations,events}.py` → **domain-model** (+ functional where the
    CLI surface changed);
  - `polis/cli/`, `polis/{models,store,matters,genesis}.py` →
    **functional**;
  - `features/**` specific to a domain → that domain;
  - everything else / shared plumbing → all domains (fail safe, run
    more, not less).
- implementation options: `dorny/paths-filter` computing a domain
  matrix, or per-workflow `on.pull_request.paths` (coarser: a workflow
  runs if any of its paths changed); pick one and document it.
- keep an escape hatch: a label/`workflow_dispatch` to force the full
  matrix; required-status-check configuration so skipped domains do not
  block merges.
- docs: the mapping table in `docs/testing.md`, and the rule that when in
  doubt a change runs more domains.

Acceptance: a PR touching only `data/world/legal/` runs the domain-model
workflow only; a PR touching `polis/provision.py` runs infrastructure +
functional; a shared/unknown change runs all.

## Completion

<!-- filled in when the task is done:
- **finished:**
- **commit:**
-->
