# 0031: Flow documentation — master + per-flow documents

- **created:** 2026-09-10T12:30:00Z
- **type:** [simulation]
- **depends-on:** 0024, 0030
- **status:** done

## Description

A document set explaining each legal **flow** through the system, with
domain explanations, practical polis commands and mermaid flow graphs:

- `docs/flows/README.md` — the master: actors, the three stores, phases,
  how the flows connect, end-to-end map;
- `docs/flows/petitions.md` — the docket: grievance → filed → heard →
  answered/dismissed (institutional time, matters.json);
- `docs/flows/legislation.md` — bill lifecycle: draft → amend →
  introduce → scrutiny → ratify/consolidate | reject (git + matters);
- `docs/flows/archive.md` — the archive as legal time: obtain/receive/
  lodge/promulgate, repeal/transplant/reconstruct/replace-history;
- `docs/flows/simulation.md` — the epoch loop: situation → candidates →
  selection → casting → story execution → write-back; epochs.

All commands verified against the CLI; AGENTS.md layout updated.

## Completion

- **finished:** 2026-09-10T13:00:00Z
- **commit:** (pending — user commits)

Delivered `docs/flows/`: README.md (master: actors, the three stores with
a mermaid map, phases, the end-to-end picture), petitions.md (docket
states + commands), legislation.md (bill lifecycle states + gitGraph of
enactment + commands), archive.md (legal-time operations, gitGraph,
path-jurisdiction), simulation.md (the director loop, template-to-flow
mapping, journal reading, epochs). Every command snippet verified against
the live CLI (amend takes repeatable `--file`; promulgate `--name`;
answering/kind/into confirmed). AGENTS.md layout updated.
