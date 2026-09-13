# 0063: Web UI for scenario authoring, live status and presentation

- **created:** 2026-09-13T19:00:00Z
- **type:** [simulation]
- **depends-on:** 0061
- **status:** open

## Description

The browser surface for the *driving* use case
(`docs/design/scenarios-vs-tests.md` §7), served locally through the
sim's front proxy (0042) and behind authentication (0052).

- scenario library (the tracked `scenarios/` examples) + authoring from
  the step catalog (0059): same contract as the TUI, no test beats;
- submission and live status (scoreboard, journal tail, current story),
  resume/cancel; eventually the narrator view (`sim present`) rendered as
  a readable record;
- one sim per deployment: the UI is a client of the 0061 service, not a
  second implementation of it; static files served through the proxy
  alongside `/gitea`, `/ci` (a new `/polis` path or a dedicated port).

Open questions: framework (server-rendered/HTMX vs SPA), where the UI
lives (operator container vs its own container), how the authenticated
user maps to scenario actors, and how much of the legal record is
readable to whom (the public/private boundary of a sim).

Acceptance: the TUI's user path (author → submit → watch → resume)
works in a browser, with the auth from 0052; documented in the user
guide.

## Completion

<!-- filled in when the task is done:
- **finished:**
- **commit:**
-->
