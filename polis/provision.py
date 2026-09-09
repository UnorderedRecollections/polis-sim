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
import subprocess
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

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


def _seed_repo(client: GogsClient, owner: str, name: str, token: str,
               world, workdir: Path) -> None:
    """Push the founding corpus if the repo is empty (idempotent)."""
    url = f"{config.GOGS_URL}/{owner}/{name}.git"
    auth_url = url.replace("://", f"://{token}@")
    clone = workdir / f"seed-{owner}-{name}"
    if clone.exists():
        return
    gitcmd.run(None, "clone", auth_url, str(clone))
    has_commits = subprocess.run(
        ["git", "-C", str(clone), "rev-parse", "--verify", "HEAD"],
        capture_output=True).returncode == 0
    if has_commits:
        return
    fed = world.federation
    for path, content in FOUNDING_FILES.items():
        p = clone / path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
    for domain in fed.domains:
        p = clone / domain / "README.md"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(f"# {domain.title()}\n\nStatutes of the {domain} domain.\n",
                     encoding="utf-8")
    for city in world.cities:
        p = clone / "municipal" / city.id / "README.md"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(f"# Municipal law of {city.display_name}\n", encoding="utf-8")
    gitcmd.run(clone, "-c", "user.name=The Keeper",
               "-c", "user.email=keeper@archive.invalid", "add", "-A")
    gitcmd.run(clone, "-c", "user.name=The Keeper",
               "-c", "user.email=keeper@archive.invalid",
               "commit", "-m", "The Founding Corpus")
    gitcmd.run(clone, "push", "origin", "HEAD:main")


def up(sim: str, with_city_containers: bool = False, force: bool = False) -> Inventory:
    _validate_sim_id(sim)
    client = GogsClient()
    preflight(client)
    world = store.load_world()
    fed = world.federation
    inv = Inventory(sim=sim, created_at=_utcnow())
    workdir = SIMS_DIR / sim / "work"
    workdir.mkdir(parents=True, exist_ok=True)

    # --- users + per-sim tokens ---------------------------------------------
    tokens: dict[str, str] = {}
    for p in world.persons:
        uname = f"{sim}-{p.username}"
        _ensure_user(client, uname, f"{uname}@{p.member_of.id}.invalid",
                     p.credentials.password, p.display_name)
        tokens[p.username] = client.create_token(uname, p.credentials.password, sim)
        p.credentials.api_tokens[f"gogs@{sim}"] = tokens[p.username]
        inv.users.append(uname)
    store.save_world(world)

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
    _seed_repo(client, archive_org, fed.repo, keeper_token, world, workdir)

    # --- city orgs + repos + collaborators ------------------------------------
    for city in world.cities:
        org = f"{sim}-{city.id}"
        _ensure_org(client, org, city.display_name)
        inv.orgs.append(org)
        _ensure_repo(client, org, fed.repo)
        inv.repos.append(f"{org}/{fed.repo}")
        client.add_collaborator(org, fed.repo, keeper_sim_user, "write")
        _seed_repo(client, org, fed.repo, keeper_token, world, workdir)
        for p in world.city_persons(city.id):
            client.add_collaborator(org, fed.repo, f"{sim}-{p.username}", "write")

    # --- per-sim slices ---------------------------------------------------------
    slices_dir = SIMS_DIR / sim / "cities"
    slices_dir.mkdir(parents=True, exist_ok=True)
    for city in world.cities:
        slice_ = store.city_slice(world, city.id)
        slice_["git"]["remotes"] = {
            "origin": f"http://gogs:3000/{sim}-{city.id}/{fed.repo}.git",
            "upstream": f"http://gogs:3000/{archive_org}/{fed.repo}.git",
        }
        for citizen in slice_["citizens"]:
            citizen["credentials"]["api_tokens"] = {
                "gogs": tokens[citizen["username"]]
            }
        (slices_dir / f"{city.id}.json").write_text(
            json.dumps(slice_, indent=2), encoding="utf-8")
    inv.slices_dir = str(slices_dir)

    # --- city containers (optional phase) ---------------------------------------
    if with_city_containers:
        inv.containers += _up_containers(sim, world, slices_dir)

    inv.notes.append("orgs are teardown-exempt (this gogs build has no org-delete route)")
    inv.save()
    return inv


def _up_containers(sim: str, world, slices_dir: Path) -> list[str]:
    image = "polis-city:latest"
    dockerfile = config.PROJECT_ROOT / "docker" / "polis-city" / "Dockerfile"
    if not dockerfile.exists():
        raise ProvisionError(f"city image Dockerfile missing: {dockerfile}")
    subprocess.run(["podman", "build", "-t", image, "-f", str(dockerfile),
                    str(config.PROJECT_ROOT)], check=True, capture_output=True)
    names = []
    for city in world.cities:
        name = f"polis-city-{city.id}-{sim}"
        podman._run(["rm", "-f", name], check=False)
        podman._run([
            "run", "-d", "--name", name,
            "--network", config.PODMAN_NETWORK,
            "-v", f"{slices_dir}/{city.id}.json:/etc/polis/city.json:ro",
            "-v", f"{config.WORLD_DIR}/legal:/polis-data/world/legal:ro",
            "-e", "POLIS_CITY_CONFIG=/etc/polis/city.json",
            "-e", "POLIS_DATA_DIR=/polis-data",
            image,
        ])
        names.append(name)
    return names


# --- status / teardown ---------------------------------------------------------

def status(sim: str) -> dict:
    inv = Inventory.load(sim)
    client = GogsClient()
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


def teardown(sim: str) -> dict:
    inv = Inventory.load(sim)
    client = GogsClient()
    done = {"repos": 0, "users": 0, "containers": 0, "orgs_kept": len(inv.orgs)}
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
    for u in inv.users:
        try:
            client.delete_user(u)
            done["users"] += 1
        except GogsError:
            pass
    return done
