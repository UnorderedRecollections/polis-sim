#!/usr/bin/env bash
# Build and run gogs — the phase-1 platform (customary machinery).
# Note: repo creation with auto_init fails on this build; create repos with
# auto_init=false and push a seed commit. This build has NO pulls API.
set -euo pipefail
source "$(dirname "$0")/env.sh"

say "build gogs image"
podman build -t polis/gogs "$DOCKER_DIR/gogs"

say "run gogs"
podman rm -f gogs 2>/dev/null || true
require_network
podman run -d \
  --restart unless-stopped \
  --name gogs \
  --network "$NETWORK" \
  -p 10022:2222 \
  -p 10880:3000 \
  -v "$DATA_DIR/gogs:/data" \
  polis/gogs
