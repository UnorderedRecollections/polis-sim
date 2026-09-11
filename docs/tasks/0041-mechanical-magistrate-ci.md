# 0041: the Mechanical Magistrate's CI (0038b) — per-sim woodpecker + OAuth + formal checks

- **created:** 2026-09-11T09:40:00Z
- **type:** [infrastructure]
- **depends-on:** 0038
- **status:** done

## Description

The remainder of the phase-2 machinery (roadmap §5; deferred from 0038):
per-sim woodpecker server + agent, OAuth wiring against the sim's gitea,
and the Mechanical Magistrate's pipeline actually running the formal
checks on proposed changes. The checklist is
`docs/notes/families-of-legal-documents.md` §6; the pipeline is authored
as the Mechanical Magistracy Act's Schedule 1
(`data/world/legal/transition/.woodpecker.yml`); the Magistrate's office
(`mechanical-magistrate`, powers `execute:formal-checks`,
`report:commit-status`) already exists in the civil registry.

Decisions taken (user, 2026-09-11): the CI is brought up by
`sim transition` (the third act erects it); the instrument renamed to
`.woodpecker.yml` (woodpecker's convention); four checks including the
council-comment constitution check; the polis-city image runs the steps
(now carries the legal-design data via POLIS_DATA_DIR).

## Completion

- **finished:** 2026-09-11T13:45:00Z
- **commit:** 2e1670b
