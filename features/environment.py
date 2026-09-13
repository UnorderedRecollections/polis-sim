"""behave environment: a throwaway provisioned sim per scenario.

Sets POLIS_PROVISIONED_SIM and reloads polis.config so every polis
module (which reads config attributes at call time) points at the
scenario's sim. The sim is destroyed afterwards.

Platform selection (task 0053): `-D platform=gitea` (or a scenario
@gitea tag) backs the scenario with that product; default gogs. The
civil registry (world.json) is snapshotted before and restored after
every scenario — the phase transition flips it globally.
"""
from __future__ import annotations

import importlib
import os
import re
import shutil
import tempfile
from pathlib import Path


def _sim_id(name: str) -> str:
    # gogs usernames cap at 35 chars; users are named <sim>-<username>,
    # so sim ids cap at 13 chars
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:9] or "scenario"
    return f"bdd-{slug}"


def _platform(context, scenario) -> str:
    requested = context.config.userdata.get("platform")
    if requested:
        return requested
    tags = set(scenario.tags)
    if "gitea" in tags:
        return "gitea"
    if "gogs" in tags:
        return "gogs"
    return "gogs"


def _world_file() -> Path:
    import polis.config
    return Path(polis.config.WORLD_FILE)


def before_scenario(context, scenario):
    context.sim = _sim_id(scenario.name)
    context.platform = _platform(context, scenario)
    context._world_backup = None
    world = _world_file()
    if world.exists():
        backup_dir = Path(tempfile.mkdtemp(prefix="polis-bdd-world-"))
        context._world_backup = backup_dir / "world.json"
        shutil.copy(world, context._world_backup)
    os.environ["POLIS_PROVISIONED_SIM"] = context.sim
    import polis.config
    importlib.reload(polis.config)   # recompute endpoints/secrets for the sim
    context.petition_id = None
    context.bill_branch = None
    context.matter_id = None


def after_scenario(context, scenario):
    from polis import provision
    backup = getattr(context, "_world_backup", None)
    if backup and Path(backup).exists():
        shutil.copy(backup, _world_file())   # the transition flips it globally
    try:
        provision.destroy(context.sim)
    except Exception as e:
        print(f"[cleanup] destroy {context.sim} failed: {e}")
    os.environ.pop("POLIS_PROVISIONED_SIM", None)
    import polis.config
    importlib.reload(polis.config)
