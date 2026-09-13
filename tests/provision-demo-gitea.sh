#!/usr/bin/env bash
# Gitea-platform provisioning demo (task 0037): a phase-1 sim hosted on
# gitea — up → a namespaced citizen clones and reads the founding corpus
# → slice carries the gitea product + token → status → teardown → nothing
# remains. Phase stays 1 (the federation's procedure is unchanged by the
# product it runs on).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SIM="prov-gitea-01"
WORK="$(mktemp -d "${TMPDIR:-/tmp}/polis-prov-gitea.XXXXXX")"

say() { printf '\n\033[1m== %s ==\033[0m\n' "$*"; }
cleanup() {
  say "cleanup (best effort)"
  (cd "$ROOT" && uv run polis provision destroy "$SIM" --yes) > /dev/null 2>&1 || true
  rm -rf "$WORK" "$ROOT/data/sims/$SIM"
  echo "cleanup done"
}
trap cleanup EXIT

cd "$ROOT"

say "provision up $SIM --platform gitea"
uv run polis provision up "$SIM" --platform gitea

say "verify: a namespaced citizen can clone her city archive and read the founding corpus"
TOKEN=$(uv run python - <<'EOF'
import json
s = json.load(open("data/sims/prov-gitea-01/cities/cogswich.json"))
p = next(p for p in s["citizens"] if p["username"] == "m.grimsbane")
print(p["credentials"]["api_tokens"]["gitea"])
EOF
)
PORT=$(python3 -c "import json; print(json.load(open('data/sims/$SIM/secrets.json'))['proxy_port'])")
git clone -q "http://$TOKEN@localhost:$PORT/gitea/$SIM-cogswich/common-law.git" "$WORK/cogswich"
test -f "$WORK/cogswich/constitution/01-foundation.md" \
  && echo "  founding corpus present in the city archive"
test -f "$WORK/cogswich/constitution/02-customary-machinery.md" \
  && echo "  phase 1 recorded at the founding (Article 3)"
grep -q "one common law" "$WORK/cogswich/constitution/01-foundation.md" \
  && echo "  constitution reads correctly"

say "verify: the sim slice points at the gitea product and stays in phase 1"
uv run python - <<'EOF'
import json
s = json.load(open("data/sims/prov-gitea-01/cities/cogswich.json"))
sec = json.load(open("data/sims/prov-gitea-01/secrets.json"))
port = sec["proxy_port"]
assert s["federation"]["phase"] == 1, s["federation"]
assert s["federation"]["platform"] == "gitea", s["federation"]
assert s["git"]["remotes"]["origin"] == f"http://host.containers.internal:{port}/gitea/prov-gitea-01-cogswich/common-law.git", s["git"]["remotes"]
grim = next(c for c in s["citizens"] if c["username"] == "m.grimsbane")
assert grim["credentials"]["api_tokens"]["gitea"], "slice citizen has no gitea token"
assert "gogs" not in grim["credentials"]["api_tokens"], "slice should not carry a gogs token"
print("  slice product, remotes and tokens ok")
EOF

say "verify: the front proxy serves gitea under its path"
uv run python - <<'EOF'
import json
import httpx
s = json.load(open("data/sims/prov-gitea-01/secrets.json"))
port = s["proxy_port"]
r = httpx.get(f"http://localhost:{port}/gitea/", timeout=10)
assert r.status_code in (200, 302), r.status_code
print("  gitea reachable through the sim proxy on its path")
EOF

say "provision status $SIM"
uv run polis provision status "$SIM" > /dev/null && echo "  all inventory items present"

say "idempotency: a second up --force reconciles without duplication"
uv run polis provision up "$SIM" --platform gitea --force > /dev/null
echo "  re-provision ok"

say "provision teardown $SIM"
uv run polis provision teardown "$SIM" --yes

say "verify nothing remains"
if uv run polis provision status "$SIM" > /dev/null 2>&1; then
  echo "FAIL: resources remain after teardown"; exit 1
else
  echo "  no provisioned resources remain"
fi

say "GITEA PROVISION DEMO PASSED"
