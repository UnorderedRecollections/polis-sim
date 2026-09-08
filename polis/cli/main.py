"""polis — operator's tool for the git-law federation simulation."""
from __future__ import annotations

import typer

from . import (
    archive,
    assign,
    bill,
    city,
    citynode,
    docket,
    gitea,
    gogs,
    health,
    office,
    person,
    sim,
    woodpecker,
    world,
)

app = typer.Typer(
    name="polis",
    help=(
        "Model the federation (world/city/person/office/assign) and operate the "
        "institutional apparatus it runs on (gogs/gitea/woodpecker/citynode/health)."
    ),
    no_args_is_help=True,
)

# domain commands — the conceptual operations
app.add_typer(world.app, name="world")
app.add_typer(city.app, name="city")
app.add_typer(person.app, name="person")
app.add_typer(office.app, name="office")
app.add_typer(assign.app, name="assign")

# legislative machinery — every command builds a Plan and exposes --isomorphism
app.add_typer(docket.app, name="docket")
app.add_typer(bill.app, name="bill")
app.add_typer(archive.app, name="archive")

# simulation runs — the journal and (later) replay
app.add_typer(sim.app, name="sim")

# component commands — the technical subsystems
app.add_typer(gogs.app, name="gogs")
app.add_typer(gitea.app, name="gitea")
app.add_typer(woodpecker.app, name="woodpecker")
app.add_typer(citynode.app, name="citynode")
app.add_typer(health.app, name="health")

if __name__ == "__main__":
    app()
