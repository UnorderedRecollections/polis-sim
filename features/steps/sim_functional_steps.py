"""Sim-backed functional steps (task 0069).

`GIven a provisioned sim seeded from "<jurisdiction>"` (sim_steps) leaves a
throwaway sim running; these steps run the real CLI against it, keeping
`POLIS_PROVISIONED_SIM` set (unlike the isolated-federation runner).
"""
from __future__ import annotations

import os
import shlex
import subprocess
from pathlib import Path

from behave import when

ROOT = Path(__file__).resolve().parents[2]


@when('I run polis against the sim with "{args}"')
def run_polis_sim(context, args):
    env = dict(os.environ)
    env["POLIS_PROVISIONED_SIM"] = context.sim
    env["COLUMNS"] = "200"
    context.last = subprocess.run(["uv", "run", "polis", *shlex.split(args)],
                                  cwd=ROOT, env=env, capture_output=True, text=True)
