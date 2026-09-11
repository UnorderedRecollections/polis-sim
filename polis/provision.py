"""polis provision — the porcelain layer over the platform plumbing.

Assembles everything one sim instance needs (docs/design/provisioning.md):
users with per-sim tokens, the archive org/repo + founding corpus, city
orgs/repos, per-sim slices, an inventory (provision.json) that status and
teardown consume. Idempotent: re-running `up` reconciles.

Platform abstraction (task 0037 — phase is a procedure, not a product):
`up --platform gogs|gitea` stands the sim's own platform container up.
Either product can host phase 1 (matter-store proceedings, local
incorporation); the federation's `phase` never follows the product. Each
product's quirks (gogs: no pulls API, no org-delete route, auto_init
fails; gitea: scopes on token creation, org repos via /orgs route, no
org delete while repos remain) live in its bring-up/notes here and in the
clients.

Naming (everything carries the sim id):
  org   <sim>-archive, repo common-law
  orgs  <sim>-<city>, repo common-law (plain repos — gogs has no forks
        API; city repos are seeded by pushing the founding corpus)
  users <sim>-<username>
  containers polis-city-<city>-<sim>
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import config, store
from .clients import podman
from .clients.gitea import GiteaClient, GiteaError
from .clients.gogs import GogsClient, GogsError
from .clients.woodpecker import WoodpeckerClient
from .legislation import gitcmd
from .sim.journal import SIMS_DIR


class ProvisionError(RuntimeError):
    pass


API_ERRORS = (GogsError, GiteaError)


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


@dataclass
class Inventory:
    sim: str
    created_at: str = ""
    platform: str = "gogs"         # the provisioned product (gogs | gitea)
    users: list[str] = field(default_factory=list)
    orgs: list[str] = field(default_factory=list)
    repos: list[str] = field(default_factory=list)        # "owner/name"
    containers: list[str] = field(default_factory=list)
    slices_dir: str = ""
    network: str = ""                # the sim's private podman network
    platform_port: int = 0           # host port → the sim's platform :3000
    notes: list[str] = field(default_factory=list)

    def save(self) -> Path:
        path = SIMS_DIR / self.sim / "provision.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")
        return path

    @classmethod
    def load(cls, sim: str) -> "Inventory":
        path = SIMS_DIR / sim / "provision.json"
        if not path.exists():
            raise ProvisionError(f"no provisioned sim '{sim}' (expected {path})")
        raw = json.loads(path.read_text(encoding="utf-8"))
        inv = cls(**{k: v for k, v in raw.items() if k in cls.__dataclass_fields__})
        # pre-0037 inventories: no platform/platform_port (gogs era)
        if not inv.platform_port:
            inv.platform_port = raw.get("gogs_port", 0)
        return inv


def _validate_sim_id(sim: str) -> None:
    import re
    if not re.fullmatch(r"[a-z][a-z0-9-]{1,30}", sim):
        raise ProvisionError(
            f"bad sim id '{sim}' — use a short slug like 'harbour-01' "
            "(lowercase letters/digits/hyphens, starting with a letter)")
    # gogs usernames cap at 35 chars (verified); sim users are named
    # <sim>-<username> (the world's longest username is 21 chars)
    if len(sim) > 13:
        raise ProvisionError(
            f"sim id '{sim}' is too long ({len(sim)} > 13) — gogs usernames "
            "('<sim>-<username>') cap at 35 characters")


# --- the sim's own platform (task 0027): network + postgres + <platform> ------
#
# A sim is fully self-contained: <sim>-net, <sim>-postgres, <sim>-gogs or
# <sim>-gitea (host port allocated at up-time). Inside the network the
# platform URL is constant (http://<sim>-<platform>:3000) — slices, operator
# and city containers use it; the host port exists only for the operator's
# CLI (provisioning, ad-hoc checks). Per-sim secrets live in
# data/sims/<sim>/secrets.json (gitignored), never in world.json.
#
# Task 0037: the platform is the *product*. Either product hosts phase 1.

POSTGRES_IMAGE = "polis/postgres"


@dataclass(frozen=True)
class PlatformSpec:
    name: str                       # "gogs" | "gitea" (also the secrets-key prefix)
    image: str                      # podman image
    dockerfile: str                 # dir under docker/ with the Dockerfile
    client: Any                     # client class (GogsClient | GiteaClient)
    notes: str                      # quirks isolated here, for the inventory

    def container(self, sim: str) -> str:
        return f"{sim}-{self.name}"

    def url_internal(self, sim: str) -> str:
        return f"http://{self.container(sim)}:3000"


PLATFORMS: dict[str, PlatformSpec] = {
    "gogs": PlatformSpec(
        name="gogs", image="polis/gogs", dockerfile="gogs", client=GogsClient,
        notes="orgs/repos/users die with the sim's gogs (its volumes are at "
              "{plat_dir}) — delete with the sim dir",
    ),
    "gitea": PlatformSpec(
        name="gitea", image="polis/gitea", dockerfile="gitea", client=GiteaClient,
        notes="orgs/repos/users die with the sim's gitea (its volumes are at "
              "{plat_dir}) — delete with the sim dir",
    ),
}


def platform_dir(sim: str) -> Path:
    return SIMS_DIR / sim / "platform"


def secrets_path(sim: str) -> Path:
    return SIMS_DIR / sim / "secrets.json"


def load_secrets(sim: str) -> dict:
    path = secrets_path(sim)
    if not path.exists():
        raise ProvisionError(f"no secrets for sim '{sim}' (expected {path})")
    return json.loads(path.read_text(encoding="utf-8"))


def sim_platform(sim: str) -> str:
    """The provisioned product of a sim ("gogs" default for pre-0037 sims)."""
    path = SIMS_DIR / sim / "provision.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8")).get("platform") or "gogs"
    return load_secrets(sim).get("platform") or "gogs"


def sim_platform_client(sim: str):
    """A client against the sim's own platform, as the sim's admin."""
    platform = sim_platform(sim)
    secrets = load_secrets(sim)
    spec = PLATFORMS[platform]
    return spec.client(token=secrets["admin_token"],
                       base_url=f"http://localhost:{secrets[f'{platform}_port']}")


def _free_port(base: int = 11880) -> int:
    import socket
    for port in range(base, base + 200):
        with socket.socket() as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return port
    raise ProvisionError("no free host port for the sim's platform")


def _ensure_platform_images(spec: PlatformSpec) -> None:
    for image, dockerfile in ((spec.image, spec.dockerfile),
                              (POSTGRES_IMAGE, "postgres")):
        df = config.PROJECT_ROOT / "docker" / dockerfile / "Dockerfile"
        if not df.exists():
            raise ProvisionError(f"platform Dockerfile missing: {df}")
        if podman._run(["image", "exists", image], check=False).returncode != 0:
            proc = podman._run(["build", "-t", image, "-f", str(df),
                                str(config.PROJECT_ROOT)], check=False)
            if proc.returncode != 0:
                raise ProvisionError(f"building {image} failed: {proc.stderr.strip()[:300]}")


def _pg_password() -> str:
    return (os.environ.get("POSTGRES_PASSWORD")
            or config._load_env_file().get("POSTGRES_PASSWORD")
            or "gogs")


def _up_postgres(sim: str, inv: Inventory, password: str) -> str:
    """The sim's shared postgres (already running or freshly started).
    Returns the container name."""
    net = f"{sim}-net"
    pg = f"{sim}-postgres"
    plat = platform_dir(sim)
    (plat / "postgres").mkdir(parents=True, exist_ok=True)
    podman._run(["network", "create", net], check=False)
    if not podman.container_running(pg):
        podman._run(["rm", "-f", pg], check=False)
        proc = podman._run([
            "run", "-d", "--name", pg, "--network", net,
            "-v", f"{plat / 'postgres'}:/var/lib/postgresql/data",
            "-e", "POSTGRES_USER=gogs", "-e", f"POSTGRES_PASSWORD={password}",
            "-e", "POSTGRES_DB=gogs", POSTGRES_IMAGE,
        ])
        if proc.returncode != 0:
            raise ProvisionError(f"postgres start failed: {proc.stderr.strip()[:300]}")
    import time
    for _ in range(60):                       # postgres must be ready before the platform
        if podman._run(["exec", pg, "pg_isready", "-U", "gogs"],
                       check=False).returncode == 0:
            break
        time.sleep(1)
    else:
        raise ProvisionError(f"{pg} never became ready")
    inv.containers.append(pg)
    inv.network = net
    return pg


def _ensure_postgres_db(pg: str, name: str) -> None:
    """Create a database in the sim's postgres if missing (gitea needs its
    own; the volume may predate it). Retried: pg_isready turns true during
    the entrypoint's temporary bootstrap phase, when CREATE DATABASE still
    gets torn down with the restart."""
    import time
    ok, out = podman.exec_ok(pg, ["psql", "-U", "gogs", "-tAc",
                                  f"SELECT 1 FROM pg_database WHERE datname = '{name}'"])
    if ok and "1" in out:
        return
    for _ in range(30):
        if podman._run(["exec", pg, "psql", "-U", "gogs", "-c",
                        f"CREATE DATABASE {name}"], check=False).returncode == 0:
            return
        time.sleep(1)
    raise ProvisionError(f"could not create database '{name}' in {pg}")


def _up_gogs(sim: str, inv: Inventory, pg: str, password: str,
             port: int, admin_password: str) -> dict:
    """The gogs container + admin user + token (customary-era platform)."""
    import secrets as secrets_mod
    import time
    import httpx

    gg = f"{sim}-gogs"
    plat = platform_dir(sim)
    conf = plat / "gogs" / "gogs" / "conf"
    conf.mkdir(parents=True, exist_ok=True)
    (conf / "app.ini").write_text(f"""[database]
TYPE     = postgres
HOST     = {pg}:5432
NAME     = gogs
USER     = gogs
PASSWORD = {password}
SSL_MODE = disable

[security]
INSTALL_LOCK = true
SECRET_KEY   = {secrets_mod.token_hex(8)}

[server]
DOMAIN       = localhost
HTTP_PORT    = 3000
EXTERNAL_URL = http://localhost:{port}/
DISABLE_SSH  = true

[repository]
DEFAULT_BRANCH = main

[service]
DISABLE_REGISTRATION = true

[auth]
REQUIRE_EMAIL_CONFIRMATION = false

[email]
ENABLED = false
""", encoding="utf-8")

    podman._run(["rm", "-f", gg], check=False)
    proc = podman._run([
        "run", "-d", "--name", gg, "--network", f"{sim}-net",
        "--restart", "unless-stopped",
        "-p", f"{port}:3000",
        "-v", f"{plat / 'gogs'}:/data", PLATFORMS["gogs"].image,
    ])
    if proc.returncode != 0:
        raise ProvisionError(f"gogs start failed: {proc.stderr.strip()[:300]}")
    inv.containers.append(gg)
    inv.platform_port = port

    # wait for the web layer (first start runs migrations — can take a while)
    url = f"http://localhost:{port}"
    print(f"[provision] waiting for gogs at {url} …", file=sys.stderr, flush=True)
    for _ in range(90):
        try:
            if httpx.get(url, timeout=2.0).status_code < 500:
                break
        except Exception:
            pass
        time.sleep(1)
    else:
        raise ProvisionError(f"gogs at {url} never came up")

    # the web layer answers before the DB schema is fully migrated — retry
    last_err = ""
    for _ in range(60):
        proc = podman._run([
            "exec", gg, "/app/gogs/gogs", "admin", "create-user",
            "--name", "operator", "--password", admin_password,
            "--email", f"operator@{sim}.invalid", "--admin",
        ], check=False)
        if proc.returncode == 0:
            break
        last_err = (proc.stderr + proc.stdout).strip()[:300]
        if "already exists" in last_err:
            break
        time.sleep(1)
    else:
        raise ProvisionError(f"admin user creation failed: {last_err}")

    return {"platform": "gogs", "admin_username": "operator",
            "admin_password": admin_password, "gogs_port": port,
            "gogs_url_external": url, "gogs_url_internal": f"http://{gg}:3000"}


def _up_gitea(sim: str, inv: Inventory, pg: str, password: str,
              port: int, admin_password: str) -> dict:
    """The gitea container + admin user + token (codified-machinery product;
    a valid phase-1 host since task 0037)."""
    import secrets as secrets_mod
    import time
    import httpx

    gt = f"{sim}-gitea"
    plat = platform_dir(sim)
    (plat / "gitea").mkdir(parents=True, exist_ok=True)
    _ensure_postgres_db(pg, "gitea")

    env = {
        "GITEA__database__DB_TYPE": "postgres",
        "GITEA__database__HOST": f"{pg}:5432",
        "GITEA__database__NAME": "gitea",
        "GITEA__database__USER": "gogs",
        "GITEA__database__PASSWD": password,
        "GITEA__database__SSL_MODE": "disable",
        "GITEA__server__DOMAIN": "localhost",
        # ROOT_URL shapes the clone URLs gitea reports (webhooks, forge
        # payloads) — CI step containers reach gitea on the sim network,
        # never through the mac loopback
        "GITEA__server__ROOT_URL": f"http://{gt}:3000/",
        "GITEA__server__HTTP_PORT": "3000",
        "GITEA__security__INSTALL_LOCK": "true",
        "GITEA__security__SECRET_KEY": secrets_mod.token_hex(16),
        # webhooks target the in-network woodpecker (a private address) —
        # the whole apparatus is local; the delivery check reads
        # security.ALLOWED_HOST_LIST
        "GITEA__security__ALLOWED_HOST_LIST": "host.containers.internal,localhost",
        "GITEA__webhook__ALLOW_LOCALNETWORK_HOSTS": "true",
        "GITEA__service__DISABLE_REGISTRATION": "true",
        "GITEA__repository__DEFAULT_BRANCH": "main",
        "USER_UID": "1000",
        "USER_GID": "1000",
    }
    run_args = ["run", "-d", "--name", gt, "--network", f"{sim}-net",
                "--restart", "unless-stopped", "-p", f"{port}:3000"]
    for k, v in env.items():
        run_args += ["-e", f"{k}={v}"]
    run_args += ["-v", f"{plat / 'gitea'}:/data", PLATFORMS["gitea"].image]

    podman._run(["rm", "-f", gt], check=False)
    proc = podman._run(run_args)
    if proc.returncode != 0:
        raise ProvisionError(f"gitea start failed: {proc.stderr.strip()[:300]}")
    inv.containers.append(gt)
    inv.platform_port = port

    url = f"http://localhost:{port}"
    print(f"[provision] waiting for gitea at {url} …", file=sys.stderr, flush=True)
    for _ in range(90):
        try:
            if httpx.get(url, timeout=2.0).status_code < 500:
                break
        except Exception:
            pass
        time.sleep(1)
    else:
        raise ProvisionError(f"gitea at {url} never came up")

    # headless bootstrap: the CLI refuses root and needs the work dir env;
    # the web layer answers before migrations finish — retry
    last_err = ""
    token = ""
    for attempt in range(60):
        proc = podman._run([
            "exec", "-u", "git", "-e", "HOME=/data/git", "-e", "GITEA_WORK_DIR=/data/gitea",
            gt, "gitea", "admin", "user", "create",
            "--username", "operator", "--password", admin_password,
            "--email", f"operator@{sim}.invalid", "--admin",
            "--must-change-password=false",
            "--access-token", "--access-token-name", "provision",
        ], check=False)
        out = proc.stdout + proc.stderr
        if proc.returncode == 0 or "already exists" in out:
            for line in out.splitlines():
                if "Access token was successfully created" in line:
                    token = line.split("...", 1)[-1].strip()
            break
        last_err = out.strip()[:300]
        if attempt % 10 == 9:
            print(f"[provision] gitea admin bootstrap retry {attempt + 1}/60 …",
                  file=sys.stderr, flush=True)
        time.sleep(1)
    else:
        raise ProvisionError(f"gitea admin user creation failed: {last_err}")

    secrets = {"platform": "gitea", "admin_username": "operator",
               "admin_password": admin_password, "gitea_port": port,
               "gitea_url_external": url, "gitea_url_internal": f"http://{gt}:3000"}
    if token:      # re-provision may find the user already present (no token
        secrets["admin_token"] = token   # on stdout) — fall back to the old one
    return secrets


def _up_platform(sim: str, inv: Inventory, platform: str) -> dict:
    """Network + postgres + <platform> + admin + admin token. Returns the secrets."""
    import secrets as secrets_mod

    spec = PLATFORMS[platform]
    _ensure_platform_images(spec)
    pg = _up_postgres(sim, inv, _pg_password())

    # re-provisioning reuses the existing platform volume — keep its admin
    # credentials, don't mint new (wrong) ones
    existing = json.loads(secrets_path(sim).read_text(encoding="utf-8")) \
        if secrets_path(sim).exists() else None
    admin_password = existing["admin_password"] if existing else secrets_mod.token_urlsafe(12)

    port = _free_port()
    secrets = _up_gogs(sim, inv, pg, _pg_password(), port, admin_password) \
        if platform == "gogs" else \
        _up_gitea(sim, inv, pg, _pg_password(), port, admin_password)

    if "admin_token" not in secrets:
        url = secrets[f"{platform}_url_external"]
        secrets["admin_token"] = existing["admin_token"] if existing else \
            PLATFORMS[platform].client(token="-", base_url=url).create_token(
                "operator", admin_password, "provision")
    secrets_path(sim).write_text(json.dumps(secrets, indent=2), encoding="utf-8")
    return secrets


def preflight(client) -> None:
    try:
        who = client.whoami()
    except API_ERRORS as e:
        raise ProvisionError(f"platform unreachable or token invalid: {e}") from e
    if not who.get("login"):
        raise ProvisionError("platform token did not authenticate")
    if not store.world_exists():
        raise ProvisionError("no world yet — run `polis world genesis` first")
    try:
        gitcmd.run(None, "--version")
    except Exception as e:
        raise ProvisionError(f"git unusable: {e}") from e


def _ensure_user(client, username: str, email: str, password: str,
                 display: str) -> None:
    try:
        client.create_user(username, email, password, display)
    except API_ERRORS as e:
        if "already exists" not in str(e) and "422" not in str(e):
            raise


def _ensure_org(client, username: str, full_name: str = "") -> None:
    try:
        client.create_org(username, full_name)
    except API_ERRORS as e:
        if "already exists" not in str(e) and "422" not in str(e):
            raise


def _ensure_repo(client, owner: str, name: str) -> None:
    if not client.repo_exists(owner, name):
        client.create_repo(owner, name)


FOUNDING_FILES = {
    "constitution/01-foundation.md": (
        "# Article 1 — Foundation\n\n"
        "The Concord of the Nine Cities recognizes one common law.\n\n"
        "# Article 2 — Custom\n\n"
        "The customs of the cities, as they stood at the founding, are law "
        "until altered by the common procedure.\n"
    ),
    "constitution/02-customary-machinery.md": (
        "# Article 3 — The Customary Machinery\n\n"
        "At the founding, the Concord's machinery is customary. The archive\n"
        "host knows refs and nothing of offices, petitions or approvals: the\n"
        "constitution is enforced by people, and the record of its proceedings\n"
        "is kept by the institutions alone.\n\n"
        "The Concord operates in phase 1 — the customary era. The machinery\n"
        "may be codified only by law enacted through the common procedure; no\n"
        "institution of the Concord may alter the machinery except by an act\n"
        "of the Concord.\n"
    ),
}


def _founding_repo(world, workdir: Path) -> Path:
    """The founding corpus, committed ONCE — every repo in the sim receives
    the same commit, so all histories are related (the founding is one act;
    the cities receive copies of the one archive)."""
    repo = workdir / "seed-founding"
    if (repo / ".git").exists():
        return repo
    repo.mkdir(parents=True, exist_ok=True)
    fed = world.federation
    gitcmd.run(repo, "init", "-b", "main")
    for path, content in FOUNDING_FILES.items():
        p = repo / path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
    for domain in fed.domains:
        p = repo / domain / "README.md"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(f"# {domain.title()}\n\nStatutes of the {domain} domain.\n",
                     encoding="utf-8")
    for city in world.cities:
        p = repo / "municipal" / city.id / "README.md"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(f"# Municipal law of {city.display_name}\n", encoding="utf-8")
    gitcmd.run(repo, "-c", "user.name=The Keeper", "-c", "user.email=keeper@archive.invalid", "add", "-A")
    gitcmd.run(repo, "-c", "user.name=The Keeper", "-c", "user.email=keeper@archive.invalid",
               "commit", "-m", "The Founding Corpus")
    return repo


def _seed_repo(client, owner: str, name: str, token: str,
               world, workdir: Path, base_url: str) -> None:
    """Push the founding corpus if the repo is empty (idempotent)."""
    url = f"{base_url}/{owner}/{name}.git"
    auth_url = url.replace("://", f"://{token}@")
    probe = subprocess.run(["git", "ls-remote", auth_url, "main"],
                           capture_output=True, text=True)
    if probe.returncode == 0 and probe.stdout.strip():
        return                                # already seeded
    founding = _founding_repo(world, workdir)
    gitcmd.run(founding, "push", auth_url, "main:main")


def up(sim: str, platform: str = "gogs", with_city_containers: bool = False,
       force: bool = False) -> Inventory:
    if platform not in PLATFORMS:
        raise ProvisionError(f"unknown platform '{platform}' "
                             f"(choose from: {', '.join(PLATFORMS)})")
    _validate_sim_id(sim)
    world = store.load_world()
    fed = world.federation
    inv = Inventory(sim=sim, created_at=_utcnow(), platform=platform)
    workdir = SIMS_DIR / sim / "work"
    workdir.mkdir(parents=True, exist_ok=True)

    # --- the sim's own platform: network, postgres, <platform> ---------------
    secrets = _up_platform(sim, inv, platform)
    client = sim_platform_client(sim)
    preflight(client)
    base_url = secrets[f"{platform}_url_external"]

    # --- users + per-sim tokens ---------------------------------------------
    tokens: dict[str, str] = {}
    for p in world.persons:
        uname = f"{sim}-{p.username}"
        _ensure_user(client, uname, f"{uname}@{p.member_of.id}.invalid",
                     p.credentials.password, p.display_name)
        tokens[p.username] = client.create_token(uname, p.credentials.password, sim)
        inv.users.append(uname)
    # NOTE: per-sim tokens go ONLY into the sim slices (below) — the civil
    # registry (world.json) never carries per-sim machinery credentials.

    keeper_token = tokens["e.vexley"] if "e.vexley" in tokens else next(iter(tokens.values()))

    # --- archive org + repo + founding corpus --------------------------------
    # the Keeper of the Federal Rolls needs write everywhere he seeds/merges
    keeper_username = "e.vexley"
    keeper_sim_user = f"{sim}-{keeper_username}"

    archive_org = f"{sim}-archive"
    _ensure_org(client, archive_org, "The Federal Archive")
    inv.orgs.append(archive_org)
    _ensure_repo(client, archive_org, fed.repo)
    inv.repos.append(f"{archive_org}/{fed.repo}")
    client.add_collaborator(archive_org, fed.repo, keeper_sim_user, "write")
    _seed_repo(client, archive_org, fed.repo, keeper_token, world, workdir, base_url)

    # --- city orgs + repos + collaborators ------------------------------------
    # gitea: city repos are FORKS of the federal archive (cross-repo PRs
    # require the head repo to be a real fork — phase-2 proceedings, 0038).
    # gogs: no forks API — plain repos seeded by push (phase 1 has no PRs).
    # The Keeper's write grant precedes any seed push.
    for city in world.cities:
        org = f"{sim}-{city.id}"
        _ensure_org(client, org, city.display_name)
        inv.orgs.append(org)
        if platform == "gitea":
            if not client.repo_exists(org, fed.repo):
                client.create_fork(archive_org, fed.repo, org)
        else:
            _ensure_repo(client, org, fed.repo)
        inv.repos.append(f"{org}/{fed.repo}")
        client.add_collaborator(org, fed.repo, keeper_sim_user, "write")
        for p in world.city_persons(city.id):
            client.add_collaborator(org, fed.repo, f"{sim}-{p.username}", "write")
        if platform != "gitea":
            _seed_repo(client, org, fed.repo, keeper_token, world, workdir, base_url)

    # --- per-sim slices ---------------------------------------------------------
    slices_dir = SIMS_DIR / sim / "cities"
    slices_dir.mkdir(parents=True, exist_ok=True)
    internal = secrets[f"{platform}_url_internal"]
    for city in world.cities:
        slice_ = store.city_slice(world, city.id)
        slice_["federation"]["platform"] = platform     # the provisioned product
        slice_["git"]["remotes"] = {
            "origin": f"{internal}/{sim}-{city.id}/{fed.repo}.git",
            "upstream": f"{internal}/{archive_org}/{fed.repo}.git",
        }
        for citizen in slice_["citizens"]:
            citizen["credentials"]["api_tokens"] = {
                platform: tokens[citizen["username"]]
            }
        (slices_dir / f"{city.id}.json").write_text(
            json.dumps(slice_, indent=2), encoding="utf-8")
    inv.slices_dir = str(slices_dir)

    # --- operator container (the director's home — always) ----------------------
    inv.containers.append(_run_operator_container(sim))

    # --- city containers (optional phase) ---------------------------------------
    if with_city_containers:
        inv.containers += _up_containers(sim, world, slices_dir)

    inv.notes.append(PLATFORMS[platform].notes.format(plat_dir=platform_dir(sim)))
    inv.save()
    return inv


CITY_IMAGE = "polis-city:latest"


def _ensure_image() -> str:
    """Build the operator/city image (contains the polis package — always
    rebuilt so the containers run the current code)."""
    dockerfile = config.PROJECT_ROOT / "docker" / "polis-city" / "Dockerfile"
    if not dockerfile.exists():
        raise ProvisionError(f"city image Dockerfile missing: {dockerfile}")
    subprocess.run(["podman", "build", "-t", CITY_IMAGE, "-f", str(dockerfile),
                    str(config.PROJECT_ROOT)], check=True, capture_output=True)
    return CITY_IMAGE


def _run_operator_container(sim: str) -> str:
    """Create the sim's operator container (the director's home).

    On the platform network (no host-swap, ever); the sim's whole run dir
    is mounted at /sim (rw) — slices, matters, journal, stories, situation
    — and the legal source data is mounted read-only like in city nodes.
    The host CLI proxies platform-touching actions into this container.
    """
    image = _ensure_image()
    name = f"polis-operator-{sim}"
    podman._run(["rm", "-f", name], check=False)
    sim_dir = SIMS_DIR / sim
    sim_dir.mkdir(parents=True, exist_ok=True)
    podman._run([
        "run", "-d", "--name", name,
        "--network", f"{sim}-net",
        "-v", f"{sim_dir}:/sim:rw",
        # the world mount is WRITABLE: the phase transition (task 0038) is
        # the Keeper's own archival act, and it records the new machinery
        # state in the civil registry (world.json) from inside the operator
        "-v", f"{config.WORLD_DIR}:/polis-data/world",
        "-e", "POLIS_DATA_DIR=/polis-data",
        "-e", "POLIS_SIM_DIR=/sim",
        "-e", "POLIS_MATTERS_FILE=/sim/matters.json",
        "-w", "/sim",
        image,
    ])
    return name


def _up_containers(sim: str, world, slices_dir: Path) -> list[str]:
    image = _ensure_image()
    # every city gets its own persistent docket — municipal grievances are
    # the city's own record, kept on the host (inspectable), mounted rw
    dockets = SIMS_DIR / sim / "dockets"
    dockets.mkdir(parents=True, exist_ok=True)
    names = []
    for city in world.cities:
        name = f"polis-city-{city.id}-{sim}"
        docket = dockets / f"{city.id}.json"
        if not docket.exists():
            docket.write_text('{"matters": []}', encoding="utf-8")
        podman._run(["rm", "-f", name], check=False)
        podman._run([
            "run", "-d", "--name", name,
            "--network", f"{sim}-net",
            "-v", f"{slices_dir}/{city.id}.json:/etc/polis/city.json:ro",
            "-v", f"{config.WORLD_DIR}/legal:/polis-data/world/legal:ro",
            "-v", f"{docket}:/polis-city/matters.json:rw",
            "-e", "POLIS_CITY_CONFIG=/etc/polis/city.json",
            "-e", "POLIS_DATA_DIR=/polis-data",
            "-e", "POLIS_MATTERS_FILE=/polis-city/matters.json",
            image,
        ])
        names.append(name)
    return names


# --- the Mechanical Magistrate's CI (task 0041) ---------------------------------

WOODPECKER_SERVER_IMAGE = "polis/woodpecker-server"
WOODPECKER_AGENT_IMAGE = "polis/woodpecker-agent"


def up_woodpecker(sim: str) -> None:
    """Erect the Mechanical Magistrate's CI (task 0041): per-sim woodpecker
    server + agent, the OAuth application on the sim's gitea, the
    Magistrate's first login (the OAuth dance), the archive repo enabled
    for builds, and the forge webhook. Idempotent."""
    import secrets as secrets_mod
    import time

    import httpx

    inv = Inventory.load(sim)
    secrets = load_secrets(sim)
    wp = f"{sim}-woodpecker-server"
    agent = f"{sim}-woodpecker-agent"
    if secrets.get("woodpecker_token") and podman.container_running(wp):
        return                            # already erected
    if inv.platform != "gitea":
        raise ProvisionError("the CI is erected only on gitea-hosted sims")
    world = store.load_world()
    gitea_port = secrets["gitea_port"]
    gitea_url = secrets["gitea_url_external"]
    magistrate_user = f"{sim}-mechanical-magistrate"
    mag_pw = next(p.credentials.password for p in world.persons
                  if p.username == "mechanical-magistrate")

    # images
    for image, df in ((WOODPECKER_SERVER_IMAGE, "woodpecker"),
                      (WOODPECKER_AGENT_IMAGE, "woodpecker-agent")):
        dockerfile = config.PROJECT_ROOT / "docker" / df / "Dockerfile"
        if not dockerfile.exists():
            raise ProvisionError(f"woodpecker Dockerfile missing: {dockerfile}")
        if podman._run(["image", "exists", image], check=False).returncode != 0:
            podman._run(["build", "-t", image, "-f", str(dockerfile),
                         str(config.PROJECT_ROOT)], check=True)

    wp_port = _free_port()
    agent_secret = secrets_mod.token_urlsafe(16)
    grpc_secret = secrets_mod.token_urlsafe(16)

    # 1. the OAuth application on the sim's gitea (before the server starts).
    #    Two redirect URIs: the operator's loopback AND the WOODPECKER_HOST
    #    form the server itself uses at exchange time.
    gt = GiteaClient(token=secrets["admin_token"], base_url=gitea_url)
    oauth = gt._request("POST", "/api/v1/user/applications/oauth2", json={
        "name": "woodpecker",
        "redirect_uris": [f"http://localhost:{wp_port}/authorize",
                          f"http://host.containers.internal:{wp_port}/authorize"],
        "confidential_client": True,
    }).json()

    # 2. the Magistrate's gitea token (the pipeline's API credential)
    mag_token = gt.create_token(magistrate_user, mag_pw, "ci")

    # 3. the server
    plat = platform_dir(sim)
    (plat / "woodpecker" / "server").mkdir(parents=True, exist_ok=True)
    server_env = {
        "WOODPECKER_OPEN": "true",
        # the forge's webhook calls WOODPECKER_HOST/api/hook — the forge
        # (a VM container) reaches the published port through the mac
        # loopback; a localhost URL would resolve to the forge itself
        "WOODPECKER_HOST": f"http://host.containers.internal:{wp_port}",
        "WOODPECKER_AGENT_SECRET": agent_secret,
        "WOODPECKER_GRPC_SECRET": grpc_secret,
        "WOODPECKER_ADMIN": magistrate_user,
        "WOODPECKER_GITEA": "true",
        "WOODPECKER_GITEA_URL": f"http://{sim}-gitea:3000",
        "WOODPECKER_DEV_GITEA_OAUTH_URL": f"http://localhost:{gitea_port}",
        "WOODPECKER_GITEA_CLIENT": oauth["client_id"],
        "WOODPECKER_GITEA_SECRET": oauth["client_secret"],
    }
    run_args = ["run", "-d", "--name", wp, "--network", f"{sim}-net",
                "--restart", "unless-stopped", "-p", f"{wp_port}:8000"]
    for k, v in server_env.items():
        run_args += ["-e", f"{k}={v}"]
    run_args += ["-v", f"{plat / 'woodpecker' / 'server'}:/var/lib/woodpecker",
                 WOODPECKER_SERVER_IMAGE]
    podman._run(["rm", "-f", wp], check=False)
    proc = podman._run(run_args)
    if proc.returncode != 0:
        raise ProvisionError(f"woodpecker server start failed: {proc.stderr.strip()[:300]}")

    # 4. the agent (the macOS VM quirks: root, SELinux, the VM socket)
    (plat / "woodpecker" / "agent").mkdir(parents=True, exist_ok=True)
    podman._run(["rm", "-f", agent], check=False)
    proc = podman._run([
        "run", "-d", "--name", agent,
        "--user", "0:0", "--security-opt", "label=disable",
        "--network", f"{sim}-net",
        "-v", f"{plat / 'woodpecker' / 'agent'}:/etc/woodpecker",
        "-v", "/run/user/501/podman/podman.sock:/var/run/docker.sock",
        "-e", "DOCKER_HOST=unix:///var/run/docker.sock",
        "-e", f"WOODPECKER_SERVER={wp}:9000",
        "-e", f"WOODPECKER_AGENT_SECRET={agent_secret}",
        "-e", f"WOODPECKER_BACKEND_DOCKER_NETWORK={sim}-net",
        WOODPECKER_AGENT_IMAGE,
    ])
    if proc.returncode != 0:
        raise ProvisionError(f"woodpecker agent start failed: {proc.stderr.strip()[:300]}")

    # 5. wait for the server
    wp_url = f"http://localhost:{wp_port}"
    print(f"[provision] waiting for woodpecker at {wp_url} …", file=sys.stderr, flush=True)
    for _ in range(60):
        try:
            if httpx.get(f"{wp_url}/healthz", timeout=2.0).status_code == 204:
                break
        except Exception:
            pass
        time.sleep(1)
    else:
        raise ProvisionError(f"woodpecker at {wp_url} never came up")

    # 6. the Magistrate's first login — the OAuth dance (gitea session →
    #    grant → woodpecker session → CSRF → mint the API token)
    wp_token = _woodpecker_oauth_login(gitea_url, magistrate_user, mag_pw,
                                       wp_url, oauth["client_id"])

    # 7. enable the archive repo (the Magistrate must hold admin rights on
    #    the forge repo it guards). Woodpecker registers its own forge
    #    webhook at enable time — WOODPECKER_HOST (above) makes it
    #    deliverable from inside the forge's network.
    wc = WoodpeckerClient(token=wp_token, base_url=wp_url)
    archive_org = f"{sim}-archive"
    gt.add_collaborator(archive_org, "common-law", magistrate_user, "admin")
    repo_id = gt._request("GET", f"/api/v1/repos/{archive_org}/common-law").json()["id"]
    enabled = wc.enable_repo(repo_id, archive_org, "common-law")
    # fork PRs are blocked pending approval by default (require_approval:
    # "forks") — the Magistrate's office already holds the approval; let
    # the checks run. (v3 enum: none | forks | all.)
    wc._request("PATCH", f"/api/repos/{enabled.get('id')}",
                json={"require_approval": "none"})

    # the cities hold copies of the one archive — sync the forks so every
    # repo carries the codified machinery (a PR's pipeline config is read
    # from its HEAD — the fork)
    synced = 0
    for org in [o for o in inv.orgs if o != archive_org]:
        proc = subprocess.run(
            ["git", "push", "-q",
             f"http://{secrets['admin_token']}@localhost:{gitea_port}/"
             f"{org}/common-law.git", "main:main"],
            cwd=str(SIMS_DIR / sim / "common-law"), capture_output=True, text=True)
        if proc.returncode == 0:
            synced += 1
    print(f"[provision] {synced} city archives synced to the codified machinery",
          file=sys.stderr, flush=True)

    # the formal checks' gitea context, injected into every pipeline step
    # (global secrets — WOODPECKER_ENVIRONMENT's comma format mangles URLs)
    wc.create_global_secret("POLIS_GITEA_URL", f"http://{sim}-gitea:3000",
                            ["pull_request"])
    wc.create_global_secret("POLIS_GITEA_TOKEN", mag_token, ["pull_request"])

    # 8. persist
    secrets.update({
        "woodpecker_port": wp_port, "woodpecker_url_external": wp_url,
        "woodpecker_token": wp_token, "woodpecker_agent_secret": agent_secret,
        "woodpecker_gitea_client": oauth["client_id"],
        "woodpecker_gitea_secret": oauth["client_secret"],
    })
    secrets_path(sim).write_text(json.dumps(secrets, indent=2), encoding="utf-8")
    inv.containers += [wp, agent]
    inv.save()


def _woodpecker_oauth_login(gitea_url: str, username: str, password: str,
                            wp_url: str, client_id: str) -> str:
    """The Magistrate logs into the CI: gitea session → OAuth grant →
    woodpecker session → CSRF token → the woodpecker API token (a JWT).
    Gitea quirks: no CSRF field on the login form; the grant form needs
    granted=true; already-authorized apps redirect straight to the
    callback."""
    import re

    import httpx

    s = httpx.Client(base_url=gitea_url, follow_redirects=False, timeout=20)
    if s.get("/user/login").status_code != 200:
        raise ProvisionError(f"gitea login page unreachable at {gitea_url}")
    r = s.post("/user/login", data={"user_name": username, "password": password})
    if r.status_code not in (302, 303):
        raise ProvisionError(f"gitea login as {username} failed: {r.status_code}")
    # the authorize redirect MUST match the redirect woodpecker sends at
    # exchange time (WOODPECKER_HOST + /authorize), or gitea refuses the
    # grant ("redirect_uri differs"); we only READ the callback Location —
    # never follow it — so the unreachable host doesn't matter here
    port = wp_url.rsplit(":", 1)[-1]
    redirect_uri = f"http://host.containers.internal:{port}/authorize"
    r = s.get("/login/oauth/authorize"
              f"?client_id={client_id}&redirect_uri={redirect_uri}&response_type=code")
    if r.status_code in (302, 303):
        loc = r.headers.get("Location", "")
    else:
        fields = {m.group(1): m.group(2) for m in
                  re.finditer(r'<input type="hidden" name="([^"]+)" value="([^"]*)">',
                              r.text)}
        fields["granted"] = "true"
        loc = s.post("/login/oauth/grant", data=fields).headers.get("Location", "")
    if not loc or "code=" not in loc:
        raise ProvisionError(f"gitea OAuth grant failed: {loc[:200]}")
    # exchange the code against the operator's loopback (the code is not
    # bound to the redirect host), walking the redirects manually
    from urllib.parse import urljoin
    ws = httpx.Client(base_url=wp_url, follow_redirects=False, timeout=20)
    code_url = re.sub(r"^https?://[^/]+", wp_url, loc)   # localhost, same path+query
    url = code_url
    sess = None
    for _ in range(5):
        r = ws.get(url)
        sess = r.cookies.get("user_sess") or sess
        if r.status_code in (302, 303, 307, 308):
            url = urljoin(url, r.headers.get("Location", ""))
            continue
        break
    if not sess:
        raise ProvisionError("woodpecker login did not establish a session")
    headers = {"Cookie": f"user_sess={sess}"}
    cfg = httpx.get(f"{wp_url}/web-config.js", headers=headers, timeout=10)
    csrf = re.search(r'WOODPECKER_CSRF = "([^"]*)"', cfg.text)
    if not csrf or not csrf.group(1):
        raise ProvisionError("woodpecker login did not establish a session")
    r = httpx.post(f"{wp_url}/api/user/token",
                   headers={**headers, "X-CSRF-Token": csrf.group(1)}, timeout=10)
    if r.status_code != 200:
        raise ProvisionError(f"woodpecker token mint failed: {r.status_code}")
    return r.text.strip()


# --- status / teardown ---------------------------------------------------------

def status(sim: str) -> dict:
    inv = Inventory.load(sim)
    client = sim_platform_client(sim)
    report = {"sim": sim, "ok": True, "platform": inv.platform, "items": []}

    def item(kind: str, name: str, exists: bool, note: str = ""):
        report["items"].append({"kind": kind, "name": name, "exists": exists, "note": note})
        if not exists:
            report["ok"] = False

    for u in inv.users:
        item("user", u, client.user_exists(u))
    for r in inv.repos:
        owner, name = r.split("/", 1)
        item("repo", r, client.repo_exists(owner, name))
    for o in inv.orgs:
        if inv.platform == "gitea":
            item("org", o, client.org_exists(o))
        else:
            item("org", o, True, "existence not checked (no org-delete/list-by-name route)")
    for c in inv.containers:
        item("container", c, podman.container_running(c),
             podman.container(c).get("State") if podman.container(c) else "absent")
    item("slices", inv.slices_dir, Path(inv.slices_dir).is_dir())
    return report


def stop(sim: str) -> dict:
    """Pause the sim: stop its containers, keep volumes/slices/journal."""
    inv = Inventory.load(sim)
    stopped = []
    for c in inv.containers:
        if podman.container_running(c):
            podman._run(["stop", c], check=False)
            stopped.append(c)
    return {"stopped": stopped}


def start(sim: str) -> dict:
    """Resume a stopped sim, in dependency order (postgres must be ready
    before gogs, or gogs crash-loops on connect refusal)."""
    import time
    inv = Inventory.load(sim)
    pg = f"{sim}-postgres"
    order = ([pg] if pg in inv.containers else []) + \
            [c for c in inv.containers if c != pg]
    started = []
    for c in order:
        if not podman.container_running(c):
            podman._run(["start", c], check=False)
            started.append(c)
        if c == pg:
            for _ in range(60):
                if podman._run(["exec", pg, "pg_isready", "-U", "gogs"],
                               check=False).returncode == 0:
                    break
                time.sleep(1)
    return {"started": started}


def sim_containers(sim: str) -> list[str]:
    """All containers belonging to a sim, matched by NAME PATTERN (the
    inventory goes stale; names don't)."""
    proc = podman._run(["ps", "-a", "--format", "{{.Names}}"], check=False)
    names = proc.stdout.split()
    return sorted(n for n in names
                  if n in (f"{sim}-postgres", f"{sim}-gogs", f"{sim}-gitea",
                           f"{sim}-woodpecker-server", f"{sim}-woodpecker-agent",
                           f"polis-operator-{sim}")
                  or (n.startswith("polis-city-") and n.endswith(f"-{sim}")))


def destroy(sim: str) -> dict:
    """Full controlled removal of a sim: API cleanup (best effort), every
    container, the network, and the sim dir itself. Tolerant of partial
    state (torn-down or half-provisioned sims, missing inventory)."""
    import shutil
    done: dict[str, Any] = {"repos": 0, "users": 0, "containers": [],
                            "network": None, "dir": None}

    # API cleanup if the sim's platform answers (orgs die with it regardless)
    try:
        inv = Inventory.load(sim)
        client = sim_platform_client(sim)
        for r in inv.repos:
            owner, name = r.split("/", 1)
            try:
                client.delete_repo(owner, name)
                done["repos"] += 1
            except API_ERRORS:
                pass
        if inv.platform == "gitea":
            for o in inv.orgs:
                try:
                    client.delete_org(o)
                except API_ERRORS:
                    pass
        for u in inv.users:
            try:
                client.delete_user(u)
                done["users"] += 1
            except API_ERRORS:
                pass
    except Exception:
        pass                                    # platform gone or inventory stale — fine

    for c in sim_containers(sim):
        podman._run(["rm", "-f", c], check=False)
        done["containers"].append(c)
    podman._run(["network", "rm", f"{sim}-net"], check=False)
    done["network"] = f"{sim}-net"
    # container restarts leave anonymous volumes behind (the platform
    # images declare VOLUMEs); prune the orphans — a full VM disk is the
    # alternative
    podman._run(["volume", "prune", "-f"], check=False)

    sim_dir = SIMS_DIR / sim
    if sim_dir.exists():
        shutil.rmtree(sim_dir)
        done["dir"] = str(sim_dir)
    return done


def list_sims() -> list[dict]:
    """Every sim known on this host: dirs, live containers, record summary."""
    sims: set[str] = set()
    if SIMS_DIR.is_dir():
        sims |= {p.name for p in SIMS_DIR.iterdir() if p.is_dir()}
    proc = podman._run(["ps", "-a", "--format", "{{.Names}}"], check=False)
    for n in proc.stdout.split():
        for suffix in ("-postgres", "-gogs", "-gitea"):
            if n.endswith(suffix) and not n.startswith("polis-"):
                sims.add(n[: -len(suffix)])
        if n.startswith("polis-operator-"):
            sims.add(n.removeprefix("polis-operator-"))
        if n.startswith("polis-city-") and n.count("-") >= 3:
            sims.add(n.rsplit("-", 1)[-1])
    out = []
    for sim in sorted(sims):
        sim_dir = SIMS_DIR / sim
        containers = sim_containers(sim)
        running = [c for c in containers if podman.container_running(c)]
        record = {}
        journal = sim_dir / "journal.jsonl"
        if journal.exists():
            record["entries"] = len(journal.read_text(encoding="utf-8").splitlines())
        out.append({"sim": sim, "dir": sim_dir.exists(), "containers": containers,
                    "running": running, **record})
    return out


def teardown(sim: str) -> dict:
    inv = Inventory.load(sim)
    client = sim_platform_client(sim)
    done = {"repos": 0, "users": 0, "containers": 0}
    for r in inv.repos:
        owner, name = r.split("/", 1)
        try:
            client.delete_repo(owner, name)
            done["repos"] += 1
        except API_ERRORS:
            pass
    if inv.platform == "gitea":
        for o in inv.orgs:
            try:
                client.delete_org(o)
            except API_ERRORS:
                pass
    # users before containers — the API must still be reachable
    for u in inv.users:
        try:
            client.delete_user(u)
            done["users"] += 1
        except API_ERRORS:
            pass
    for c in inv.containers:
        podman._run(["rm", "-f", c], check=False)
        done["containers"] += 1
    if inv.network:
        podman._run(["network", "rm", inv.network], check=False)
        done["network"] = inv.network
    return done
