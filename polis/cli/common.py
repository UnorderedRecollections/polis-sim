"""Shared helpers for CLI commands."""
from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from ..models import World
from ..store import load_world

console = Console()
err_console = Console(stderr=True)


def die(message: str) -> None:
    err_console.print(f"[bold red]error:[/bold red] {message}")
    raise typer.Exit(code=1)


def get_world() -> World:
    return load_world()


def lookup(world: World, kind: str, finder, key: str):
    try:
        return finder(key)
    except KeyError as e:
        die(f"{kind} not found: {e.args[0]}")


def status_table(title: str, columns: list[str]) -> Table:
    table = Table(title=title, header_style="bold cyan", title_justify="left")
    for col in columns:
        table.add_column(col)
    return table


# --- legislation helpers -------------------------------------------------------

def get_chamber(as_user: str, city: str | None, repo_dir: str | None):
    """Load the legislative Chamber, turning configuration errors into CLI errors.
    (load_chamber itself obtains the working copy on first use.)"""
    from ..legislation.chamber import ChamberError, load_chamber

    try:
        return load_chamber(as_user=as_user, city=city, repo_dir=repo_dir)
    except ChamberError as e:
        die(str(e))


def enact(plan, isomorphism: bool):
    """Render the plan instead of executing it when --isomorphism is given.
    Returns the executed steps' results (empty list when rendering)."""
    if isomorphism:
        plan.render_isomorphism()
        return []
    try:
        return plan.execute()
    except Exception as e:  # ChamberError, GitError, platform errors
        die(str(e))
