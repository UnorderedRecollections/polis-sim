#!/usr/bin/env bash
# Build and run gitea — the phase-2 platform (codified machinery).
# Requires the shared postgres (scripts/infra/postgres.sh) to be running.
set -euo pipefail
source "$(dirname "$0")/env.sh"

say "build gitea image"
podman build -t polis/gitea "$DOCKER_DIR/gitea"

say "run gitea"
podman rm -f gitea 2>/dev/null || true
require_network
podman run -d \
  --name gitea \
  --network "$NETWORK" \
  -p 3001:3000 \
  -p 2222:22 \
  -e USER_UID=1000 \
  -e USER_GID=1000 \
  -e GITEA__database__DB_TYPE=postgres \
  -e GITEA__database__HOST=postgres-gogs:5432 \
  -e GITEA__database__NAME=gitea \
  -e GITEA__database__USER=gitea \
  -e GITEA__database__PASSWD=gitea \
  -v "$DATA_DIR/gitea:/data" \
  polis/gitea
