"""polis provision — porcelain: assemble (and remove) a sim instance's world."""
from __future__ import annotations

import json
from typing import Optional

import typer

from .. import config, provision
from .common import console, die, status_table

app = typer.Typer(no_args_is_help=True, help="Provision a complete sim instance (users, repos, slices, containers).")


def _sim(sim: Optional[str]) -> str:
    """Sim id defaults to the context (POLIS_PROVISIONED_SIM)."""
    sid = sim or config.PROVISIONED_SIM
    if not sid:
        die("sim id required (or export POLIS_PROVISIONED_SIM=<sim>)")
    return sid


@app.command()
def up(
    sim: Optional[str] = typer.Argument(None, help="Sim instance id (default: POLIS_PROVISIONED_SIM)."),
    platform: str = typer.Option("gogs", "--platform",
                                 help="The platform product hosting the sim: gogs | gitea "
                                      "(phase is a procedure, not a product — either hosts phase 1)."),
    with_city_containers: bool = typer.Option(False, "--with-city-containers",
                                              help="Also build/run the polis-city containers."),
    force: bool = typer.Option(False, "--force", help="Re-provision even if an inventory exists."),
) -> None:
    """Provision a sim instance (idempotent)."""
    from ..clients import podman
    from ..sim.journal import SIMS_DIR
    sim = _sim(sim)
    if platform not in ("gogs", "gitea"):
        die(f"unknown platform '{platform}' — choose gogs or gitea")
    # the guard checks liveness, not files: after a teardown the sim dir
    # (inventory, journal, secrets) remains, but re-provisioning over it is
    # exactly what `up` is for — the platform layer reuses volumes/secrets
    inv_path = SIMS_DIR / sim / "provision.json"
    existing_platform = "gogs"
    if inv_path.exists():
        try:
            existing_platform = json.loads(inv_path.read_text(encoding="utf-8")).get("platform") or "gogs"
        except Exception:
            pass
    already = inv_path.exists() and \
        podman.container_running(f"{sim}-{existing_platform}")
    if already and not force:
        die(f"'{sim}' is already provisioned and running — use --force to re-provision")
    try:
        inv = provision.up(sim, platform=platform, with_city_containers=with_city_containers)
    except provision.ProvisionError as e:
        die(str(e))
    console.print(f"[green]sim '{sim}' provisioned[/green] (platform: {inv.platform})")
    console.print(f"  users:      {len(inv.users)}")
    console.print(f"  repos:      {len(inv.repos)} (archive + {len(inv.repos)-1} city)")
    console.print(f"  orgs:       {len(inv.orgs)} [dim](die with the sim's {inv.platform})[/dim]")
    console.print(f"  slices:     {inv.slices_dir}")
    if inv.containers:
        console.print(f"  containers: {len(inv.containers)}")


@app.command()
def status(
    sim: Optional[str] = typer.Argument(None, help="Sim instance id (default: POLIS_PROVISIONED_SIM)."),
) -> None:
    """Check the provisioned resources against the inventory."""
    sim = _sim(sim)
    try:
        report = provision.status(sim)
    except provision.ProvisionError as e:
        die(str(e))
    table = status_table(f"provision status — {sim} (platform: {report.get('platform', 'gogs')})",
                         ["kind", "name", "state", "note"])
    for it in report["items"]:
        state = "[green]present[/green]" if it["exists"] else "[red]MISSING[/red]"
        table.add_row(it["kind"], it["name"], state, it["note"])
    console.print(table)
    if not report["ok"]:
        raise typer.Exit(code=1)


@app.command()
def stop(
    sim: Optional[str] = typer.Argument(None, help="Sim instance id (default: POLIS_PROVISIONED_SIM)."),
) -> None:
    """Pause the sim (containers stopped; volumes, journal and secrets kept)."""
    sim = _sim(sim)
    try:
        done = provision.stop(sim)
    except provision.ProvisionError as e:
        die(str(e))
    console.print(f"[green]sim '{sim}' stopped[/green] ({len(done['stopped'])} containers)"
                  " — `polis provision start` resumes it")


@app.command()
def start(
    sim: Optional[str] = typer.Argument(None, help="Sim instance id (default: POLIS_PROVISIONED_SIM)."),
) -> None:
    """Resume a stopped sim (dependency order: postgres → gogs → the rest)."""
    sim = _sim(sim)
    try:
        done = provision.start(sim)
    except provision.ProvisionError as e:
        die(str(e))
    console.print(f"[green]sim '{sim}' started[/green] ({len(done['started'])} containers)")


@app.command(name="list")
def list_() -> None:
    """Every sim known on this host (dirs, containers, record summary)."""
    sims = provision.list_sims()
    if not sims:
        console.print("[dim]no sims — `polis provision up <sim>` creates one[/dim]")
        return
    table = status_table("sims on this host", ["sim", "dir", "containers", "running", "journal"])
    for s in sims:
        table.add_row(s["sim"],
                      "[green]yes[/green]" if s["dir"] else "[red]no[/red]",
                      str(len(s["containers"])), str(len(s["running"])),
                      f"{s['entries']} entries" if s.get("entries") is not None else "—")
    console.print(table)


@app.command()
def destroy(
    sim: Optional[str] = typer.Argument(None, help="Sim instance id (default: POLIS_PROVISIONED_SIM)."),
    yes: bool = typer.Option(False, "--yes", help="Confirm full removal."),
) -> None:
    """FULLY remove a sim: repos/users (best effort), all its containers
    (matched by name, tolerant of stale inventories), its network, and the
    sim dir. This is the controlled `rm -rf`."""
    sim = _sim(sim)
    if not yes:
        die(f"this removes sim '{sim}' entirely (containers, network, "
            f"data/sims/{sim}) — re-run with --yes")
    done = provision.destroy(sim)
    console.print(f"[green]sim '{sim}' destroyed[/green]: "
                  f"{len(done['containers'])} containers, network {done['network']}, "
                  f"{done['repos']} repos, {done['users']} users, "
                  f"{'sim dir removed' if done['dir'] else 'no sim dir'}")


@app.command()
def teardown(
    sim: Optional[str] = typer.Argument(None, help="Sim instance id (default: POLIS_PROVISIONED_SIM)."),
    yes: bool = typer.Option(False, "--yes", help="Confirm deletion."),
) -> None:
    """Delete exactly what the inventory lists (orgs are exempt — no route)."""
    sim = _sim(sim)
    if not yes:
        die("refusing without --yes")
    try:
        done = provision.teardown(sim)
    except provision.ProvisionError as e:
        die(str(e))
    console.print(f"[green]sim '{sim}' torn down[/green]: "
                  f"{done['repos']} repos, {done['users']} users, "
                  f"{done['containers']} containers deleted"
                  + (f", network {done['network']} removed" if done.get("network") else "")
                  + "; orgs die with the sim's platform — remove data/sims/" + sim
                  + " to free its volumes")
