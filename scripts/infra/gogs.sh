#!/usr/bin/env bash
# Build and run gogs — the phase-1 platform (customary machinery), behind
# the dev-rig front proxy (task 0042): no HTTP port of its own; reach it at
# http://localhost:10800/gogs/ (or the canonical name with the hosts entry).
# The app.ini is written once, with the canonical EXTERNAL_URL.
# Note: repo creation with auto_init fails on this build; create repos with
# auto_init=false and push a seed commit. This build has NO pulls API.
set -euo pipefail
source "$(dirname "$0")/env.sh"

INI="$DATA_DIR/gogs/gogs/conf/app.ini"
if [[ ! -f "$INI" ]]; then
  say "write gogs app.ini (canonical URL = the dev-rig proxy)"
  mkdir -p "$(dirname "$INI")"
  cat > "$INI" <<EOF
[database]
TYPE     = postgres
HOST     = postgres-gogs:5432
NAME     = gogs
USER     = gogs
PASSWORD = ${POSTGRES_PASSWORD:?set POSTGRES_PASSWORD in .env}
SSL_MODE = disable

[security]
INSTALL_LOCK = true
SECRET_KEY   = $(openssl rand -hex 16)

[server]
DOMAIN       = host.containers.internal
HTTP_PORT    = 3000
EXTERNAL_URL = http://host.containers.internal:${PROXY_PORT}/gogs/
DISABLE_SSH  = true

[repository]
DEFAULT_BRANCH = main

[service]
DISABLE_REGISTRATION = true

[email]
ENABLED = false
EOF
elif ! grep -q "host.containers.internal:${PROXY_PORT}" "$INI"; then
  echo "note: $INI does not point at the dev-rig proxy — update EXTERNAL_URL" \
       "to http://host.containers.internal:${PROXY_PORT}/gogs/ for correct links" >&2
fi

say "build gogs image"
podman build -t polis/gogs "$DOCKER_DIR/gogs"

say "run gogs"
podman rm -f gogs 2>/dev/null || true
require_network
podman run -d \
  --restart unless-stopped \
  --name gogs \
  --network "$NETWORK" \
  -v "$DATA_DIR/gogs:/data" \
  polis/gogs

ensure_proxy
say "gogs is behind the proxy: http://localhost:${PROXY_PORT}/gogs/"
