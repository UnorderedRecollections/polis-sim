# 0065: task workflow — review state, feature branches + PRs, label hygiene

- **created:** 2026-09-14T07:47:45Z
- **type:** [infrastructure]
- **depends-on:** none
- **status:** done

## Description

Change the mandatory task workflow (AGENTS.md "Task workflow" and the
task template, `docs/tasks/0000-task-template.md`) to require review
before completion:

- **statuses:** `open → in-progress → review → done` — `review` means the
  PR is open and awaiting approval (mirrored by the new `review` GitHub
  label);
- **feature branch + PR:** every task is implemented on
  `task/NNNN-slug` (one task per branch) and reaches `main` only through
  a pull request; the PR title is `NNNN: <task title>`, its body
  summarizes what/why/verification and closes the issue (`Closes #<n>`);
- **review state:** when the PR opens, the issue moves
  `in-progress` → `review` and gets the PR link as a comment; the local
  file's status becomes `review` (in the branch);
- **approval gate:** only an approval on GitHub allows the merge; the
  merge closes the issue; only then is the task marked `done` locally
  with its Completion metadata (a bookkeeping commit on `main`);
- **label hygiene (from 0064):** a closed issue carries neither
  `in-progress` nor `review` — `Closes` does not remove labels, so they
  are cleaned after the merge; the verification commands are recorded in
  the workflow.

Deliverables: AGENTS.md + the task template updated; the `review` label
exists; the two chore tasks (0064, 0065) themselves land through PRs.

## Progress log

- **2026-09-14 — implemented.** AGENTS.md "Task workflow" rewritten
  (branch/PR/review/approval/label hygiene, with the exact `gh` commands)
  and the template's status line extended with `review`; the `review`
  label was created on the repository; 0064 and 0065 are themselves
  implemented on `task/…` branches with PRs.

## Completion

- **finished:** 2026-09-14T07:58:30Z
- **commit:** 33b5c5c (merge of PR #29)
