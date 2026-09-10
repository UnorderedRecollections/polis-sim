"""behave environment: a throwaway provisioned sim per scenario.

Sets POLIS_PROVISIONED_SIM and reloads polis.config so every polis
module (which reads config attributes at call time) points at the
scenario's sim. The sim is destroyed afterwards.
"""
from __future__ import annotations

import importlib
import os
import re


def _sim_id(name: str) -> str:
    # gogs usernames cap at 35 chars; users are named <sim>-<username>,
    # so sim ids cap at 13 chars
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:9] or "scenario"
    return f"bdd-{slug}"


def before_scenario(context, scenario):
    context.sim = _sim_id(scenario.name)
    os.environ["POLIS_PROVISIONED_SIM"] = context.sim
    import polis.config
    importlib.reload(polis.config)   # recompute endpoints/secrets for the sim
    context.petition_id = None
    context.bill_branch = None
    context.matter_id = None


def after_scenario(context, scenario):
    from polis import provision
    try:
        provision.destroy(context.sim)
    except Exception as e:
        print(f"[cleanup] destroy {context.sim} failed: {e}")
    os.environ.pop("POLIS_PROVISIONED_SIM", None)
    import polis.config
    importlib.reload(polis.config)
