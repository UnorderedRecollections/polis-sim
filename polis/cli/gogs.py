"""polis gogs — operate the phase-1 platform (customary machinery)."""
from __future__ import annotations

from typing import Optional

import typer

from ..clients.gogs import GogsClient, GogsError
from .common import console, die, status_table

app = typer.Typer(no_args_is_help=True, help="Gogs: the phase-1 institutional apparatus.")
users_app = typer.Typer(no_args_is_help=True, help="User accounts on gogs.")
orgs_app = typer.Typer(no_args_is_help=True, help="Organizations on gogs.")
repos_app = typer.Typer(no_args_is_help=True, help="Repositories on gogs.")
app.add_typer(users_app, name="users")
app.add_typer(orgs_app, name="orgs")
app.add_typer(repos_app, name="repos")


def _client() -> GogsClient:
    try:
        return GogsClient()
    except RuntimeError as e:
        die(str(e))


@app.command()
def whoami() -> None:
    """Show which identity the configured API key authenticates as."""
    try:
        user = _client().whoami()
    except GogsError as e:
        die(str(e))
    console.print(f"{user.get('login')} <{user.get('email')}> (id={user.get('id')})")


@app.command()
def status() -> None:
    """Quick overview: identity, org and repo counts."""
    client = _client()
    try:
        user = client.whoami()
        orgs = client.list_orgs()
        repos = client.list_repos()
    except GogsError as e:
        die(str(e))
    console.print(f"[green]gogs up[/green] — authenticated as {user.get('login')}")
    console.print(f"  orgs:  {len(orgs)}")
    console.print(f"  repos: {len(repos)}")


@users_app.command(name="list")
def users_list(query: str = typer.Option("", "--query", help="Filter substring.")) -> None:
    """List user accounts."""
    try:
        users = _client().search_users(query)
    except GogsError as e:
        die(str(e))
    table = status_table("gogs users", ["id", "username", "full name", "email"])
    for u in users:
        table.add_row(str(u.get("id")), u.get("username", ""), u.get("full_name", ""), u.get("email", ""))
    console.print(table)


@users_app.command(name="create")
def users_create(
    username: str = typer.Option(...),
    email: str = typer.Option(...),
    password: str = typer.Option(...),
    full_name: str = typer.Option("", "--full-name"),
) -> None:
    """Create a user account (admin operation)."""
    try:
        user = _client().create_user(username, email, password, full_name)
    except GogsError as e:
        die(str(e))
    console.print(f"[green]created gogs user:[/green] {user.get('username', username)}")


@users_app.command(name="delete")
def users_delete(
    username: str = typer.Argument(...),
    yes: bool = typer.Option(False, "--yes", help="Confirm deletion."),
) -> None:
    """Delete a user account (admin operation)."""
    if not yes:
        die("refusing without --yes")
    try:
        _client().delete_user(username)
    except GogsError as e:
        die(str(e))
    console.print(f"[green]deleted gogs user:[/green] {username}")


@orgs_app.command(name="list")
def orgs_list() -> None:
    """List organizations visible to the configured identity."""
    try:
        orgs = _client().list_orgs()
    except GogsError as e:
        die(str(e))
    table = status_table("gogs orgs", ["id", "username", "full name"])
    for o in orgs:
        table.add_row(str(o.get("id")), o.get("username", ""), o.get("full_name", ""))
    console.print(table)


@orgs_app.command(name="create")
def orgs_create(
    username: str = typer.Option(...),
    full_name: str = typer.Option("", "--full-name"),
) -> None:
    """Create an organization."""
    try:
        org = _client().create_org(username, full_name)
    except GogsError as e:
        die(str(e))
    console.print(f"[green]created gogs org:[/green] {org.get('username', username)}")


@repos_app.command(name="list")
def repos_list() -> None:
    """List repositories."""
    try:
        repos = _client().list_repos()
    except GogsError as e:
        die(str(e))
    table = status_table("gogs repos", ["id", "full name", "private", "fork"])
    for r in repos:
        table.add_row(
            str(r.get("id")), r.get("full_name", ""),
            str(r.get("private", "")), str(r.get("fork", "")),
        )
    console.print(table)
