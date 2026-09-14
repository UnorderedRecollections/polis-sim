"""Infrastructure-failure steps (task 0067) — the shared sim.

The scenarios mutate one provisioned sim (stop a container, occupy the
proxy port, delete a repository, remove the operator) and restore it, so
each case asserts the agreed behavior from `docs/design/failure-modes.md`:
fail fast with a remedy, no bare traceback, inspectable state, idempotent
recovery.
"""
from __future__ import annotations

import os
import socket
import subprocess
import threading
import time
from pathlib import Path

from behave import given, then, when

from polis import provision
from polis.clients import containers

ROOT = Path(__file__).resolve().parents[2]


def _run(context, *args: str) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env["POLIS_PROVISIONED_SIM"] = context.sim
    return subprocess.run(["uv", "run", "polis", *args], cwd=ROOT, env=env,
                          capture_output=True, text=True)


def _out(context) -> str:
    return (context.last.stdout or "") + (context.last.stderr or "")


def _platform_ready(context) -> None:
    """Wait until the sim's platform answers before a step touches it: on a
    slow runner a resumed/re-provisioned platform can lag behind the
    container state (task 0067)."""
    provision._wait_platform(context.sim)


@given("the shared sim is provisioned")
def shared_sim(context):
    provision.Inventory.load(context.sim)


@given("the gogs platform is stopped")
def stop_platform(context):
    containers.stop(f"{context.sim}-gogs")


@given("the proxy is stopped")
def stop_proxy(context):
    containers.rm(f"{context.sim}-proxy")


@given("the proxy port is occupied by another process")
def occupy_port(context):
    port = provision.load_secrets(context.sim)["proxy_port"]
    # SO_REUSEADDR: after the proxy is force-removed its port mapping can
    # leave TIME_WAIT sockets on 11880 (docker-proxy teardown on the CI
    # runners), which plain bind rejects for ~60s; a *live* listener still
    # refuses the bind. Retry bounded to be safe (tasks 0073/0074).
    deadline = time.time() + 30
    while True:
        hog = socket.socket()
        hog.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            hog.bind(("0.0.0.0", port))
            break
        except OSError as e:
            hog.close()
            if time.time() >= deadline:
                raise AssertionError(
                    f"could not occupy port {port} within 30s: {e}")
            time.sleep(1)
    hog.listen(16)

    def _serve() -> None:
        while True:
            try:
                conn, _ = hog.accept()
                conn.close()
            except OSError:
                return

    threading.Thread(target=_serve, daemon=True).start()
    context.hog = hog


@given("the archive repository is deleted")
def delete_archive(context):
    inv = provision.Inventory.load(context.sim)
    archive = next(r for r in inv.repos
                   if r.endswith("/common-law") and "-archive/" in r)
    owner, name = archive.split("/", 1)
    _platform_ready(context)
    client = provision.sim_platform_client(context.sim)
    last: Exception | None = None
    for _ in range(6):
        try:
            client.delete_repo(owner, name)
            return
        except provision.API_ERRORS as e:
            last = e
            time.sleep(5)
    raise AssertionError(f"deleting {archive} kept failing: {last}")


@given("the operator container is removed")
def remove_operator(context):
    containers.rm(f"polis-operator-{context.sim}")


@given("a run is started")
def start_run(context):
    context.last = _run(context, "sim", "new",
                        "--situation", "data/world/legal/norms/fisheries.yaml")
    assert context.last.returncode == 0, _out(context)[-300:]


@when("the port is freed")
def free_port(context):
    context.hog.close()


@when("I start the sim's containers")
def start_containers(context):
    provision.start(context.sim)


@when("I provision the sim again with --force")
def force_up(context):
    context.last = _run(context, "provision", "up", context.sim, "--force")


@when("I ask provision status")
def ask_status(context):
    context.last = _run(context, "provision", "status", context.sim)


@when("I drive the sim one step")
def drive_one(context):
    _platform_ready(context)
    context.last = _run(context, "sim", "drive", "--steps", "1")


@then("provision status is green")
def status_green(context):
    deadline = time.time() + 60
    while time.time() < deadline:
        if context.last.returncode == 0:
            return
        time.sleep(5)
        context.last = _run(context, "provision", "status", context.sim)
    assert False, _out(context)[-300:]


@then("provision status fails")
def status_fails(context):
    out = _out(context)
    assert context.last.returncode != 0, f"status unexpectedly succeeded: {out[-300:]}"
    assert "Traceback" not in out, out[-300:]


@then('provision status reports missing "{text}"')
def status_reports_missing(context, text):
    report = provision.status(context.sim)
    missing = [i["name"] for i in report["items"] if not i["exists"]]
    assert not report["ok"] or missing, \
        "status is green but the failure was expected"
    assert any(text in name for name in missing), \
        f"'{text}' not among the missing items: {missing}"


@then('the failure names "{text}"')
def failure_names(context, text):
    out = _out(context)
    assert context.last.returncode != 0, f"expected failure, got exit=0: {out[-300:]}"
    assert text in out, f"'{text}' not in: {out[-300:]}"
    assert "Traceback" not in out, out[-300:]


@then("the drive degrades to local execution")
def drive_degrades(context):
    out = _out(context)
    assert context.last.returncode == 0, out[-300:]
    assert "no operator container running" in out, f"warning missing: {out[-300:]}"


@then("a story was enacted")
def story_enacted(context):
    from polis.sim.director import load_stories
    stories = load_stories(context.sim)
    assert stories and stories[-1].status == "enacted", \
        (stories[-1].error if stories else "no stories") or "no stories"
