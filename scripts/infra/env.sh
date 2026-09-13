# Shared helpers for infra scripts. Source this; do not execute.
# Loads secrets from the project .env (process env always wins).

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DATA_DIR="$ROOT/.state"
DOCKER_DIR="$ROOT/docker"
NETWORK="gogs-local"
PROXY_PORT="${POLIS_PROXY_PORT:-10800}"

if [[ -f "$ROOT/.env" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "$ROOT/.env"
  set +a
fi

die() { printf '\033[1;31merror:\033[0m %s\n' "$*" >&2; exit 1; }
say() { printf '\n\033[1m== %s ==\033[0m\n' "$*"; }

require_network() {
  podman network exists "$NETWORK" || podman network create "$NETWORK" > /dev/null
}

ensure_proxy() {
  if ! podman container exists proxy > /dev/null 2>&1; then
    "$ROOT/scripts/infra/proxy.sh" > /dev/null
  elif ! podman container running proxy > /dev/null 2>&1; then
    podman start proxy > /dev/null
  fi
}
