#!/usr/bin/env bash
# Build and run the Woodpecker CI server + agent — the Mechanical
# Magistrate's engine room (phase 2). Runtime-neutral since task 0043: the
# agent's socket mount and flags come from env.sh's runtime helpers.
set -euo pipefail
source "$(dirname "$0")/env.sh"

say "build woodpecker images"
rt build -t polis/woodpecker-server "$DOCKER_DIR/woodpecker"
rt build -t polis/woodpecker-agent "$DOCKER_DIR/woodpecker-agent"

say "run woodpecker-server"
rt rm -f woodpecker-server 2>/dev/null || true
require_network
# shellcheck disable=SC2046  (flags are word-split on purpose)
rt run -d \
  --restart unless-stopped \
  --name woodpecker-server \
  --network "$NETWORK" \
  $(rt_host_alias_flags) \
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
rt rm -f woodpecker-agent 2>/dev/null || true
# shellcheck disable=SC2046  (flags are word-split on purpose)
rt run -d \
  --restart unless-stopped \
  --name woodpecker-agent \
  --network "$NETWORK" \
  $(rt_agent_flags) \
  $(rt_host_alias_flags) \
  -v "$DATA_DIR/woodpecker/agent/01:/etc/woodpecker" \
  -e WOODPECKER_SERVER="woodpecker-server:9000" \
  -e WOODPECKER_AGENT_SECRET="w00000d" \
  -e WOODPECKER_BACKEND_DOCKER_NETWORK="$NETWORK" \
  polis/woodpecker-agent
