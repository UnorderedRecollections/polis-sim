# 0001: Overall design for the simulator

- **created:** 2026-09-08T16:57:20Z
- **type:** [simulation]
- **depends-on:** (none)
- **status:** in-progress

## Description

Produce the overall design of the simulation engine, covering four
requirements:

1. step-by-step **replay** of a simulation from a log-like structure (file);
2. **interaction with the per-city containers** (`polis-city-*`);
3. a **legal story generator** producing use cases (petitions, bills,
   amendments, conflicts) as simulation material;
4. a **Behave (BDD) foundation** with a pre-built step/object library so
   scenarios are human-readable for a non-technical audience.

Deliverable: `docs/design/simulator.md`, reconciling these with the existing
ontology (three stores, two clocks) and the recorded design debts
(`docs/todo/simulation-service-requirements.md`).

## Completion

<!-- filled in when the task is done:
- **finished:**
- **commit:**
-->
