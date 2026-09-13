# Writing scenarios — driving a running simulation

Status: current (task 0060). This is the **author-facing** guide: how a
non-technical user intervenes in a running sim with a Gherkin scenario.
The developer-facing side — running the software's tests — lives in
[`docs/testing.md`](testing.md); the design boundary between the two is
[`docs/design/scenarios-vs-tests.md`](design/scenarios-vs-tests.md).

A scenario is not a test. Tests assert and fail a build; a scenario
**drives the world**: its beats are performed by the sim's machinery,
its expectations are **goals** the federation may or may not reach, and
the sim always goes on.

## 1. The lifecycle

```bash
export POLIS_PROVISIONED_SIM=my-sim-01          # or pass --run
uv run polis provision up my-sim-01             # once
uv run polis sim new --situation data/world/legal/norms/fisheries.yaml

uv run polis sim steps --scope user             # the vocabulary
uv run polis sim submit ../scenarios/northern-banks-quota.feature
uv run polis sim scenarios                      # the scoreboard
uv run polis sim drive --steps 3                # service the queue (+ 3 seeded stories)
uv run polis sim resume <slug>                  # retry a paused scenario
```

## 2. Anatomy of a scenario

One scenario per file; beats come from the **user** vocabulary
(`uv run polis sim steps --scope user`, `--json` for the UIs). The
Gherkin keyword decides *when* a beat runs:

| keyword | kind | when |
|---|---|---|
| `Given` | precondition | **at submission** (the world is already set up) |
| `When` / `And` after it | action | one action beat per `drive` step |
| `Then` / `And` after it | goal | evaluated as reached; failing it pauses the scenario |

Beats name the world the way the world names itself:

- **cities and resources** come from the world/seed (`cogswich`,
  `northern banks` → the `northern_banks` resource);
- **actors are cast**: "the fishers of brasshaven" becomes a legislator
  of Brasshaven, the Keeper enacts, the jurist reviews — an omniscient
  narrator's shorthand;
- **documents** land in the corpus layout: `constitution/`, the domain
  dirs (`fisheries`, `taxation`, …), or `municipal/<city>/`; the title
  becomes the file name;
- **norms** are cited by id from the situation (`N-0001`); a remedy is
  one of the jurisdiction's rule forms (`quota`, `open_access`, …).

## 3. Phase constraints

The federation's phase is a procedure: what a scenario can do depends on
it (and `the federation codifies its machinery` is the transition
itself).

| beat | phase 1 (customary) | phase 2 (codified) |
|---|---|---|
| petition / docket goals | matter-store entry | real platform issue |
| draft / introduce / ratify | branch + local incorporation | cross-repo pull request |
| `the jurist approves the bill` | — (reviews need the platform's PR machinery) | review comment, `SCRUTINY — APPROVED` |
| Magistrate's verdicts | — | CI commit-status on the PR |
| archive/corpus/norm goals | yes | yes |

`the federation codifies its machinery` performs the legal transition;
**the CI erection is the driver's job, not the scenario's** — today the
host does it (`polis sim transition`), the service will (task 0061).
Until then, transition a sim on the host and then submit phase-2
scenarios.

## 4. Goals, failure and resume

- A goal that does not hold **pauses** the scenario (recorded in the
  journal, with the beat and the reason); the sim and every other
  scenario continue.
- `polis sim scenarios` shows the scoreboard; `polis sim resume <slug>`
  makes the failed beat pending again — fix the world (or wait for the
  federation to move) and keep driving.
- Actions can fail the same way (a chamber error, a missing norm): same
  pause, same resume.
- There is no `cancel` yet; a scenario can be paused indefinitely.

## 5. What is rejected

Scenarios using the **test** vocabulary are rejected at submission with
an explanatory message: provisioning (`a provisioned sim …`) and
operator-machinery introspection (`the Mechanical Magistrate's CI is
erected`) are the harness's, never the author's. `polis sim steps` shows
the scope of every form.

## 6. Examples

- [`scenarios/northern-banks-quota.feature`](../scenarios/northern-banks-quota.feature)
  — a phase-I quota campaign.
- [`scenarios/codified-procedure.feature`](../scenarios/codified-procedure.feature)
  — a phase-II municipal bill with review and the Magistrate's check.

More of the flow — the journal, the matter store, the director's own
stories — is in [`docs/flows/simulation.md`](flows/simulation.md).

## 7. The UI horizon

The scenario catalog (`polis sim steps --json`) and the lifecycle
commands above are the contract the future TUI (0062) and Web UI (0063)
will render: browse the user vocabulary, author/submit a scenario, watch
the scoreboard, resume.
