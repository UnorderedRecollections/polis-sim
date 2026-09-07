#!/usr/bin/env bash
# Bring the whole apparatus up via docker compose (or podman-compose).
set -euo pipefail
source "$(dirname "$0")/env.sh"

cd "$DOCKER_DIR"
if command -v docker > /dev/null && docker compose version > /dev/null 2>&1; then
  docker compose --env-file "$ROOT/.env" up -d --build
elif command -v podman-compose > /dev/null; then
  podman-compose --env-file "$ROOT/.env" up -d --build
else
  die "neither 'docker compose' nor 'podman-compose' available — use the per-service scripts instead"
fi
