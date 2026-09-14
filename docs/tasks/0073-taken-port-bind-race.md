# 0073: flaky "taken proxy port" scenario on docker runners

- **created:** 2026-09-14T12:17:56Z
- **type:** [bugfix]
- **depends-on:** 0067
- **status:** done

## Description

The infrastructure suite's "a taken proxy port is refused and recovers"
scenario is flaky on GitHub's docker runners: `Given the proxy port is
occupied by another process` can fail with `OSError: [Errno 98] Address
already in use` immediately after the proxy container is force-removed —
the runtime's port forwarder is not always gone when `rm -f` returns.
The scenario then errors before its recovery steps, which cascades into
the following shared-sim scenarios (their platform is unreachable,
because the proxy was never restored).

Fixed by retrying the bind in the Given with a bounded deadline (30s)
and a clear message; a real conflict still fails. Observed in run
34842167952 (PR #22), 2026-09-14.

Acceptance: the infrastructure workflow passes on the runner (the
scenario's bind does not race the port forwarder's teardown).

## Completion

- **finished:** 2026-09-14T12:26:02Z
- **commit:** 3161c3e (PR #24)
