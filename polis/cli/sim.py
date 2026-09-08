"""polis sim — simulation runs: the journal, presentation and (later) replay."""
from __future__ import annotations

from typing import Optional

import typer
from rich.panel import Panel

from ..sim import runtime as runtime_mod
from ..sim.journal import Journal, list_runs, new_run
from ..sim.norms import load_norm_file
from .common import console, die, status_table

app = typer.Typer(no_args_is_help=True, help="Simulation runs and the journal.")


def _load_runtime(run_id: str) -> runtime_mod.Runtime:
    """Runtime on an existing run (journal + situation if present)."""
    journal = Journal(run_id)
    if not journal.path.exists():
        die(f"no such run '{run_id}' (see `polis sim list`)")
    sit_path = journal.path.parent / "situation.yaml"
    situation = load_norm_file(sit_path) if sit_path.exists() else None
    return runtime_mod.Runtime(journal, situation, sit_path if situation else None)


@app.command(name="new")
def new(
    run_id: str = typer.Argument(..., help="Run id, e.g. harbour-dues-01."),
    situation: Optional[str] = typer.Option(
        None, "--situation", help="Seed situation YAML to copy in (bootstrap point)."),
) -> None:
    """Start a simulation run (empty journal; optional situation seed)."""
    from pathlib import Path
    from ..sim.norms import load_norm_file as lnf, save_norm_file

    journal = new_run(run_id)
    if situation:
        src = Path(situation)
        if not src.exists():
            die(f"situation file not found: {src}")
        save_norm_file(lnf(src), journal.path.parent / "situation.yaml",
                       description=f"bootstrap from {src.name}")
        console.print(f"[green]run started:[/green] {run_id} (situation: {src.name})")
    else:
        console.print(f"[green]run started:[/green] {run_id}")


@app.command(name="list")
def list_() -> None:
    """List simulation runs."""
    runs = list_runs()
    if not runs:
        console.print("[dim]no runs yet — `polis sim new <run-id>`[/dim]")
        return
    table = status_table("simulation runs", ["run", "entries"])
    for r in runs:
        table.add_row(r, str(len(Journal(r).entries())))
    console.print(table)


@app.command()
def present(
    run_id: str = typer.Argument(..., help="Run to present."),
    last: Optional[int] = typer.Option(None, "--last", help="Only the last N entries."),
) -> None:
    """Narrated step-through of a run from its journal (no infra contact)."""
    rt = _load_runtime(run_id)
    entries = rt.journal.entries()
    if last:
        entries = entries[-last:]
    if not entries:
        console.print(f"[dim]run '{run_id}' has no journal entries yet[/dim]")
        return
    for e in entries:
        if e.kind == "observation":
            console.print(f"[magenta]{e.seq}.[/magenta] [italic]observed by {e.actor}: "
                          f"{e.action}[/italic] {e.result}")
            continue
        lines = [f"[bold]{e.action}[/bold]  [dim]({e.ts})[/dim]"]
        for k, v in e.params.items():
            if v is not None:
                lines.append(f"  {k}: {v}")
        if e.result.get("id"):
            lines.append(f"  → {e.result['id']}")
        a = e.anchors
        if a.get("main_before") or a.get("main_after"):
            lines.append(f"  main: {a.get('main_before','?')} → {a.get('main_after','?')}")
        if a.get("matter"):
            lines.append(f"  matter: {a['matter']}")
        if a.get("situation"):
            lines.append(f"  situation: {a['situation']}")
        console.print(Panel("\n".join(lines), title=f"{e.seq} — {e.actor}",
                            title_align="left", border_style="cyan"))


@app.command(name="runtime")
def runtime_(
    run_id: str = typer.Argument(..., help="Run to attach to."),
) -> None:
    """Show the runtime state for a run (journal size, situation summary)."""
    rt = _load_runtime(run_id)
    console.print(f"run: [bold]{run_id}[/bold]")
    console.print(f"  journal entries: {len(rt.journal.entries())}")
    if rt.situation is not None:
        live = rt.situation.in_force()
        console.print(f"  situation: {len(live)} norms in force, "
                      f"{len(rt.situation.holdings)} holdings")
    else:
        console.print("  situation: [dim]none attached[/dim]")
