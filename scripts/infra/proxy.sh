#!/usr/bin/env bash
# Run the dev rig's front proxy (task 0042): the only container publishing
# an HTTP port (10800). Routes /gogs, /gitea, /ci to the services on the
# gogs-local network. The sims run their own per-sim proxies.
set -euo pipefail
source "$(dirname "$0")/env.sh"

say "build proxy image"
podman build -t polis/caddy "$DOCKER_DIR/caddy"

say "run proxy"
podman rm -f proxy 2>/dev/null || true
require_network
podman run -d \
  --restart unless-stopped \
  --name proxy \
  --network "$NETWORK" \
  -p 10800:10800 \
  -v "$DOCKER_DIR/caddy/Caddyfile.dev:/etc/caddy/Caddyfile:ro" \
  polis/caddy
