"""CLI-level steps on an isolated federation (task 0066).

These steps run `polis` as a subprocess against a temporary POLIS_DATA_DIR
so a scenario never touches the repository's runtime state (world.json,
sims). The tracked legal seed (`data/world/legal/`) is symlinked into the
temporary world, exactly as a real deployment would mount it.

Container-free by design: they serve the domain-model and functional
domains, so those workflows run anywhere `uv` does.
"""
from __future__ import annotations

import os
import shlex
import shutil
import subprocess
import tempfile
from pathlib import Path

from behave import given, then, when

ROOT = Path(__file__).resolve().parents[2]


def _isolated_dir(context) -> Path:
    tmp = getattr(context, "isolated_dir", None)
    if tmp:
        return tmp
    tmp = Path(tempfile.mkdtemp(prefix="polis-bdd-isolated-"))
    (tmp / "world").mkdir(parents=True, exist_ok=True)
    os.symlink(ROOT / "data" / "world" / "legal", tmp / "world" / "legal")

    def _cleanup() -> None:
        shutil.rmtree(tmp, ignore_errors=True)
        context.isolated_dir = None

    context.isolated_dir = tmp
    if hasattr(context, "add_cleanup"):
        context.add_cleanup(_cleanup)
    return tmp


def _run(context, *args: str) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env.pop("POLIS_PROVISIONED_SIM", None)
    env["POLIS_DATA_DIR"] = str(_isolated_dir(context))
    # wide terminal so Rich does not wrap/truncate table cells: assertions
    # on full identifiers stay meaningful
    env["COLUMNS"] = "200"
    return subprocess.run(["uv", "run", "polis", *args], cwd=ROOT, env=env,
                          capture_output=True, text=True)


@given("an isolated federation is generated")
def isolated_federation(context):
    context.last = _run(context, "world", "genesis")
    assert context.last.returncode == 0, \
        (context.last.stdout + context.last.stderr)[-500:]


@given("an isolated federation directory without a world")
def isolated_without_world(context):
    _isolated_dir(context)


@when('I run polis with "{args}"')
def run_polis(context, args):
    # `{data_dir}` stands for the scenario's isolated world (e.g. a
    # `--repo-dir` that must exist), `{repo_dir}` for a fixture git repo
    # a step set up; shlex keeps quoted titles together
    args = (args.replace("{data_dir}", str(_isolated_dir(context)))
                .replace("{repo_dir}", str(getattr(context, "repo_dir", ""))))
    context.last = _run(context, *shlex.split(args))


def _flat(text: str) -> str:
    # Rich wraps output at the terminal width; assertions ignore the wrap
    return " ".join(text.split())


@then("the command succeeds")
def command_succeeds(context):
    assert context.last.returncode == 0, \
        (context.last.stdout + context.last.stderr)[-500:]


@then("the command fails")
def command_fails(context):
    assert context.last.returncode != 0, \
        f"expected failure, got exit=0: {(context.last.stdout + context.last.stderr)[-300:]}"


@then('the output contains "{text}"')
def output_contains(context, text):
    out = _flat(context.last.stdout + context.last.stderr)
    assert _flat(text) in out, f"'{text}' not in the command output: {out[-300:]}"


@then('the output does not contain "{text}"')
def output_does_not_contain(context, text):
    out = _flat(context.last.stdout + context.last.stderr)
    assert _flat(text) not in out, f"'{text}' unexpectedly in the command output: {out[-300:]}"


@then("every jurisdiction accepts a generated situation")
def every_jurisdiction_situation(context):
    slugs = sorted(p.stem for p in
                   (ROOT / "data" / "world" / "legal" / "jurisdictions").glob("*.yaml"))
    assert len(slugs) == 15, f"expected 15 jurisdictions, found {slugs}"
    for slug in slugs:
        proc = _run(context, "world", "situation", "new", slug)
        assert proc.returncode == 0, \
            f"{slug}: {(proc.stdout + proc.stderr)[-200:]}"
