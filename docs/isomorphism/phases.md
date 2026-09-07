# The Two Eras — customary and codified machinery

The simulation runs in two phases (`federation.phase` in `world.json`).

## Phase 1 — customary machinery (gogs)

The Confederation has cities, citizens, legislators, delegates, jurists,
archivists — and a git repository on gogs that is **merely an archive in the
mechanical sense**. Petitions, proceedings, reviews and approvals exist
institutionally and socially, outside the software (in the matter store).

Workflow:

```
City B drafts law → local deliberation → City B Archivist commits
→ city repo branch → copy sent / incorporation proposed
→ federal proceedings (people) → Federal Archivist merges by hand
→ common law → git push → gogs records the result
```

Nothing in gogs prevents an archivist from violating the constitution; the
legitimacy of a merge comes from the institution. Customary review is
recorded by convention (`bill scrutinize` enters findings into the matter's
record).

## Phase 2 — codified machinery (gitea + Woodpecker)

The same institutions, now with codified forms: PRs (petitions), platform
reviews (scrutiny), CODEOWNERS (machine-readable jurisdiction), branch
protection (entrenchment), CI (the Mechanical Magistrate, executing formal
legality).

## The transition is enacted through the old machinery

The constitutional moment: phase 2 is brought into being by **phase-1
procedure** — three ratified bills:

1. a bill committing `CODEOWNERS` (jurisdiction becomes machine-readable);
2. a bill committing `.woodpecker.yml` (the Magistrate is erected);
3. the enabling acts for branch protection and the gitea migration.

After ratification, `federation.phase` flips to 2, city slices point at
gitea, and the same command surface (`docket`/`bill`/`archive`) dispatches
onto the codified platform.

## Known debts for the transition

- `docs/todo/docket-refactoring-for-phase-ii.md` — the platform dispatch in
  docket/bill must become a proceedings-backend interface; the phase-2
  institutional mapping (does the record stay in matters or move into the
  platform?) is an open decision.
