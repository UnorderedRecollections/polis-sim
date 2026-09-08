# 0019: Runtime v1 — journal, enact() transaction facade, sim CLI

- **created:** 2026-09-09T10:40:00Z
- **type:** [simulation]
- **depends-on:** 0001, 0018, 0008
- **status:** in-progress

## Description

A usable runtime (Behave and the director depend on it):

- `polis/sim/journal.py` — append-only JSONL journal per run
  (`data/sims/<run>/journal.jsonl`): every action with before/after anchors
  (git heads, matter ids, norm ids touched).
- `polis/sim/runtime.py` — the **enact() transaction facade**: one call =
  one legal act (one Plan executed) = one journal entry. The simulation
  never touches git stepwise. Typed move methods (file_petition,
  draft_bill, introduce_bill, scrutinize, ratify, reject, repeal…)
  dispatching to `polis.legislation`, plus **situation write-back** at
  ratify/repeal (norms.py operations on a NormSet attached to the run).
- `polis sim` CLI: `new`, `list`, `present <run>` (narrated replay from the
  journal, no infra contact).
- `tests/sim-runtime-demo.sh` — full scenario against a throwaway gogs
  repo (e2e-style): obtain → petition → bill → scrutiny → ratify with norm
  write-back; assert journal anchors and norm status transitions.

## Completion

<!-- filled in when the task is done:
- **finished:**
- **commit:**
-->
