"""polis woodpecker — operate the CI server (the Magistrate's engine room)."""
from __future__ import annotations

import time

import typer

from ..clients.woodpecker import WoodpeckerClient, WoodpeckerError
from .common import console, die, status_table

app = typer.Typer(no_args_is_help=True, help="Woodpecker CI: the automatic formal-legality machinery.")
agents_app = typer.Typer(no_args_is_help=True, help="Build agents registered with the server.")
app.add_typer(agents_app, name="agents")


def _client() -> WoodpeckerClient:
    try:
        return WoodpeckerClient()
    except RuntimeError as e:
        die(str(e))


@app.command()
def whoami() -> None:
    """Show which identity the configured API key authenticates as."""
    try:
        user = _client().whoami()
    except WoodpeckerError as e:
        die(str(e))
    console.print(f"{user.get('login')} <{user.get('email')}> (id={user.get('id')})")


@agents_app.command(name="list")
def agents_list() -> None:
    """List registered agents and whether they are alive."""
    try:
        agents = _client().list_agents()
    except WoodpeckerError as e:
        die(str(e))
    now = int(time.time())
    table = status_table("woodpecker agents", ["id", "name", "platform", "backend", "last contact", "state"])
    for a in agents:
        last = a.get("last_contact") or 0
        silence = now - last if last else None
        alive = silence is not None and silence < 300
        table.add_row(
            str(a.get("id")), a.get("name") or "[dim]—[/dim]",
            a.get("platform") or "?", a.get("backend") or "?",
            f"{silence}s ago" if silence is not None else "never",
            "[green]live[/green]" if alive else "[red]stale[/red]",
        )
    console.print(table)


@agents_app.command(name="delete")
def agents_delete(
    agent_id: int = typer.Argument(...),
    yes: bool = typer.Option(False, "--yes", help="Confirm deletion."),
) -> None:
    """De-register an agent (e.g. a stale record)."""
    if not yes:
        die("refusing without --yes")
    try:
        _client().delete_agent(agent_id)
    except WoodpeckerError as e:
        die(str(e))
    console.print(f"[green]deleted agent:[/green] {agent_id}")
