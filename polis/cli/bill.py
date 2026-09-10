"""polis bill — proposed enactments moving through the legislative machinery."""
from __future__ import annotations

from typing import Optional

import typer

from ..legislation import bill as bills
from .common import console, enact, get_chamber, status_table

app = typer.Typer(no_args_is_help=True, help="Bills: lines of legal development petitioning for enactment.")

AS = typer.Option(..., "--as", help="Acting person (username).")
CITY = typer.Option(None, "--city", help="City slice to act from (operator mode).")
REPO_DIR = typer.Option(None, "--repo-dir", help="Local clone of the corpus.")
ISOMORPHISM = typer.Option(False, "--isomorphism", help="Render the machinery instead of executing it.")


@app.command()
def draft(
    title: str = typer.Option(..., "--title", help="Title of the bill."),
    base: str = typer.Option("main", "--base", help="Foundation the draft diverges from."),
    kind: Optional[str] = typer.Option(None, "--kind", help="Scaffold a document: act | amendment | repeal."),
    into: Optional[str] = typer.Option(None, "--into", help="Jurisdictional directory, e.g. taxation or municipal/cogswich."),
    target: Optional[str] = typer.Option(None, "--target", help="Target act (amendment/repeal)."),
    answering: Optional[str] = typer.Option(None, "--answering", help="Docketed petition (PET-…) this bill answers."),
    as_user: str = AS, city: Optional[str] = CITY, repo_dir: Optional[str] = REPO_DIR,
    isomorphism: bool = ISOMORPHISM,
) -> None:
    """Drafting begins — an alternative legal history opens (create the bill branch)."""
    chamber = get_chamber(as_user, city, repo_dir)
    plan = bills.draft(chamber, title, base, kind=kind, into=into, target=target,
                       answering=answering)
    enact(plan, isomorphism)
    if not isomorphism:
        console.print(f"[green]bill drafted:[/green] {bills.branch_of(title)}")


@app.command()
def amend(
    bill: str = typer.Argument(..., help="Bill branch, e.g. bill/harbour-dues."),
    files: Optional[list[str]] = typer.Option(None, "--file", help="Changed file (repeatable)."),
    all_files: bool = typer.Option(False, "--all", help="Record all changes in the working tree."),
    justification: str = typer.Option(..., "--justification", help="Justification of the archival act (commit message)."),
    as_user: str = AS, city: Optional[str] = CITY, repo_dir: Optional[str] = REPO_DIR,
    isomorphism: bool = ISOMORPHISM,
) -> None:
    """Record a change to the bill, with justification (commit on the branch)."""
    from .common import die
    if not all_files and not files:
        die("nothing to record — pass --file (repeatable) or --all")
    chamber = get_chamber(as_user, city, repo_dir)
    plan = bills.amend(chamber, bill, files or [], justification, all_files)
    enact(plan, isomorphism)


@app.command()
def introduce(
    bill: str = typer.Argument(..., help="Bill branch to introduce."),
    title: str = typer.Option(..., "--title", help="Title of the petition."),
    body: str = typer.Option("", "--body", help="Preamble and reasons."),
    answering: Optional[str] = typer.Option(None, "--answering", help="Docketed petition (PET-…) this bill answers."),
    as_user: str = AS, city: Optional[str] = CITY, repo_dir: Optional[str] = REPO_DIR,
    isomorphism: bool = ISOMORPHISM,
) -> None:
    """Lodge the draft and petition the federation for incorporation."""
    chamber = get_chamber(as_user, city, repo_dir)
    plan = bills.introduce(chamber, bill, title, body, answering=answering)
    results = enact(plan, isomorphism)
    if not isomorphism:
        matter = results[-1] if results else None
        matter_id = getattr(matter, "id", None)
        console.print(f"[green]bill introduced[/green] — {matter_id or 'the petition'} is before the federation")


@app.command()
def debate(
    bill: str = typer.Argument(..., help="Bill branch."),
    body: str = typer.Option(..., "--body", help="Contribution to the deliberation."),
    as_user: str = AS, city: Optional[str] = CITY, repo_dir: Optional[str] = REPO_DIR,
    isomorphism: bool = ISOMORPHISM,
) -> None:
    """Deliberate upon the petition (comment on the PR)."""
    chamber = get_chamber(as_user, city, repo_dir)
    plan = bills.debate(chamber, bill, body)
    enact(plan, isomorphism)


@app.command()
def scrutinize(
    bill: str = typer.Argument(..., help="Bill branch."),
    verdict: str = typer.Option(..., "--verdict", help="approve | request-changes."),
    body: str = typer.Option("", "--body", help="Findings of the scrutiny."),
    as_user: str = AS, city: Optional[str] = CITY, repo_dir: Optional[str] = REPO_DIR,
    isomorphism: bool = ISOMORPHISM,
) -> None:
    """Institutional scrutiny of the bill (phase 1: recorded by custom, as a finding comment)."""
    chamber = get_chamber(as_user, city, repo_dir)
    plan = bills.scrutinize(chamber, bill, verdict, body)
    enact(plan, isomorphism)


@app.command()
def ratify(
    bill: str = typer.Argument(..., help="Bill branch."),
    as_user: str = AS, city: Optional[str] = CITY, repo_dir: Optional[str] = REPO_DIR,
    isomorphism: bool = ISOMORPHISM,
) -> None:
    """Enact the bill into the authoritative history (merge; jurisdiction-checked)."""
    chamber = get_chamber(as_user, city, repo_dir)
    plan = bills.ratify(chamber, bill)
    enact(plan, isomorphism)
    if not isomorphism:
        console.print(f"[green]bill ratified:[/green] {bill} is now law")


@app.command()
def consolidate(
    bill: str = typer.Argument(..., help="Bill branch."),
    act_title: str = typer.Option(..., "--act-title", help="Title of the consolidated act."),
    as_user: str = AS, city: Optional[str] = CITY, repo_dir: Optional[str] = REPO_DIR,
    isomorphism: bool = ISOMORPHISM,
) -> None:
    """Codify a messy legislative process into one coherent act (squash merge)."""
    chamber = get_chamber(as_user, city, repo_dir)
    plan = bills.consolidate(chamber, bill, act_title)
    enact(plan, isomorphism)
    if not isomorphism:
        console.print(f"[green]act codified:[/green] {act_title}")


@app.command()
def reject(
    bill: str = typer.Argument(..., help="Bill branch."),
    as_user: str = AS, city: Optional[str] = CITY, repo_dir: Optional[str] = REPO_DIR,
    isomorphism: bool = ISOMORPHISM,
) -> None:
    """The petition fails (close the PR unmerged)."""
    chamber = get_chamber(as_user, city, repo_dir)
    plan = bills.reject(chamber, bill)
    enact(plan, isomorphism)
    if not isomorphism:
        console.print(f"[green]bill rejected:[/green] {bill}")


@app.command(name="list")
def list_(
    state: str = typer.Option("open", "--state", help="open | closed | all."),
    as_user: Optional[str] = typer.Option(None, "--as",
                                          help="Act as this person (phase-2 dispatch); "
                                          "omit for the plain matter record."),
    city: Optional[str] = CITY, repo_dir: Optional[str] = REPO_DIR,
) -> None:
    """List bills before the federation — read-only; no --as needed in phase 1."""
    if as_user:
        chamber = get_chamber(as_user, city, repo_dir)
        prs = bills.list_bills(chamber, state=state)
    else:
        from .. import matters as matters_mod
        store = matters_mod.load_matters()
        ms = [m for m in store.matters if m.kind == "bill"]
        if state == "open":
            ms = [m for m in ms if m.is_open]
        elif state == "closed":
            ms = [m for m in ms if not m.is_open]
        prs = [m.model_dump(mode="json") for m in ms]
    table = status_table("bills", ["id", "title", "branch", "petitioner", "status"])
    for pr in prs:
        table.add_row(
            str(pr.get("id") or f"#{pr.get('number')}"), pr.get("title", ""),
            pr.get("branch") or (pr.get("head") or {}).get("ref", ""),
            pr.get("proposer") or (pr.get("user") or {}).get("username", ""),
            pr.get("status") or pr.get("state", ""),
        )
    console.print(table)
