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
    console.print(f"[green]petition filed:[/green] {matter.id if matter else ''} — {title}")


@app.command(name="list")
def list_(
    state: str = typer.Option("open", "--state", help="open | closed | all."),
    as_user: str = AS, city: Optional[str] = CITY, repo_dir: Optional[str] = REPO_DIR,
) -> None:
    """List petitions on the docket."""
    chamber = get_chamber(as_user, city, repo_dir)
    petitions = docket.list_petitions(chamber, state=state)
    table = status_table("docket", ["id", "title", "petitioner", "city", "status"])
    for p in petitions:
        if "id" in p:  # matter (phase 1)
            table.add_row(p["id"], p.get("title", ""), p.get("proposer", ""),
                          p.get("city", ""), p.get("status", ""))
        else:  # platform issue (phase 2)
            table.add_row(f"#{p.get('number')}", p.get("title", ""),
                          (p.get("user") or {}).get("username", ""), "", p.get("state", ""))
    console.print(table)


@app.command()
def show(
    matter: str = typer.Argument(..., help="Matter id (PET-0007) or issue number."),
    as_user: str = AS, city: Optional[str] = CITY, repo_dir: Optional[str] = REPO_DIR,
) -> None:
    """Show one docket entry, with its procedural record."""
    chamber = get_chamber(as_user, city, repo_dir)
    try:
        p = docket.get_petition(chamber, matter)
    except Exception as e:
        die(str(e))
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
