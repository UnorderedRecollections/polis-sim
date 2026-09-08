"""polis world — genesis and inspection of the whole federation."""
from __future__ import annotations

from typing import Optional

import typer

from .. import config, store
from ..genesis import build_world
from ..sim import ontology
from ..sim.legaldata import load_jurisdictions, load_moves, load_templates
from .common import console, die, get_world, status_table

app = typer.Typer(no_args_is_help=True, help="Genesis and inspection of the federation.")
jurisdictions_app = typer.Typer(no_args_is_help=True, help="The fifteen jurisdictions (legal-design data).")
moves_app = typer.Typer(no_args_is_help=True, help="Legal moves (story primitives).")
templates_app = typer.Typer(no_args_is_help=True, help="Story grammars.")
actors_app = typer.Typer(no_args_is_help=True, help="Actor kinds of the legal DSL.")
legal_objects_app = typer.Typer(no_args_is_help=True, help="Legal object kinds of the legal DSL.")
procedural_events_app = typer.Typer(no_args_is_help=True, help="Procedural events of the legal DSL.")
relations_app = typer.Typer(no_args_is_help=True, help="Legal relations of the legal DSL.")
app.add_typer(jurisdictions_app, name="jurisdictions")
app.add_typer(moves_app, name="moves")
app.add_typer(templates_app, name="templates")
app.add_typer(actors_app, name="actors")
app.add_typer(legal_objects_app, name="legal-objects")
app.add_typer(procedural_events_app, name="procedural-events")
app.add_typer(relations_app, name="relations")


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


# --- legal-design data (data/world/legal/) -------------------------------------

@jurisdictions_app.command(name="list")
def jurisdictions_list() -> None:
    """List the fifteen jurisdictions."""
    table = status_table(
        "Jurisdictions",
        ["slug", "name", "corpus dir", "resources", "actors", "rule forms", "disputes"],
    )
    for j in load_jurisdictions().values():
        table.add_row(
            j.jurisdiction, j.name, j.corpus_dir or "[dim]—[/dim]",
            str(len(j.resources)), str(len(j.actors)),
            str(len(j.rule_forms)), str(len(j.disputes)),
        )
    console.print(table)


@jurisdictions_app.command(name="show")
def jurisdictions_show(slug: str = typer.Argument(..., help="Jurisdiction slug, e.g. citizenship.")) -> None:
    """Show one jurisdiction in full."""
    j = load_jurisdictions().get(slug)
    if j is None:
        die(f"unknown jurisdiction '{slug}' (see `polis world jurisdictions list`)")
    console.print(f"[bold]{j.name}[/bold] ({j.jurisdiction})")
    console.print(f"  corpus dir: {j.corpus_dir or '— (not yet enacted)'}")
    for label, items in [
        ("resources", j.resources),
        ("actors", j.actors),
        ("activities", j.activities),
        ("resource properties", j.resource_properties),
        ("rule forms", j.rule_forms),
        ("disputes", j.disputes),
    ]:
        console.print(f"  {label}:")
        for item in items:
            console.print(f"    - {item}")


@moves_app.command(name="list")
def moves_list() -> None:
    """List the legal moves and their command-surface mapping."""
    moves = load_moves()
    table = status_table("Legal moves", ["move"])
    for m in moves.legal_moves:
        table.add_row(m)
    console.print(table)
    if moves.machinery_aliases:
        alias = status_table("Machinery aliases (NOT legal moves)", ["machinery", "the move it executes"])
        for machinery, move in moves.machinery_aliases.items():
            alias.add_row(machinery, move)
        console.print(alias)


@templates_app.command(name="list")
def templates_list() -> None:
    """List the story grammars."""
    table = status_table("Story templates", ["story type", "participants", "blocks"])
    for t in load_templates().values():
        table.add_row(t.story_type, ", ".join(t.participants), str(len(t.sequence)))
    console.print(table)


@templates_app.command(name="show")
def templates_show(story_type: str = typer.Argument(..., help="Story type, e.g. resource_dispute.")) -> None:
    """Show one story grammar: participants and sequence."""
    t = load_templates().get(story_type)
    if t is None:
        die(f"unknown story template '{story_type}' (see `polis world templates list`)")
    console.print(f"[bold]{t.story_type}[/bold]")
    console.print("  participants:")
    for role, kind in t.participants.items():
        console.print(f"    {role}: {kind}")
    console.print("  sequence:")
    for i, block in enumerate(t.sequence, 1):
        console.print(f"    {i}. {block}")


# --- ontology query surface (storage-agnostic; YAML today, a DB later) ---------

_JURISDICTION_COMPONENTS = {
    "actors": "actors",
    "resources": "resources",
    "activities": "activities",
    "properties": "resource_properties",
    "rule-forms": "rule_forms",
    "disputes": "disputes",
}


@jurisdictions_app.command(name="inspect")
def jurisdictions_inspect(
    slug: str = typer.Argument(..., help="Jurisdiction slug, e.g. citizenship."),
    component: str = typer.Argument(
        ..., help=f"Component: {' | '.join(_JURISDICTION_COMPONENTS)}."),
) -> None:
    """Show one component of a jurisdiction."""
    j = load_jurisdictions().get(slug)
    if j is None:
        die(f"unknown jurisdiction '{slug}' (see `polis world jurisdictions list`)")
    attr = _JURISDICTION_COMPONENTS.get(component)
    if attr is None:
        die(f"unknown component '{component}' (choose from: {', '.join(_JURISDICTION_COMPONENTS)})")
    console.print(f"[bold]{j.name}[/bold] — {component}:")
    for item in getattr(j, attr):
        console.print(f"  - {item}")


@actors_app.command(name="list")
def actors_list(
    jurisdiction: Optional[str] = typer.Option(
        None, "--jurisdiction", help="Only actor kinds of this jurisdiction."),
) -> None:
    """List every registered actor kind (core + jurisdiction-registered)."""
    if jurisdiction:
        j = ontology.JURISDICTIONS.get(jurisdiction)
        if j is None:
            die(f"unknown jurisdiction '{jurisdiction}'")
        types = j.actor_types()
    else:
        types = sorted(ontology.ACTORS.values(), key=lambda t: (t.parent or "", t.kind))
    table = status_table("Actor kinds", ["kind", "label", "parent", "flags"])
    for t in types:
        flags = " ".join(f for f in (
            "abstract" if t.abstract else "", "collective" if t.collective else "") if f)
        table.add_row(t.kind, t.label, t.parent or "[dim]—[/dim]", flags or "")
    console.print(table)


@actors_app.command(name="show")
def actors_show(kind: str = typer.Argument(..., help="Actor kind, e.g. legislator or harbor-master.")) -> None:
    """Show one actor kind with its derivation chain."""
    t = ontology.actor_type(kind)
    console.print(f"[bold]{t.label}[/bold] ({t.kind})")
    console.print(f"  parent:     {t.parent or '— (root)'}")
    console.print(f"  abstract:   {t.abstract}")
    console.print(f"  collective: {t.collective}")
    console.print("  derives:    " + " → ".join(ontology.derivation_chain(kind)))


@legal_objects_app.command(name="list")
def legal_objects_list() -> None:
    """List all legal object kinds."""
    table = status_table("Legal objects", ["kind", "label", "implemented", "note"])
    for t in ontology.LEGAL_OBJECTS.values():
        table.add_row(
            t.kind, t.label,
            "[green]yes[/green]" if t.implemented else "[dim]no[/dim]",
            t.note or "",
        )
    console.print(table)


@procedural_events_app.command(name="list")
def procedural_events_list() -> None:
    """List all procedural events and their matter-store mappings."""
    table = status_table("Procedural events", ["kind", "label", "matter event"])
    for t in ontology.PROCEDURAL_EVENTS.values():
        table.add_row(t.kind, t.label, t.matter_event or "[dim]— (reserved)[/dim]")
    console.print(table)


@relations_app.command(name="list")
def relations_list() -> None:
    """List the legal relations."""
    table = status_table("Legal relations", ["kind"])
    for t in ontology.LEGAL_RELATIONS.values():
        table.add_row(t.kind)
    console.print(table)
