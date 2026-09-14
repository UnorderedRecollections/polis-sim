# 0045: GitHub Actions — domain test workflows (umbrella)

- **created:** 2026-09-11T16:00:00Z
- **type:** [infrastructure]
- **depends-on:** none
- **status:** in-progress

## Description

Umbrella for the CI test workflows. The scope is split into tasks
0066–0070 (0045a–e); this file tracks the whole and closes when they
land. Direction (agreed 2026-09-14):

- **one workflow per test domain** (`.github/workflows/`):
  - **infrastructure** — how the system handles failures of the
    underlying infrastructure (0067);
  - **domain-model** — the simulated legal system and its ontology
    (0068);
  - **functional** — how the application works; one Behave suite per
    `polis` subcommand (0069);
- **all tests are Behave `.feature`s**; the domain is expressed as tags
  (`@infrastructure`, `@domain`, `@functional`) so each scenario belongs
  to exactly the right workflow;
- **path-filtered triggering** — a PR runs only the domains whose code
  changed — is the follow-up (0070);
- the original quality checks (ruff, format, pyright/mypy) stay part of
  this umbrella and can land as their own workflow later;
- caching via `astral-sh/setup-uv`; the workflows must stay green on
  `main`.

## Split

- **0066 (0045a)** — workflow skeleton + domain tags + minimal
  container-free suites (in review).
- **0067 (0045b)** — infrastructure domain in Behave: port the local
  deployment failure suite (0055) to `features/`.
- **0068 (0045c)** — domain-model domain in Behave: port the
  jurisdiction/legal-seed suite (0054).
- **0069 (0045d)** — functional domain in Behave: one suite per `polis`
  subcommand.
- **0070 (0045e)** — path-filtered workflow triggering.

## Completion

<!-- filled in when the task is done:
- **finished:**
- **commit:**
-->
