"""polis health — quick diagnosis of every technical subsystem.

Each check reports ok / warn / fail. `polis health` (no subcommand) runs all
subsystems and exits non-zero if anything fails, so it can be wired into
scripts.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import typer

from .. import config
from ..clients import podman
from ..clients.gitea import GiteaClient
from ..clients.gogs import GogsClient
from ..clients.woodpecker import WoodpeckerClient
from ..store import world_exists
from .common import console, get_world, status_table

app = typer.Typer(
    invoke_without_command=True,
    help="Health checks for gogs, gitea, woodpecker, postgres, podman and city nodes.",
)


@dataclass
class Check:
    name: str
    ok: bool
    detail: str = ""
    warn: bool = False  # not-ok renders as a warning instead of a failure


# --- subsystem check suites -------------------------------------------------

def check_gogs() -> list[Check]:
    if config.PROVISIONED_SIM and config.sim_platform() == "gitea":
        return [Check("gogs: n/a in this sim", True,
                      "platform: gitea (gogs checks apply to gogs-platformed sims)",
                      warn=True)]
    container = (f"{config.PROVISIONED_SIM}-gogs" if config.PROVISIONED_SIM else "gogs")
    checks = [Check("gogs: container running", podman.container_running(container),
                    f"container '{container}' should be up")]
    try:
        client = GogsClient()
        user = client.whoami()
        checks.append(Check("gogs: API token valid", True, f"authenticated as {user.get('login')}"))
        repos = client.list_repos()
        checks.append(Check("gogs: repo search reachable", True, f"{len(repos)} repos"))
    except Exception as e:
        checks.append(Check("gogs: API token valid", False, str(e)[:200]))
    return checks


def check_gitea() -> list[Check]:
    if config.PROVISIONED_SIM and config.sim_platform() == "gogs":
        return [Check("gitea: n/a in this sim", True,
                      "platform: gogs (gitea checks apply to gitea-platformed sims)",
                      warn=True)]
    container = (f"{config.PROVISIONED_SIM}-gitea" if config.PROVISIONED_SIM else "gitea")
    checks = [Check("gitea: container running", podman.container_running(container),
                    f"container '{container}' should be up")]
    try:
        client = GiteaClient()
        checks.append(Check("gitea: version", True, f"v{client.version()}"))
        user = client.whoami()
        checks.append(Check("gitea: API token valid", True, f"authenticated as {user.get('login')}"))
        users = client.admin_users()
        checks.append(Check("gitea: admin access", True, f"{len(users)} users visible"))
    except Exception as e:
        checks.append(Check("gitea: API token valid", False, str(e)[:200]))
    return checks


def check_woodpecker() -> list[Check]:
    if config.PROVISIONED_SIM:
        return [Check("woodpecker: n/a in a sim context", True,
                      "the Mechanical Magistrate is erected in phase 2", warn=True)]
    checks = [
        Check("woodpecker: server container running", podman.container_running("woodpecker-server"),
              "container 'woodpecker-server' should be up"),
        Check("woodpecker: agent container running", podman.container_running("woodpecker-agent"),
              "container 'woodpecker-agent' should be up"),
    ]
    try:
        client = WoodpeckerClient()
        checks.append(Check("woodpecker: /healthz", client.healthz()))
        user = client.whoami()
        checks.append(Check("woodpecker: API token valid", True, f"authenticated as {user.get('login')}"))
        live = client.live_agents()
        checks.append(Check("woodpecker: agent connected", len(live) > 0,
                            f"{len(live)} live agent(s)" if live else "no agent contacted the server recently"))
    except Exception as e:
        checks.append(Check("woodpecker: API token valid", False, str(e)[:200]))
    return checks


def check_postgres() -> list[Check]:
    name = config.POSTGRES_CONTAINER
    checks = [Check("postgres: container running", podman.container_running(name),
                    f"container '{name}' should be up")]
    if not checks[0].ok:
        return checks
    ready, out = podman.exec_ok(name, ["pg_isready", "-U", "gogs"])
    checks.append(Check("postgres: pg_isready", ready, out))
    if config.PROVISIONED_SIM:
        databases = ("gitea",) if config.sim_platform() == "gitea" else ("gogs",)
    else:
        databases = ("gogs", "gitea")
    for db in databases:
        ok, out = podman.exec_ok(name, ["psql", "-U", "gogs", "-d", db, "-tAc", "SELECT 1"])
        checks.append(Check(f"postgres: database '{db}' queryable", ok, out))
    return checks


def check_podman() -> list[Check]:
    try:
        state = podman.machine_state()
        machine_ok = state.lower() == "running"
        checks = [
            Check("podman: machine running", machine_ok, f"state: {state}"),
            Check("podman: network exists", podman.network_exists(config.PODMAN_NETWORK),
                  f"network '{config.PODMAN_NETWORK}'"),
        ]
        if config.PROVISIONED_SIM:
            op = f"polis-operator-{config.PROVISIONED_SIM}"
            checks.append(Check("operator: container running",
                                podman.container_running(op), f"container '{op}'"))
        return checks
    except podman.PodmanError as e:
        return [Check("podman: CLI usable", False, str(e))]


def check_citynodes() -> list[Check]:
    if not world_exists():
        return [Check("citynodes: world exists", False, "run `polis world genesis` first")]
    world = get_world()
    suffix = f"-{config.PROVISIONED_SIM}" if config.PROVISIONED_SIM else ""
    checks = []
    for city in world.cities:
        name = f"{config.CITY_CONTAINER_PREFIX}{city.id}{suffix}"
        checks.append(Check(
            f"citynode: {city.id} container", podman.container_running(name),
            f"'{name}' not built yet", warn=True,
        ))
    return checks


SUITES: dict[str, Callable[[], list[Check]]] = {
    "gogs": check_gogs,
    "gitea": check_gitea,
    "woodpecker": check_woodpecker,
    "postgres": check_postgres,
    "podman": check_podman,
    "citynodes": check_citynodes,
}


def _render(suite_name: str, checks: list[Check]) -> bool:
    table = status_table(f"health: {suite_name}", ["check", "status", "detail"])
    failed = False
    for c in checks:
        if c.ok:
            status = "[green]ok[/green]"
        elif c.warn:
            status = "[yellow]warn[/yellow]"
        else:
            status = "[red]FAIL[/red]"
            failed = True
        table.add_row(c.name, status, c.detail)
    console.print(table)
    return failed


def _run_suite(name: str) -> None:
    failed = _render(name, SUITES[name]())
    if failed:
        raise typer.Exit(code=1)


@app.callback()
def all_(ctx: typer.Context) -> None:
    """Run every subsystem's checks (default when no subcommand is given)."""
    if ctx.invoked_subcommand is not None:
        return
    if config.PROVISIONED_SIM:
        console.print(f"[dim]sim context: {config.PROVISIONED_SIM} "
                      f"(POLIS_PROVISIONED_SIM, platform: {config.sim_platform()})[/dim]")
    any_failed = False
    for name in SUITES:
        any_failed |= _render(name, SUITES[name]())
    if any_failed:
        raise typer.Exit(code=1)


@app.command()
def gogs() -> None:
    """Checks for the phase-1 platform."""
    _run_suite("gogs")


@app.command()
def gitea() -> None:
    """Checks for the phase-2 platform."""
    _run_suite("gitea")


@app.command()
def woodpecker() -> None:
    """Checks for the CI server and its agent."""
    _run_suite("woodpecker")


@app.command()
def postgres() -> None:
    """Checks for the database backing the platforms."""
    _run_suite("postgres")


@app.command(name="podman")
def podman_command() -> None:
    """Checks for the container runtime and network."""
    _run_suite("podman")


@app.command()
def citynodes() -> None:
    """Checks for the city containers (expected absent in phase 0)."""
    _run_suite("citynodes")
