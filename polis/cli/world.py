"""polis world — genesis and inspection of the whole federation."""
from __future__ import annotations

from typing import Optional

import typer

from .. import config, store
from ..genesis import build_world
from .common import console, die, get_world, status_table

app = typer.Typer(no_args_is_help=True, help="Genesis and inspection of the federation.")


@app.command()
def genesis(
    seed: int = typer.Option(42, help="Deterministic seed for names/passwords."),
    force: bool = typer.Option(False, "--force", help="Overwrite an existing world."),
) -> None:
    """Generate the founding population: 9 cities, 63 persons, all offices."""
    if store.world_exists() and not force:
        die(f"a world already exists at {config.WORLD_FILE} — use --force to overwrite")
    world = build_world(seed=seed)
    path = store.save_world(world)
    exported = store.export_all_cities(world)
    console.print(f"[green]world created[/green] (seed={seed}) -> {path}")
    console.print(f"  cities:  {len(world.cities)}")
    console.print(f"  persons: {len(world.persons)}")
    console.print(f"  offices: {len(world.offices)}")
    console.print(f"  city slices exported: {len(exported)} -> {config.CITIES_DIR}")


@app.command()
def show() -> None:
    """Print a summary of the current world."""
    if not store.world_exists():
        die(f"no world yet — run `polis world genesis` (expected at {config.WORLD_FILE})")
    world = get_world()
    fed = world.federation
    console.print(f"[bold]{fed.name}[/bold]  (phase {fed.phase}, repo {fed.archive_org}/{fed.repo})")

    cities = status_table("Cities", ["id", "display name", "persons", "local offices"])
    for c in world.cities:
        persons = world.city_persons(c.id)
        offices = [o for o in world.offices if o.scope == f"city:{c.id}"]
        cities.add_row(c.id, c.display_name, str(len(persons)), str(len(offices)))
    console.print(cities)

    offices = status_table("Offices", ["id", "title", "kind", "scope", "occupant"])
    for o in world.offices:
        offices.add_row(o.id, o.title, o.kind, o.scope, o.occupant or "[dim]vacant[/dim]")
    console.print(offices)

    by_agency: dict[str, int] = {}
    for p in world.persons:
        by_agency[p.agency] = by_agency.get(p.agency, 0) + 1
    console.print("persons by agency: " + ", ".join(f"{k}={v}" for k, v in sorted(by_agency.items())))


@app.command()
def path() -> None:
    """Print the location of world.json."""
    console.print(config.WORLD_FILE)


@app.command(name="export")
def export(
    city: Optional[str] = typer.Argument(None, help="City id to export (all if omitted)."),
) -> None:
    """Export per-city container configuration slices to world/cities/."""
    world = get_world()
    if city:
        try:
            world.find_city(city)
        except KeyError as e:
            die(e.args[0])
        console.print(store.export_city(world, city))
    else:
        for p in store.export_all_cities(world):
            console.print(p)
