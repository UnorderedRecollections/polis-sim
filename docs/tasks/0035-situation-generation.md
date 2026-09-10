# 0035: situation generation

- **created:** 2026-09-10T18:00:00Z
- **type:** [simulation]
- **depends-on:** 0031
- **status:** done

## Description

polis world situation new <jurisdiction> scaffold (norms from rule_forms, holdings from actors x resources, seeded) + single-file validation (world legal validate <file>) + authoring conventions doc.

See docs/design/roadmap.md for context and ordering.

## Completion

- **finished:** 2026-09-10T21:00:00Z
- **commit:** (pending — user commits)

Delivered: `polis/sim/situations.py` (generator, **paradigm-aware**:
resource paradigms → one norm per resource; conduct/status and
political-burden paradigms → one norm per activity with the regulated
conduct as object and institution-typed holdings, following the
hand-written seeds' pattern — all 15 jurisdictions generate and
validate) with rule_forms cycled, aspects from the incompatibility
table, holdings from activities × actors × seeded cities; norms bind
resource USERS not overseers — else all harm is "allocated" and the
situation holds no friction, caught live when the first generation
skipped every story) +
`polis world situation new <jurisdiction> [--seed N] [--out PATH]
[--force]` (stdout preview default; validates before writing) +
`polis world legal validate <file>` (single-file: registry cross-check +
active conflicts) + `docs/design/situation-authoring.md` (conventions:
id schemes, jurisdiction key, subjects≠everyone, validation gates).
Verified full cycle: generate → validate → provision → sim new → first
tick enacts. Regressions: behave, director-demo, e2e green.
