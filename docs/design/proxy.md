# The front proxy — one entrypoint per deployment

Status: implemented (task 0042). Approved 2026-09-13; proxy:
**caddy** (HTTP only — everything is local). Supersedes the in-network /
host URL split of the provisioning era (0037/0041).

## 1. The problem

Three audiences address the same services, each needing a different URL
form: the host browser/operator CLI (`localhost:<port>`), in-network
containers (`http://<sim>-<service>:3000|8000`), the forge's webhooks
(`host.containers.internal:<port>`). The workarounds this forced (gitea
`ROOT_URL` in-network vs browser links; `WOODPECKER_HOST=localhost` plus
a webhook delete-and-repoint; SSRF allowlists; unstable `_free_port`
addresses) all disappear once **one URL resolves from everywhere**.

## 2. Canonical authority

Base URL for every component: `http://host.containers.internal:<P>`.

- **In-network**: podman's built-in `host.containers.internal` resolves
  to the host; a request to `<P>` lands on the host-published port and is
  forwarded back into the proxy (gvproxy hairpin — spike-verified
  2026-09-13 with a sibling container fetching a published port).
- **Host**: the name does not resolve out of the box → a one-time
  `/etc/hosts` entry `127.0.0.1 host.containers.internal`
  (`scripts/infra/hosts.sh add|remove`, sudo). Without it, in-network
  traffic still works; host browser links do not. `provision up` warns.
- Caddy is bound to `:P` (not the hostname), so `localhost:<P>` also
  serves host-side API calls before the hosts entry exists.

Rejected alternatives: `.localhost` network aliases (aardvark forwards
them upstream; in-container they resolve to 127.0.0.1 — spike-verified),
per-sim `/etc/hosts` entries, host-network tricks on macOS.

## 3. Routing

One caddy container per deployment: `<sim>-proxy` on `<sim>-net` (and one
for the shared dev rig), publishing the deployment's **only** host port
`P:P`. The Caddyfile is generated at provisioning and mounted read-only.
Prefix handling differs per service (spike-verified 2026-09-13):

| path | upstream | route | notes |
|---|---|---|---|
| `/gitea/*` | `<sim>-gitea:3000` | `handle_path` (**strip**) | gitea routes at `/`, generates `/gitea/…` links; ROOT_URL subpath |
| `/ci/*` | `<sim>-woodpecker-server:8000` | `handle` (**keep**) | prefix is part of `WOODPECKER_HOST` (v3) |
| `/gogs/*` | `<sim>-gogs:3000` | `handle_path` (**strip**) | gogs routes at `/`, generates `/gogs/…` links |
| `/` | redirect | | to the platform's path |

`P` is allocated once and persisted (`secrets.json` → `proxy_port`); a
re-`up --force` reuses it — retires `_free_port` churn. The dev rig uses
the same scheme on `host.containers.internal:10800`.

The proxy **forces the canonical Host upstream**
(`header_up Host host.containers.internal:P`): the services derive their
clone and webhook URLs from the request host, and host-side clients reach
the proxy as `localhost`. Without it the forge hands the CI a
`localhost:<P>` clone URL, unreachable from a pipeline step container
(found live while building the BDD transition suite, task 0053).

## 4. Service configuration

- **gitea**: `GITEA__server__ROOT_URL=http://host.containers.internal:P/gitea/`;
  `ALLOWED_HOST_LIST=host.containers.internal` (one private target left:
  the proxy; `ALLOW_LOCALNETWORK_HOSTS` stays).
- **woodpecker**: `WOODPECKER_HOST=http://host.containers.internal:P/ci`,
  `WOODPECKER_GITEA_URL=http://host.containers.internal:P/gitea`, OAuth app
  with ONE redirect URI (`…/ci/authorize`). The webhook woodpecker
  registers at enable time is now deliverable as-is — the
  delete-and-repoint block in `up_woodpecker` is deleted.
  `WOODPECKER_EXPERT_WEBHOOK_HOST` remains unused unless the prefix
  handling misbehaves.
- **gogs**: `EXTERNAL_URL=http://host.containers.internal:P/gogs/`.
- **CI context**: global secrets `POLIS_GITEA_URL` canonical; slice
  remotes (`origin`/`upstream`) canonical; the Keeper's and cities' pushes
  and clones all go through the proxy.

## 5. Provisioning wiring

- `_up_proxy(sim, platform, with_ci)` — run `<sim>-proxy`, write the
  Caddyfile to `data/sims/<sim>/platform/caddy/Caddyfile`, record the
  container and `proxy_port`/`proxy_url` in `provision.json`/`secrets.json`.
- gogs/gitea/woodpecker stop publishing `-p`; their internal ports stay
  3000/8000.
- `Inventory` gains `proxy_port`; `status`, `stop`, `start`, `destroy`,
  `sim_containers`, `list_sims` learn the `<sim>-proxy` name.
- Readiness checks (currently `http://localhost:<port>`) go through the
  proxy path; a failed prefix configuration fails provisioning loudly.

## 6. Operator / CLI consequences

- `config.py`: `GOGS_URL`/`GITEA_URL`/`WOODPECKER_URL` resolve to
  `proxy_url + /gogs|/gitea|/ci` (sim secrets first, then dev-rig
  default), so host-side clients and chambers use the canonical URL.
- `chamber._host_swap` becomes the identity — slice remotes are already
  canonical. The `POLIS_*` override hooks remain for tests.
- `beats.py` (`b_archive_contains`) and `cli/archive.py` drop their
  `*_url_internal`/`*_url_external` branching.
- `_woodpecker_oauth_login` uses the single canonical redirect; the
  CSRF/login dance is unchanged.

## 7. Prefix support — spike-verified 2026-09-13

| service | behavior | verdict |
|---|---|---|
| gitea | routes at `/`; `ROOT_URL` subpath shapes generated links; proxy strips | 200 |
| gogs | same: proxy strips; links under `/gogs/` | 200 |
| woodpecker v3 | `WOODPECKER_HOST` includes `/ci`; proxy must NOT strip | `healthz` 204 |
| caddy | `handle_path` (strip) vs `handle` (pass) per route | verified |

No fallback needed: all three serve correctly behind the proxy with the
per-route strip setting above.

## 8. Dev rig

`docker/docker-compose.yml` gains a `proxy` service (caddy, :10800) and
the per-service scripts (`gitea.sh`, `woodpecker.sh`, `gogs.sh`) point
their root URLs at it; `scripts/infra/proxy.sh` runs it outside compose.
`smoke.sh` checks each path through the proxy.

## 9. Out of scope

Authentication at the proxy (task 0052), container-runtime agnosticism
(0043), TLS (all local), export/import interaction.

## 10. Verification

- existing: `tests/provision-demo.sh`, `tests/provision-demo-gitea.sh`,
  `tests/director-demo.sh`, `tests/transition-demo.sh`, `behave` — green;
- new: clone and CI run through the proxy; the webhook delivers without
  the repoint; gitea-rendered links resolve on the host; `up --force`
  keeps the port; `provision status` lists the proxy.
