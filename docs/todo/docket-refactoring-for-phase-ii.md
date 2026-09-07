# TODO: Docket/bill refactoring for phase II

## The problem

After the phase-1 ontology fix, `polis/legislation/docket.py` and parts of
`bill.py` dispatch on `chamber.platform` at almost every entry point:

- phase 1 (gogs): petitions and bills are **matter-store entries** with an
  event record;
- phase 2 (gitea): petitions are **platform issues**, bills are **PRs**.

The two backends differ in more than transport:

- **identity**: matters are `PET-####`/`ACT-####`; platform objects are issue/PR
  numbers. The CLI papered over this (`matter` argument accepts either, with
  `int(matter_id.lstrip("#"))` conversions), which will get brittle.
- **state model**: matters have rich status (`submitted/deliberating/
  scrutinized/ratified/rejected/dismissed`) + an event record; issues/PRs have
  only open/closed (+ comments). Phase-2 code must decide how the institutional
  state maps onto platform state (labels? comment conventions? status checks?).
- **list/show shapes**: the CLI already branches on `"id" in p` / `"events" in
  p` to render two different record shapes.

## What to do at the phase-II transition

1. Extract a **proceedings backend interface** (open/comment/scrutinize/close/
   list/get with matter-shaped semantics) with two implementations:
   `MattersBackend` (file store) and `PlatformBackend` (gitea issues/PRs).
   Docket/bill call the interface; the platform dispatch disappears from the
   legal layer.
2. Decide the **phase-2 institutional mapping** deliberately, not ad hoc:
   does phase 2 keep the matter store as the institutional record *and* mirror
   to gitea (the codified platform merely executes), or does the record truly
   move into the platform? The fiction wants the latter ("codified
   machinery"), but event-sourced proceedings (see
   `simulation-service-requirements.md`) may want the former.
3. Retire the number/PET-id dual-typing in the CLI: one matter identity
   scheme, backend-resolved.
4. The `families-of-legal-documents.md` §6 checklist (Mechanical Magistrate CI
   spec) assumes machine-readable documents; phase-2 docket objects should
   carry document references (ACT ids) so CI can correlate proceedings with
   the corpus.
