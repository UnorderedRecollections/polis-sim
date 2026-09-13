#!/usr/bin/env bash
# Bring the whole apparatus up via docker compose (or podman-compose).
set -euo pipefail
source "$(dirname "$0")/env.sh"

cd "$DOCKER_DIR"
if [[ "$CONTAINER_RUNTIME_NAME" == "docker" ]] && docker compose version > /dev/null 2>&1; then
  docker compose --env-file "$ROOT/.env" up -d --build
elif command -v podman-compose > /dev/null; then
  podman-compose --env-file "$ROOT/.env" up -d --build
elif command -v podman > /dev/null && podman compose version > /dev/null 2>&1; then
  podman compose --env-file "$ROOT/.env" up -d --build
else
  die "no compose provider for $CONTAINER_RUNTIME_NAME — install docker compose or podman-compose, or use the per-service scripts"
fi
