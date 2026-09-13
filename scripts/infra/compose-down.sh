#!/usr/bin/env bash
# Bring the compose stack down (data in ../.state is preserved).
set -euo pipefail
source "$(dirname "$0")/env.sh"

cd "$DOCKER_DIR"
if [[ "$CONTAINER_RUNTIME_NAME" == "docker" ]] && docker compose version > /dev/null 2>&1; then
  docker compose down
elif command -v podman-compose > /dev/null; then
  podman-compose down
elif command -v podman > /dev/null && podman compose version > /dev/null 2>&1; then
  podman compose down
else
  die "no compose provider for $CONTAINER_RUNTIME_NAME"
fi
