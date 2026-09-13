"""polis world — genesis and inspection of the whole federation."""
from __future__ import annotations

from typing import Optional

import typer

from .. import config, store
from ..genesis import build_world
from ..sim import ontology
from ..sim.legaldata import load_jurisdictions, load_moves, load_templates
from ..sim.norms import load_seed_norms, load_norm_file, validate_norm_set
from ..sim.resources import load_resources, find_resource
from .common import console, die, get_world, status_table

app = typer.Typer(no_args_is_help=True, help="Genesis and inspection of the federation.")
jurisdictions_app = typer.Typer(no_args_is_help=True, help="The fifteen jurisdictions (legal-design data).")
moves_app = typer.Typer(no_args_is_help=True, help="Legal moves (story primitives).")
templates_app = typer.Typer(no_args_is_help=True, help="Story grammars.")
actors_app = typer.Typer(no_args_is_help=True, help="Actor kinds of the legal DSL.")
legal_objects_app = typer.Typer(no_args_is_help=True, help="Legal object kinds of the legal DSL.")
procedural_events_app = typer.Typer(no_args_is_help=True, help="Procedural events of the legal DSL.")
relations_app = typer.Typer(no_args_is_help=True, help="Legal relations of the legal DSL.")
paradigms_app = typer.Typer(no_args_is_help=True, help="Jurisdiction paradigms (structural kinds).")
norms_app = typer.Typer(no_args_is_help=True, help="Norms — the rules in force (seed or snapshot).")
resources_app = typer.Typer(no_args_is_help=True, help="Concrete resources stories revolve around.")
events_app = typer.Typer(no_args_is_help=True, help="Event candidates (friction-derived story seeds).")
app.add_typer(jurisdictions_app, name="jurisdictions")
app.add_typer(moves_app, name="moves")
app.add_typer(templates_app, name="templates")
legal_app = typer.Typer(no_args_is_help=True, help="The legal seed as a whole (bootstrap step 2).")
app.add_typer(actors_app, name="actors")
app.add_typer(legal_app, name="legal")
app.add_typer(legal_objects_app, name="legal-objects")
app.add_typer(procedural_events_app, name="procedural-events")
app.add_typer(relations_app, name="relations")
app.add_typer(paradigms_app, name="paradigms")
app.add_typer(norms_app, name="norms")
app.add_typer(resources_app, name="resources")
app.add_typer(events_app, name="events")


@app.command()
def genesis(
    seed: int = typer.Option(42, help="Deterministic seed for names/passwords."),
    force: bool = typer.Option(False, "--force", help="Overwrite an existing world."),
    cities: Optional[int] = typer.Option(
        None, "--cities", help="How many cities (default: the canonical nine; "
        "the name pool is longer for scale runs — task 0056)."),
    legislators_per_city: int = typer.Option(
        3, "--legislators-per-city", help="Citizen-legislators per city."),
    delegates_per_city: int = typer.Option(
        2, "--delegates-per-city", help="Local delegates per city."),
) -> None:
    """Generate the founding population: the canonical 9 cities, 64 persons,
    all offices — or a scaled world for the performance harness."""
    if store.world_exists() and not force:
        die(f"a world already exists at {config.WORLD_FILE} — use --force to overwrite")
    try:
        world = build_world(seed=seed, cities=cities,
                            legislators_per_city=legislators_per_city,
                            delegates_per_city=delegates_per_city)
    except ValueError as e:
        die(str(e))
    path = store.save_world(world)
    exported = store.export_all_cities(world)
    scale = "" if (cities is None and legislators_per_city == 3
                   and delegates_per_city == 2) else "  [yellow](scaled world)[/yellow]"
    console.print(f"[green]world created[/green] (seed={seed}){scale} -> {path}")
    console.print(f"  cities:  {len(world.cities)}")
    console.print(f"  persons: {len(world.persons)}")
    console.print(f"  offices: {len(world.offices)}")
    console.print(f"  city slices exported: {len(exported)} -> {config.CITIES_DIR}")


@app.command()
def cleanup(
    yes: bool = typer.Option(False, "--yes", help="Apply the removals."),
) -> None:
    """Remove per-sim residue from the civil registry (dry-run by default).

    Provisioning once wrote per-sim API tokens (`gogs@<sim>`) into
    world.json; the registry must not carry machinery credentials — the
    sim slices under data/sims/<sim>/ are their only home.
    """
    if not store.world_exists():
        die(f"no world yet — run `polis world genesis` (expected at {config.WORLD_FILE})")
    world = get_world()
    residue: dict[str, list[str]] = {}          # key -> usernames
    for p in world.persons:
        for key in list((p.credentials.api_tokens or {}).keys()):
            if "@" in key:
                residue.setdefault(key, []).append(p.username)
    if not residue:
        console.print("[green]registry is clean[/green] — no per-sim residue")
        return
    table = status_table("per-sim residue in world.json", ["key", "persons"])
    for key, users in sorted(residue.items()):
        table.add_row(key, str(len(users)))
    console.print(table)
    if not yes:
        console.print("[yellow]dry run[/yellow] — re-run with --yes to remove these keys")
        return
    for p in world.persons:
        p.credentials.api_tokens = {k: v for k, v in (p.credentials.api_tokens or {}).items()
                                    if "@" not in k}
    store.save_world(world)
    store.export_all_cities(world)
    console.print(f"[green]removed {sum(len(v) for v in residue.values())} token(s) "
                  f"across {len(residue)} key(s)[/green]; city slices re-exported")


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
        ["slug", "name", "corpus dir", "paradigms", "resources", "actors", "rule forms", "disputes"],
    )
    for j in load_jurisdictions().values():
        table.add_row(
            j.jurisdiction, j.name, j.corpus_dir or "[dim]—[/dim]",
            ", ".join(j.paradigms) or "[dim]—[/dim]",
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
    console.print(f"  paradigms:  {', '.join(j.paradigms) or '—'}")
    for label, items in [
        ("resources", j.resources),
        ("actors", j.actors),
        ("activities", j.activity_verbs()),
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
    if component == "incompatibilities":
        console.print(f"[bold]{j.name}[/bold] — incompatibilities:")
        for r in j.incompatibilities:
            over = f" over {r.over}" if r.over else ""
            console.print(f"  - {r.between[0]} ⊥ {r.between[1]} ({r.kind}{over})")
            if r.note:
                console.print(f"    [dim]{r.note}[/dim]")
        return
    attr = _JURISDICTION_COMPONENTS.get(component)
    if attr is None:
        die(f"unknown component '{component}' (choose from: {', '.join(_JURISDICTION_COMPONENTS)}, incompatibilities)")
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


@paradigms_app.command(name="list")
def paradigms_list() -> None:
    """List the jurisdiction paradigms (structural kinds)."""
    table = status_table("Paradigms", ["kind", "label", "holding object types", "impact kinds"])
    for t in ontology.PARADIGMS.values():
        table.add_row(t.kind, t.label,
                      ", ".join(t.holding_object_types), ", ".join(t.impact_kinds))
    console.print(table)


@paradigms_app.command(name="show")
def paradigms_show(kind: str = typer.Argument(..., help="Paradigm kind, e.g. resource.")) -> None:
    """Show one paradigm in full."""
    t = ontology.PARADIGMS.get(kind)
    if t is None:
        die(f"unknown paradigm '{kind}' (see `polis world paradigms list`)")
    console.print(f"[bold]{t.label}[/bold] ({t.kind})")
    console.print(f"  {t.description}")
    console.print(f"  holding object types: {', '.join(t.holding_object_types) or '—'}")
    console.print(f"  impact kinds:         {', '.join(t.impact_kinds) or '—'}")
    members = [j.slug for j in ontology.JURISDICTIONS.values() if kind in j.paradigms]
    console.print(f"  jurisdictions:        {', '.join(members) or '—'}")


# --- norms (rules in force) ----------------------------------------------------

def _load_norm_set(file: Optional[str]) -> dict[str, "object"]:
    """Load seed norms, or one snapshot file (seed and snapshot: one format)."""
    from pathlib import Path
    if file:
        ns = load_norm_file(Path(file))
        return {Path(file).stem: ns}
    return load_seed_norms()


@norms_app.command(name="list")
def norms_list(
    jurisdiction: Optional[str] = typer.Option(None, "--jurisdiction", help="Only this jurisdiction."),
    in_force: bool = typer.Option(False, "--in-force", help="Only norms currently in force."),
    file: Optional[str] = typer.Option(None, "--file", help="A snapshot/seed YAML instead of the seeds."),
) -> None:
    """List norms (rules in force) from the seeds or a snapshot."""
    sets = _load_norm_set(file)
    if jurisdiction:
        if jurisdiction not in sets:
            die(f"no norms for jurisdiction '{jurisdiction}'")
        sets = {jurisdiction: sets[jurisdiction]}
    table = status_table(
        "Norms",
        ["id", "jurisdiction", "rule form", "object", "aspect", "source", "status"],
    )
    for slug, ns in sets.items():
        norms = ns.in_force() if in_force else ns.norms
        for n in norms:
            src = n.source + (f" ({n.source_ref})" if n.source_ref else "")
            table.add_row(n.id, slug, n.rule_form,
                          f"{n.object.kind} ({n.object.type})", n.aspect, src, n.status)
    console.print(table)


@norms_app.command(name="show")
def norms_show(
    norm_id: str = typer.Argument(..., help="Norm id, e.g. N-0001."),
    file: Optional[str] = typer.Option(None, "--file", help="A snapshot/seed YAML instead of the seeds."),
) -> None:
    """Show one norm in full."""
    sets = _load_norm_set(file)
    for slug, ns in sets.items():
        for n in ns.norms:
            if n.id == norm_id:
                console.print(f"[bold]{n.id}[/bold] — {n.rule_form}  (jurisdiction: {slug})")
                console.print(f"  object:        {n.object.kind} ({n.object.type})")
                console.print(f"  aspect:        {n.aspect}")
                console.print(f"  subjects:      {', '.join(n.subjects) or '—'}")
                console.print(f"  beneficiaries: {', '.join(n.beneficiaries) or '—'}")
                console.print(f"  source:        {n.source}" + (f" ({n.source_ref})" if n.source_ref else ""))
                console.print(f"  status:        {n.status}")
                contested = ns.contested(n.id)
                if contested:
                    console.print("  contested by:  " + ", ".join(c.id for c in contested))
                problems = validate_norm_set(ns, slug)
                if problems:
                    console.print("  [yellow]validation problems:[/yellow]")
                    for p in problems:
                        console.print(f"    - {p}")
                return
    die(f"unknown norm '{norm_id}'")


# --- resources ------------------------------------------------------------------

@resources_app.command(name="list")
def resources_list(
    jurisdiction: Optional[str] = typer.Option(None, "--jurisdiction", help="Only this jurisdiction."),
) -> None:
    """List the concrete resources (per-jurisdiction YAML files)."""
    from ..sim.resources import validate_resources
    files = load_resources()
    if jurisdiction:
        if jurisdiction not in files:
            die(f"no resources for jurisdiction '{jurisdiction}'")
        files = {jurisdiction: files[jurisdiction]}
    table = status_table("Resources", ["kind", "jurisdiction", "label", "properties", "customary uses"])
    for slug, resources in files.items():
        for r in resources.values():
            table.add_row(r.resource, slug, r.label,
                          str(len(r.properties)), str(len(r.customary_use)))
    console.print(table)
    problems = validate_resources()
    if problems:
        console.print("[yellow]validation problems:[/yellow]")
        for p in problems:
            console.print(f"  - {p}")


@resources_app.command(name="show")
def resources_show(
    kind: str = typer.Argument(..., help="Resource slug, e.g. northern_banks."),
    jurisdiction: Optional[str] = typer.Option(None, "--jurisdiction", help="Scope the lookup."),
) -> None:
    """Show one resource in full."""
    try:
        r = find_resource(kind, jurisdiction)
    except KeyError as e:
        die(e.args[0])
    console.print(f"[bold]{r.label or r.resource}[/bold] ({r.resource}, {r.jurisdiction})")
    if r.properties:
        console.print("  properties:")
        for k, v in r.properties.items():
            console.print(f"    {k}: {v}")
    if r.customary_use:
        console.print("  customary use:")
        for u in r.customary_use:
            console.print(f"    - {u}")
    if r.narrative:
        console.print(f"  narrative: {r.narrative}")


# --- the legal seed as a whole ---------------------------------------------------

@legal_app.command(name="validate")
def legal_validate(
    file: Optional[str] = typer.Argument(
        None, help="Validate ONE situation/norms file instead of the whole seed."),
) -> None:
    """Validate the foundational legal state — or a single situation file."""
    from ..sim.events import validate_signatures
    from ..sim.resources import validate_resources
    from ..sim.situations import validate_situation

    if file:
        from pathlib import Path
        src = Path(file)
        if not src.exists():
            die(f"file not found: {file}")
        import yaml
        jurisdiction = (yaml.safe_load(src.read_text(encoding="utf-8")) or {}).get("jurisdiction")
        if not jurisdiction:
            die(f"{src.name} has no 'jurisdiction:' key — not a situation file")
        ns = load_norm_file(src)
        problems = validate_situation(ns, jurisdiction)
        if problems:
            console.print(f"[bold red]{src.name} invalid:[/bold red]")
            for p in problems:
                console.print(f"  - {p}")
            raise typer.Exit(code=1)
        console.print(f"[green]{src.name} valid[/green] "
                      f"({len(ns.norms)} norms, {len(ns.holdings)} holdings, "
                      f"jurisdiction: {jurisdiction})")
        return

    problems: list[str] = []
    problems += validate_resources()
    problems += validate_signatures()

    seeds = load_seed_norms()
    for slug in load_jurisdictions():
        if slug not in seeds:
            problems.append(f"{slug}: no norm seed file")
    for slug, ns in seeds.items():
        problems += validate_norm_set(ns, slug)

    # the seed must contain no active strict conflicts of laws
    jurisdictions = load_jurisdictions()
    for slug, ns in seeds.items():
        for a, b in ns.conflicts(jurisdictions[slug].incompatibilities):
            problems.append(
                f"{slug}: active conflict of laws in the seed: "
                f"{a.id} ({a.rule_form}) ⊥ {b.id} ({b.rule_form}) "
                f"over {a.object.kind}/{a.aspect}")

    n_norms = sum(len(ns.norms) for ns in seeds.values())
    n_holdings = sum(len(ns.holdings) for ns in seeds.values())
    console.print(
        f"legal seed: {len(load_jurisdictions())} jurisdictions, "
        f"{sum(len(v) for v in load_resources().values())} resources, "
        f"{n_norms} norms, {n_holdings} holdings"
    )
    if problems:
        console.print("[bold red]validation failed:[/bold red]")
        for p in problems:
            console.print(f"  - {p}")
        raise typer.Exit(code=1)
    console.print("[green]the foundational legal state is consistent[/green]")


situation_app = typer.Typer(no_args_is_help=True,
                            help="Situations: generate and inspect simulation seeds.")


@situation_app.command(name="new")
def situation_new(
    jurisdiction: str = typer.Argument(..., help="Jurisdiction slug, e.g. fisheries."),
    seed: Optional[int] = typer.Option(None, "--seed", help="Determinism seed for variety."),
    out: Optional[str] = typer.Option(None, "--out",
                                      help="Write here (default: print to stdout)."),
    force: bool = typer.Option(False, "--force", help="Overwrite an existing file."),
) -> None:
    """Generate a valid situation.yaml from the jurisdiction's own data
    (norms per resource, holdings from activities × actors × cities)."""
    from pathlib import Path
    from ..sim.norms import save_norm_file
    from ..sim.situations import SituationError, generate_situation, validate_situation

    try:
        ns = generate_situation(jurisdiction, seed=seed)
    except SituationError as e:
        die(str(e))
    problems = validate_situation(ns, jurisdiction)
    if problems:
        console.print("[bold red]generated situation is invalid (a generator bug):[/bold red]")
        for p in problems:
            console.print(f"  - {p}")
        raise typer.Exit(code=1)
    if out is None:
        import yaml
        console.print(yaml.safe_dump(
            {"jurisdiction": jurisdiction,
             **ns.model_dump(mode="json", exclude={"description"})},
            sort_keys=False, allow_unicode=True))
        console.print("[dim]— validate with: polis world legal validate <file>; "
                      "write with --out[/dim]")
        return
    dest = Path(out)
    if dest.exists() and not force:
        die(f"{out} exists — use --force to overwrite")
    dest.parent.mkdir(parents=True, exist_ok=True)
    import yaml
    payload = {"jurisdiction": jurisdiction,
               **ns.model_dump(mode="json", exclude_none=True)}
    dest.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True),
                    encoding="utf-8")
    console.print(f"[green]situation written:[/green] {dest} "
                  f"({len(ns.norms)} norms, {len(ns.holdings)} holdings)")


app.add_typer(situation_app, name="situation")


@legal_app.command(name="audit")
def legal_audit(
    slug: Optional[str] = typer.Argument(None, help="Jurisdiction to audit (all if omitted)."),
) -> None:
    """Run the new-jurisdiction checklist (extensibility-api.md §1)."""
    from ..sim.extensibility import audit_all, audit_jurisdiction

    audits = {slug: audit_jurisdiction(slug)} if slug else audit_all()
    if slug and slug not in load_jurisdictions():
        die(f"unknown jurisdiction '{slug}'")
    failed = False
    for name, steps in audits.items():
        console.print(f"[bold]{name}[/bold]")
        for s in steps:
            mark = "[green]ok[/green]" if s.ok else "[red]MISSING[/red]"
            if not s.ok:
                failed = True
            console.print(f"  {mark:18} {s.step}" + (f" — {s.detail}" if s.detail else ""))
    if failed:
        raise typer.Exit(code=1)


# --- event candidates -------------------------------------------------------------

@events_app.command(name="candidates")
def events_candidates(
    jurisdiction: str = typer.Option(..., "--jurisdiction", help="Jurisdiction slug."),
    show_all: bool = typer.Option(False, "--all", help="Include uncharged candidates."),
) -> None:
    """Compute event candidates (story seeds) against the seed situation."""
    from ..sim.events import charged_candidates

    jurisdictions = load_jurisdictions()
    j = jurisdictions.get(jurisdiction)
    if j is None:
        die(f"unknown jurisdiction '{jurisdiction}'")
    ns = load_seed_norms().get(jurisdiction)
    if ns is None:
        die(f"no seed norms for '{jurisdiction}'")
    cands = charged_candidates(j, ns)
    if not show_all:
        cands = [c for c in cands if c.charged]
    if not cands:
        console.print(f"[dim]no {'charged ' if not show_all else ''}candidates in {jurisdiction}[/dim]")
        return
    table = status_table(
        f"event candidates — {jurisdiction}",
        ["actor", "activity", "object", "impact", "harms", "norms in question"],
    )
    for c in cands:
        harms = ", ".join(
            f"{h.holding.id} ({h.holding.holder.actor_kind}"
            + (f" of {h.holding.holder.city}" if h.holding.holder.city else "") + ")"
            for h in c.harmed
        ) or "[dim]—[/dim]"
        norms = ", ".join(sorted({n for h in c.harmed for n in h.norms_in_question})) or "[dim]—[/dim]"
        table.add_row(c.actor.label(), c.verb, c.object_kind, c.impact, harms, norms)
    console.print(table)
