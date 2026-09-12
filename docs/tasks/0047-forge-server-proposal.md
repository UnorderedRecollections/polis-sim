# 0047: proposal — a polis-native forge (minimal gogs/gitea-compatible API)

- **created:** 2026-09-11T16:00:00Z
- **type:** [infrastructure]
- **depends-on:** 0042
- **status:** open

## Description

Propose a small FastAPI server implementing exactly the API surface the
simulation consumes (a *mechanical archive host* — the fiction is on our
side: the platform knows refs and nothing of institutions). Two roles:

1. **Mock/testing** — a drop-in fake for gogs/gitea so tests and the
   demo flows run without the real platforms (fast, deterministic,
   failure-injectable); behind the same `Platform` client surface.
2. **Replacement** — eventually THE platform for simulations, retiring
   gogs/gitea entirely (the proxy from task 0042 becomes its front).

Deliverable: `docs/design/forge-server.md` containing

- the exact route inventory (from `clients/gitea.py` + `clients/gogs.py`
  + the probed PR/hook/OAuth/status routes in AGENTS.md);
- the git-backed storage design (bare repos on disk, the three stores
  untouched);
- the OAuth dance + webhook delivery + commit-status endpoints the CI
  (task 0048) needs;
- quirk-compatibility: which quirks to keep (scopes on token creation)
  vs drop (auto-close on merge? fork requirement for cross-repo PRs?);
- test mode switches (latency, failure injection, rate limits).

## Completion

<!-- filled in when the task is done:
- **finished:**
- **commit:**
-->
