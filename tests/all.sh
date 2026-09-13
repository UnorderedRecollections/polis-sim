#!/usr/bin/env bash
# Full verification (task 0058): every suite and demo this machine can run.
#
#   tests/all.sh              # fast + slow behave + self-contained demos;
#                             # dev-rig checks only if the shared rig answers
#   tests/all.sh --dev-rig    # the dev-rig checks are REQUIRED, not skipped
#
# The fast/slow split (docs/testing.md) keeps the edit-run loop quick; this
# runner is the one command that runs everything and reports a summary. The
# CI tasks (0045/0049) should call it.
set -uo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
unset POLIS_PROVISIONED_SIM

DEV_RIG=0
case "${1:-}" in
  --dev-rig) DEV_RIG=1 ;;
  "") ;;
  *) echo "usage: tests/all.sh [--dev-rig]" >&2; exit 2 ;;
esac

PASSED=()
FAILED=()
SKIPPED=()

run() { # name command...
  local name="$1"; shift
  printf '\n\033[1m== %s ==\033[0m\n' "$name"
  if "$@"; then
    PASSED+=("$name")
    printf '\n\033[32mPASS\033[0m %s\n' "$name"
  else
    FAILED+=("$name")
    printf '\n\033[31mFAIL\033[0m %s\n' "$name"
  fi
}

run "runtime agnosticism (docker stubbed, podman live)" bash tests/runtime-agnosticism.sh
run "beat vocabulary scopes (user/test)" bash tests/beat-scopes.sh
run "queue driver semantics (stub execute_beat)" uv run python tests/queue_driver_test.py
run "fast behave (phase I)" uv run behave features/
run "slow gitea suites (phase I -> transition -> phase II)" bash tests/bdd-phase2.sh
run "cross-jurisdiction suite (15 stories)" bash tests/jurisdictions.sh
run "provisioning demo (gogs)" bash tests/provision-demo.sh
run "provisioning demo (gitea)" bash tests/provision-demo-gitea.sh
run "director demo" bash tests/director-demo.sh
run "scenario authoring demo (submit -> drive -> done)" bash tests/scenarios-demo.sh
run "transition demo" bash tests/transition-demo.sh

# --- the dev rig: required with --dev-rig, detected otherwise ---------------
GOGS_URL="${POLIS_GOGS_URL:-http://localhost:10800/gogs}"
if [[ $DEV_RIG -eq 1 ]] || curl -sf -o /dev/null "$GOGS_URL/" 2>/dev/null; then
  run "dev-rig smoke" bash scripts/infra/smoke.sh
  run "sim runtime demo (dev rig)" bash tests/sim-runtime-demo.sh
  run "e2e gogs (dev rig)" bash tests/e2e-gogs.sh
else
  SKIPPED+=("dev-rig checks (no rig at $GOGS_URL)")
  printf '\n\033[33mSKIP\033[0m dev-rig checks: no rig at %s\n' "$GOGS_URL"
  printf '     start the dev rig, then re-run `tests/all.sh --dev-rig`\n'
fi

# --- summary ----------------------------------------------------------------
printf '\n\033[1m== summary ==\033[0m\n'
for n in ${PASSED[@]+"${PASSED[@]}"}; do printf '  \033[32mpass\033[0m  %s\n' "$n"; done
for n in ${SKIPPED[@]+"${SKIPPED[@]}"}; do printf '  \033[33mskip\033[0m  %s\n' "$n"; done
for n in ${FAILED[@]+"${FAILED[@]}"}; do printf '  \033[31mFAIL\033[0m  %s\n' "$n"; done
if (( ${#FAILED[@]} > 0 )); then
  printf '\n\033[1;31mFULL VERIFICATION FAILED\033[0m (%d of %d run)\n' \
    "${#FAILED[@]}" "$(( ${#PASSED[@]} + ${#FAILED[@]} ))"
  exit 1
fi
printf '\n\033[1;32mFULL VERIFICATION PASSED\033[0m (%d run, %d skipped)\n' \
  "${#PASSED[@]}" "${#SKIPPED[@]}"
