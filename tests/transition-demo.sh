#!/usr/bin/env bash
# Phase-transition demo (task 0038): on a gitea-hosted sim, `sim transition`
# enacts the three codified-machinery acts through the customary procedure;
# the third ratification flips the federation to phase 2 (situation +
# registry + slices). Then a real phase-2 legislative flow runs: petitions
# are gitea issues, bills are PRs, ratification merges via the platform.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SIM="tran-demo-01"
WORLD="$ROOT/data/world/world.json"
WORK="$(mktemp -d "${TMPDIR:-/tmp}/polis-tran.XXXXXX")"

say() { printf '\n\033[1m== %s ==\033[0m\n' "$*"; }
cleanup() {
  say "cleanup (best effort)"
  (cd "$ROOT" && uv run polis provision destroy "$SIM" --yes) > /dev/null 2>&1 || true
  rm -rf "$WORK" "$ROOT/data/sims/$SIM"
  # the transition flips the CIVIL REGISTRY (world.json) — restore it
  cp "$WORK/world-backup.json" "$WORLD" 2>/dev/null || true
  echo "cleanup done"
}
trap cleanup EXIT

cd "$ROOT"
# the transition is a one-time event — the demo starts from phase 1
uv run python -c "from polis import store; w = store.load_world(); w.federation.phase = 1; store.save_world(w)"
cp "$WORLD" "$WORK/world-backup.json"
export POLIS_PROVISIONED_SIM="$SIM"

say "provision up $SIM --platform gitea"
uv run polis provision up "$SIM" --platform gitea > /dev/null

say "bootstrap the run"
uv run polis sim new --situation data/world/legal/norms/fisheries.yaml --seed fixed-tran-1

say "enact the transition"
uv run polis sim transition

say "verify: the registry, slices and situation record phase 2"
uv run python - <<'EOF'
import json
from pathlib import Path
w = json.load(open("data/world/world.json"))
assert w["federation"]["phase"] == 2, w["federation"]
for sp in Path("data/sims/tran-demo-01/cities").glob("*.json"):
    s = json.loads(sp.read_text())
    assert s["federation"]["phase"] == 2, sp
    assert s["federation"]["platform"] == "gitea", sp
sit = open("data/sims/tran-demo-01/situation.yaml").read()
assert "phase: 2" in sit, sit
print("  phase 2 recorded everywhere")
EOF

say "verify: the three acts and their instruments are in the corpus"
git -C data/sims/tran-demo-01/common-law fetch origin main > /dev/null 2>&1 || true
for f in constitution/assigned-legal-authority-act.md \
         constitution/constitutional-approval-act.md \
         constitution/mechanical-magistracy-act.md \
         constitution/branch-protection.md \
         CODEOWNERS woodpecker.yml; do
  git -C data/sims/tran-demo-01/common-law cat-file -e "main:$f" 2>/dev/null \
    && echo "  corpus: $f" || { echo "FAIL: $f missing from the corpus"; exit 1; }
done
git -C data/sims/tran-demo-01/common-law show "main:constitution/assigned-legal-authority-act.md" \
  | grep -q "status: enacted" && echo "  acts flipped to enacted"

say "verify: the edition is promulgated"
uv run python - <<'EOF'
import json, httpx
s = json.load(open("data/sims/tran-demo-01/secrets.json"))
port = s["gitea_port"]
c = httpx.Client(base_url=f"http://localhost:{port}",
                 headers={"Authorization": f"token {s['admin_token']}"}, timeout=10)
tags = c.get("/api/v1/repos/tran-demo-01-archive/common-law/tags").json()
assert any(t["name"] == "codified-machinery" for t in tags), tags
print("  tag codified-machinery lodged in the federal archive")
EOF

say "verify: the story is recorded"
uv run python - <<'EOF'
import json
stories = json.load(open("data/sims/tran-demo-01/stories.json"))
t = [s for s in stories if s["template"] == "phase_transition"]
assert t and t[-1]["status"] == "enacted", t
print("  phase_transition story enacted")
EOF

say "phase 2: a citizen files a petition — a real gitea issue"
PETITION=$(uv run polis docket file --as m.grimsbane --city cogswich \
  --title "Phase-2 petition about the northern banks" \
  --body "The codified docket hears this grievance." | sed 's/.*#\([0-9]*\).*/\1/')
echo "  petition: #$PETITION"
uv run python - <<EOF
import json, httpx
s = json.load(open("data/sims/tran-demo-01/secrets.json"))
port = s["gitea_port"]
c = httpx.Client(base_url=f"http://localhost:{port}",
                 headers={"Authorization": f"token {s['admin_token']}"}, timeout=10)
issues = c.get("/api/v1/repos/tran-demo-01-archive/common-law/issues",
               params={"state": "open", "type": "issues"}).json()
assert any(i["title"].startswith("Phase-2 petition") for i in issues), issues
print("  the petition is a real issue on the federal archive")
EOF

say "phase 2: a bill becomes a real PR"
uv run polis bill draft --as m.grimsbane --city cogswich \
  --title "Northern Banks Codified Access Act" --kind act --into municipal/cogswich > /dev/null
uv run polis bill amend bill/northern-banks-codified-access-act --as m.grimsbane --city cogswich \
  --file municipal/cogswich/northern-banks-codified-access-act.md \
  --justification "Lodging the draft for the codified procedure." > /dev/null
uv run polis bill introduce bill/northern-banks-codified-access-act --as m.grimsbane --city cogswich \
  --title "Northern Banks Codified Access Act" --body "A phase-2 petition for incorporation." \
  --answering "$PETITION" > /dev/null
uv run python - <<'EOF'
import json, httpx
s = json.load(open("data/sims/tran-demo-01/secrets.json"))
port = s["gitea_port"]
c = httpx.Client(base_url=f"http://localhost:{port}",
                 headers={"Authorization": f"token {s['admin_token']}"}, timeout=10)
prs = c.get("/api/v1/repos/tran-demo-01-archive/common-law/pulls",
            params={"state": "open"}).json()
assert any("northern-banks-codified-access" in (p.get("head") or {}).get("ref", "") for p in prs), prs
print("  the bill is a real PR against the federal archive")
EOF

say "phase 2: scrutiny and ratification through the platform"
uv run polis bill scrutinize bill/northern-banks-codified-access-act --as b.grimsbane --city hushpoole \
  --verdict approve --body "Consistent with the codified procedure." > /dev/null
uv run polis bill ratify bill/northern-banks-codified-access-act --as e.vexley --city cogswich > /dev/null
uv run python - <<'EOF'
import json, httpx
s = json.load(open("data/sims/tran-demo-01/secrets.json"))
port = s["gitea_port"]
c = httpx.Client(base_url=f"http://localhost:{port}",
                 headers={"Authorization": f"token {s['admin_token']}"}, timeout=10)
r = c.get("/api/v1/repos/tran-demo-01-archive/common-law/contents/"
          "municipal%2Fcogswich%2Fnorthern-banks-codified-access-act.md")
assert r.status_code == 200, r.text[:200]
print("  the act entered the corpus through the platform merge")
prs = c.get("/api/v1/repos/tran-demo-01-archive/common-law/pulls",
            params={"state": "open"}).json()
assert not any("northern-banks-codified-access" in (p.get("head") or {}).get("ref", "") for p in prs)
print("  the PR is merged and closed")
EOF

say "TRANSITION DEMO PASSED"
