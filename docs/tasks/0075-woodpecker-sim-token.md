# 0075: the sim's woodpecker token is not resolved in a sim context

- **created:** 2026-09-14T13:07:22Z
- **type:** [bugfix]
- **depends-on:** 0041
- **status:** in-progress

## Description

`config.woodpecker_token()` resolves only `POLIS_WOODPECKER_TOKEN` or
`WOODPECKER_API_KEY` (env/.env), unlike `gogs_token()` which prefers the
provisioned sim's own token from `secrets.json`. `provision.up_woodpecker`
stores the Magistrate's minted token as `woodpecker_token` in the sim's
secrets, so after a phase transition the generic `polis woodpecker …`
commands in a sim context fail with `missing credential` instead of
addressing the sim's CI.

- `woodpecker_token()` now prefers `_SECRETS["woodpecker_token"]` when
  `POLIS_PROVISIONED_SIM` is set (and no explicit `POLIS_WOODPECKER_TOKEN`
  override), mirroring `gogs_token()`.
- Found while porting the functional suite (task 0069): the
  `features/woodpecker.feature` scenario only passes with this fix.

Acceptance: after the transition, `POLIS_PROVISIONED_SIM=<sim> polis
woodpecker whoami` answers as the sim's Magistrate.

## Completion

<!-- filled in when the task is done:
- **finished:**
- **commit:**
-->
