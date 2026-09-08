# 0008: Bootstrapping — the foundational state of rules-in-force

- **created:** 2026-09-08T18:50:38Z
- **type:** [simulation]
- **depends-on:** 0007, 0009, 0010, 0011, 0016
  (0012/0013 feed the *director*, not the seed — not required here)
- **status:** in-progress

## Description

Rules-in-force must start from a **seed**: an initial *foundational state*
in which the nine cities already exist with customary rules. As laws are
passed, the rules-in-force evolve from that seed.

Investigate and document what bootstrapping requires:

- what the foundational state contains (per city? per jurisdiction? which
  customary norms/holdings exist at genesis, and who wrote them — the
  "customary constitution" problem);
- how the seed is produced (authored YAML? generated from jurisdiction
  data? a founding act in the fiction?);
- how enactments mutate the rules-in-force (write-back from ratification:
  source flips custom → statute, supersession, repeal);
- where the foundational state lives (run-scoped situation store vs. a
  shared seed file all runs start from);
- relation to `polis world genesis` (is the legal seed part of genesis, or
  separate?).

Deliverable: design document + (if clear) a seed format proposal.

## Completion

<!-- filled in when the task is done:
- **finished:**
- **commit:**
-->
