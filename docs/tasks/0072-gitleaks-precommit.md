# 0072: gitleaks secret scanning in the pre-commit hook

- **created:** 2026-09-14T11:49:31Z
- **type:** [infrastructure]
- **depends-on:** 0071
- **status:** review

## Description

Extend the pre-commit guard (0071) with **gitleaks** so a staged secret
cannot enter the repository.

- `.githooks/pre-commit` runs `gitleaks protect --staged --redact
  --no-banner --exit-code 1` after the contributor check; any finding
  refuses the commit.
- **Fail closed**: if `gitleaks` is not installed the hook refuses the
  commit with the install hint (a silent skip would make the guard
  meaningless). `--no-verify` remains a deliberate, forbidden bypass.
- AGENTS.md notes the scan next to the credentials rule.
- False positives are handled with a `.gitleaks.toml` allowlist if/when
  one appears; none are expected in the current tree.

Acceptance: a staged fake secret is refused with a clear message and no
commit is created; a clean commit passes with the scan active.

## Progress log

- **2026-09-14 — implemented and tested.** Hook extended; AGENTS.md
  updated. Verified: staging a fake AWS key pair refuses the commit
  (gitleaks finding, nothing committed); a normal commit completes with
  the scan active. Landed directly on `main` while the remote repository
  is absent (deleted over the earlier identity leak); the issue mirror
  will be filed when the repository is recreated.

## Completion

<!-- filled in when the task is done (after the PR is approved and merged):
- **finished:**
- **commit:**
-->
