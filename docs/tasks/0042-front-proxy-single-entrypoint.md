# 0042: a single front proxy — the one entrypoint to the apparatus

- **created:** 2026-09-11T15:00:00Z
- **type:** [infrastructure]
- **depends-on:** 0041
- **status:** done

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

## Implementation proposal (approved 2026-09-13)

**Validated by spike (2026-09-13):**

- a sibling container reaching `http://host.containers.internal:<published
  port>` lands on the host-published port (gvproxy hairpin) — works;
- `.localhost` network aliases are forwarded upstream (in-container they
  resolve to 127.0.0.1) — rejected;
- macOS resolves `*.localhost` but NOT `host.containers.internal` on the
  host → one-time `/etc/hosts` line needed for host browser/CLI links;
- woodpecker v3: the path prefix belongs to `WOODPECKER_HOST`
  (`http://host:P/ci`); `WOODPECKER_ROOT_PATH` is not a v3 setting;
  `WOODPECKER_EXPERT_WEBHOOK_HOST` remains as an escape hatch.

**Authority model: one URL everywhere.** Canonical base
`http://host.containers.internal:<P>` for gitea `ROOT_URL`,
`WOODPECKER_HOST`, clone URLs, webhook URLs, OAuth redirects, slice
remotes, CI global secrets, operator CLI and browser. The host reaches it
through the `/etc/hosts` entry → 127.0.0.1 → the published proxy port;
containers through podman's DNS. Caddy binds `:P` so `localhost:<P>` also
serves host-side API calls before the hosts entry exists.

**Routing.** One caddy container per sim (`<sim>-proxy`, caddy:2-alpine)
on `<sim>-net`, publishing the ONLY host port `P:P`; `P` allocated once,
persisted in `secrets.json`, reused by `up --force`. Paths are passed
through unstripped so the services' own prefix handling matches:

- `/gitea/*` → `<sim>-gitea:3000`
- `/ci/*` → `<sim>-woodpecker-server:8000`
- `/gogs/*` → `<sim>-gogs:3000`
- `/` → redirect to the platform path

The Caddyfile is generated per sim and mounted read-only.

**Work items**

1. `docker/caddy/` — caddy image + Caddyfile template.
2. `provision.py` — `_up_proxy`; platforms/CI stop publishing ports;
   canonical ROOT_URL/webhooks/global secrets/slice remotes; delete the
   webhook delete-and-repoint block; proxy in
   inventory/status/stop/start/destroy/`sim_containers`; secrets
   `proxy_port`/`proxy_url`.
3. `config.py` — platform URLs = `proxy_url + /gitea|/gogs|/ci`; dev-rig
   default `host.containers.internal:10800`.
4. `chamber.py` — `_host_swap` becomes identity (URLs already canonical);
   keep the `POLIS_*` test hooks.
5. `beats.py`, `cli/archive.py` — drop internal/external branching;
   `_woodpecker_oauth_login` — one redirect URI (`…/ci/authorize`).
6. Dev rig — compose `proxy` service + `scripts/infra/proxy.sh`;
   gitea.sh/woodpecker.sh point at it; smoke.sh checks each path.
7. `scripts/infra/hosts.sh add|remove` (sudo) + preflight in
   `provision up`/`health`.
8. Docs — `docs/design/proxy.md`; services/*, running-a-simulation.md,
   AGENTS.md; demos parse `proxy_port`/`proxy_url`.

**Verification.** Provision demos (gogs + gitea), director, transition
and behave stay green; new assertions: clone/CI through the proxy,
webhook delivered with no repoint, gitea links resolve on the host,
`up --force` keeps the port.

**Risks / fallbacks.** gogs sub-path support (verify first; fallback: a
dedicated proxy port for gogs, still proxied); the SSRF allowlist
shrinks to `host.containers.internal` but stays; hairpin for in-network
fetches (local only); `/etc/hosts` needs one-time sudo.

## Progress log

- **2026-09-13 — prefix spike (step 1).** caddy + gogs + gitea +
  woodpecker stood up behind one caddy port; **problem:** gitea and gogs
  do NOT serve requests under the forwarded prefix (gitea routed
  `/gitea/` as `user.UsernameSubRoute` → 404; gogs 404'd), while
  woodpecker is the opposite (its prefix must be forwarded intact —
  `/ci/healthz` → 204). Fix: per-route caddy semantics — `handle_path`
  (strip) for `/gitea` and `/gogs`, `handle` (pass) for `/ci`; ROOT_URL /
  EXTERNAL_URL still carry the prefix so generated links are correct.
  Design note §3/§7 corrected. Verified: gitea 200 + `/gitea/…` links,
  gogs 200 + `/gogs/…` links, woodpecker 204.

- **2026-09-13 — steps 2–5 implemented; all three demos pass.**
  `docker/caddy/` (Dockerfile + templated Caddyfile), `_up_proxy` with a
  persisted `proxy_port` (reused by `up --force`), platform/CI containers
  stop publishing ports, canonical `host.containers.internal:<P>` URLs in
  gitea `ROOT_URL`, woodpecker `WOODPECKER_HOST`, slice remotes, CI global
  secrets; the webhook delete-and-repoint block is gone (the registered
  hook is deliverable as-is); the OAuth app has ONE redirect URI and the
  host-side login rewrites the callback to localhost so provisioning needs
  no `/etc/hosts` entry. `config.py`/`chamber.py` keep host-swapping, so
  `beats.py`/`cli/archive.py` resolve per-platform. Problems:
  - Caddyfile generation with `str.format` broke on the config's literal
    `{}` braces → switched to `string.Template` (`$placeholders`);
  - gogs bootstrap race: token creation right after `create-user` hit a
    caddy 502 while gogs settled → retry loops in `_up_platform` and
    `preflight`;
  - **verified:** `tests/provision-demo.sh` (gogs),
    `tests/provision-demo-gitea.sh`, `tests/director-demo.sh`,
    `tests/transition-demo.sh` all pass; gitea remote messages and CI
    clones now show the one canonical URL.

- **2026-09-13 — steps 6–7: dev rig + hosts helper.** The shared dev rig
  moves behind the same scheme: `docker/caddy/Caddyfile.dev` +
  `scripts/infra/proxy.sh` (port 10800, the only HTTP entrypoint), compose
  gains the `proxy` service, gogs/gitea/woodpecker stop publishing HTTP
  (SSH kept as a git transport), their root URLs point at the canonical
  name, `env.sh` gains `ensure_proxy`, `smoke.sh` checks the proxy and the
  per-path URLs, `config.py` dev-rig defaults move to
  `localhost:10800/{gogs,gitea,ci}`. `scripts/infra/hosts.sh add|remove`
  manages the one-time `/etc/hosts` entry; `provision up` prints a note
  when it is missing and `polis health hosts` reports it (warn, not
  fail). gogs.sh writes a canonical `app.ini` on first run. Verified: the
  proxy builds, starts and routes (502 without upstreams, as expected);
  full dev-rig smoke still needs `.env` credentials on a configured
  machine.

## Completion

- **finished:** 2026-09-13T16:25:49Z
- **commit:** fd2e744 (series: 4a98cdc design note → d32ab37 per-sim proxy
  → fd2e744 dev rig + docs; completion metadata in this commit)

Final state: one caddy proxy per deployment is the only host-published
HTTP entrypoint; canonical base `http://host.containers.internal:<P>`
(gitea `ROOT_URL`, `WOODPECKER_HOST`, clone/webhook URLs, slice remotes,
CI global secrets); per-route prefix semantics (gitea/gogs stripped,
woodpecker kept); the webhook repoint is gone; one OAuth redirect;
`proxy_port` persists across `--force`; dev rig, smoke and `polis health
hosts` included. Verified: `tests/provision-demo.sh` (with the port
assertion), `tests/provision-demo-gitea.sh`, `tests/director-demo.sh`,
`tests/transition-demo.sh`, `uv run behave features/` — all passing; the
dev-rig proxy builds, starts and routes (full dev-rig smoke needs `.env`
credentials on a configured machine).
