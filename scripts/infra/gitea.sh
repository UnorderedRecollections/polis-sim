#!/usr/bin/env bash
# Build and run gitea — the phase-2 platform (codified machinery), also a
# valid phase-1 host (task 0037). Requires the shared postgres
# (scripts/infra/postgres.sh) to be running.
#
# HEADLESS BOOTSTRAP (task 0040): no web installer. The admin identity
# comes from .env (GITEA_ADMIN_USERNAME/PASSWORD/EMAIL); the account is
# created with the `gitea admin user create` CLI and a full-scope token is
# minted and written back into .env as GITEA_API_KEY.
set -euo pipefail
source "$(dirname "$0")/env.sh"

GITEA_ADMIN_USERNAME="${GITEA_ADMIN_USERNAME:?set GITEA_ADMIN_USERNAME in .env (see .env.example)}"
GITEA_ADMIN_PASSWORD="${GITEA_ADMIN_PASSWORD:?set GITEA_ADMIN_PASSWORD in .env}"
GITEA_ADMIN_EMAIL="${GITEA_ADMIN_EMAIL:?set GITEA_ADMIN_EMAIL in .env}"

say "build gitea image"
podman build -t polis/gitea "$DOCKER_DIR/gitea"

say "ensure the gitea database exists"
# pg_isready turns true during postgres' temp bootstrap phase — retry the
# CREATE DATABASE (same race as the sim bring-up, task 0037).
for _ in $(seq 1 30); do
  if podman exec postgres-gogs psql -U gogs -tAc \
      "SELECT 1 FROM pg_database WHERE datname='gitea'" 2>/dev/null | grep -q 1; then
    break
  fi
  if podman exec postgres-gogs psql -U gogs -c "CREATE DATABASE gitea" > /dev/null 2>&1; then
    break
  fi
  sleep 1
done

say "run gitea"
mkdir -p "$DATA_DIR/gitea"
podman rm -f gitea 2>/dev/null || true
require_network
podman run -d \
  --restart unless-stopped \
  --name gitea \
  --network "$NETWORK" \
  -p 3001:3000 \
  -p 2222:22 \
  -e USER_UID=1000 \
  -e USER_GID=1000 \
  -e GITEA__database__DB_TYPE=postgres \
  -e GITEA__database__HOST=postgres-gogs:5432 \
  -e GITEA__database__NAME=gitea \
  -e GITEA__database__USER=gogs \
  -e GITEA__database__PASSWD="${POSTGRES_PASSWORD:?set POSTGRES_PASSWORD in .env}" \
  -e GITEA__security__INSTALL_LOCK=true \
  -e GITEA__security__ALLOWED_HOST_LIST=host.containers.internal,localhost \
  -e GITEA__webhook__ALLOW_LOCALNETWORK_HOSTS=true \
  -e GITEA__server__DOMAIN=localhost \
  -e GITEA__server__ROOT_URL=http://localhost:3001/ \
  -e GITEA__server__HTTP_PORT=3000 \
  -e GITEA__service__DISABLE_REGISTRATION=true \
  -e GITEA__repository__DEFAULT_BRANCH=main \
  -v "$DATA_DIR/gitea:/data" \
  polis/gitea

say "wait for the web layer"
for _ in $(seq 1 90); do
  code=$(curl -s -o /dev/null -w '%{http_code}' http://localhost:3001 2>/dev/null || true)
  if [[ "$code" != "000" ]] && (( code < 500 )); then
    break
  fi
  sleep 1
done

say "bootstrap the admin account (headless)"
# the CLI refuses root; runs as the container's git user. The web layer
# answers before migrations finish — retry.
for attempt in $(seq 1 60); do
  out=$(podman exec -u git -e HOME=/data/git -e GITEA_WORK_DIR=/data/gitea gitea \
    gitea admin user create \
    --username "$GITEA_ADMIN_USERNAME" \
    --password "$GITEA_ADMIN_PASSWORD" \
    --email "$GITEA_ADMIN_EMAIL" \
    --admin \
    --must-change-password=false \
    --access-token --access-token-name polis 2>&1) || true
  if grep -q "user already exists" <<<"$out"; then
    echo "  admin '$GITEA_ADMIN_USERNAME' already exists"
    break
  fi
  if grep -q "Access token was successfully created" <<<"$out"; then
    echo "  admin '$GITEA_ADMIN_USERNAME' created"
    break
  fi
  sleep 1
done

TOKEN=$(grep -o 'Access token was successfully created\.\.\..*' <<<"$out" \
          | sed 's/.*\.\.\. //' | tr -d '[:space:]')
if [[ -n "$TOKEN" ]]; then
  say "write the minted token into .env (GITEA_API_KEY)"
  if grep -q '^GITEA_API_KEY=' "$ROOT/.env"; then
    sed -i '' "s|^GITEA_API_KEY=.*|GITEA_API_KEY=$TOKEN|" "$ROOT/.env"
  else
    printf '\nGITEA_API_KEY=%s\n' "$TOKEN" >> "$ROOT/.env"
  fi
  echo "  GITEA_API_KEY updated"
else
  echo "  note: no token minted (admin pre-existed?) — reuse the existing GITEA_API_KEY" >&2
fi

say "verify"
GITEA_API_KEY=$(grep '^GITEA_API_KEY=' "$ROOT/.env" | cut -d= -f2-)
curl -sf -H "Authorization: token $GITEA_API_KEY" \
  http://localhost:3001/api/v1/user > /dev/null \
  && echo "  gitea up — authenticated as $GITEA_ADMIN_USERNAME"
