#!/usr/bin/env bash
# Add or remove the canonical front-proxy host entry (task 0042):
#     127.0.0.1 host.containers.internal
#
# Why: the canonical base URL of every deployment is
# http://host.containers.internal:<port>. Containers resolve that name
# through podman; the HOST only resolves it after this /etc/hosts entry —
# without it, browser links rendered by gitea/woodpecker do not open (the
# operator CLI and provisioning keep working through the localhost alias
# the proxy also binds). Requires sudo.
set -euo pipefail
source "$(dirname "$0")/env.sh"

ENTRY="127.0.0.1 host.containers.internal"

case "${1:-}" in
  add)
    if awk '{ $1=""; sub(/^ /,""); print }' /etc/hosts 2>/dev/null | grep -qw host.containers.internal; then
      echo "already present: $ENTRY"
      exit 0
    fi
    printf '%s\n' "$ENTRY" | sudo tee -a /etc/hosts > /dev/null
    echo "added: $ENTRY"
    ;;
  remove)
    sudo sed -i '' '/host\.containers\.internal/d' /etc/hosts
    echo "removed any host.containers.internal entries"
    ;;
  *)
    die "usage: hosts.sh add|remove"
    ;;
esac
