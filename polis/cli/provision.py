"""polis provision — porcelain: assemble (and remove) a sim instance's world."""
from __future__ import annotations

import typer

from .. import provision
from .common import console, die, status_table

app = typer.Typer(no_args_is_help=True, help="Provision a complete sim instance (users, repos, slices, containers).")


@app.command()
def up(
    sim: str = typer.Argument(..., help="Sim instance id, e.g. harbour-01."),
    with_city_containers: bool = typer.Option(False, "--with-city-containers",
                                              help="Also build/run the polis-city containers."),
    force: bool = typer.Option(False, "--force", help="Re-provision even if an inventory exists."),
) -> None:
    """Provision a sim instance (idempotent)."""
    from ..sim.journal import SIMS_DIR
    if (SIMS_DIR / sim / "provision.json").exists() and not force:
        die(f"'{sim}' is already provisioned — use --force to re-provision")
    try:
        inv = provision.up(sim, with_city_containers=with_city_containers)
    except provision.ProvisionError as e:
        die(str(e))
    console.print(f"[green]sim '{sim}' provisioned[/green]")
    console.print(f"  users:      {len(inv.users)}")
    console.print(f"  repos:      {len(inv.repos)} (archive + {len(inv.repos)-1} city)")
    console.print(f"  orgs:       {len(inv.orgs)} [dim](teardown-exempt)[/dim]")
    console.print(f"  slices:     {inv.slices_dir}")
    if inv.containers:
        console.print(f"  containers: {len(inv.containers)}")


@app.command()
def status(
    sim: str = typer.Argument(..., help="Sim instance id."),
) -> None:
    """Check the provisioned resources against the inventory."""
    try:
        report = provision.status(sim)
    except provision.ProvisionError as e:
        die(str(e))
    table = status_table(f"provision status — {sim}", ["kind", "name", "state", "note"])
    for it in report["items"]:
        state = "[green]present[/green]" if it["exists"] else "[red]MISSING[/red]"
        table.add_row(it["kind"], it["name"], state, it["note"])
    console.print(table)
    if not report["ok"]:
        raise typer.Exit(code=1)


@app.command()
def teardown(
    sim: str = typer.Argument(..., help="Sim instance id."),
    yes: bool = typer.Option(False, "--yes", help="Confirm deletion."),
) -> None:
    """Delete exactly what the inventory lists (orgs are exempt — no route)."""
    if not yes:
        die("refusing without --yes")
    try:
        done = provision.teardown(sim)
    except provision.ProvisionError as e:
        die(str(e))
    console.print(f"[green]sim '{sim}' torn down[/green]: "
                  f"{done['repos']} repos, {done['users']} users, "
                  f"{done['containers']} containers deleted; "
                  f"{done['orgs_kept']} orgs kept (no delete route)")
