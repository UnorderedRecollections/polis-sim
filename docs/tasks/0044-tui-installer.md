# 0044: a TUI installer — guided bring-up of a simulation

- **created:** 2026-09-11T16:00:00Z
- **type:** [infrastructure]
- **depends-on:** none
- **status:** open

## Description

`polis install` — an interactive (rich/textual) wizard that takes a user
from nothing to a running simulation, hiding the command surface behind
a guided path:

1. preflight checks (uv present, container runtime + machine running,
   free ports, .env secrets) with fix hints;
2. world genesis + legal-seed validation;
3. sim provisioning (platform choice, sim id, `--with-city-containers`);
4. run bootstrap (situation/jurisdiction picker, seed);
5. a "demo mode" that then drives phase-1 stories, offers the
   transition, and shows phase-2 proceedings + the CI verdicts;
6. teardown from the same UI.

Plain text-dialog fallback when not a TTY (non-interactive: the wizard
becomes a `--yes`-style defaults path). Should compose the existing
porcelain commands only — no new machinery — and surface the same
`--isomorphism` rendering for the legal moves it performs.

## Completion

<!-- filled in when the task is done:
- **finished:**
- **commit:**
-->
