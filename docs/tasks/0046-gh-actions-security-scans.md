# 0046: GitHub Actions — security scans

- **created:** 2026-09-11T16:00:00Z
- **type:** [infrastructure]
- **depends-on:** 0045
- **status:** open

## Description

A security workflow (`.github/workflows/security.yml`), on PRs and on a
schedule:

- dependency audit: `uv` lock audit / pip-audit over the resolved set;
- SAST: bandit over `polis/`;
- secret scanning: gitleaks (history + PR diffs) — note the repo's
  history legitimately contains the scrubbed session notes and the
  pre-scrub personal email; gitleaks config must not fail the build on
  those historical findings (baseline), but must block NEW leaks;
- container images: trivy scans of `docker/*` builds (polis-city,
  gitea/gogs postgres wrappers, woodpecker wrappers, the future proxy).

Policy: vulnerabilities are reported as findings; only critical/high in
the *first-party* images fail the merge. No `.env` or real secrets ever
enter the repo (already gitignored — the scan verifies it).

## Completion

<!-- filled in when the task is done:
- **finished:**
- **commit:**
-->
