#!/usr/bin/env bash
# Scenario-authoring demo (task 0060): a user scenario from scenarios/ is
# submitted to a running sim and serviced by the director to completion —
# the submit -> drive -> done path, with every beat accounted for.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SIM="scen-demo-01"

say() { printf '\n\033[1m== %s ==\033[0m\n' "$*"; }
cleanup() {
  say "cleanup (best effort)"
  (cd "$ROOT" && uv run polis provision destroy "$SIM" --yes) > /dev/null 2>&1 || true
  rm -rf "$ROOT/data/sims/$SIM"
  echo "cleanup done"
}
trap cleanup EXIT

cd "$ROOT"
export POLIS_PROVISIONED_SIM="$SIM"

say "provision the sim"
uv run polis provision up "$SIM" > /dev/null

say "start the run (fisheries seed)"
uv run polis sim new --situation data/world/legal/norms/fisheries.yaml --seed fixed-scen-1

say "the vocabulary a scenario author sees"
uv run polis sim steps --scope user

say "submit scenarios/northern-banks-quota.feature"
uv run polis sim submit scenarios/northern-banks-quota.feature

say "drive: one action beat per step, the federation's stories around it"
uv run polis sim drive --steps 3

say "verify: the scenario reached done with every beat executed/passed"
uv run python - <<EOF
import json
from pathlib import Path

states = list((Path("data/sims/$SIM") / "queues").glob("*.state.json"))
assert states, "no scenario state found"
for p in states:
    st = json.loads(p.read_text())
    print(f"  {st['slug']}: {st['status']}")
    for b in st["beats"]:
        print(f"    {b['status']:9} {b['text'][:70]}")
    assert st["status"] == "done", f"{st['slug']} is {st['status']}: {st.get('error')}"
    bad = [b for b in st["beats"] if b["status"] not in ("executed", "passed", "skipped")]
    assert not bad, bad
print("  the scenario completed on a live sim")
EOF

say "SCENARIOS DEMO PASSED"
