# 0061: the scenario service — identity, event-sourced sessions, replay

- **created:** 2026-09-13T19:00:00Z
- **type:** [simulation]
- **depends-on:** 0060, 0052
- **status:** open

## Description

`docs/design/scenarios-vs-tests.md` §7, absorbing
`docs/todo/simulation-service-requirements.md`. Turn the queue into the
driver a UI can talk to.

- **Chamber-independent identity.** Scenario beats resolve actors
  through the world (persons, offices, casting rules), not through the
  director's `_Cast`/Chamber test assumptions; once 0052 lands, an
  authenticated user can be the actor behind a submission, with
  authorization (who may file/ratify what is an institutional fact, not
  a UI check).
- **Event-sourced sessions.** Every scenario transition (submitted, beat
  executed, goal reached, paused, resumed, cancelled) is an event in the
  scenario's record; the current scoreboard is a projection of the
  events. Sessions survive process restarts (state on disk, already
  partly true in `queues/`).
- **Stepping and replay.** Replay a scenario from its events
  (deterministic given the journal), and step it independently of the
  seeded director stories; keep the two clocks explicit: git history =
  legal time, scenario/matter events = institutional time.
- **Long-running wrapper.** A thin service (in the operator container,
  the roadmap's natural home) that watches the queue directory or
  exposes a submit/status/control API (HTTP/MCP) and streams the
  journal; the CLI and the UIs become clients.
- **Tests** for identity resolution, session persistence, replay and the
  service boundary.

Acceptance: a scenario session survives a restart; replay reproduces the
scoreboard; a client can submit, watch and control over the service
boundary; no behave dependency anywhere in the driving layer.

## Completion

<!-- filled in when the task is done:
- **finished:**
- **commit:**
-->
