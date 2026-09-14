# 0074: taken-port bind vs TIME_WAIT; keep the shared sim on failure

- **created:** 2026-09-14T12:35:00Z
- **type:** [bugfix]
- **depends-on:** 0073
- **status:** done

## Description

Follow-up to 0073 — its bind retry made the taken-port scenario fail
differently: the CI rerun (PR #22, run 34843464408) showed the port
refusing a plain bind for the full 30s after the proxy was force-removed,
which is the signature of TCP `TIME_WAIT` sockets left by the container's
port mapping (docker-proxy teardown), not a brief lag. The scenario then
errored before its recovery steps and cascaded into the following
shared-sim scenarios.

- `occupy_port` sets `SO_REUSEADDR` before binding (TIME_WAIT sockets no
  longer block it; a *live* listener still refuses), keeping the bounded
  retry as a safety net.
- Failure diagnostics actually work now: behave has no
  `context.failed`, so `after_all` never kept the shared sim. Failures
  are tracked via `scenario.status` (behave.model_core.Status) and the
  sim is kept for the workflow's diagnostics step.
- The workflow diagnostics print the detected runtime and the listening
  sockets, and read container logs through the detected runtime
  (podman or docker), not docker alone.

Acceptance: the infrastructure workflow passes on the runner; a future
failure leaves the sim containers behind, with their logs visible in the
job output.

## Completion

- **finished:** 2026-09-14T12:45:54Z
- **commit:** aba9c41 (PR #26)
