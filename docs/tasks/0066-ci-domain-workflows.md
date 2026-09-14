# 0066: CI workflows — domain skeleton (0045a)

- **created:** 2026-09-14T10:01:36Z
- **type:** [infrastructure]
- **depends-on:** none
- **status:** review

## Description

First slice of 0045: the domain-tagged Behave suites and one GitHub
Actions workflow per domain, all container-free where possible so CI is
green from the start.

- domain tags: `@domain`, `@infrastructure`, `@functional` (`@slow`
  stays opt-in);
- **domain-model** (`features/domain-model.feature`): the legal seed
  validates, all fifteen jurisdictions generate situations, the registry
  is populated — on an isolated federation (`POLIS_DATA_DIR` temp dir
  with the tracked `data/world/legal/` symlinked in), so scenarios never
  touch the repo's runtime state;
- **infrastructure** (`features/infrastructure.feature`): a runtime is
  detected as podman or docker, unknown runtimes are rejected with the
  choices, the runtime declares its canonical-host handling;
- **functional** (`features/functional.feature`): the command groups and
  the generated world are inspectable; `northern-banks` and
  `phase-transition` are tagged `@functional` (CI runs `not @slow` until
  the container suites are runner-ready);
- workflows: `.github/workflows/{infrastructure,domain-model,functional}.yml`
  (`astral-sh/setup-uv` cache, `uv sync --frozen`, `behave --tags …`);
- `docs/testing.md` documents the domain/CI mapping.

Acceptance: each tag runs green locally; the workflows invoke exactly
those tag expressions; `uv run behave features/` stays green.

## Progress log

- **2026-09-14 — implemented.** Features + steps (isolated CLI steps,
  runtime steps) + the three workflows; existing features tagged
  `@functional`; `docs/testing.md` updated; all tags verified locally
  (domain 4/4, infrastructure 3/3, functional 2/2 + the tagged
  container scenarios excluded from CI until 0067+).

## Completion

<!-- filled in when the task is done (after the PR is approved and merged):
- **finished:**
- **commit:**
-->
