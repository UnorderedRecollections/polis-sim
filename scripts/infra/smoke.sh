#!/usr/bin/env bash
# Smoke tests for the apparatus. Usage:
#   scripts/infra/smoke.sh           — check every service
#   scripts/infra/smoke.sh gogs      — check one service
# Each check covers: container running, HTTP endpoint reachable, and the
# API key from .env authenticating. Exits non-zero on any failure.
set -uo pipefail
source "$(dirname "$0")/env.sh"

GOGS_URL="${POLIS_GOGS_URL:-http://localhost:10800/gogs}"
GITEA_URL="${POLIS_GITEA_URL:-http://localhost:10800/gitea}"
WOODPECKER_URL="${POLIS_WOODPECKER_URL:-http://localhost:10800/ci}"

FAILED=0
pass() { printf '  \033[32mok\033[0m   %s\n' "$*"; }
fail() { printf '  \033[31mFAIL\033[0m %s\n' "$*"; FAILED=1; }
check() { # name, command...
  local name="$1"; shift
  if "$@" > /dev/null 2>&1; then pass "$name"; else fail "$name"; fi
}

smoke_proxy() {
  say "proxy (port 10800 — the only HTTP entrypoint)"
  check "container running" rt_container_exists proxy
  check "gitea path reachable" curl -sf -o /dev/null http://localhost:10800/gitea/
  check "gogs path reachable" curl -sf -o /dev/null http://localhost:10800/gogs/
}

smoke_postgres() {
  say "postgres"
  check "container running" rt_container_exists postgres-gogs
  check "pg_isready" rt exec postgres-gogs pg_isready -U gogs
  check "database 'gogs' queryable" \
    rt exec postgres-gogs psql -U gogs -d gogs -tAc "SELECT 1"
  check "database 'gitea' queryable" \
    rt exec postgres-gogs psql -U gogs -d gitea -tAc "SELECT 1"
}

smoke_gogs() {
  say "gogs ($GOGS_URL)"
  check "container running" rt_container_exists gogs
  check "HTTP reachable" curl -sf -o /dev/null "$GOGS_URL/"
  [[ -n "${GOGS_API_KEY:-}" ]] || { fail "GOGS_API_KEY set in .env"; return; }
  check "GOGS_API_KEY authenticates" \
    curl -sf -o /dev/null -H "Authorization: token $GOGS_API_KEY" "$GOGS_URL/api/v1/user"
}

smoke_gitea() {
  say "gitea ($GITEA_URL)"
  check "container running" rt_container_exists gitea
  check "HTTP reachable" curl -sf -o /dev/null "$GITEA_URL/"
  [[ -n "${GITEA_API_KEY:-}" ]] || { fail "GITEA_API_KEY set in .env"; return; }
  check "GITEA_API_KEY authenticates" \
    curl -sf -o /dev/null -H "Authorization: token $GITEA_API_KEY" "$GITEA_URL/api/v1/user"
  check "GITEA_API_KEY has admin access" \
    curl -sf -o /dev/null -H "Authorization: token $GITEA_API_KEY" "$GITEA_URL/api/v1/admin/users"
}

_wp_healthz() { [[ "$(curl -s -o /dev/null -w '%{http_code}' "$WOODPECKER_URL/healthz")" == "204" ]]; }
_wp_agent_registered() {
  curl -sf -H "Authorization: Bearer $WOODPECKER_API_KEY" "$WOODPECKER_URL/api/agents" | grep -q '\[{'
}

smoke_woodpecker() {
  say "woodpecker ($WOODPECKER_URL)"
  check "server container running" rt_container_exists woodpecker-server
  check "agent container running" rt_container_exists woodpecker-agent
  check "healthz" _wp_healthz
  [[ -n "${WOODPECKER_API_KEY:-}" ]] || { fail "WOODPECKER_API_KEY set in .env"; return; }
  check "WOODPECKER_API_KEY authenticates" \
    curl -sf -o /dev/null -H "Authorization: Bearer $WOODPECKER_API_KEY" "$WOODPECKER_URL/api/user"
  check "an agent is registered" _wp_agent_registered
}

SERVICES=(proxy postgres gogs gitea woodpecker)
if [[ $# -gt 0 ]]; then
  for s in "$@"; do
    [[ " ${SERVICES[*]} " == *" $s "* ]] || die "unknown service '$s' (${SERVICES[*]})"
  done
  SERVICES=("$@")
fi
for s in "${SERVICES[@]}"; do "smoke_$s"; done

if [[ $FAILED -ne 0 ]]; then
  say "SMOKE TESTS FAILED"; exit 1
fi
say "ALL SMOKE TESTS PASSED"
