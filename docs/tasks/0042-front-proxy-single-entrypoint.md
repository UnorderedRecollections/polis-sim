# 0042: a single front proxy — the one entrypoint to the apparatus

- **created:** 2026-09-11T15:00:00Z
- **type:** [infrastructure]
- **depends-on:** 0041
- **status:** open

## Description

Add a reverse proxy that becomes the **only** entrypoint to the
apparatus's services (gogs/gitea/woodpecker — and later anything else),
collapsing the URL topology that has cost a pile of ad-hoc workarounds.

## Why (the pain this retires)

Three audiences address the same services today, each needing a
different URL form:

- the **host browser / operator CLI** — `localhost:<allocated port>`;
- **in-network containers** (the operator, the CI step containers, the
  forge) — `http://<sim>-<service>:3000|8000|9000`;
- **the forge's outbound calls** (webhooks) — currently looped through
  `host.containers.internal:<port>`.

The workarounds this has already forced (see AGENTS.md platform facts):

- gitea `ROOT_URL` must be the in-network name (clone URLs for the CI),
  breaking operator-facing links;
- `WOODPECKER_HOST` must be `localhost` for browser-friendly status
  links, breaking the forge webhook — "fixed" by repointing the
  registered hook to the in-network URL after enable;
- gitea's SSRF `ALLOWED_HOST_LIST` + `ALLOW_LOCALNETWORK_HOSTS` opened
  for private webhook targets;
- per-sim dynamic ports from `_free_port(11880+)`, so nothing has a
  stable address.

## Shape of the solution (sketch — to be designed at implementation)

- One proxy per deployment (the shared dev rig, and **per sim** on
  `<sim>-net`), the only container publishing a host port.
- All services publish internal ports only (no `-p` on gitea/woodpecker
  anymore); the proxy routes stable public paths/hostnames to them
  (e.g. `http://localhost:<sim-port>/gitea`, `/ci`, `/gogs`, or
  per-service stable ports).
- Components then get ONE host: gitea `ROOT_URL`, `WOODPECKER_HOST`,
  webhook URLs, clone URLs and the operator's CLI all point at the
  proxy — reachable from the host AND in-network (its in-network alias).
- The proxy config is templated at provisioning (per-sim services);
  path-prefix routing must respect each service's expectations (gitea
  and woodpecker work under prefixes with `ROOT_URL`/`WOODPECKER_ROOT_PATH`).
- Proxy: **caddy** (decided 2026-09-13) — HTTP only (all local), one
  container per deployment, one published port; the Caddyfile is
  templated per sim at provisioning.

## Deliverables (at implementation time)

- design note (`docs/design/proxy.md`): routing table per sim, prefix
  rules, service config changes (`ROOT_URL`, `WOODPECKER_ROOT_PATH`,
  webhook/ALLOWED_HOST_LIST simplification);
- the proxy image/container + provisioning wiring (`provision up`
  brings it up; services stop publishing their own ports);
- retire the workarounds listed above (in-network ROOT_URL vs browser
  links, the webhook repoint, `host.containers.internal` loops);
- update the demos/tests that parse ports out of secrets.json;
- docs: services/*, running-a-simulation.md, AGENTS.md.

## Completion

<!-- filled in when the task is done:
- **finished:**
- **commit:**
-->
