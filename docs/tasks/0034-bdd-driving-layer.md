# 0034: Gherkin as the intervention language

- **created:** 2026-09-10T18:00:00Z
- **type:** [simulation]
- **depends-on:** 0033
- **status:** done

## Description

Gherkin for non-technical users to drive and intervene in simulations —
and, via the same step bindings, executable tests. ONE binding, TWO
drivers (roadmap §1):

- **0034a** ✅ (2026-09-10): scenario model + parser
  (`polis/sim/scenario.py` — feature → ordered beats: setup|action|
  expectation) + step bindings over runtime.enact
  (`features/steps/sim_steps.py`) + behave driver
  (`features/environment.py`: throwaway sim per scenario, destroyed
  after; config reload as secrets appear). First feature
  (`features/northern-banks.feature`) passes; e2e/director/runtime
  regressions green. Fixes it surfaced: gogs usernames cap at **35**
  chars (sim ids now capped at 13 in `_validate_sim_id`);
  `load_chamber` itself obtains the working copy on first use (moved
  out of the CLI so in-process drivers get it too).
- **0034b** ✅ (2026-09-10): `polis sim submit/scenarios/resume` +
  `polis/sim/queue.py` (state per scenario under
  `data/sims/<sim>/queues/`; setup beats at submission, sim-creation
  beat validated+skipped; one action beat per scenario per drive step,
  expectations as reached; pause on failure, `sim resume` to retry) +
  `polis/sim/beats.py` (the shared binding table — behave and the queue
  use one vocabulary). Verified live: on a running sim the submitted
  scenario reached **done** (all expectations passed) while the
  director enacted five seeded stories around it; a quotes-capture bug
  and a pause/retry path were exercised for real. Regressions: behave,
  director-demo, e2e all green.

Narration model (agreed 2026-09-10): **(b) omniscient narrator** —
users write "what happens", the machinery casts it; beats execute in
submission order. The alternative **(a) per-party beats** — a scenario
IS a party's agenda, executed on that party's turn (director.md §3
policies) — is reserved for the multi-user service era.

Out of scope (later): the long-running service wrapper (watched queue
dir / POST / MCP) and the web UI over `sim present`.

See docs/design/roadmap.md for context and ordering.

## Completion

- **finished:** 2026-09-10T20:00:00Z
- **commit:** (pending — user commits)
