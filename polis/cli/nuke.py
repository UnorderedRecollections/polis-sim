"""polis nuke — implementation-breaching commands.

Operations that deliberately go AROUND the platforms' APIs (which don't
offer the needed routes). Each command is dangerous, prefix-scoped, and
requires --yes. Not part of the fiction; rig maintenance only.
"""
from __future__ import annotations

import subprocess

import typer

from .. import config
from .common import console, die, status_table

app = typer.Typer(no_args_is_help=True, help="Implementation-breaching commands (DB surgery). Dangerous.")
gogs_app = typer.Typer(no_args_is_help=True, help="Direct operations on the gogs database.")
app.add_typer(gogs_app, name="gogs")


def _psql(sql: str) -> str:
    proc = subprocess.run(
        ["podman", "exec", config.POSTGRES_CONTAINER,
         "psql", "-U", "gogs", "-d", "gogs", "-v", "ON_ERROR_STOP=1", "-tAc", sql],
        capture_output=True, text=True, timeout=30,
    )
    if proc.returncode != 0:
        die(f"psql failed: {proc.stderr.strip()[:300]}")
    return proc.stdout.strip()


def _orgs_matching(prefix: str) -> list[tuple[str, str]]:
    out = _psql(
        "SELECT id, name FROM \"user\" WHERE type = 1 "
        f"AND lower_name LIKE '{prefix.lower()}%' ORDER BY name"
    )
    rows = [line.split("|", 1) for line in out.splitlines() if "|" in line]
    return [(r[0], r[1]) for r in rows]


@gogs_app.command(name="orgs")
def gogs_orgs(
    prefix: str = typer.Argument(..., help="Org-name prefix to delete, e.g. prov-demo-01-"),
    yes: bool = typer.Option(False, "--yes", help="Execute the DB cascade."),
) -> None:
    """Delete gogs organizations by prefix — via direct DB cascade.

    The gogs API has no org-delete route (404). Orgs are rows in "user"
    (type=1) with dependents in org_user/team/team_repo/team_user.
    """
    orgs = _orgs_matching(prefix)
    if not orgs:
        console.print(f"[dim]no orgs matching '{prefix}%'[/dim]")
        return
    table = status_table(f"orgs matching '{prefix}%'", ["id", "name"])
    for oid, name in orgs:
        table.add_row(oid, name)
    console.print(table)
    if not yes:
        console.print(f"[yellow]preview only[/yellow] — {len(orgs)} org(s) would be "
                      "deleted with all team/membership rows. Re-run with --yes.")
        return
    ids = ",".join(oid for oid, _ in orgs)
    cascade = f"""
BEGIN;
DELETE FROM team_repo WHERE org_id IN ({ids});
DELETE FROM team_user WHERE org_id IN ({ids});
DELETE FROM team      WHERE org_id IN ({ids});
DELETE FROM org_user  WHERE org_id IN ({ids});
DELETE FROM "user"    WHERE id IN ({ids}) AND type = 1;
COMMIT;
"""
    _psql(cascade)
    console.print(f"[green]deleted {len(orgs)} org(s)[/green] matching '{prefix}%'"
                  " (teams, memberships and repo links included)")
