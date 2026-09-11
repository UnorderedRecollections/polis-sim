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


def _run_id(run_id: Optional[str]) -> str:
    """Run id defaults to the provisioned-sim context (POLIS_PROVISIONED_SIM)."""
    from .. import config
    rid = run_id or config.PROVISIONED_SIM
    if not rid:
        die("run id required (or export POLIS_PROVISIONED_SIM=<sim>)")
    return rid


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
    run_id: Optional[str] = typer.Argument(None, help="Run id (== sim id; default: POLIS_PROVISIONED_SIM)."),
    situation: Optional[str] = typer.Option(
        None, "--situation", help="Seed situation YAML to copy in (bootstrap point)."),
    jurisdiction: Optional[str] = typer.Option(
        None, "--jurisdiction", help="Jurisdiction the run legislates in "
        "(default: the situation file's stem)."),
    seed: Optional[str] = typer.Option(
        None, "--seed", help="Determinism seed (default: generated, recorded in run.json)."),
) -> None:
    """Start a simulation run (empty journal; optional situation seed)."""
    import secrets
    from pathlib import Path
    from ..sim.director import RunConfig
    from ..sim.norms import load_norm_file as lnf, save_norm_file

    run_id = _run_id(run_id)
    journal = new_run(run_id)
    jur = jurisdiction
    if situation:
        src = Path(situation)
        if not src.exists():
            die(f"situation file not found: {src}")
        save_norm_file(lnf(src), journal.path.parent / "situation.yaml",
                       description=f"bootstrap from {src.name}")
        jur = jur or src.stem
    if jur:
        RunConfig(run=run_id, jurisdiction=jur,
                  seed=seed or secrets.token_hex(4)).save()
        console.print(f"[green]run started:[/green] {run_id} "
                      f"(jurisdiction: {jur}, situation: {Path(situation).name if situation else 'none'})")
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
    run_id: Optional[str] = typer.Argument(None, help="Run to present (default: POLIS_PROVISIONED_SIM)."),
    last: Optional[int] = typer.Option(None, "--last", help="Only the last N entries."),
    epoch: Optional[str] = typer.Option(None, "--epoch", help="Narrate a saved epoch "
                                        "(see `polis sim epochs`) instead of the live record."),
) -> None:
    """Narrated step-through of a run from its journal (no infra contact)."""
    rid = _run_id(run_id)
    if epoch:
        from ..sim import journal as journal_mod
        from ..sim import runtime as runtime_mod
        path = journal_mod.epochs_dir(rid) / epoch / "journal.jsonl"
        if not path.exists():
            die(f"no epoch '{epoch}' for run '{rid}' (see `polis sim epochs`)")
        journal = journal_mod.Journal(rid)
        journal.path = path
        rt = runtime_mod.Runtime(journal)
    else:
        rt = _load_runtime(rid)
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


@app.command()
def drive(
    run_id: Optional[str] = typer.Argument(None, help="Run to drive (default: POLIS_PROVISIONED_SIM)."),
    steps: int = typer.Option(1, "--steps", help="How many stories to drive."),
    local: bool = typer.Option(False, "--local",
                               help="Execute in-process (used inside the operator container)."),
) -> None:
    """Drive the run forward: N stories, end to end (docs/design/director.md).

    Host-side, this proxies into the sim's operator container; --local runs
    the director in-process (where the network and mounts are).
    """
    run_id = _run_id(run_id)
    if not local:
        from ..clients import podman
        name = f"polis-operator-{run_id}"
        try:
            proxied = podman.container_running(name)
        except Exception:
            proxied = False          # podman hiccup — degrade, never crash
        if proxied:
            import subprocess
            proc = subprocess.run(
                ["podman", "exec", name, "polis", "sim", "drive", run_id,
                 "--steps", str(steps), "--local"])
            raise typer.Exit(proc.returncode)
        console.print("[yellow]no operator container running — executing locally "
                      "(host-swapped URLs)[/yellow]")
    from ..sim import director
    try:
        stories = director.drive(run_id, steps)
    except director.DirectorError as e:
        die(str(e))
    for s in stories:
        style = {"enacted": "green", "failed": "red", "skipped": "yellow"}.get(s.status, "white")
        console.print(f"[{style}]{s.id}: {s.status}[/{style}] "
                      f"{s.bindings.get('title', '')} "
                      f"[dim](matter: {s.matter or '—'})[/dim]")
        if s.error:
            console.print(f"  [red]{s.error}[/red]")


@app.command()
def tick(
    run_id: Optional[str] = typer.Argument(None, help="Run to drive (default: POLIS_PROVISIONED_SIM)."),
    local: bool = typer.Option(False, "--local"),
) -> None:
    """One story — `sim drive --steps 1`."""
    drive(_run_id(run_id), 1, local)


@app.command()
def transition(
    run_id: Optional[str] = typer.Argument(None, help="Run to transition (default: POLIS_PROVISIONED_SIM)."),
    local: bool = typer.Option(False, "--local",
                               help="Execute in-process (used inside the operator container)."),
) -> None:
    """Enact the phase transition (task 0038): the three acts of the
    codified machinery (data/world/legal/transition/) are introduced and
    ratified through the customary procedure; the third ratification flips
    the federation to phase 2 (situation + registry + slices). Requires a
    gitea-hosted sim (`provision up --platform gitea`). When the story is
    enacted, the host erects the Mechanical Magistrate's CI (task 0041).
    """
    run_id = _run_id(run_id)
    if not local:
        from ..clients import podman
        name = f"polis-operator-{run_id}"
        try:
            proxied = podman.container_running(name)
        except Exception:
            proxied = False          # podman hiccup — degrade, never crash
        if proxied:
            import subprocess
            proc = subprocess.run(
                ["podman", "exec", name, "polis", "sim", "transition", run_id,
                 "--local"])
            if proc.returncode == 0:
                _erect_ci(run_id)
            raise typer.Exit(proc.returncode)
        console.print("[yellow]no operator container running — executing locally "
                      "(host-swapped URLs)[/yellow]")
    from ..sim import transition as transition_mod
    try:
        story = transition_mod.transition(run_id)
    except transition_mod.DirectorError as e:
        die(str(e))
    style = {"enacted": "green", "failed": "red"}.get(story.status, "white")
    console.print(f"[{style}]{story.id}: {story.status}[/{style}] "
                  f"acts: {', '.join(story.bindings.get('acts', []))}")
    if story.error:
        console.print(f"  [red]{story.error}[/red]")
    else:
        console.print(f"[bold]the federation now operates in phase 2[/bold] "
                      f"(edition: {story.bindings.get('edition', '')})")
        _erect_ci(run_id)


def _erect_ci(run_id: str) -> None:
    """The third act erects the Mechanical Magistrate — bring its CI up.
    The operator container has no podman; the host wrapper (the proxied
    call site) performs the bring-up."""
    import os
    if os.environ.get("POLIS_SIM_DIR"):
        return    # inside the operator container — the host handles this
    from .. import provision
    try:
        provision.up_woodpecker(run_id)
        console.print("[bold]the Mechanical Magistrate's CI is erected[/bold] "
                      "(woodpecker server + agent, OAuth, the archive repo enabled)")
    except provision.ProvisionError as e:
        console.print(f"[yellow]CI bring-up failed: {e}[/yellow]")


@app.command()
def submit(
    feature: str = typer.Argument(..., help="Path to a .feature file (one scenario)."),
    run_id: Optional[str] = typer.Option(None, "--run", help="Target run (default: POLIS_PROVISIONED_SIM)."),
    name: Optional[str] = typer.Option(None, "--name", help="Scenario name override."),
) -> None:
    """Submit a scenario to a RUNNING sim (0034b): setup beats execute now,
    action/expectation beats are serviced by the director, one per step.
    """
    from ..sim import queue as queue_mod
    rid = _run_id(run_id)
    try:
        st = queue_mod.submit(rid, feature, name)
    except queue_mod.QueueError as e:
        die(str(e))
    console.print(f"[green]scenario accepted:[/green] {st.name} "
                  f"({len(st.beats)} beats, {st.position} executed at submission)")
    console.print("[dim]the director services one action beat per drive step — "
                  "`polis sim scenarios` shows the scoreboard[/dim]")


@app.command()
def scenarios(
    run_id: Optional[str] = typer.Argument(None, help="Run to inspect (default: POLIS_PROVISIONED_SIM)."),
) -> None:
    """The scenario scoreboard: queued scenarios and their beat statuses."""
    from ..sim import queue as queue_mod
    rid = _run_id(run_id)
    states = queue_mod.list_scenarios(rid)
    if not states:
        console.print(f"[dim]no scenarios queued for '{rid}' — `polis sim submit`[/dim]")
        return
    for st in states:
        style = {"active": "cyan", "paused": "red", "done": "green"}.get(st.status, "white")
        console.print(f"[{style}]{st.name}[/{style}] — {st.status}"
                      + (f" [red]({st.error})[/red]" if st.error else ""))
        table = status_table(None, ["line", "kind", "status", "beat"])
        for b in st.beats:
            table.add_row(str(b.line), b.kind, b.status, b.text[:60])
        console.print(table)


@app.command()
def resume(
    slug: str = typer.Argument(..., help="Scenario slug (see `polis sim scenarios`)."),
    run_id: Optional[str] = typer.Option(None, "--run", help="Target run (default: POLIS_PROVISIONED_SIM)."),
) -> None:
    """Re-activate a paused scenario (the failed beat becomes pending again)."""
    from ..sim import queue as queue_mod
    rid = _run_id(run_id)
    try:
        st = queue_mod.resume(rid, slug)
    except queue_mod.QueueError as e:
        die(str(e))
    console.print(f"[green]scenario resumed:[/green] {st.name} — "
                  "the next drive step retries the failed beat")


@app.command()
def stories(
    run_id: Optional[str] = typer.Argument(None, help="Run to inspect (default: POLIS_PROVISIONED_SIM)."),
) -> None:
    """The run's story records (docs/design/director.md §6)."""
    from ..sim.director import load_stories
    stories_ = load_stories(_run_id(run_id))
    if not stories_:
        console.print(f"[dim]run '{run_id}' has no stories yet — `polis sim drive`[/dim]")
        return
    table = status_table(f"stories — {run_id}",
                         ["id", "status", "template", "title", "matter", "cast"])
    for s in stories_:
        cast = ", ".join(f"{k}={v}" for k, v in s.cast.items())
        table.add_row(s.id, s.status, s.template,
                      s.bindings.get("title", ""), s.matter or "—", cast)
    console.print(table)


@app.command()
def fresh(
    run_id: Optional[str] = typer.Argument(None, help="Run to reset (default: POLIS_PROVISIONED_SIM)."),
    yes: bool = typer.Option(False, "--yes", help="Confirm archiving + clearing the record."),
    name: Optional[str] = typer.Option(None, "--name", help="Epoch name (default: timestamp)."),
) -> None:
    """Start a fresh epoch: archive the current record, then clear it.

    The MACHINERY is untouched (platform, slices, secrets — and the legal
    archive's git history, which does not roll back; for a blank legal
    slate, teardown + rm -rf the sim dir). Afterwards, `polis sim new`
    bootstraps the new epoch.
    """
    from ..sim import journal as journal_mod
    from ..sim.journal import _utcnow
    rid = _run_id(run_id)
    epoch = name or _utcnow().replace(":", "").replace("-", "").lower()
    if not yes:
        die(f"this archives the current record of '{rid}' to epochs/{epoch} "
            "and clears it — re-run with --yes")
    try:
        dest = journal_mod.save_epoch(rid, epoch)
    except (FileExistsError, FileNotFoundError) as e:
        die(str(e))
    removed = journal_mod.clear_record(rid)
    console.print(f"[green]epoch saved:[/green] {dest}")
    console.print(f"[green]record cleared[/green] ({', '.join(removed)}) "
                  f"— `polis sim new` starts the fresh epoch")


@app.command()
def epochs(
    run_id: Optional[str] = typer.Argument(None, help="Run to inspect (default: POLIS_PROVISIONED_SIM)."),
) -> None:
    """List the run's saved epochs (records archived by `sim fresh`)."""
    from ..sim import journal as journal_mod
    rid = _run_id(run_id)
    names = journal_mod.list_epochs(rid)
    if not names:
        console.print(f"[dim]no saved epochs for '{rid}' — `polis sim fresh` archives one[/dim]")
        return
    table = status_table(f"epochs — {rid}", ["epoch", "entries", "span"])
    for n in names:
        journal = journal_mod.Journal(rid)
        journal.path = journal_mod.epochs_dir(rid) / n / "journal.jsonl"
        es = journal.entries()
        span = f"{es[0].ts} → {es[-1].ts}" if es else "—"
        table.add_row(n, str(len(es)), span)
    console.print(table)


@app.command(name="runtime")
def runtime_(
    run_id: Optional[str] = typer.Argument(None, help="Run to attach to (default: POLIS_PROVISIONED_SIM)."),
) -> None:
    """Show the runtime state for a run (journal size, situation summary)."""
    rt = _load_runtime(_run_id(run_id))
    console.print(f"run: [bold]{rt.journal.run_id}[/bold]")
    console.print(f"  journal entries: {len(rt.journal.entries())}")
    if rt.situation is not None:
        live = rt.situation.in_force()
        console.print(f"  situation: {len(live)} norms in force, "
                      f"{len(rt.situation.holdings)} holdings")
    else:
        console.print("  situation: [dim]none attached[/dim]")
