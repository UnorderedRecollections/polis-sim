# 0062: TUI for scenario authoring and live interaction

- **created:** 2026-09-13T19:00:00Z
- **type:** [simulation]
- **depends-on:** 0061
- **status:** open

## Description

The first UI surface for the *driving* use case
(`docs/design/scenarios-vs-tests.md` §7): a terminal UI a non-technical
user can operate against a running sim — the audience that should never
need `polis sim submit` flags or shell fluency.

- browse the step catalog (`polis sim steps`, 0059) with plain-language
  descriptions of each user beat and its parameters;
- author or adapt a scenario (guided forms; an editor path for the
  Gherkin-literate), validate it before submission;
- submit to the running sim (the service from 0061), follow the
  scoreboard and journal live, and resume/cancel paused scenarios;
- works locally against the sim's operator/service; no browser, no
  credentials beyond the sim's own (auth lands with 0052/0061).

Acceptance: a user who knows the domain, not the tooling, can author a
scenario, submit it, and watch it finish — documented in the user guide.
Stack: the project already builds its CLI output on rich; a TUI library
(e.g. Textual) is the natural fit.

## Completion

<!-- filled in when the task is done:
- **finished:**
- **commit:**
-->
