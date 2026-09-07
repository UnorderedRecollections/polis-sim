"""polis city — create and inspect the polities of the federation."""
from __future__ import annotations

from typing import Optional

import typer

from .. import store
from ..models import City
from ..names import slugify
from .common import console, die, get_world, lookup, status_table

app = typer.Typer(no_args_is_help=True, help="Cities: the polities of the federation.")


@app.command()
def create(
    name: str = typer.Option(..., "--name", help="Display name, e.g. 'Cogswich'."),
    city_id: Optional[str] = typer.Option(None, "--id", help="Slug id (default: derived from name)."),
) -> None:
    """Found a new city."""
    world = get_world()
    cid = city_id or slugify(name)
    if not cid:
        die("could not derive a city id — pass --id explicitly")
    if any(c.id == cid for c in world.cities):
        die(f"city '{cid}' already exists")
    world.cities.append(City(id=cid, display_name=name))
    store.save_world(world)
    console.print(f"[green]city founded:[/green] {name} (id={cid})")


@app.command(name="list")
def list_() -> None:
    """List all cities."""
    world = get_world()
    table = status_table("Cities", ["id", "display name", "persons", "local offices"])
    for c in world.cities:
        persons = world.city_persons(c.id)
        offices = [o for o in world.offices if o.scope == f"city:{c.id}"]
        table.add_row(c.id, c.display_name, str(len(persons)), str(len(offices)))
    console.print(table)


@app.command()
def show(city_id: str = typer.Argument(..., help="City id, e.g. cogswich.")) -> None:
    """Show one city: its citizens and its locally-scoped offices."""
    world = get_world()
    city = lookup(world, "city", world.find_city, city_id)
    console.print(f"[bold]{city.display_name}[/bold] (id={city.id})")

    persons = world.city_persons(city.id)
    table = status_table("Citizens", ["username", "display name", "agency", "roles", "offices"])
    for p in persons:
        table.add_row(p.username, p.display_name, p.agency, ", ".join(p.roles), ", ".join(p.occupies))
    console.print(table)

    offices = [o for o in world.offices if o.scope == f"city:{city.id}"]
    if offices:
        otable = status_table("Local offices", ["id", "title", "occupant"])
        for o in offices:
            otable.add_row(o.id, o.title, o.occupant or "[dim]vacant[/dim]")
        console.print(otable)
