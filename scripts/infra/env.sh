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

# --- the container runtime (task 0043): podman first, then docker ------------
if [[ -n "${POLIS_RUNTIME:-}" ]]; then
  CONTAINER_RUNTIME="$(command -v "$POLIS_RUNTIME" || true)"
else
  CONTAINER_RUNTIME="$(command -v podman || command -v docker || true)"
fi
[[ -n "$CONTAINER_RUNTIME" ]] \
  || die "no container runtime found — install podman or docker, or set POLIS_RUNTIME"
CONTAINER_RUNTIME_NAME="$(basename "$CONTAINER_RUNTIME")"

rt() { "$CONTAINER_RUNTIME" "$@"; }

rt_container_exists() { rt container inspect "$1" > /dev/null 2>&1; }
rt_container_running() {
  [[ "$(rt inspect -f '{{.State.Running}}' "$1" 2>/dev/null)" == "true" ]]
}
rt_network_exists() { rt network inspect "$1" > /dev/null 2>&1; }

rt_host_alias_flags() {
  # podman resolves host.containers.internal natively; docker needs the alias
  if [[ "$CONTAINER_RUNTIME_NAME" != "podman" ]]; then
    printf -- '--add-host host.containers.internal:host-gateway'
  fi
}

rt_socket_path() {
  if [[ -n "${POLIS_CONTAINER_SOCKET:-}" ]]; then
    printf '%s' "$POLIS_CONTAINER_SOCKET"
  elif [[ "$CONTAINER_RUNTIME_NAME" == "podman" ]]; then
    printf '/run/user/%s/podman/podman.sock' "$(id -u)"
  else
    printf '/var/run/docker.sock'
  fi
}

rt_agent_flags() {
  local socket
  socket="$(rt_socket_path)"
  if [[ "$CONTAINER_RUNTIME_NAME" == "podman" ]]; then
    # podman-machine on macOS: root maps to the VM's core user (socket
    # owner); label=disable or CoreOS SELinux denies the mount
    printf -- '--user 0:0 --security-opt label=disable -v %s:/var/run/docker.sock -e DOCKER_HOST=unix:///var/run/docker.sock' "$socket"
  else
    printf -- '-v %s:/var/run/docker.sock -e DOCKER_HOST=unix:///var/run/docker.sock' "$socket"
  fi
}

# compose interpolation needs these in the environment
POLIS_CONTAINER_SOCKET="$(rt_socket_path)"
export CONTAINER_RUNTIME CONTAINER_RUNTIME_NAME POLIS_CONTAINER_SOCKET

require_network() {
  rt_network_exists "$NETWORK" || rt network create "$NETWORK" > /dev/null
}

ensure_proxy() {
  if ! rt_container_exists proxy; then
    "$ROOT/scripts/infra/proxy.sh" > /dev/null
  elif ! rt_container_running proxy; then
    rt start proxy > /dev/null
  fi
}
