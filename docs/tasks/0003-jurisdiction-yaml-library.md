# 0003: Jurisdiction YAML library (legal design data)

- **created:** 2026-09-08T17:20:00Z
- **type:** [simulation]
- **depends-on:** 0002
- **status:** done

## Description

Create `data/world/legal/jurisdictions/<slug>.yaml` for all fifteen
jurisdictions, starting from the user's `fisheries.yaml` sketch, with schema
improvements (documented in `docs/design/story-data-model.md`):

- `actions` → split into `activities` (what actors do with the resource —
  domain verbs) vs legal moves (which live in `moves.yaml`);
- add `resource_properties` and `rule_forms` (from the task-0002 conflict
  grammar), so each file can actually drive conflict generation;
- add `corpus_dir` where the jurisdiction is backed by the corpus today.

Also: review `moves.yaml` (legal moves vs machinery — `merge`/`revert` are
the machinery of `ratify`/`repeal`), review the resource-dispute template,
and add a small validated loader (`polis/sim/legaldata.py`, pyyaml) so the
story generator is truly data-driven. The `world.enact(...)`
story-block-as-transaction idea is noted for later exploration.

## Completion

- **finished:** 2026-09-10T21:48:57Z
- **commit:** 5103692
