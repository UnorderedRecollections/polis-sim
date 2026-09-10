# 0012: Activity signatures — design document

- **created:** 2026-09-08T18:51:08Z
- **type:** [simulation]
- **depends-on:** 0007, 0009
- **status:** done

## Description

Activity signatures (upgrading jurisdiction `activities` from bare verbs to
structured objects: `verb / actors / affects / impact` + preconditions and
typical friction) are **substantial in scope** — they are the engine of
event synthesis. Write a design document covering:

- the signature schema (who may perform it, what it targets, which resource
  properties it affects, the impact kind, preconditions, what it typically
  disrupts);
- how signatures combine with holdings and norms to produce event
  candidates;
- how impacts write back to the situation when an event is executed;
- a worked example in at least two structurally different jurisdictions
  (one resource-based, one conduct-based).

Deliverable: `docs/design/activity-signatures.md`.

## Completion

- **finished:** 2026-09-10T21:48:57Z
- **commit:** d13c75b
