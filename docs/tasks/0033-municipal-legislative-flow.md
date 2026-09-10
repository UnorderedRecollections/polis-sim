# 0033: Municipal legislative flow in city containers

- **created:** 2026-09-10T16:30:00Z
- **type:** [simulation]
- **depends-on:** 0021, 0024
- **status:** done

## Description

Acting inside a city container currently breaks municipal legality twice:

1. **The docket falls into a void**: city containers have no
   `POLIS_MATTERS_FILE`, so `docket file` writes a container-local
   ephemeral matters.json — invisible to the sim, lost on recreate.
   Fix: provision mounts a per-city docket
   `data/sims/<sim>/dockets/<city>.json` (rw) and sets
   `POLIS_MATTERS_FILE` — municipal grievances are the city's own
   persistent record (the federal docket stays the sim's matters.json).
2. **Ratification always targets the federal archive**: for municipal
   law (bills into `municipal/<city>/`), the local archivist must enact
   into the CITY's archive (origin), not upstream. Fix: ratify/
   consolidate resolve the destination from the ratifier's merge powers —
   `**` (Keeper) → upstream; municipal-only patterns → origin — fetching
   `<dest> main` before the bill branch and pushing there.

Verify end-to-end inside a city container (not the Keeper's city):
petition → draft into `municipal/<city>/` → amend → introduce →
ratify as the local archivist → the enactment merge is in the city repo,
not the federal archive. Document in docs/flows/petitions.md +
legislation.md.

## Completion

- **finished:** 2026-09-10T17:30:00Z
- **commit:** (pending — user commits)

1. **City dockets**: provisioning mounts per-city
   `data/sims/<sim>/dockets/<city>.json` (rw) as `POLIS_MATTERS_FILE`;
   `load_matters` treats an empty file as an empty docket.
2. **Municipal enactment**: `_enactment_dest()` — ratify/consolidate
   resolve the destination from the ratifier's merge powers (`**` →
   upstream/federal; municipal-only → origin/city archive), fetch
   `<dest> main` first, push there. Plan rendering reflects the dest.
3. **Bill-line resume**: `draft` checks out an origin-existing branch
   (`checkout -b branch FETCH_HEAD`) instead of diverging — half-failed
   flows and fresh clones resume instead of colliding.

Verified end-to-end inside `polis-city-brasshaven-clean-test-01`:
petition → municipal draft → amend → introduce → ratify by the local
archivist (e.fallowfield); the enactment merge is in the brasshaven
repo, the federal archive carries no trace. Regressions: e2e-gogs,
director-demo, sim-runtime-demo all pass. Docs: petitions.md (municipal
dockets), legislation.md (enactment destination + the full municipal
command sequence).
