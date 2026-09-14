#!/usr/bin/env bash
# Deployment/provisioning failure suite (task 0055): fail fast with a
# remedy (or deliberate degrade), state inspectable, recovery idempotent.
# Provisions one sim and injects local deployment failures.
#
#   tests/failures.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
unset POLIS_PROVISIONED_SIM

uv run python tests/failures_test.py "$@"
