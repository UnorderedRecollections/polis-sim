# 0071: contributor whitelist — pre-commit identity guard

- **created:** 2026-09-14T11:34:52Z
- **type:** [infrastructure]
- **depends-on:** none
- **status:** done

## Description

Guard against leaking a non-project identity into commit metadata: a
pre-commit hook that refuses any commit whose author or committer is not
listed in `.contributor-whitelist` (repository root; one email per line,
`#` comments and blanks ignored; for now only
`unordered.recollections@letterboxes.org`).

- `.githooks/pre-commit` **fails closed** (a missing whitelist refuses),
  checks `git var GIT_AUTHOR_IDENT` **and** `GIT_COMMITTER_IDENT` — so
  `--author` overrides are caught too — and prints the allowed identities
  on refusal.
- Activate once per clone: `git config core.hooksPath .githooks`
  (repository-local config). `--no-verify` bypasses the hook; AGENTS.md
  forbids using another identity regardless.
- AGENTS.md's credentials rule points at the hook; extending the
  whitelist is an explicit, reviewed edit of the file.

Acceptance: a commit with a non-whitelisted `user.email` or `--author` is
refused with a clear message and no commit is created; the project
identity commits normally.

## Progress log

- **2026-09-14 — implemented and tested.** `.contributor-whitelist` (one
  address) and `.githooks/pre-commit` added; `core.hooksPath` set to
  `.githooks` in the repository-local config. Verified: a commit with a
  non-whitelisted `user.email` is refused, an `--author` override is
  refused, and no commit object is created in either case.

## Completion

- **finished:** 2026-09-14T11:50:41Z (landed directly on `main` while the
  remote repository was deleted; no PR — recorded in the issue mirror)
- **commit:** d2f29cd
