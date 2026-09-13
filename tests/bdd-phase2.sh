#!/usr/bin/env bash
# The gitea-backed BDD suites (task 0053) — slow: each scenario provisions
# containers; the phase-transition one enacts the transition and runs the
# Mechanical Magistrate's CI. Kept out of the default `behave features/`
# run; run this when touching provisioning, the platform backings, the
# transition or the CI.
#
#   tests/bdd-phase2.sh                 # phase I on gitea + the full arc
#   tests/bdd-phase2.sh --tags @gitea   # pass behave flags through
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

say() { printf '\n\033[1m== %s ==\033[0m\n' "$*"; }

if [[ $# -gt 0 ]]; then
  uv run behave features/phase-transition.feature "$@"
  exit 0
fi

say "phase I on gitea (the same scenario as the default gogs run)"
uv run behave features/northern-banks.feature -D platform=gitea

say "phase I -> transition -> phase II on gitea"
uv run behave features/phase-transition.feature --tags @slow
