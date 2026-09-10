"""polis provision — the porcelain layer over the platform plumbing.

Assembles everything one sim instance needs (docs/design/provisioning.md):
users with per-sim tokens, the archive org/repo + founding corpus, city
orgs/repos, per-sim slices, an inventory (provision.json) that status and
teardown consume. Idempotent: re-running `up` reconciles.

Naming (everything carries the sim id):
  org   <sim>-archive, repo common-law
  orgs  <sim>-<city>, repo common-law (plain repos — this gogs build has no
        forks API; city repos are seeded by pushing the founding corpus)
  users <sim>-<username>
  containers polis-city-<city>-<sim>
"""
from __future__ import annotations

import json
import os
import subprocess
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import config, store
from .clients import podman
from .clients.gogs import GogsClient, GogsError
from .legislation import gitcmd
from .sim.journal import SIMS_DIR


class ProvisionError(RuntimeError):
    pass


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


@dataclass
class Inventory:
    sim: str
    created_at: str = ""
    users: list[str] = field(default_factory=list)
    orgs: list[str] = field(default_factory=list)
    repos: list[str] = field(default_factory=list)        # "owner/name"
    containers: list[str] = field(default_factory=list)
    slices_dir: str = ""
    network: str = ""                # the sim's private podman network
    gogs_port: int = 0               # host port → the sim's gogs :3000
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
        return cls(**json.loads(path.read_text(encoding="utf-8")))


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


# --- the sim's own platform (task 0027): network + postgres + gogs --------------
#
# A sim is fully self-contained: <sim>-net, <sim>-postgres, <sim>-gogs (host
# port allocated at up-time). Inside the network the gogs URL is constant
# (http://<sim>-gogs:3000) — slices, operator and city containers use it; the
# host port exists only for the operator's CLI (provisioning, ad-hoc checks).
# Per-sim secrets live in data/sims/<sim>/secrets.json (gitignored), never in
# world.json.

GOGS_IMAGE = "polis/gogs"
POSTGRES_IMAGE = "polis/postgres"


def platform_dir(sim: str) -> Path:
    return SIMS_DIR / sim / "platform"


def secrets_path(sim: str) -> Path:
    return SIMS_DIR / sim / "secrets.json"


def load_secrets(sim: str) -> dict:
    path = secrets_path(sim)
    if not path.exists():
        raise ProvisionError(f"no secrets for sim '{sim}' (expected {path})")
    return json.loads(path.read_text(encoding="utf-8"))


def sim_gogs_client(sim: str) -> GogsClient:
    """A client against the sim's own gogs, as the sim's admin."""
    secrets = load_secrets(sim)
    return GogsClient(token=secrets["admin_token"],
                      base_url=f"http://localhost:{secrets['gogs_port']}")


def _free_port(base: int = 11880) -> int:
    import socket
    for port in range(base, base + 200):
        with socket.socket() as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return port
    raise ProvisionError("no free host port for the sim's gogs")


def _ensure_platform_images() -> None:
    for image, dockerfile in ((GOGS_IMAGE, "gogs"), (POSTGRES_IMAGE, "postgres")):
        df = config.PROJECT_ROOT / "docker" / dockerfile / "Dockerfile"
        if not df.exists():
            raise ProvisionError(f"platform Dockerfile missing: {df}")
        if podman._run(["image", "exists", image], check=False).returncode != 0:
            proc = podman._run(["build", "-t", image, "-f", str(df),
                                str(config.PROJECT_ROOT)], check=False)
            if proc.returncode != 0:
                raise ProvisionError(f"building {image} failed: {proc.stderr.strip()[:300]}")


def _up_platform(sim: str, inv: Inventory) -> dict:
    """Network + postgres + gogs + admin + admin token. Returns the secrets."""
    import secrets as secrets_mod
    import time

    import httpx

    _ensure_platform_images()
    net = f"{sim}-net"
    pg, gg = f"{sim}-postgres", f"{sim}-gogs"
    port = _free_port()
    plat = platform_dir(sim)
    conf = plat / "gogs" / "gogs" / "conf"
    conf.mkdir(parents=True, exist_ok=True)
    (plat / "postgres").mkdir(parents=True, exist_ok=True)

    pg_password = (os.environ.get("POSTGRES_PASSWORD")
                   or config._load_env_file().get("POSTGRES_PASSWORD")
                   or "gogs")
    # re-provisioning reuses the existing platform volume — keep its admin
    # credentials, don't mint new (wrong) ones
    existing = json.loads(secrets_path(sim).read_text(encoding="utf-8")) \
        if secrets_path(sim).exists() else None
    admin_password = existing["admin_password"] if existing else secrets_mod.token_urlsafe(12)
    (conf / "app.ini").write_text(f"""[database]
TYPE     = postgres
HOST     = {pg}:5432
NAME     = gogs
USER     = gogs
PASSWORD = {pg_password}
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

    podman._run(["network", "create", net], check=False)
    podman._run(["rm", "-f", pg, gg], check=False)
    proc = podman._run([
        "run", "-d", "--name", pg, "--network", net,
        "-v", f"{plat / 'postgres'}:/var/lib/postgresql/data",
        "-e", "POSTGRES_USER=gogs", "-e", f"POSTGRES_PASSWORD={pg_password}",
        "-e", "POSTGRES_DB=gogs", POSTGRES_IMAGE,
    ])
    if proc.returncode != 0:
        raise ProvisionError(f"postgres start failed: {proc.stderr.strip()[:300]}")
    for _ in range(60):                       # postgres must be ready before gogs
        if podman._run(["exec", pg, "pg_isready", "-U", "gogs"],
                       check=False).returncode == 0:
            break
        time.sleep(1)
    else:
        raise ProvisionError(f"{pg} never became ready")
    proc = podman._run([
        "run", "-d", "--name", gg, "--network", net,
        "--restart", "unless-stopped",
        "-p", f"{port}:3000",
        "-v", f"{plat / 'gogs'}:/data", GOGS_IMAGE,
    ])
    if proc.returncode != 0:
        raise ProvisionError(f"gogs start failed: {proc.stderr.strip()[:300]}")
    inv.containers += [pg, gg]
    inv.network = net
    inv.gogs_port = port

    # wait for the web layer (first start runs migrations — can take a while)
    url = f"http://localhost:{port}"
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
    admin_token = existing["admin_token"] if existing else GogsClient(
        token="-", base_url=url).create_token("operator", admin_password, "provision")
    secrets = {"admin_username": "operator", "admin_password": admin_password,
               "admin_token": admin_token, "gogs_port": port,
               "gogs_url_external": url, "gogs_url_internal": f"http://{gg}:3000"}
    secrets_path(sim).write_text(json.dumps(secrets, indent=2), encoding="utf-8")
    return secrets


def preflight(client: GogsClient) -> None:
    try:
        who = client.whoami()
    except GogsError as e:
        raise ProvisionError(f"gogs unreachable or token invalid: {e}") from e
    if not who.get("login"):
        raise ProvisionError("gogs token did not authenticate")
    if not store.world_exists():
        raise ProvisionError("no world yet — run `polis world genesis` first")
    try:
        gitcmd.run(None, "--version")
    except Exception as e:
        raise ProvisionError(f"git unusable: {e}") from e


def _ensure_user(client: GogsClient, username: str, email: str, password: str,
                 display: str) -> None:
    try:
        client.create_user(username, email, password, display)
    except GogsError as e:
        if "already exists" not in str(e) and "422" not in str(e):
            raise


def _ensure_org(client: GogsClient, username: str, full_name: str = "") -> None:
    try:
        client.create_org(username, full_name)
    except GogsError as e:
        if "already exists" not in str(e) and "422" not in str(e):
            raise


def _ensure_repo(client: GogsClient, owner: str, name: str) -> None:
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


def _seed_repo(client: GogsClient, owner: str, name: str, token: str,
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


def up(sim: str, with_city_containers: bool = False, force: bool = False) -> Inventory:
    _validate_sim_id(sim)
    world = store.load_world()
    fed = world.federation
    inv = Inventory(sim=sim, created_at=_utcnow())
    workdir = SIMS_DIR / sim / "work"
    workdir.mkdir(parents=True, exist_ok=True)

    # --- the sim's own platform: network, postgres, gogs ------------------------
    secrets = _up_platform(sim, inv)
    client = sim_gogs_client(sim)
    preflight(client)
    base_url = secrets["gogs_url_external"]

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
    for city in world.cities:
        org = f"{sim}-{city.id}"
        _ensure_org(client, org, city.display_name)
        inv.orgs.append(org)
        _ensure_repo(client, org, fed.repo)
        inv.repos.append(f"{org}/{fed.repo}")
        client.add_collaborator(org, fed.repo, keeper_sim_user, "write")
        _seed_repo(client, org, fed.repo, keeper_token, world, workdir, base_url)
        for p in world.city_persons(city.id):
            client.add_collaborator(org, fed.repo, f"{sim}-{p.username}", "write")

    # --- per-sim slices ---------------------------------------------------------
    slices_dir = SIMS_DIR / sim / "cities"
    slices_dir.mkdir(parents=True, exist_ok=True)
    internal = secrets["gogs_url_internal"]
    for city in world.cities:
        slice_ = store.city_slice(world, city.id)
        slice_["git"]["remotes"] = {
            "origin": f"{internal}/{sim}-{city.id}/{fed.repo}.git",
            "upstream": f"{internal}/{archive_org}/{fed.repo}.git",
        }
        for citizen in slice_["citizens"]:
            citizen["credentials"]["api_tokens"] = {
                "gogs": tokens[citizen["username"]]
            }
        (slices_dir / f"{city.id}.json").write_text(
            json.dumps(slice_, indent=2), encoding="utf-8")
    inv.slices_dir = str(slices_dir)

    # --- operator container (the director's home — always) ----------------------
    inv.containers.append(_run_operator_container(sim))

    # --- city containers (optional phase) ---------------------------------------
    if with_city_containers:
        inv.containers += _up_containers(sim, world, slices_dir)

    inv.notes.append("orgs/repos/users die with the sim's gogs (its volumes are at "
                     f"{platform_dir(sim)}) — delete with the sim dir")
    inv.save()
    return inv


CITY_IMAGE = "polis-city:latest"


def _ensure_image() -> str:
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
        "-v", f"{config.WORLD_DIR}:/polis-data/world:ro",
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


# --- status / teardown ---------------------------------------------------------

def status(sim: str) -> dict:
    inv = Inventory.load(sim)
    client = sim_gogs_client(sim)
    report = {"sim": sim, "ok": True, "items": []}

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
                  if n in (f"{sim}-postgres", f"{sim}-gogs", f"polis-operator-{sim}")
                  or (n.startswith("polis-city-") and n.endswith(f"-{sim}")))


def destroy(sim: str) -> dict:
    """Full controlled removal of a sim: API cleanup (best effort), every
    container, the network, and the sim dir itself. Tolerant of partial
    state (torn-down or half-provisioned sims, missing inventory)."""
    import shutil
    done: dict[str, Any] = {"repos": 0, "users": 0, "containers": [],
                            "network": None, "dir": None}

    # API cleanup if the sim's gogs answers (orgs die with it regardless)
    try:
        inv = Inventory.load(sim)
        client = sim_gogs_client(sim)
        for r in inv.repos:
            owner, name = r.split("/", 1)
            try:
                client.delete_repo(owner, name)
                done["repos"] += 1
            except GogsError:
                pass
        for u in inv.users:
            try:
                client.delete_user(u)
                done["users"] += 1
            except GogsError:
                pass
    except Exception:
        pass                                    # gogs gone or inventory stale — fine

    for c in sim_containers(sim):
        podman._run(["rm", "-f", c], check=False)
        done["containers"].append(c)
    podman._run(["network", "rm", f"{sim}-net"], check=False)
    done["network"] = f"{sim}-net"

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
        for suffix in ("-postgres", "-gogs"):
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
    client = sim_gogs_client(sim)
    done = {"repos": 0, "users": 0, "containers": 0}
    for r in inv.repos:
        owner, name = r.split("/", 1)
        try:
            client.delete_repo(owner, name)
            done["repos"] += 1
        except GogsError:
            pass
    for c in inv.containers:
        podman._run(["rm", "-f", c], check=False)
        done["containers"] += 1
    if inv.network:
        podman._run(["network", "rm", inv.network], check=False)
        done["network"] = inv.network
    for u in inv.users:
        try:
            client.delete_user(u)
            done["users"] += 1
        except GogsError:
            pass
    return done
