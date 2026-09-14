"""Deployment/provisioning failure suite (task 0055).

Each case injects one local failure and asserts the behavior agreed in
`docs/design/failure-modes.md`: fail fast with a remedy (or degrade
deliberately), no bare traceback, state inspectable, recovery idempotent.
Deliberately non-exhaustive — it helps developers and technical users
debug a local deployment, not every exotic failure.

Run: uv run python tests/failures_test.py
"""
from __future__ import annotations

import json
import os
import shutil
import socket
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SIM = "fail-01"

_results: list[tuple[str, bool]] = []


def check(name: str, ok: bool, detail: str = "") -> bool:
    _results.append((name, bool(ok)))
    print(f"  {'ok  ' if ok else 'FAIL'} {name}" + (f" — {detail}" if detail and not ok else ""),
          flush=True)
    return bool(ok)


def tail(proc: subprocess.CompletedProcess) -> str:
    text = ((proc.stdout or "") + (proc.stderr or "")).strip().replace("\n", " ")
    return f"exit={proc.returncode}: {text[-220:]}"


def run_cli(*args: str) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env["POLIS_PROVISIONED_SIM"] = SIM
    return subprocess.run(["uv", "run", "polis", *args], cwd=ROOT, env=env,
                          capture_output=True, text=True)


def case_unknown_runtime() -> None:
    from polis.clients import containers
    try:
        containers.get_runtime("bogus")
        check("unknown container runtime fails with a clear message", False,
              "a bogus runtime was accepted")
    except containers.ContainerError as e:
        check("unknown container runtime fails with a clear message", "bogus" in str(e))


def case_missing_world(world_file: Path) -> None:
    from polis.clients import containers
    backup = world_file.with_name("world.json.failtest-backup")
    shutil.move(str(world_file), str(backup))
    try:
        proc = run_cli("provision", "up", SIM)
        text = proc.stdout + proc.stderr
        check("missing world fails fast with the remedy",
              proc.returncode != 0 and "no world yet" in text and "Traceback" not in text,
              tail(proc))
        left = [n for n in (f"{SIM}-proxy", f"{SIM}-gogs", f"{SIM}-postgres")
                if containers.container(n)]
        check("missing world leaves no containers behind", not left, str(left))
    finally:
        shutil.move(str(backup), str(world_file))


def case_platform_down() -> None:
    from polis import provision
    from polis.clients import containers
    containers.stop(f"{SIM}-gogs")
    proc = run_cli("provision", "status", SIM)
    text = proc.stdout + proc.stderr
    check("platform down: status fails naming the container",
          proc.returncode != 0 and f"{SIM}-gogs" in text, tail(proc))
    provision.start(SIM)
    proc = run_cli("provision", "status", SIM)
    check("platform down: start + status recovers", proc.returncode == 0, tail(proc))


def case_port_conflict() -> None:
    import threading

    from polis import provision
    from polis.clients import containers
    port = provision.load_secrets(SIM)["proxy_port"]
    containers.rm(f"{SIM}-proxy")
    hog = socket.socket()
    try:
        hog.bind(("0.0.0.0", port))
        hog.listen(16)
    except OSError as e:
        hog.close()
        check("taken proxy port: injection possible", False, str(e))
        return

    def _serve() -> None:
        while True:
            try:
                conn, _ = hog.accept()
                conn.close()
            except OSError:
                return

    threading.Thread(target=_serve, daemon=True).start()
    try:
        proc = run_cli("provision", "up", SIM, "--force")
        text = proc.stdout + proc.stderr
        check("taken proxy port fails naming the port",
              proc.returncode != 0 and str(port) in text and "already in use" in text,
              tail(proc))
    finally:
        hog.close()
    proc = run_cli("provision", "up", SIM, "--force")
    check("taken proxy port: freeing it recovers with re-up", proc.returncode == 0, tail(proc))


def case_partial_resources() -> None:
    from polis import provision
    inv = provision.Inventory.load(SIM)
    archive = next(r for r in inv.repos if r.endswith("/common-law") and "-archive/" in r)
    owner, name = archive.split("/", 1)
    provision.sim_platform_client(SIM).delete_repo(owner, name)
    proc = run_cli("provision", "status", SIM)
    text = proc.stdout + proc.stderr
    check("missing repo: status reports it and fails",
          proc.returncode != 0 and archive in text, tail(proc))
    proc = run_cli("provision", "up", SIM, "--force")
    check("missing repo: re-up reconciles", proc.returncode == 0, tail(proc))
    proc = run_cli("provision", "status", SIM)
    check("missing repo: status green after recovery", proc.returncode == 0, tail(proc))


def case_operator_degrade() -> None:
    from polis.clients import containers
    from polis.sim.director import load_stories
    containers.rm(f"polis-operator-{SIM}")
    proc = run_cli("sim", "new", "--situation", "data/world/legal/norms/fisheries.yaml")
    check("run created for the degrade case", proc.returncode == 0, tail(proc))
    proc = run_cli("sim", "drive", "--steps", "1")
    text = proc.stdout + proc.stderr
    check("missing operator: drive degrades to local with a warning",
          proc.returncode == 0 and "no operator container running" in text, tail(proc))
    stories = load_stories(SIM)
    check("missing operator: a story still enacted",
          bool(stories) and stories[-1].status == "enacted",
          (stories[-1].error if stories else "no stories") or "")
    proc = run_cli("provision", "up", SIM, "--force")
    check("missing operator: re-up restores the operator", proc.returncode == 0, tail(proc))


def _cleanup() -> None:
    from polis import provision
    try:
        provision.destroy(SIM)
    except Exception:
        pass
    shutil.rmtree(ROOT / "data/sims" / SIM, ignore_errors=True)


def main() -> int:
    from polis import config, store

    print(f"deployment failure suite (sim={SIM})", flush=True)
    world = store.load_world()
    if world.federation.phase != 1:
        world.federation.phase = 1
        store.save_world(world)

    case_unknown_runtime()
    case_missing_world(Path(config.WORLD_FILE))
    try:
        proc = run_cli("provision", "up", SIM)
        if check("baseline provisioning", proc.returncode == 0, tail(proc)):
            case_platform_down()
            case_port_conflict()
            case_partial_resources()
            case_operator_degrade()
    finally:
        _cleanup()

    failed = [name for name, ok in _results if not ok]
    print(f"\nsummary: {len(_results) - len(failed)}/{len(_results)} checks passed")
    for name in failed:
        print(f"  FAIL {name}")
    if failed:
        print("\nDEPLOYMENT FAILURE SUITE FAILED")
        return 1
    print("\nDEPLOYMENT FAILURE SUITE PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
