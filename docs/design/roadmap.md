# Roadmap — UX consolidation and the road to phase 2

Status: agreed direction (2026-09-10). Tasks: 0034–0039.

The system works but is unwieldy at the surface: too many commands to
drive a story by hand, situations are hand-authored, phase 1 is
implicitly gogs-bound, and phase 2 is a wall instead of a door. Five
workstreams, ordered.

## 1. Gherkin as the intervention language (task 0034) — the UX answer

Gherkin is for **non-technical users to drive and intervene in a running
simulation** — and, sharing the same step bindings, for executable tests.
behave-the-runner is the synchronous consumer; the live sim consumes
scenarios **incrementally** — the two drivers, one binding:

```
.feature ──parse──► scenario model (ordered beats: actions | expectations)
                     ├── behave driver (synchronous: CI, regression)
                     └── director queue (incremental: live sims)
```

- **scenario model**: Given = setup/precondition, When = action
  (executed via runtime.enact), Then = expectation (evaluated into a
  scenario *scoreboard* — pass/fail observations in the journal).
- **live mode**: `polis sim submit <feature>` validates statically
  (persons, city pairs, jurisdictions, templates) and appends to the
  run's queue (`data/sims/<sim>/queues/` — appendable while running, per
  director.md §3). Each drive step services pending queue beats first,
  then continues seeded stories. User interventions change the
  situation → the director's candidates recompute → the federation
  *reacts*. Execution-time beat failure pauses the scenario (recorded),
  never crashes the sim.
- **test mode**: `features/` + behave (dev dependency); `@live`
  scenarios provision throwaway sims, destroyed after.
- **the service horizon**: the run dir is the state; a long-running
  service is a thin wrapper — watch the queue dir (or POST/MCP) for new
  features, tick on a clock, stream the journal to observers (a web UI
  renders `sim present` later). The operator container is where that
  service naturally lives.
- Phases: 0034a model+parser+bindings+behave; 0034b `sim submit` +
  queue consumption + scoreboard; service wrapper later.

## 2. Situation generation (task 0035)

Today: situations are hand-written YAML; only whole-seed validation
exists. Add:

- `polis world situation new <jurisdiction>` — scaffold a valid
  situation.yaml from the jurisdiction's data (norms over its rule_forms,
  holdings from actors × resources; seeded for variety);
- `polis world legal validate <file>` — validate a single situation/
  norms file (today: only the whole seed);
- docs: authoring conventions (id schemes, paradigm constraints).

## 3. Phase 1 made explicit + the transition corpus (task 0036)

- Mark phase 1 explicitly everywhere: `federation.phase` is already in
  world.json — surface it in `provision status`, `health`, docs; the
  sim's corpus records its phase at the founding.
- **The transition is legislation**: author the legal content that
  establishes phase 2 — a "Mechanical Magistracy Act" (or three acts)
  carrying CODEOWNERS, branch protection and `.woodpecker.yml` into the
  federal archive, per docs/notes/families-of-legal-documents.md §6.
  This task delivers the *content* (act texts + artifacts + a story
  template `phase_transition`); the machinery effect is task 0038.

## 4. Platform abstraction (task 0037) — de-gogs phase 1

Phase is a **procedure**, not a product. Refactor so phase 1 has no
gogs dependency:

- a `Platform` interface on the provisioning side (ensure user/org/
  repo/collaborator/token, delete user/repo, platform container bring-up)
  with `GogsPlatform` (default) and `GiteaPlatform`;
- `provision up --platform gitea` stands up gitea for a sim while the
  federation remains in phase 1 (matter-store petitions, local
  incorporation — no PRs);
- the chamber already dispatches on `federation.phase` — unchanged;
- quirk isolation: gogs-specifics (no pulls API, org cascade nuke,
  auto_init) live in `GogsPlatform` alone.

Depends on nothing; blocks task 0038.

## 5. Phase-transition machinery (task 0038)

When the transition act(s) from 0036 are ratified:

- the federation's `phase` flips to 2 (recorded via the ordinary
  situation/matter channels, not by editing world.json by hand);
- per-sim phase-2 provisioning: gitea (or reuse from 0037) + woodpecker
  per sim, OAuth wiring, the Mechanical Magistrate's CI active;
- the docket/bill CLI dispatch switches to real PRs — same command
  surface (the long-planned proceedings-backend swap).

## 6. LLM integration (task 0039, then MCP)

Seams already exist; add one provider boundary, OFF by default:

- **v1 — generated legal prose**: bill text and grievance particulars
  from the director's mechanical bindings (the exact point where today
  "Northern Banks Quota Act" is a template fill). All generated text is
  recorded in the journal with provenance (`generated: true, model: …`)
  — replay consumes the journal, so determinism holds.
- **v2 — voices**: debate contributions, scrutiny findings.
- **later — MCP server**: polis exposed as MCP tools so an external
  agent can author scenario queues (director §3 already names this
  channel) or drive cities. After 0034 gives a clean action surface.

Provider boundary: `POLIS_LLM_*` env config (base URL, model, key),
httpx only, no SDK lock-in; absent config = today's mechanical text.

## Order and rationale

0034 first (the daily-driver UX + regression net everything else needs),
0035 close behind (feeds BDD and sims), then 0036/0037 in parallel,
0038 once both land, 0039 whenever — it's isolated by the provider
boundary.
