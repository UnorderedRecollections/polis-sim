"""polis citynode — the city containers (each one a polity with its own archive).

City containers are named polis-city-<city-id>. They do not exist yet in
phase 0; these commands report their absence honestly.
"""
from __future__ import annotations

from typing import Optional

import typer

from .. import config
from ..clients import containers
from ..store import world_exists
from .common import console, die, get_world, status_table

app = typer.Typer(no_args_is_help=True, help="City containers: the simulated polities.")


def container_name(city_id: str) -> str:
    return f"{config.CITY_CONTAINER_PREFIX}{city_id}"


@app.command(name="list")
def list_() -> None:
    """List all federation cities and the state of their container, if any."""
    if not world_exists():
        die("no world yet — run `polis world genesis` first")
    world = get_world()
    try:
        running = containers.get_runtime().by_name()
    except containers.ContainerError as e:
        die(str(e))
    table = status_table("city nodes", ["city", "container", "state"])
    for city in world.cities:
        name = container_name(city.id)
        c = running.get(name)
        state = c["State"] if c else "[dim]not created[/dim]"
        table.add_row(city.id, name, state)
    console.print(table)


@app.command()
def status(
    city_id: str = typer.Argument(..., help="City id, e.g. cogswich."),
) -> None:
    """Show the container state of one city."""
    name = container_name(city_id)
    try:
        c = containers.container(name)
    except containers.ContainerError as e:
        die(str(e))
    if c is None:
        console.print(f"[yellow]{name}: not created[/yellow] (city container images are not built yet)")
        raise typer.Exit(code=1)
    console.print(f"{name}: {c.get('State')} (image: {c.get('Image')})")
