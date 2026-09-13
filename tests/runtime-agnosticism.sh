#!/usr/bin/env bash
# Runtime-agnosticism checks (task 0043): no docker needed — a stub docker
# CLI verifies DockerRuntime's command construction and quirks; PodmanRuntime
# is checked live (the dev machine's runtime).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

STUB_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/polis-rt.XXXXXX")"
STUB_DIR="$STUB_ROOT/bin"
LOG="$STUB_ROOT/docker.log"
mkdir -p "$STUB_DIR"
trap 'rm -rf "$STUB_ROOT"' EXIT

cat > "$STUB_DIR/docker" <<'STUB'
#!/usr/bin/env bash
printf '%s\n' "$*" >> "${DOCKER_STUB_LOG:?}"
case "$1 $2" in
  "image inspect") exit 1 ;;
  "network inspect") exit 0 ;;
  "info "*) exit 0 ;;
  "ps -a") echo "[]" ;;
  *) exit 0 ;;
esac
STUB
chmod +x "$STUB_DIR/docker"

say() { printf '\n\033[1m== %s ==\033[0m\n' "$*"; }

say "docker runtime (stub CLI — no docker required)"
DOCKER_STUB_LOG="$LOG" POLIS_RUNTIME=docker PATH="$STUB_DIR:$PATH" uv run python - <<'EOF'
from polis.clients import containers

try:
    containers.get_runtime("bogus")
    raise AssertionError("a bogus POLIS_RUNTIME was accepted")
except containers.ContainerError:
    pass

r = containers.get_runtime()
assert r.name == "docker", r.name
assert r.socket_path().endswith("/var/run/docker.sock"), r.socket_path()
joined = " ".join(r.agent_run_args())
assert "label=disable" not in joined, joined
assert "/var/run/docker.sock:/var/run/docker.sock" in joined, joined
assert r.runtime_state() == "running", r.runtime_state()
assert r.image_exists("polis/gogs") is False
assert r.network_exists("gogs-local") is True
r._run(["run", "-d", "--name", "probe", "img"])
print("  docker command construction ok")
EOF
grep -q -- "run --add-host host.containers.internal:host-gateway -d --name probe img" "$LOG" \
  && echo "  canonical host alias forced on docker run" \
  || { echo "  FAIL: docker run missing the canonical host alias"; exit 1; }
grep -q -- "image inspect polis/gogs" "$LOG" \
  && echo "  image probe uses docker image inspect" \
  || { echo "  FAIL: image probe has the wrong spelling"; exit 1; }

say "podman runtime (live, when present)"
if command -v podman > /dev/null; then
  POLIS_RUNTIME=podman uv run python - <<'EOF'
from polis.clients import containers
r = containers.get_runtime()
assert r.name == "podman", r.name
assert r.runtime_state() == "running", r.runtime_state()
assert r.image_exists("politest-nonexistent:latest") is False
assert "host.containers.internal" not in " ".join(r.host_alias_args())
joined = " ".join(r.agent_run_args())
assert "--user 0:0" in joined and "label=disable" in joined, joined
assert "/run/user/" in r.socket_path(), r.socket_path()
print("  podman quirks ok")
EOF
else
  echo "  podman absent — skipped"
fi

say "RUNTIME AGNOSTICISM PASSED"
