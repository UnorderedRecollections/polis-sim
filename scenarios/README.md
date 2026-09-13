# Example scenarios

User-authored interventions for a **running** sim — the `scenarios/` tree
is the authored-content home of the driving use case (task 0060); the
`features/` tree is the software's tests. Read
[`docs/simulation-scenarios.md`](../docs/simulation-scenarios.md) first.

Submit one to a running sim (the sim id defaults to
`POLIS_PROVISIONED_SIM`):

```bash
uv run polis sim submit scenarios/northern-banks-quota.feature
uv run polis sim scenarios     # the scoreboard
uv run polis sim drive --steps 3
```

These files carry no test tags and no harness steps: submitted scenarios
use the **user** vocabulary only (`uv run polis sim steps --scope user`).
