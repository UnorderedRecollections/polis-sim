"""polis office — create and inspect offices (jurisdictional authorities)."""
from __future__ import annotations

from typing import Optional

import typer

from .. import store
from ..models import Office
from .common import console, die, get_world, lookup, status_table

app = typer.Typer(no_args_is_help=True, help="Offices: jurisdictional authorities that grant powers.")


@app.command()
def create(
    office_id: str = typer.Option(..., "--id", help="Office id, e.g. 'local-archivist-cogswich'."),
    title: str = typer.Option(..., "--title", help="Human title, e.g. 'Archivist of Cogswich'."),
    body: str = typer.Option(..., "--body", help="Institutional body, e.g. 'local-archive', 'domain:taxation'."),
    kind: str = typer.Option("juridical", "--kind", help="juridical | mechanical."),
    scope: str = typer.Option("federal", "--scope", help="'federal' or 'city:<id>'."),
    power: Optional[list[str]] = typer.Option(
        None, "--power", help="Granted power (repeatable), e.g. 'merge:municipal/cogswich/**'."
    ),
) -> None:
    """Establish a new office."""
    world = get_world()
    if kind not in ("juridical", "mechanical"):
        die(f"unknown office kind '{kind}'")
    if any(o.id == office_id for o in world.offices):
        die(f"office '{office_id}' already exists")
    if scope.startswith("city:"):
        lookup(world, "city", world.find_city, scope.split(":", 1)[1])
    office = Office(
        id=office_id, title=title, body=body, kind=kind,  # type: ignore[arg-type]
        scope=scope, powers=power or [],
    )
    world.offices.append(office)
    store.save_world(world)
    console.print(f"[green]office established:[/green] {title} (id={office_id})")


@app.command(name="list")
def list_(
    vacant: bool = typer.Option(False, "--vacant", help="Only offices without an occupant."),
    scope: Optional[str] = typer.Option(None, "--scope", help="Filter by scope, e.g. 'federal' or 'city:cogswich'."),
) -> None:
    """List offices."""
    world = get_world()
    offices = world.offices
    if vacant:
        offices = [o for o in offices if o.occupant is None]
    if scope:
        offices = [o for o in offices if o.scope == scope]
    table = status_table("Offices", ["id", "title", "kind", "scope", "occupant"])
    for o in offices:
        table.add_row(o.id, o.title, o.kind, o.scope, o.occupant or "[dim]vacant[/dim]")
    console.print(table)


@app.command()
def show(office_id: str = typer.Argument(...)) -> None:
    """Show one office: its powers and occupant."""
    world = get_world()
    o = lookup(world, "office", world.find_office, office_id)
    console.print(f"[bold]{o.title}[/bold] ({o.id})")
    console.print(f"  body:     {o.body}")
    console.print(f"  kind:     {o.kind}")
    console.print(f"  scope:    {o.scope}")
    console.print(f"  occupant: {o.occupant or '— (vacant)'}")
    console.print("  powers:")
    for p in o.powers:
        console.print(f"    - {p}")


@app.command()
def vacate(office_id: str = typer.Argument(..., help="Office to vacate.")) -> None:
    """Remove the occupant of an office (the office itself persists)."""
    world = get_world()
    office = lookup(world, "office", world.find_office, office_id)
    if office.occupant is None:
        die(f"office '{office_id}' is already vacant")
    person = world.find_person(office.occupant)
    person.occupies.remove(office_id)
    former = office.occupant
    office.occupant = None
    store.save_world(world)
    console.print(f"[green]office vacated:[/green] {office_id} (formerly {former})")
