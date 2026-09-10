# 0007: Story generation — what is missing from the data model

- **created:** 2026-09-08T18:30:00Z
- **type:** [simulation]
- **depends-on:** 0001, 0003, 0005
- **status:** done

## Description

Conceptual task: determine what is missing from the data model / ontology to
generate legal stories end to end:

1. what it means to **initialize a jurisdiction** (a legal situation to start
   from) and to **synthesize events** that play out in it and drive the sim;
2. what is needed to **generate disputes** — in particular whether dispute
   generation can be pure code or needs an LLM (with an MCP exposing the
   ontology to the model).

Deliverable: `docs/design/story-generation.md` — gap analysis (have vs
missing), proposed data-model additions, the code-vs-LLM decision, and one
worked end-to-end story trace.

## Completion

- **finished:** 2026-09-10T21:48:57Z
- **commit:** 1bf15c3
