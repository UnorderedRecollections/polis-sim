#!/usr/bin/env bash
# Bring the compose stack down (data in ../.state is preserved).
set -euo pipefail
source "$(dirname "$0")/env.sh"

cd "$DOCKER_DIR"
if command -v docker > /dev/null && docker compose version > /dev/null 2>&1; then
  docker compose down
elif command -v podman-compose > /dev/null; then
  podman-compose down
else
  die "neither 'docker compose' nor 'podman-compose' available"
fi
