# 0045: GitHub Actions — code quality

- **created:** 2026-09-11T16:00:00Z
- **type:** [infrastructure]
- **depends-on:** none
- **status:** open

## Description

A CI workflow (`.github/workflows/quality.yml`) that runs on every PR
and push:

- lint: ruff (config into pyproject.toml);
- type check: pyright or mypy over `polis/`;
- format check: ruff format --check;
- unit tests: pytest for the pure layers (ontology/norms/resources
  loaders, plan/documents, formal-check logic — everything that needs
  no containers);
- BDD: the behave suite, on a per-sim throwaway basis if a container
  runtime is available (docker on ubuntu runners), or the
  non-provisioned scenarios only.

Caching via `uv` (setup-uv action); no secrets required; the workflow
must stay green on the current tree before it lands.

## Completion

<!-- filled in when the task is done:
- **finished:**
- **commit:**
-->
