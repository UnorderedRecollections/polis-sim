#!/usr/bin/env bash
# Build and run the Woodpecker CI server + agent — the Mechanical
# Magistrate's engine room (phase 2).
#
# Agent notes for podman-machine on macOS:
# - the podman socket must be the VM-internal rootless socket
#   (/run/user/501/...); the host-forwarded socket cannot be mounted
#   (virtiofs can't mount sockets);
# - --user 0:0: container root maps to the VM's core user, the socket owner;
# - --security-opt label=disable: CoreOS SELinux would otherwise deny access.
set -euo pipefail
source "$(dirname "$0")/env.sh"

say "build woodpecker images"
podman build -t polis/woodpecker-server "$DOCKER_DIR/woodpecker"
podman build -t polis/woodpecker-agent "$DOCKER_DIR/woodpecker-agent"

say "run woodpecker-server"
podman rm -f woodpecker-server 2>/dev/null || true
require_network
podman run -d \
  --restart unless-stopped \
  --name woodpecker-server \
  --network "$NETWORK" \
  -v "$DATA_DIR/woodpecker/server:/var/lib/woodpecker" \
  -e WOODPECKER_OPEN=true \
  -e WOODPECKER_HOST="http://host.containers.internal:${PROXY_PORT}/ci" \
  -e WOODPECKER_AGENT_SECRET="w00000d" \
  -e WOODPECKER_ADMIN="${GITEA_ADMIN_USERNAME:?set GITEA_ADMIN_USERNAME in .env}" \
  -e WOODPECKER_GITEA=true \
  -e WOODPECKER_GITEA_URL="http://host.containers.internal:${PROXY_PORT}/gitea" \
  -e WOODPECKER_DEV_GITEA_OAUTH_URL="http://host.containers.internal:${PROXY_PORT}/gitea" \
  -e WOODPECKER_EXPERT_FORGE_OAUTH_HOST="http://host.containers.internal:${PROXY_PORT}/gitea" \
  -e WOODPECKER_GITEA_CLIENT="${WOODPECKER_GITEA_CLIENT:?set WOODPECKER_GITEA_CLIENT in .env}" \
  -e WOODPECKER_GITEA_SECRET="${WOODPECKER_GITEA_SECRET:?set WOODPECKER_GITEA_SECRET in .env}" \
  polis/woodpecker-server

ensure_proxy
say "woodpecker is behind the proxy: http://localhost:${PROXY_PORT}/ci"

say "run woodpecker-agent"
podman rm -f woodpecker-agent 2>/dev/null || true
podman run -d \
  --restart unless-stopped \
  --name woodpecker-agent \
  --user 0:0 \
  --security-opt label=disable \
  --network "$NETWORK" \
  -v "$DATA_DIR/woodpecker/agent/01:/etc/woodpecker" \
  -v /run/user/501/podman/podman.sock:/var/run/docker.sock \
  -e DOCKER_HOST="unix:///var/run/docker.sock" \
  -e WOODPECKER_SERVER="woodpecker-server:9000" \
  -e WOODPECKER_AGENT_SECRET="w00000d" \
  -e WOODPECKER_BACKEND_DOCKER_NETWORK="$NETWORK" \
  polis/woodpecker-agent
