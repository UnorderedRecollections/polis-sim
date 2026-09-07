"""polis person — create and inspect persons (citizens and officers)."""
from __future__ import annotations

import secrets
from typing import Optional

import typer

from .. import store
from ..models import POLITICAL_ROLES, Credentials, GitIdentity, Membership, Person
from ..names import make_username
from .common import console, die, get_world, lookup, status_table

app = typer.Typer(no_args_is_help=True, help="Persons: citizens, delegates and officers of the law.")


@app.command()
def create(
    name: str = typer.Option(..., "--name", help="Display name, e.g. 'Edwina Vane'."),
    city: Optional[str] = typer.Option(None, "--city", help="City id the person is a citizen of."),
    role: Optional[list[str]] = typer.Option(
        None, "--role", help=f"Political role (repeatable): {', '.join(POLITICAL_ROLES)}."
    ),
    agency: Optional[str] = typer.Option(
        None, "--agency", help="political | juridical | mechanical. Default: political if --role given, else juridical."
    ),
    institution: Optional[str] = typer.Option(
        None, "--institution", help="Institutional body id, for persons without citizenship (e.g. federal-magistracy)."
    ),
    username: Optional[str] = typer.Option(None, "--username", help="Login name (default: derived)."),
    email: Optional[str] = typer.Option(None, "--email", help="Email (default: derived)."),
) -> None:
    """Bring a person into the federation."""
    world = get_world()
    roles = role or []

    for r in roles:
        if r not in POLITICAL_ROLES:
            die(f"unknown political role '{r}' (choose from: {', '.join(POLITICAL_ROLES)})")

    if agency is None:
        agency = "political" if roles else "juridical"
    if agency not in ("political", "juridical", "mechanical"):
        die(f"unknown agency '{agency}'")
    if agency == "political" and not roles:
        die("a political person needs at least one --role")
    if roles and agency != "political":
        die("political roles require --agency political")
    if agency == "mechanical" and city:
        die("a mechanical agent belongs to an institution, not to a city")

    if agency == "mechanical" or (city is None and institution):
        if not institution:
            die("--institution is required for a person without citizenship")
        member_of = Membership(type="institution", id=institution)
        default_email_domain = f"{institution}.invalid"
    else:
        if not city:
            die("--city is required for citizens and officers")
        lookup(world, "city", world.find_city, city)
        member_of = Membership(type="city", id=city)
        default_email_domain = f"{city}.invalid"

    taken = {p.username for p in world.persons}
    uname = username or make_username(name, taken)
    if uname in taken:
        die(f"username '{uname}' already taken")
    mail = email or f"{uname}@{default_email_domain}"

    person = Person(
        username=uname,
        display_name=name,
        email=mail,
        agency=agency,  # type: ignore[arg-type]
        member_of=member_of,
        roles=roles,
        git=GitIdentity(author_name=name, author_email=mail),
        credentials=Credentials(password=secrets.token_urlsafe(12)),
    )
    world.persons.append(person)
    store.save_world(world)
    console.print(f"[green]person created:[/green] {person.display_name} ({person.username}, {person.agency})")


@app.command(name="list")
def list_(
    city: Optional[str] = typer.Option(None, "--city", help="Only citizens of this city."),
    agency: Optional[str] = typer.Option(None, "--agency", help="Filter by agency kind."),
) -> None:
    """List persons."""
    world = get_world()
    persons = world.persons
    if city:
        persons = [p for p in persons if p.member_of.type == "city" and p.member_of.id == city]
    if agency:
        persons = [p for p in persons if p.agency == agency]
    table = status_table("Persons", ["username", "display name", "agency", "member of", "roles", "occupies"])
    for p in persons:
        table.add_row(
            p.username, p.display_name, p.agency,
            f"{p.member_of.type}:{p.member_of.id}",
            ", ".join(p.roles), ", ".join(p.occupies),
        )
    console.print(table)


@app.command()
def show(username: str = typer.Argument(...)) -> None:
    """Show one person in full (credentials partially masked)."""
    world = get_world()
    p = lookup(world, "person", world.find_person, username)
    console.print(f"[bold]{p.display_name}[/bold] ({p.username})")
    console.print(f"  agency:     {p.agency}")
    console.print(f"  member of:  {p.member_of.type}:{p.member_of.id}")
    console.print(f"  roles:      {', '.join(p.roles) or '—'}")
    console.print(f"  occupies:   {', '.join(p.occupies) or '—'}")
    console.print(f"  email:      {p.email}")
    console.print(f"  git author: {p.git.author_name} <{p.git.author_email}>")
    console.print(f"  password:   {p.credentials.password}")
    tokens = {k: (v[:6] + "…" if v else None) for k, v in p.credentials.api_tokens.items()}
    console.print(f"  api tokens: {tokens or '—'}")
