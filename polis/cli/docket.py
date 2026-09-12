"""polis docket — grievances entering the institutional record (§16).

Phase 1: the docket is kept by the institutions themselves (the matter store);
the mechanical archive knows nothing of petitions.
"""
from __future__ import annotations

from typing import Optional

import typer

from ..legislation import docket
from .common import console, die, enact, get_chamber, status_table

app = typer.Typer(no_args_is_help=True, help="The docket: petitions and grievances.")

AS = typer.Option(..., "--as", help="Acting person (username).")
CITY = typer.Option(None, "--city", help="City slice to act from (operator mode).")
REPO_DIR = typer.Option(None, "--repo-dir", help="Local clone of the corpus.")
ISOMORPHISM = typer.Option(False, "--isomorphism", help="Render the machinery instead of executing it.")


@app.command(name="file")
def file_(
    title: str = typer.Option(..., "--title", help="The grievance, in one line."),
    body: str = typer.Option("", "--body", help="Particulars of the grievance."),
    as_user: str = AS, city: Optional[str] = CITY, repo_dir: Optional[str] = REPO_DIR,
    isomorphism: bool = ISOMORPHISM,
) -> None:
    """A recognized problem, request or dispute enters the docket."""
    chamber = get_chamber(as_user, city, repo_dir)
    plan = docket.file_petition(chamber, title, body)
    if isomorphism:
        enact(plan, True)
        return
    results = enact(plan, False)
    matter = results[0] if results else None
    if isinstance(matter, dict):                      # platform issue (phase 2)
        ref = f"#{matter.get('number')}"
    else:                                             # matter-store entry (phase 1)
        ref = matter.id if matter else ""
    console.print(f"[green]petition filed:[/green] {ref} — {title}")


@app.command(name="list")
def list_(
    state: str = typer.Option("open", "--state", help="open | closed | all."),
    as_user: Optional[str] = typer.Option(None, "--as",
                                          help="Act as this person (phase-2 dispatch); "
                                          "omit for the plain matter record."),
    city: Optional[str] = typer.Option(None, "--city",
                                       help="Only petitions originating from this city."),
    repo_dir: Optional[str] = REPO_DIR,
) -> None:
    """List petitions on the docket — all of them, or one city's with --city.

    Without --as this reads the matter record directly (phase 1); no
    chamber, no city/person pair needed.
    """
    if as_user:
        chamber = get_chamber(as_user, city, repo_dir)
        petitions = docket.list_petitions(chamber, state=state)
    else:
        from .. import store
        if store.load_world().federation.phase == 2:
            die("phase 2 — the docket lives on the platform: "
                "pass --as <user> --city <city>")
        from .. import matters as matters_mod
        store = matters_mod.load_matters()
        ms = [m for m in store.matters if m.kind == "petition"]
        if state == "open":
            ms = [m for m in ms if m.is_open]
        elif state == "closed":
            ms = [m for m in ms if not m.is_open]
        if city:
            ms = [m for m in ms if m.city == city]
        petitions = [m.model_dump(mode="json") for m in ms]
    table = status_table("docket", ["id", "title", "petitioner", "city", "status"])
    for p in petitions:
        if "number" in p:  # platform issue (phase 2)
            table.add_row(f"#{p.get('number')}", p.get("title", ""),
                          (p.get("user") or {}).get("username", ""), "", p.get("state", ""))
        else:  # matter (phase 1)
            table.add_row(p["id"], p.get("title", ""), p.get("proposer", ""),
                          p.get("city", ""), p.get("status", ""))
    console.print(table)


@app.command()
def show(
    matter: str = typer.Argument(..., help="Matter id (PET-0007) or issue number."),
    as_user: Optional[str] = typer.Option(None, "--as",
                                          help="Act as this person (phase-2 dispatch); "
                                          "omit for the plain matter record."),
    city: Optional[str] = CITY, repo_dir: Optional[str] = REPO_DIR,
) -> None:
    """Show one docket entry, with its procedural record (read-only —
    no --as/--city needed in phase 1)."""
    if as_user:
        chamber = get_chamber(as_user, city, repo_dir)
        try:
            p = docket.get_petition(chamber, matter)
        except Exception as e:
            die(str(e))
    else:
        from .. import store
        if store.load_world().federation.phase == 2:
            die("phase 2 — the docket lives on the platform: "
                "pass --as <user> --city <city>")
        from .. import matters as matters_mod
        store = matters_mod.load_matters()
        m = next((m for m in store.matters if m.id == matter), None)
        if m is None:
            die(f"no such matter '{matter}'")
        p = m.model_dump(mode="json")
    if "events" in p:  # matter (phase 1)
        console.print(f"[bold]{p['id']} — {p['title']}[/bold]  ({p['status']})")
        console.print(f"petitioner: {p['proposer']} of {p['city']}")
        for e in p["events"]:
            detail = f"\n    {e['detail']}" if e.get("detail") else ""
            console.print(f"  {e['date'][:10]}  {e['event']}  — {e['actor']}{detail}")
    else:  # platform issue (phase 2)
        console.print(f"[bold]#{p.get('number')} {p.get('title')}[/bold]  ({p.get('state')})")
        console.print(f"petitioner: {(p.get('user') or {}).get('username', '—')}")
        console.print(p.get("body") or "[dim](no particulars)[/dim]")


@app.command()
def comment(
    matter: str = typer.Argument(..., help="Matter id (PET-0007) or issue number."),
    body: str = typer.Option(..., "--body", help="What is said on the grievance."),
    as_user: str = AS, city: Optional[str] = CITY, repo_dir: Optional[str] = REPO_DIR,
    isomorphism: bool = ISOMORPHISM,
) -> None:
    """Speak on a docketed grievance; the record grows."""
    chamber = get_chamber(as_user, city, repo_dir)
    plan = docket.comment_petition(chamber, matter, body)
    enact(plan, isomorphism)


@app.command()
def dismiss(
    matter: str = typer.Argument(..., help="Matter id (PET-0007) or issue number."),
    as_user: str = AS, city: Optional[str] = CITY, repo_dir: Optional[str] = REPO_DIR,
    isomorphism: bool = ISOMORPHISM,
) -> None:
    """Deny the grievance further hearing (the record remains)."""
    chamber = get_chamber(as_user, city, repo_dir)
    plan = docket.dismiss_petition(chamber, matter)
    enact(plan, isomorphism)
    if not isomorphism:
        console.print(f"[green]petition {matter} dismissed[/green]")
