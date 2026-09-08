#!/usr/bin/env bash
# Build and run the shared postgres (backing store for gogs + gitea).
set -euo pipefail
source "$(dirname "$0")/env.sh"

say "build postgres image"
podman build -t polis/postgres "$DOCKER_DIR/postgres"

say "run postgres-gogs"
podman rm -f postgres-gogs 2>/dev/null || true
require_network
podman run -d \
  --restart unless-stopped \
  --name postgres-gogs \
  --network "$NETWORK" \
  -v "$DATA_DIR/postgres:/var/lib/postgresql/data" \
  -e POSTGRES_USER=gogs \
  -e POSTGRES_PASSWORD="${POSTGRES_PASSWORD:?set POSTGRES_PASSWORD in .env}" \
  -e POSTGRES_DB=gogs \
  polis/postgres
