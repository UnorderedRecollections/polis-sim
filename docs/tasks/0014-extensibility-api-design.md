# 0014: Extensibility — adding actors/jurisdictions, an LLM-facing API

- **created:** 2026-09-08T18:51:22Z
- **type:** [simulation]
- **depends-on:** 0008, 0009, 0010, 0011, 0012, 0013
- **status:** open

## Description

Think through how **adding a new actor kind or a new jurisdiction** works
once all of the above exists — and whether we can expose an API (MCP) that
lets an LLM understand *what are the steps* to define a jurisdiction:

- the complete checklist for a new jurisdiction (ontology registration,
  jurisdiction YAML, resources, norms/holdings seed, incompatibilities,
  activity signatures, corpus dir, casting implications);
- the same for a new actor kind;
- what an MCP surface would look like: read tools (query ontology,
  jurisdictions, situation) + a validated write tool
  (`propose_jurisdiction` / `propose_actor`) that checks the proposal
  against every requirement and reports what's missing;
- validation rules (schema, parity with ontology, conflict grammar
  completeness) so an LLM can iterate toward a valid definition.

Deliverable: `docs/design/extensibility-api.md`.

## Completion

<!-- filled in when the task is done:
- **finished:**
- **commit:**
-->
