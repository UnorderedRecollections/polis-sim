#!/usr/bin/env bash
# Director demo (task 0024): provision a sim, then let the director drive
# two full stories end-to-end through the operator container — assert the
# matters ratified, the situation evolved, the journal anchors chain, and
# the archive's git history carries the enactment merges.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SIM="dir-demo-01"
set -a; source "$ROOT/.env"; set +a
# the demo drives phase-1 stories — pin the registry to phase 1 (the
# transition demo flips it; this one must not inherit that)
(cd "$ROOT" && uv run python -c "from polis import store; w = store.load_world(); w.federation.phase = 1; store.save_world(w)")
sim_gogs() {  # the sim's own gogs (available after provisioning)
  python3 -c "import json; print(json.load(open('$ROOT/data/sims/$SIM/secrets.json'))['gogs_url_external'])"
}

say() { printf '\n\033[1m== %s ==\033[0m\n' "$*"; }
cleanup() {
  say "cleanup"
  (cd "$ROOT" && uv run polis provision teardown "$SIM" --yes >/dev/null 2>&1 || true)
  rm -rf "$ROOT/data/sims/$SIM"   # the sim's whole world, platform volumes included
  echo "cleanup done"
}
trap cleanup EXIT

say "provision the sim (users, repos, slices, operator container)"
(cd "$ROOT" && uv run polis provision up "$SIM")

say "start the run (situation = fisheries seed)"
(cd "$ROOT" && uv run polis sim new "$SIM" \
  --situation "$ROOT/data/world/legal/norms/fisheries.yaml")

say "drive two stories"
(cd "$ROOT" && uv run polis sim drive "$SIM" --steps 2)

say "assert: stories, situation, journal, archive history"
(cd "$ROOT" && SIM="$SIM" GOGS="$(sim_gogs)" uv run python - <<'PY'
import json, os, subprocess, tempfile
from pathlib import Path
from polis.sim.director import load_stories
from polis.sim.journal import Journal
from polis.sim.norms import load_norm_file

sim = os.environ["SIM"]
rd = Path("data/sims") / sim

stories = load_stories(sim)
assert len(stories) == 2, f"expected 2 stories, got {len(stories)}"
assert all(s.status == "enacted" for s in stories), [s.status for s in stories]
assert all(s.matter for s in stories), "every story produced a matter"

# situation: two new statutory norms (either may itself be superseded by the
# next story — oscillation is a true story), each a valid rule form
ns = load_norm_file(rd / "situation.yaml")
statutory = [n for n in ns.norms if n.source == "statute"]
assert len(statutory) == 2, f"expected 2 new statutory norms, got {len(statutory)}"
assert any(n.status == "in_force" for n in statutory)
import yaml
jdata = yaml.safe_load(open("data/world/legal/jurisdictions/fisheries.yaml"))
assert all(n.rule_form in jdata["rule_forms"] for n in statutory)
assert all(n.source_ref for n in statutory), "statutes cite their matter"
for s in stories:
    assert s.bindings["remedy"] in jdata["rule_forms"]

# journal: the anchors chain (each ratify's main_before == previous main_after)
entries = Journal(sim).entries()
ratifies = [e for e in entries if e.action == "bill.ratify"]
assert len(ratifies) == 2, f"expected 2 ratifications, got {len(ratifies)}"
assert ratifies[0].anchors["main_after"] == ratifies[1].anchors["main_before"], \
    "journal anchors do not chain"
assert ratifies[0].anchors["main_before"] != ratifies[0].anchors["main_after"]
story_anchors = [e for e in entries if e.kind == "anchor" and e.action == "story"]
assert len(story_anchors) == 2, "each story must close with a story anchor"

# the archive's git history carries two enactment merges
with tempfile.TemporaryDirectory() as tmp:
    subprocess.run(["git", "clone", "-q",
                    f"{os.environ['GOGS']}/{sim}-archive/common-law.git", tmp],
                   check=True)
    log = subprocess.run(["git", "-C", tmp, "log", "--merges", "--oneline"],
                         capture_output=True, text=True, check=True).stdout
    merges = [l for l in log.splitlines() if l.strip()]
    assert len(merges) == 2, f"expected 2 enactment merges, got {len(merges)}: {log}"

print(f"stories: {[s.id + ':' + s.status for s in stories]}")
print(f"statutory norms: {[n.id + '=' + n.rule_form + '(' + n.status + ')' for n in statutory]}")
print("anchors chain; 2 enactment merges in the archive")
PY
)

say "the narrated record"
(cd "$ROOT" && uv run polis sim present "$SIM" --last 6)

say "DIRECTOR DEMO PASSED"
