# 0048: proposal — a minimal CI/CD runner to replace woodpecker

- **created:** 2026-09-11T16:00:00Z
- **type:** [infrastructure]
- **depends-on:** 0047
- **status:** open

## Description

Propose a small runner for the Mechanical Magistrate's needs, replacing
woodpecker (which is heavy and cost us many quirks: fork-PR approval,
`require_approval` enum, CSRF token dance, WOODPECKER_HOST/webhook
split, the v3 `steps:` schema, the macOS agent flags).

The simulation needs only:

- one pipeline per PR on the archive repo;
- read the pipeline spec (keep `.woodpecker.yml`-compatible, or move to
  a polis-native schema);
- run steps as containers on the sim's network;
- inject the checks' context (`POLIS_GITEA_URL/TOKEN`, CI env);
- report commit statuses (`report:commit-status` — the Magistrate's
  office);
- expose build logs (for `sim present`-style narration).

Deliverable: `docs/design/ci-runner.md` — design sketch, the config
format decision, the webhook/status contracts against the forge server
(task 0047), and the migration plan from woodpecker (including what the
transition story's third act says — the schedule renames, not the law).

## Completion

<!-- filled in when the task is done:
- **finished:**
- **commit:**
-->
