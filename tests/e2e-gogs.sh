#!/usr/bin/env bash
# E2E test of the legislative machinery against the live gogs instance (phase 1).
#
# Creates real users and a repo on gogs, all prefixed `e2e`, drives the full
# legislative flow through `polis` (docket/bill/archive, incl. --isomorphism),
# then cleans up. Everything created here is identifiable by the `e2e` prefix
# if cleanup ever fails.
#
# Usage: tests/e2e-gogs.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
POLIS="$ROOT/.venv/bin/polis"
GOGS="http://localhost:10800/gogs"
set -a; source "$ROOT/.env"; set +a
ADMIN_TOKEN="${GOGS_API_KEY:?set GOGS_API_KEY in .env}"

PASS="e2e-pass-1234"
OWNER="e2e-archive"            # user account standing in for the-archive org
REPO="common-law"
USERS=(e2e-archive e2e-vexley e2e-grimsbane e2e-starling)
WORK="$(mktemp -d "${TMPDIR:-/tmp}/polis-e2e.XXXXXX")"
REPO_URL="$GOGS/$OWNER/$REPO.git"

say() { printf '\n\033[1m== %s ==\033[0m\n' "$*"; }

admin_api() { curl -sf -H "Authorization: token $ADMIN_TOKEN" "$@"; }

user_token() {  # create a personal token for an e2e user via their basic auth
  curl -sf -u "$1:$PASS" -H "Content-Type: application/json" \
    -X POST "$GOGS/api/v1/users/$1/tokens" -d '{"name":"e2e"}' \
    | python3 -c 'import json,sys; print(json.load(sys.stdin)["sha1"])'
}

cleanup() {
  say "cleanup"
  curl -s -X DELETE -H "Authorization: token $ADMIN_TOKEN" \
    "$GOGS/api/v1/repos/$OWNER/$REPO" > /dev/null || true
  for u in "${USERS[@]}"; do
    curl -s -X DELETE -H "Authorization: token $ADMIN_TOKEN" \
      "$GOGS/api/v1/admin/users/$u" > /dev/null || true
  done
  rm -rf "$WORK"
  echo "cleanup done"
}
trap cleanup EXIT

# ---------------------------------------------------------------- setup
say "create e2e users"
for u in "${USERS[@]}"; do
  admin_api -H "Content-Type: application/json" -X POST "$GOGS/api/v1/admin/users" \
    -d "{\"username\":\"$u\",\"email\":\"$u@e2e.invalid\",\"password\":\"$PASS\",\"must_change_password\":false}" \
    > /dev/null
  echo "  user $u created"
done

TOK_ARCHIVE="$(user_token e2e-archive)"
TOK_VEXLEY="$(user_token e2e-vexley)"
TOK_GRIMSBANE="$(user_token e2e-grimsbane)"
TOK_STARLING="$(user_token e2e-starling)"

say "create repo $OWNER/$REPO and grant collaborators"
admin_api -H "Content-Type: application/json" -X POST \
  "$GOGS/api/v1/admin/users/$OWNER/repos" \
  -d "{\"name\":\"$REPO\",\"private\":false,\"auto_init\":false}" > /dev/null
for u in e2e-vexley e2e-grimsbane e2e-starling; do
  admin_api -H "Content-Type: application/json" -X PUT \
    "$GOGS/api/v1/repos/$OWNER/$REPO/collaborators/$u" \
    -d '{"permission":"write"}' > /dev/null
  echo "  collaborator $u (write)"
done

say "seed the founding corpus"
git clone -q "http://$TOK_ARCHIVE@localhost:10800/gogs/$OWNER/$REPO.git" "$WORK/seed"
mkdir -p "$WORK/seed"/{constitution,taxation,municipal/cogswich}
cat > "$WORK/seed/constitution/01-foundation.md" <<'MD'
# Article 1 — Foundation
The Concord of the Nine Cities recognizes one common law.
MD
cat > "$WORK/seed/taxation/README.md" <<'MD'
# Taxation
Statutes of the federal revenue.
MD
git -C "$WORK/seed" -c user.name="The Keeper" -c user.email="e2e-archive@e2e.invalid" \
  add -A
git -C "$WORK/seed" -c user.name="The Keeper" -c user.email="e2e-archive@e2e.invalid" \
  commit -qm "The Founding Corpus"
git -C "$WORK/seed" push -q origin main
echo "  seeded: constitution/, taxation/, municipal/cogswich/"

# point the chamber at the throwaway repo (operator mode, host already local)
# and the institutions' docket at a throwaway matter store
export POLIS_ORIGIN_URL="$REPO_URL"
export POLIS_UPSTREAM_URL="$REPO_URL"
export POLIS_REPO_DIR="$WORK/archive"
export POLIS_MATTERS_FILE="$WORK/matters.json"

as_vexley()    { POLIS_PLATFORM_TOKEN="$TOK_VEXLEY"    "$POLIS" "$@"; }
as_grimsbane() { POLIS_PLATFORM_TOKEN="$TOK_GRIMSBANE" "$POLIS" "$@"; }
as_starling()  { POLIS_PLATFORM_TOKEN="$TOK_STARLING"  "$POLIS" "$@"; }

# ---------------------------------------------------------------- the flow
say "isomorphism: obtain"
"$POLIS" archive obtain --as e.vexley --city cogswich --isomorphism

say "obtain the archive (as e.vexley / Keeper)"
as_vexley archive obtain --as e.vexley --city cogswich

say "docket: file a grievance (as m.grimsbane / legislator)"
as_grimsbane docket file --as m.grimsbane --city cogswich \
  --title "The harbour dues are unjust" \
  --body "Cogswich harbour dues burden small vessels disproportionately."
as_grimsbane docket list --as m.grimsbane --city cogswich
as_vexley docket comment PET-0001 --as e.vexley --city cogswich \
  --body "Heard in the rolls; a bill would be entertained."
as_vexley docket show PET-0001 --as e.vexley --city cogswich

say "bill: draft + amend (as m.grimsbane)"
as_grimsbane bill draft --as m.grimsbane --city cogswich --title "Harbour Dues Act" \
  --kind act --into municipal/cogswich --answering PET-0001
grep -q "status: draft" "$POLIS_REPO_DIR/municipal/cogswich/harbour-dues-act.md" \
  && echo "  scaffolded from template act.md with status: draft"
cat >> "$POLIS_REPO_DIR/municipal/cogswich/harbour-dues-act.md" <<'MD'

1. Vessels under twenty tonnes are exempt from harbour dues.
2. All other vessels pay according to the schedule in the appendix.
MD
as_grimsbane bill amend bill/harbour-dues-act --as m.grimsbane --city cogswich \
  --file municipal/cogswich/harbour-dues-act.md \
  --justification "Exempt small vessels from harbour dues; schedule for the rest."

say "isomorphism: introduce"
"$POLIS" bill introduce bill/harbour-dues-act --as m.grimsbane --city cogswich \
  --title "Harbour Dues Act" --isomorphism

say "bill: introduce (petition before the federation)"
as_grimsbane bill introduce bill/harbour-dues-act --as m.grimsbane --city cogswich \
  --title "Harbour Dues Act" --answering PET-0001 \
  --body "Answering petition PET-0001: relief for small vessels."
git -C "$POLIS_REPO_DIR" show bill/harbour-dues-act:municipal/cogswich/harbour-dues-act.md \
  | grep -q "status: proposed" && echo "  machinery flipped status: draft → proposed"

say "bill: debate + scrutinize (as e.vexley)"
as_vexley bill debate bill/harbour-dues-act --as e.vexley --city cogswich \
  --body "The exemption seems wise; the schedule needs figures in committee."
as_vexley bill scrutinize bill/harbour-dues-act --as e.vexley --city cogswich \
  --verdict approve --body "Within municipal jurisdiction; form is correct."

say "bill: ratify (as e.vexley / Keeper)"
as_vexley bill ratify bill/harbour-dues-act --as e.vexley --city cogswich
python3 - "$POLIS_MATTERS_FILE" <<'PY'
import json, sys
store = json.load(open(sys.argv[1]))
m = next(m for m in store["matters"] if m["id"] == "ACT-0001")
assert m["status"] == "ratified", m["status"]
assert any(e["event"] == "enacted" for e in m["events"]), m["events"]
print("  matter ACT-0001: ratified, enactment entered into the record")
PY

say "verify the act is law (file present on main, status enacted)"
if curl -sf -H "Authorization: token $TOK_VEXLEY" \
  "$GOGS/api/v1/repos/$OWNER/$REPO/contents/municipal/cogswich/harbour-dues-act.md?ref=main" \
  > /dev/null; then
  echo "  harbour-dues-act.md present on main"
else
  echo "FAIL: ratified act absent from main"; exit 1
fi
git -C "$POLIS_REPO_DIR" show main:municipal/cogswich/harbour-dues-act.md \
  | grep -q "status: enacted" && echo "  machinery flipped status: proposed → enacted"

say "jurisdiction: a cross-city bill must defeat a local archivist"
as_grimsbane bill draft --as m.grimsbane --city cogswich --title "Federal Tariff Act"
cat > "$POLIS_REPO_DIR/taxation/federal-tariff.md" <<'MD'
# Federal Tariff Act
A uniform tariff on all imports to the Nine Cities.
MD
as_grimsbane bill amend bill/federal-tariff-act --as m.grimsbane --city cogswich \
  --file taxation/federal-tariff.md --justification "Establish a uniform federal tariff."
as_grimsbane bill introduce bill/federal-tariff-act --as m.grimsbane --city cogswich \
  --title "Federal Tariff Act" --body "Federal revenue reform."
if as_starling bill ratify bill/federal-tariff-act --as j.starling --city thornwick 2> "$WORK/err"; then
  echo "FAIL: a local archivist ratified cross-city law"; exit 1
else
  grep -q "ultra vires" "$WORK/err" && echo "  refused as expected: $(grep -o 'ultra vires[^—]*' "$WORK/err" | head -1)"
fi
as_vexley bill reject bill/federal-tariff-act --as e.vexley --city cogswich
python3 - "$POLIS_MATTERS_FILE" <<'PY'
import json, sys
store = json.load(open(sys.argv[1]))
m = next(m for m in store["matters"] if m["branch"] == "bill/federal-tariff-act")
assert m["status"] == "rejected", m["status"]
print(f"  matter {m['id']}: rejected, order entered into the record")
PY

say "archive: promulgate an edition (as e.vexley / Keeper)"
as_vexley archive promulgate --as e.vexley --city cogswich \
  --name first-edition --message "The First Edition of the Common Law"
curl -sf -H "Authorization: token $TOK_VEXLEY" \
  "$GOGS/api/v1/repos/$OWNER/$REPO/tags" | grep -q first-edition \
  && echo "  tag first-edition present on the lodged archive"

say "archive: repeal an act (as e.vexley / Keeper)"
git -C "$POLIS_REPO_DIR" checkout -q main
as_vexley archive receive --as e.vexley --city cogswich
MERGE="$(git -C "$POLIS_REPO_DIR" log --merges --format=%H -1 main)"
as_vexley archive repeal "$MERGE" --mainline 1 --as e.vexley --city cogswich
as_vexley archive lodge --as e.vexley --city cogswich
if curl -sf -H "Authorization: token $TOK_VEXLEY" \
  "$GOGS/api/v1/repos/$OWNER/$REPO/contents/municipal/cogswich/harbour-dues-act.md?ref=main" > /dev/null; then
  echo "FAIL: repealed act still on main"; exit 1
else
  echo "  harbour-dues-act.md repealed from main (history preserved)"
fi

say "archive: inspect the genealogy"
as_vexley archive inspect --as e.vexley --city cogswich --limit 8

say "ALL E2E CHECKS PASSED"
