"""Thin wrapper around the podman CLI for container/network introspection."""
from __future__ import annotations

import json
import subprocess


class PodmanError(RuntimeError):
    pass


def _run(args: list[str], check: bool = True) -> subprocess.CompletedProcess:
    try:
        proc = subprocess.run(
            ["podman", *args], capture_output=True, text=True, timeout=20
        )
    except FileNotFoundError as e:
        raise PodmanError("podman CLI not found on PATH") from e
    except subprocess.TimeoutExpired as e:
        raise PodmanError(f"podman {' '.join(args)} timed out") from e
    if check and proc.returncode != 0:
        raise PodmanError(f"podman {' '.join(args)} failed: {proc.stderr.strip()[:300]}")
    return proc


def containers(all_: bool = True) -> list[dict]:
    args = ["ps", "--format", "json"]
    if all_:
        args.insert(1, "-a")
    out = _run(args).stdout.strip()
    return json.loads(out) if out else []


def container(name: str) -> dict | None:
    for c in containers():
        names = c.get("Names") or ([c["Name"]] if c.get("Name") else [])
        if name in names:
            return c
    return None


def container_running(name: str) -> bool:
    c = container(name)
    return bool(c and c.get("State") == "running")


def network_exists(name: str) -> bool:
    proc = _run(["network", "exists", name], check=False)
    return proc.returncode == 0


def machine_state() -> str:
    out = _run(["machine", "inspect", "--format", "{{.State}}"], check=False)
    return out.stdout.strip() or "unknown"


def exec_ok(container_name: str, args: list[str]) -> tuple[bool, str]:
    proc = _run(["exec", container_name, *args], check=False)
    return proc.returncode == 0, (proc.stdout + proc.stderr).strip()
