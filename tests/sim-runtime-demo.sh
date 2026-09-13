#!/usr/bin/env bash
# Demo of the runtime (task 0019): a full scenario driven through the
# enact() facade against a throwaway gogs repo, with a situation write-back
# and a journal that proves it all happened.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
GOGS="http://localhost:10800/gogs"
set -a; source "$ROOT/.env"; set +a
ADMIN_TOKEN="${GOGS_API_KEY:?}"

PASS="e2e-pass-1234"
OWNER="e2e-archive"
REPO="common-law"
USERS=(e2e-archive e2e-vexley e2e-grimsbane)
WORK="$(mktemp -d "${TMPDIR:-/tmp}/polis-sim.XXXXXX")"
REPO_URL="$GOGS/$OWNER/$REPO.git"
RUN="harbour-dues-demo"

say() { printf '\n\033[1m== %s ==\033[0m\n' "$*"; }
admin_api() { curl -sf -H "Authorization: token $ADMIN_TOKEN" "$@"; }
user_token() {
  curl -sf -u "$1:$PASS" -H "Content-Type: application/json" \
    -X POST "$GOGS/api/v1/users/$1/tokens" -d '{"name":"e2e"}' \
    | python3 -c 'import json,sys; print(json.load(sys.stdin)["sha1"])'
}
cleanup() {
  say "cleanup"
  curl -s -X DELETE -H "Authorization: token $ADMIN_TOKEN" "$GOGS/api/v1/repos/$OWNER/$REPO" >/dev/null || true
  for u in "${USERS[@]}"; do
    curl -s -X DELETE -H "Authorization: token $ADMIN_TOKEN" "$GOGS/api/v1/admin/users/$u" >/dev/null || true
  done
  rm -rf "$WORK" "$ROOT/data/sims/$RUN"
  echo "cleanup done"
}
trap cleanup EXIT

say "setup (users, repo, founding corpus)"
for u in "${USERS[@]}"; do
  admin_api -H "Content-Type: application/json" -X POST "$GOGS/api/v1/admin/users" \
    -d "{\"username\":\"$u\",\"email\":\"$u@e2e.invalid\",\"password\":\"$PASS\",\"must_change_password\":false}" > /dev/null
done
TOK_ARCHIVE="$(user_token e2e-archive)"
TOK_VEXLEY="$(user_token e2e-vexley)"
TOK_GRIMSBANE="$(user_token e2e-grimsbane)"
admin_api -H "Content-Type: application/json" -X POST "$GOGS/api/v1/admin/users/$OWNER/repos" \
  -d "{\"name\":\"$REPO\",\"private\":false,\"auto_init\":false}" > /dev/null
for u in e2e-vexley e2e-grimsbane; do
  admin_api -H "Content-Type: application/json" -X PUT \
    "$GOGS/api/v1/repos/$OWNER/$REPO/collaborators/$u" -d '{"permission":"write"}' > /dev/null
done
git clone -q "http://$TOK_ARCHIVE@${GOGS#http://}/$OWNER/$REPO.git" "$WORK/seed" 2>/dev/null
mkdir -p "$WORK/seed"/{constitution,fisheries,municipal/cogswich}
echo -e "# Article 1 — Foundation\nThe Concord of the Nine Cities recognizes one common law." \
  > "$WORK/seed/constitution/01-foundation.md"
git -C "$WORK/seed" -c user.name="The Keeper" -c user.email="e2e-archive@e2e.invalid" add -A
git -C "$WORK/seed" -c user.name="The Keeper" -c user.email="e2e-archive@e2e.invalid" \
  commit -qm "The Founding Corpus"
git -C "$WORK/seed" push -q origin main

export POLIS_ORIGIN_URL="$REPO_URL"
export POLIS_UPSTREAM_URL="$REPO_URL"
export POLIS_REPO_DIR="$WORK/archive"
export POLIS_MATTERS_FILE="$WORK/matters.json"

say "bootstrap the run (situation = fisheries seed)"
cp "$ROOT/data/world/legal/norms/fisheries.yaml" "$WORK/situation.yaml"
uv run --project "$ROOT" polis sim new "$RUN" --situation "$WORK/situation.yaml"

say "the scenario, through enact()"
TOK_GRIMSBANE="$TOK_GRIMSBANE" TOK_VEXLEY="$TOK_VEXLEY" RUN="$RUN" \
uv run --project "$ROOT" python - <<'PY'
import os
from polis.sim.runtime import Runtime, operator_chamber
from polis.sim.journal import Journal
from polis.sim.norms import Norm, NormObject, load_norm_file
from polis.legislation import archive as archive_mod
from pathlib import Path

run = os.environ["RUN"]
journal = Journal(run)
sit_path = journal.path.parent / "situation.yaml"
rt = Runtime(journal, load_norm_file(sit_path), sit_path)

grimsbane = operator_chamber("m.grimsbane", "cogswich")
grimsbane.token = os.environ["TOK_GRIMSBANE"]
vexley = operator_chamber("e.vexley", "cogswich")
vexley.token = os.environ["TOK_VEXLEY"]

# obtain the archive (raw plan via enact for the anchor)
rt.enact("e.vexley", "archive.obtain", archive_mod.obtain(vexley),
         params={}, chamber=vexley)

# a grievance enters the docket
rt.file_petition(grimsbane, "The banks are being fished out",
                 "Cogswich boats take everything; nothing for Brasshaven.")

# drafting and introduction of the remedy
rt.draft_bill(grimsbane, "Northern Banks Quota Act", kind="act", into="fisheries")
doc = Path(os.environ["POLIS_REPO_DIR"]) / "fisheries/northern-banks-quota-act.md"
assert doc.exists(), doc
rt.amend_bill(grimsbane, "bill/northern-banks-quota-act",
              ["fisheries/northern-banks-quota-act.md"],
              "Establish a quota over the Northern Banks, shared between the cities.")
res = rt.introduce_bill(grimsbane, "bill/northern-banks-quota-act",
                        "Northern Banks Quota Act", answering="PET-0001")
matter = res.entry.anchors["matter"]

# scrutiny and ratification, with the situation write-back
rt.scrutinize(vexley, "bill/northern-banks-quota-act", "approve",
              "A quota answers the grievance within fisheries custom.")
new_norm = Norm(id="N-0004", rule_form="quota",
                object=NormObject(kind="northern_banks", type="resource"),
                aspect="access_right", subjects=["fisher"],
                beneficiaries=["fisher"], source="statute", source_ref=matter)
rt.ratify(vexley, "bill/northern-banks-quota-act", new_norm=new_norm, supersedes="N-0001")

# assertions: situation evolved, journal holds the anchors
ns = load_norm_file(sit_path)
assert ns.get("N-0001").status == "superseded", ns.get("N-0001").status
assert ns.get("N-0004").status == "in_force" and ns.get("N-0004").source == "statute"
entries = rt.journal.entries()
actions = [e.action for e in entries]
assert actions == ["archive.obtain", "docket.file", "bill.draft", "bill.amend",
                   "bill.introduce", "bill.scrutinize", "bill.ratify"], actions
ratify = entries[-1]
assert ratify.anchors["main_before"] != ratify.anchors["main_after"]
assert ratify.anchors["situation"]["superseded"] == {"N-0001": "open_access"}
rt.observe("director", "quota in force", {"norm": "N-0004", "supersedes": "N-0001"})
print("scenario executed; situation evolved (open_access superseded by quota)")
PY

say "sim present — the narrated journal"
uv run --project "$ROOT" polis sim present "$RUN"

say "RUNTIME DEMO PASSED"
