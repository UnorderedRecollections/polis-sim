# 0030: Epoch management — sim fresh / epochs / present --epoch

- **created:** 2026-09-10T11:00:00Z
- **type:** [simulation]
- **depends-on:** 0024
- **status:** done

## Description

The run's *record* (journal, situation, stories, matters, run.json)
survives teardown by design, but managing it is manual (`rm -rf`).
Porcelain:

- `polis sim fresh` — archive the current record to
  `data/sims/<sim>/epochs/<timestamp>/` and clear it (journal, situation,
  stories, matters, run.json removed); the machinery (platform, slices,
  secrets, archive history) is untouched, and the next `sim new`
  bootstraps a fresh epoch on the same sim. Note honestly: the legal
  archive (git history on the platform) does NOT roll back — a blank
  legal slate is teardown + rm -rf.
- `polis sim epochs` — list saved epochs (name, entries, span).
- `polis sim present --epoch <name>` — narrate a saved epoch (read-only;
  epochs are keepsakes, not time travel — journal anchors refer to git
  history that may no longer exist on the platform).

All default the sim id to POLIS_PROVISIONED_SIM.

## Completion

- **finished:** 2026-09-10T11:15:00Z
- **commit:** (pending — user commits)

Delivered: `polis sim fresh --yes [--name N]` (archive record to
`epochs/<name>/`, clear journal/situation/stories/matters/run.json),
`polis sim epochs` (list with entries + span), `polis sim present --epoch
<name>` (narrate a keepsake). Record files defined as RECORD_FILES in
`polis/sim/journal.py`; machinery untouched. Verified live on a user sim:
191-entry epoch archived, fresh epoch started (story-0001/ACT-0001 —
institutional time restarts; the archive's git history continues, hence
"(No. 3)" acts — documented), old epoch narratable, director-demo
regression green.
