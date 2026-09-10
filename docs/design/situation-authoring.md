# Authoring situations

A *situation* is one YAML file — norms in force + holdings, in the same
format for seed and snapshot (the snapshot principle). It is what a run
legislates from (`polis sim new --situation …`).

## Generate, don't hand-write

```bash
uv run polis world situation new fisheries              # preview on stdout
uv run polis world situation new fisheries --seed 7 \
  --out situations/fisheries-s7.yaml                    # write
uv run polis world legal validate situations/fisheries-s7.yaml
```

The generator composes from the jurisdiction's own data, **following its
paradigm**:

- *resource* paradigms (fisheries, land-commons, …): one norm per
  resource, holdings of resource use;
- *conduct/status* and *political-burden* paradigms (criminal, contract,
  taxation, …): one norm per activity (object = the regulated conduct,
  the pattern of the hand-written seeds), holdings attached to the
  jurisdiction's institutions with a paradigm-admitted type
  (relationship/flow/status/…).

Rule_forms are cycled for coverage, aspects come from the
incompatibility table, holdings sample cities by seed. Two properties by
construction:

- **no active strict conflict** (one norm per resource);
- **friction exists** — norms regulate resource *users* (actors of
  depletes/enriches activities), not overseers; if every actor were a
  subject, all harm would be "allocated by law" and nothing would be
  charged (a situation that can't tell stories).

## Conventions for hand edits

- **ids**: norms `N-####`, holdings `H-####`, unique within the file
  (the director allocates the next `N-####` at enactment).
- **`jurisdiction:` key at top level** — required by
  `world legal validate <file>` and by `sim new` (when `--jurisdiction`
  is not given, the file's stem is used as fallback).
- **rule_form** must be one of the jurisdiction's `rule_forms`;
  **object.type** must be admitted by the jurisdiction's paradigms;
  **aspect** should come from the incompatibility table's `over` values
  (friction matches activities' `affects` against norm aspects).
- **holdings cite norms** (`under:`) and must never drift from them —
  a holding's `object`/`activity` reads as "holder uses object by
  activity under norm".
- **subjects ≠ everyone**: norms bind the regulated (resource users).
  Authorities/inspectors stay outside `subjects` so their acts can be
  charged.
- Editing between ticks is legitimate intervention: the director
  re-reads `situation.yaml` on every drive call.

## Validation gates

| command | scope |
|---|---|
| `polis world legal validate` | the whole tracked seed (jurisdictions, resources, norms, conflicts) |
| `polis world legal validate <file>` | one situation file (registry cross-check + active conflicts) |
| `polis world legal audit [slug]` | the new-jurisdiction checklist |
| `polis world events candidates --jurisdiction <slug>` | what the situation would *generate* — check friction before running |
