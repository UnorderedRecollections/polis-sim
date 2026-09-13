# 0058: `tests/all.sh` — one full-verification runner

- **created:** 2026-09-13T18:41:23Z
- **type:** [tests]
- **depends-on:** 0053, 0057
- **status:** in-progress

## Description

The fast/slow split is deliberate (task 0057: `behave.ini` excludes
`@slow` so the edit-run loop stays ~10 s and free of shared-state
surprises), but there is no single command that runs **everything**:
"verify" is a list in AGENTS.md, and a bare `behave` run silently skips
the transition arc. Add the missing half:

`tests/all.sh` — run the full matrix, cheap to expensive, and report a
summary:

1. `uv run behave features/` (fast suite);
2. `tests/bdd-phase2.sh` (slow gitea suites: phase I on gitea +
   phase I → transition → phase II);
3. the self-contained demos: `tests/provision-demo.sh`,
   `tests/provision-demo-gitea.sh`, `tests/director-demo.sh`,
   `tests/transition-demo.sh`;
4. dev-rig-only checks (`scripts/infra/smoke.sh`,
   `tests/sim-runtime-demo.sh`, `tests/e2e-gogs.sh`) only when the dev
   rig answers, unless `--dev-rig` is passed (then they are required,
   not skipped).

Properties: `POLIS_PROVISIONED_SIM` unset (suites set their own
context); continue after a failure and exit non-zero with a summary;
skip (with a loud note) only what the machine cannot run. Wire it as the
one-shot target for the CI tasks (0045/0049) and document it in
`docs/testing.md`/AGENTS.md.

Acceptance: `tests/all.sh` green on this machine; a deliberately broken
step fails the run and is named in the summary; `--dev-rig` without a rig
reports failures rather than skipping silently.

## Progress log

- **2026-09-13 — implemented and verified.** `tests/all.sh` added (fast
  behave → slow gitea suites → self-contained demos → dev-rig checks
  when the rig answers, required with `--dev-rig`; `POLIS_PROVISIONED_SIM`
  unset; failures collected, summary, non-zero exit). Documented in
  `docs/testing.md` §5 and the AGENTS.md Dev bullet; the runner is named
  as the CI target in tasks 0045/0049 (local files and issues #4/#8 kept
  in sync). Verified: full run green — 6 passed, 1 skipped (no dev rig
  on this machine), ~<5 min; a stubbed failing step exits 1 and is named
  in the summary.

## Completion

<!-- filled in when the task is done:
- **finished:**
- **commit:**
-->
