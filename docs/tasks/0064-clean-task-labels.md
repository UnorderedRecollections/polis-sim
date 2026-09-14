# 0064: clean the task labels — completed issues must not carry in-progress

- **created:** 2026-09-14T07:47:45Z
- **type:** [infrastructure]
- **depends-on:** none
- **status:** done

## Description

Closing a task never removed the `in-progress` label added when work
started, so every recently completed issue (0042, 0043, 0053–0060) still
carried it. This chore removes the stale labels from all closed issues
and accepts the rule — written down in 0065 — that a **closed issue
carries neither `in-progress` nor `review`**.

Deliverables:

- every closed issue free of `in-progress` and `review`;
- the verification command recorded in the workflow docs (0065):
  `gh issue list --state closed --label in-progress` (and `… --label review`)
  must be empty.

## Progress log

- **2026-09-14 — cleanup executed.** Removed `in-progress` from the closed
  issues **#1, #2, #15, #16, #19, #20, #21, #22**; verified none remains
  (`gh issue list --state closed --label in-progress` → empty; no closed
  issue carries `review` yet).

## Completion

- **finished:** 2026-09-14T07:57:49Z
- **commit:** 327a113 (merge of PR #28)
