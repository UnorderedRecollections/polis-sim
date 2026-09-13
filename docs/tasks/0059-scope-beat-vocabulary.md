# 0059: scope the beat vocabulary and expose a step catalog

- **created:** 2026-09-13T19:00:00Z
- **type:** [refactoring]
- **depends-on:** 0058
- **status:** in-progress

## Description

First step of the split in `docs/design/scenarios-vs-tests.md` §4: the
flat binding table mixes user actions, test setup, oracles and one
hybrid. Give every `Binding` a **scope** and make the boundary
mechanical.

- `polis/sim/beats.py`: `Binding.scope: user | test`; classify all
  current bindings:
  - `user`: petition/draft/ratify, scrutinize (jurist), the transition
    act (`codify`) once split;
  - `test`: the provisioned-sim setup beat, and the oracles (archive
    contains, norm superseded, petition answered, platform issue/PR,
    merged, CI verdicts, phase, corpus, CI erected).
- **Untangle the hybrid**: `b_codify` keeps the legal act
  (`transition.transition`); the host-side CI erection moves to the
  caller (the operator/host wrapper — already the pattern in
  `cli/sim.py::_erect_ci`), so the driving layer never erects
  infrastructure.
- `queue.validate`/`submit` accept **user** beats only, with a clear
  rejection message naming the scope of the offending beat; behave keeps
  executing all scopes.
- `polis sim steps [--scope user|test] [--json]` — the catalog generated
  from the table (template, scope, parameters) for the authoring UIs and
  the docs.
- Update the behave steps/environment so test-scoped setup/oracles keep
  working; the existing suites stay green.

Acceptance: a submitted scenario containing a test-scoped beat is
rejected with an explanatory message; `polis sim steps --json` lists the
user vocabulary; `tests/all.sh` green.

## Progress log

- **2026-09-13 — implemented and verified.** `Binding.scope` (`user` |
  `test`; `is_user`); the classification rule was corrected from the
  original description: **test** = harness setup + operator-machinery
  introspection, **user** = legal actions *and* in-world outcomes
  (goals) — the conservative "all oracles are test" reading would have
  left submitted scenarios with no way to state goals, contradicting the
  driving use case; the design note §4 now records the rule. Split
  `b_codify` (legal act only; the harness step erects the CI after it).
  `queue.validate(feature)` now accepts user beats only, with an
  explanatory rejection; `polis sim steps [--scope user|test] [--json]`
  (15 user / 2 test at present) is the catalog. `docs/flows/simulation.md`
  example updated (submitted scenarios no longer carry the provision
  beat); `tests/beat-scopes.sh` covers catalog + validation and runs
  first in `tests/all.sh`.
- **Verified:** `tests/beat-scopes.sh`, fast behave, `tests/bdd-phase2.sh`
  (transition + CI through the new driver split), `tests/all.sh`.

## Completion

<!-- filled in when the task is done:
- **finished:**
- **commit:**
-->
