#!/usr/bin/env bash
# The user/test vocabulary boundary (task 0059): the step catalog and the
# queue's submission validation — no sim, no containers.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

say() { printf '\n\033[1m== %s ==\033[0m\n' "$*"; }

say "the catalog"
uv run python - <<'EOF'
import json
import subprocess

out = subprocess.run(["uv", "run", "polis", "sim", "steps", "--json"],
                     capture_output=True, text=True, check=True).stdout
items = json.loads(out)
user = {i["form"] for i in items if i["scope"] == "user"}
test = {i["form"] for i in items if i["scope"] == "test"}

assert 'a petition of the <actor-kind>s of <city> about the <resource>' in user, sorted(user)
assert 'the Keeper ratifies it with remedy "<rule-form>" superseding "<norm-id>"' in user
assert 'the docket shows the petition is answered' in user
assert 'the federation codifies its machinery' in user

assert 'a provisioned sim seeded from "<jurisdiction>"' in test, sorted(test)
assert "the Mechanical Magistrate's CI is erected" in test
assert not (user & test), "a form appears in both scopes"
print(f"  {len(user)} user, {len(test)} test steps")
EOF

say "queue validation: harness beats rejected, user beats accepted"
uv run python - <<'EOF'
import tempfile
import textwrap
from pathlib import Path

from polis.sim import queue, scenario


def errors(text: str) -> list[str]:
    with tempfile.NamedTemporaryFile("w", suffix=".feature", delete=False) as f:
        f.write(textwrap.dedent(text))
        path = Path(f.name)
    return queue.validate(scenario.parse_feature(path))


bad_setup = errors("""\
    Feature: harness beat smuggled in
      Scenario: x
        Given a provisioned sim seeded from "fisheries"
        When the legislator drafts "Smuggled Act" into fisheries
    """)
assert bad_setup and "test-scoped" in bad_setup[0], bad_setup

bad_machinery = errors("""\
    Feature: infra beat smuggled in
      Scenario: x
        Given a petition of the fishers of cogswich about the northern banks
        Then the Mechanical Magistrate's CI is erected
    """)
assert bad_machinery and "test-scoped" in bad_machinery[0], bad_machinery

good = errors("""\
    Feature: a user scenario
      Scenario: x
        Given a petition of the fishers of cogswich about the northern banks
        When the legislator drafts "A Bill" into fisheries
        Then the docket shows the petition is answered
    """)
assert good == [], good
print("  harness beats rejected, user beats accepted")
EOF

say "BEAT SCOPES PASSED"
