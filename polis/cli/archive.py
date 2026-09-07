"""polis archive — the historical record itself: circulation, editions and the
exceptional archival powers (§1, §2, §12–§15)."""
from __future__ import annotations

from typing import Optional

import typer

from ..legislation import archive
from .common import console, die, enact, get_chamber

app = typer.Typer(no_args_is_help=True, help="The archive: obtain/receive/lodge, promulgate, and the exceptional powers.")

AS = typer.Option(..., "--as", help="Acting person (username).")
CITY = typer.Option(None, "--city", help="City slice to act from (operator mode).")
REPO_DIR = typer.Option(None, "--repo-dir", help="Local clone of the corpus.")
ISOMORPHISM = typer.Option(False, "--isomorphism", help="Render the machinery instead of executing it.")


@app.command()
def obtain(
    as_user: str = AS, city: Optional[str] = CITY, repo_dir: Optional[str] = REPO_DIR,
    isomorphism: bool = ISOMORPHISM,
) -> None:
    """The city receives a complete copy of the archive (clone + recognize upstream)."""
    chamber = get_chamber(as_user, city, repo_dir)
    plan = archive.obtain(chamber)
    enact(plan, isomorphism)
    if not isomorphism:
        console.print(f"[green]archive obtained[/green] -> {chamber.repo_dir}")


@app.command()
def receive(
    ref: str = typer.Option("main", "--ref", help="Line of development to receive."),
    as_user: str = AS, city: Optional[str] = CITY, repo_dir: Optional[str] = REPO_DIR,
    isomorphism: bool = ISOMORPHISM,
) -> None:
    """The gazette arrives — federal enactments are incorporated locally (pull)."""
    chamber = get_chamber(as_user, city, repo_dir)
    plan = archive.receive(chamber, ref)
    enact(plan, isomorphism)


@app.command()
def lodge(
    ref: str = typer.Option("main", "--ref", help="Line of development to lodge."),
    as_user: str = AS, city: Optional[str] = CITY, repo_dir: Optional[str] = REPO_DIR,
    isomorphism: bool = ISOMORPHISM,
) -> None:
    """Send the city's archival acts to its lodged copy (push)."""
    chamber = get_chamber(as_user, city, repo_dir)
    plan = archive.lodge(chamber, ref)
    enact(plan, isomorphism)


@app.command()
def promulgate(
    name: str = typer.Option(..., "--name", help="Name of the edition, e.g. first-codification."),
    message: str = typer.Option(..., "--message", help="Proclamation text."),
    ref: str = typer.Option("main", "--ref", help="State of the corpus being proclaimed."),
    as_user: str = AS, city: Optional[str] = CITY, repo_dir: Optional[str] = REPO_DIR,
    isomorphism: bool = ISOMORPHISM,
) -> None:
    """Proclaim a named authoritative edition (tag; Keeper only)."""
    chamber = get_chamber(as_user, city, repo_dir)
    plan = archive.promulgate(chamber, name, message, ref)
    enact(plan, isomorphism)
    if not isomorphism:
        console.print(f"[green]edition promulgated:[/green] {name}")


@app.command()
def repeal(
    act: str = typer.Argument(..., help="The act to repeal (commit hash)."),
    mainline: Optional[int] = typer.Option(None, "--mainline", help="Parent number when repealing a merge (usually 1)."),
    as_user: str = AS, city: Optional[str] = CITY, repo_dir: Optional[str] = REPO_DIR,
    isomorphism: bool = ISOMORPHISM,
) -> None:
    """Repeal an earlier act — the original remains in the record (revert; Keeper only)."""
    chamber = get_chamber(as_user, city, repo_dir)
    plan = archive.repeal(chamber, act, mainline=mainline)
    enact(plan, isomorphism)


@app.command()
def transplant(
    act: str = typer.Argument(..., help="The act to transplant (commit hash)."),
    as_user: str = AS, city: Optional[str] = CITY, repo_dir: Optional[str] = REPO_DIR,
    isomorphism: bool = ISOMORPHISM,
) -> None:
    """Import one act without its history (cherry-pick; Keeper only)."""
    chamber = get_chamber(as_user, city, repo_dir)
    plan = archive.transplant(chamber, act)
    enact(plan, isomorphism)


@app.command()
def reconstruct(
    onto: str = typer.Option(..., "--onto", help="The new historical foundation."),
    as_user: str = AS, city: Optional[str] = CITY, repo_dir: Optional[str] = REPO_DIR,
    isomorphism: bool = ISOMORPHISM,
) -> None:
    """Replay the current line of development on a new foundation (rebase; Keeper only)."""
    chamber = get_chamber(as_user, city, repo_dir)
    plan = archive.reconstruct(chamber, onto)
    enact(plan, isomorphism)


@app.command(name="replace-history")
def replace_history(
    ref: str = typer.Option("main", "--ref", help="Line whose recognized history is replaced."),
    yes: bool = typer.Option(False, "--yes", help="Confirm use of the exceptional power."),
    as_user: str = AS, city: Optional[str] = CITY, repo_dir: Optional[str] = REPO_DIR,
    isomorphism: bool = ISOMORPHISM,
) -> None:
    """Replace the recognized record (force push, §15) — exceptional; requires --yes."""
    if not isomorphism and not yes:
        die("replacement of the recognized history requires --yes")
    chamber = get_chamber(as_user, city, repo_dir)
    plan = archive.replace_history(chamber, ref)
    enact(plan, isomorphism)


@app.command()
def editions(
    as_user: str = AS, city: Optional[str] = CITY, repo_dir: Optional[str] = REPO_DIR,
) -> None:
    """List the proclaimed editions (tags)."""
    chamber = get_chamber(as_user, city, repo_dir)
    for e in archive.editions(chamber):
        console.print(e)


@app.command()
def inspect(
    limit: int = typer.Option(20, "--limit", help="How many archival acts to show."),
    as_user: str = AS, city: Optional[str] = CITY, repo_dir: Optional[str] = REPO_DIR,
) -> None:
    """Show the recent genealogy of the current line (git log)."""
    chamber = get_chamber(as_user, city, repo_dir)
    console.print(archive.inspect(chamber, limit))
