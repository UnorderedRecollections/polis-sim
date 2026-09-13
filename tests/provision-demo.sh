#!/usr/bin/env bash
# Provisioning demo (task 0021): up → a namespaced citizen clones and reads
# the founding corpus → status → teardown → nothing remains.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SIM="prov-demo-01"
WORK="$(mktemp -d "${TMPDIR:-/tmp}/polis-prov.XXXXXX")"

say() { printf '\n\033[1m== %s ==\033[0m\n' "$*"; }
cleanup() {
  say "cleanup (best effort)"
  (cd "$ROOT" && uv run polis provision teardown "$SIM" --yes) > /dev/null 2>&1 || true
  rm -rf "$WORK" "$ROOT/data/sims/$SIM"
  echo "cleanup done"
}
trap cleanup EXIT

cd "$ROOT"

say "provision up $SIM"
uv run polis provision up "$SIM"

say "verify: a namespaced citizen can clone her city archive and read the founding corpus"
TOKEN=$(uv run python - <<'EOF'
import json
s = json.load(open("data/sims/prov-demo-01/cities/cogswich.json"))
p = next(p for p in s["citizens"] if p["username"] == "m.grimsbane")
print(p["credentials"]["api_tokens"]["gogs"])
EOF
)
PORT=$(python3 -c "import json; print(json.load(open('data/sims/$SIM/secrets.json'))['proxy_port'])")
git clone -q "http://$TOKEN@localhost:$PORT/gogs/$SIM-cogswich/common-law.git" "$WORK/cogswich"
test -f "$WORK/cogswich/constitution/01-foundation.md" \
  && echo "  founding corpus present in the city archive"
grep -q "one common law" "$WORK/cogswich/constitution/01-foundation.md" \
  && echo "  constitution reads correctly"
ls "$WORK/cogswich/municipal/cogswich/README.md" > /dev/null \
  && echo "  municipal layout present"

say "verify: the sim slice points at namespaced remotes and carries the token"
uv run python - <<'EOF'
import json
s = json.load(open("data/sims/prov-demo-01/cities/cogswich.json"))
sec = json.load(open("data/sims/prov-demo-01/secrets.json"))
port = sec["proxy_port"]
assert s["git"]["remotes"]["origin"] == f"http://host.containers.internal:{port}/gogs/prov-demo-01-cogswich/common-law.git", s["git"]["remotes"]
assert s["git"]["remotes"]["upstream"] == f"http://host.containers.internal:{port}/gogs/prov-demo-01-archive/common-law.git"
grim = next(c for c in s["citizens"] if c["username"] == "m.grimsbane")
assert grim["credentials"]["api_tokens"]["gogs"], "slice citizen has no token"
fed = next(c for c in s["citizens"] if c["username"] == "e.vexley")
print("  slice remotes and tokens ok")
EOF

say "verify: the front proxy is the only published entrypoint"
uv run python - <<'EOF'
import json
import httpx
s = json.load(open("data/sims/prov-demo-01/secrets.json"))
port = s["proxy_port"]
assert httpx.get(f"http://localhost:{port}/gogs/", timeout=10).status_code in (200, 302)
assert s["platform"] == "gogs"
print("  gogs reachable through the sim proxy on its path")
EOF

say "provision status $SIM"
uv run polis provision status "$SIM" > /dev/null && echo "  all inventory items present"

say "idempotency: a second up --force reconciles without duplication"
PORT_BEFORE=$(python3 -c "import json; print(json.load(open('data/sims/$SIM/secrets.json'))['proxy_port'])")
uv run polis provision up "$SIM" --force > /dev/null
PORT_AFTER=$(python3 -c "import json; print(json.load(open('data/sims/$SIM/secrets.json'))['proxy_port'])")
[[ "$PORT_BEFORE" == "$PORT_AFTER" ]] && echo "  re-provision ok (proxy port persisted: $PORT_AFTER)"

say "provision teardown $SIM"
uv run polis provision teardown "$SIM" --yes

say "verify nothing remains"
if uv run polis provision status "$SIM" > /dev/null 2>&1; then
  echo "FAIL: resources remain after teardown"; exit 1
else
  echo "  no provisioned resources remain"
fi

say "PROVISION DEMO PASSED"
