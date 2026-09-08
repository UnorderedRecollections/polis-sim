# Shared helpers for infra scripts. Source this; do not execute.
# Loads secrets from the project .env (process env always wins).

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DATA_DIR="$ROOT/.state"
DOCKER_DIR="$ROOT/docker"
NETWORK="gogs-local"

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
