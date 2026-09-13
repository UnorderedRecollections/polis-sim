#!/usr/bin/env bash
# Cross-jurisdiction suite (task 0054): one whole director story per
# jurisdiction (15), each on a situation generated from that
# jurisdiction's own data. Slow (provisions one sim, drives 15 stories);
# keep it out of the fast loop.
#
#   tests/jurisdictions.sh                # seed 41
#   tests/jurisdictions.sh --seed 7
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
unset POLIS_PROVISIONED_SIM

uv run python tests/jurisdictions_test.py "$@"
