"""polis assign — the two dimensions: citizenship and office-holding.

Separation rule: a political person (legislator/delegate) may not occupy a
juridical office, and a juridical person may not hold political roles.
Elevation of a local archivist to Federal Archivist is permitted because
both offices are juridical.
"""
from __future__ import annotations

import typer

from .. import store
from ..models import Person
from .common import console, die, get_world, lookup

app = typer.Typer(no_args_is_help=True, help="Assign persons to cities (membership) and offices (authority).")


def _check_office_compatible(person: Person, office_kind: str, office_id: str) -> None:
    if person.agency == "political":
        die(
            f"{person.username} exercises political agency ({', '.join(person.roles)}) and "
            "may not occupy an office — that would fuse the powers the constitution separates"
        )
    if person.agency == "mechanical" and office_kind != "mechanical":
        die(f"a mechanical agent may only occupy a mechanical office, not '{office_id}'")
    if person.agency == "juridical" and office_kind == "mechanical":
        die(f"a person may not occupy the mechanical office '{office_id}' — it belongs to software")


@app.command()
def citizenship(
    username: str = typer.Argument(..., help="Person to (re)assign."),
    city_id: str = typer.Argument(..., help="City the person becomes a citizen of."),
) -> None:
    """Grant a person citizenship of a city (political membership)."""
    world = get_world()
    person = lookup(world, "person", world.find_person, username)
    lookup(world, "city", world.find_city, city_id)
    if person.agency == "mechanical":
        die("a mechanical agent belongs to an institution, not to a city")
    person.member_of = person.member_of.model_copy(update={"type": "city", "id": city_id})
    person.email = f"{person.username}@{city_id}.invalid"
    person.git.author_email = person.email
    store.save_world(world)
    console.print(f"[green]citizenship assigned:[/green] {username} is now a citizen of {city_id}")


@app.command()
def office(
    username: str = typer.Argument(..., help="Person to appoint."),
    office_id: str = typer.Argument(..., help="Office to occupy."),
) -> None:
    """Appoint a person to an office (jurisdictional authority)."""
    world = get_world()
    person = lookup(world, "person", world.find_person, username)
    office = lookup(world, "office", world.find_office, office_id)
    if office.occupant is not None:
        die(f"office '{office_id}' is occupied by {office.occupant} — vacate it first")
    _check_office_compatible(person, office.kind, office_id)
    office.occupant = person.username
    person.occupies.append(office_id)
    store.save_world(world)
    console.print(f"[green]office occupied:[/green] {username} now holds '{office_id}'")
