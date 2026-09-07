"""polis gitea — operate the phase-2 platform (codified machinery)."""
from __future__ import annotations

import typer

from ..clients.gitea import GiteaClient, GiteaError
from .common import console, die, status_table

app = typer.Typer(no_args_is_help=True, help="Gitea: the phase-2 institutional apparatus.")
users_app = typer.Typer(no_args_is_help=True, help="User accounts on gitea.")
orgs_app = typer.Typer(no_args_is_help=True, help="Organizations on gitea.")
repos_app = typer.Typer(no_args_is_help=True, help="Repositories on gitea.")
app.add_typer(users_app, name="users")
app.add_typer(orgs_app, name="orgs")
app.add_typer(repos_app, name="repos")


def _client() -> GiteaClient:
    try:
        return GiteaClient()
    except RuntimeError as e:
        die(str(e))


@app.command()
def whoami() -> None:
    """Show which identity the configured API key authenticates as."""
    try:
        user = _client().whoami()
    except GiteaError as e:
        die(str(e))
    admin = " [cyan](admin)[/cyan]" if user.get("is_admin") else ""
    console.print(f"{user.get('login')} <{user.get('email')}> (id={user.get('id')}){admin}")


@app.command()
def status() -> None:
    """Quick overview: version, identity, org and repo counts."""
    client = _client()
    try:
        version = client.version()
        user = client.whoami()
        orgs = client.list_orgs()
        repos = client.list_repos()
    except GiteaError as e:
        die(str(e))
    console.print(f"[green]gitea up[/green] (v{version}) — authenticated as {user.get('login')}")
    console.print(f"  orgs:  {len(orgs)}")
    console.print(f"  repos: {len(repos)}")


@users_app.command(name="list")
def users_list(
    query: str = typer.Option("", "--query", help="Filter substring."),
    admin: bool = typer.Option(False, "--admin", help="Use the admin endpoint (includes inactive)."),
) -> None:
    """List user accounts."""
    try:
        users = _client().admin_users() if admin else _client().search_users(query)
    except GiteaError as e:
        die(str(e))
    table = status_table("gitea users", ["id", "username", "full name", "email", "admin"])
    for u in users:
        table.add_row(
            str(u.get("id")), u.get("login", u.get("username", "")),
            u.get("full_name", ""), u.get("email", ""), "yes" if u.get("is_admin") else "",
        )
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
    except GiteaError as e:
        die(str(e))
    console.print(f"[green]created gitea user:[/green] {user.get('login', username)}")


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
    except GiteaError as e:
        die(str(e))
    console.print(f"[green]deleted gitea user:[/green] {username}")


@orgs_app.command(name="list")
def orgs_list() -> None:
    """List organizations visible to the configured identity."""
    try:
        orgs = _client().list_orgs()
    except GiteaError as e:
        die(str(e))
    table = status_table("gitea orgs", ["id", "username", "full name"])
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
    except GiteaError as e:
        die(str(e))
    console.print(f"[green]created gitea org:[/green] {org.get('username', username)}")


@repos_app.command(name="list")
def repos_list() -> None:
    """List repositories."""
    try:
        repos = _client().list_repos()
    except GiteaError as e:
        die(str(e))
    table = status_table("gitea repos", ["id", "full name", "private", "fork"])
    for r in repos:
        table.add_row(
            str(r.get("id")), r.get("full_name", ""),
            str(r.get("private", "")), str(r.get("fork", "")),
        )
    console.print(table)
