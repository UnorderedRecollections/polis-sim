"""The container runtime boundary — podman or docker (task 0043).

Everything the tooling needs from the container engine goes through here:
a `ContainerRuntime` with `PodmanRuntime`/`DockerRuntime` behind it,
auto-detected (`podman` first, then `docker`) and overridable with
`POLIS_RUNTIME`. Runtime-specific spellings and quirks live in the
implementations; provisioning, the CLI and the scripts stay neutral:

- image existence (`podman image exists` vs `docker image inspect`);
- network existence (`network exists` vs `network inspect`);
- daemon/machine state (podman machine vs `docker info`);
- the woodpecker agent's socket mount and flags (podman-machine needs
  `--user 0:0` + `--security-opt label=disable` + the VM-internal
  rootless socket; docker mounts `/var/run/docker.sock`).

Everything else (`run`, `exec`, `rm`, `stop`, `start`, `ps`, `build`,
`network create/rm`, `volume prune`) has identical spellings and stays on
the thin `_run()` passthrough.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess


class ContainerError(RuntimeError):
    pass


class ContainerRuntime:
    """One container engine. Subclasses fill the runtime-specific parts."""

    name = "container"
    binary = "container"

    # --- the thin passthrough ------------------------------------------------

    def _run(self, args: list[str], check: bool = True,
             timeout: int = 20) -> subprocess.CompletedProcess:
        if args and args[0] == "run":
            # every container gets the runtime's canonical-host alias (podman
            # provides host.containers.internal natively; docker needs it)
            args = [args[0], *self.host_alias_args(), *args[1:]]
        try:
            proc = subprocess.run(
                [self.binary, *args], capture_output=True, text=True, timeout=timeout
            )
        except FileNotFoundError as e:
            raise ContainerError(f"{self.binary} CLI not found on PATH") from e
        except subprocess.TimeoutExpired as e:
            raise ContainerError(f"{self.binary} {' '.join(args)} timed out") from e
        if check and proc.returncode != 0:
            raise ContainerError(
                f"{self.binary} {' '.join(args)} failed: {proc.stderr.strip()[:300]}")
        return proc

    # --- containers -----------------------------------------------------------

    def list_containers(self, all_: bool = True) -> list[dict]:
        args = ["ps", "--format", "json"]
        if all_:
            args.insert(1, "-a")
        out = self._run(args).stdout.strip()
        return json.loads(out) if out else []

    def by_name(self) -> dict[str, dict]:
        """All containers keyed by every name they answer to."""
        out: dict[str, dict] = {}
        for c in self.list_containers():
            names = c.get("Names")
            if isinstance(names, str):
                names = [names]
            if not names:
                names = [c["Name"]] if c.get("Name") else []
            for n in names:
                out[n] = c
        return out

    def container(self, name: str) -> dict | None:
        return self.by_name().get(name)

    def container_running(self, name: str) -> bool:
        c = self.container(name)
        return bool(c and c.get("State") == "running")

    def container_names(self) -> list[str]:
        proc = self._run(["ps", "-a", "--format", "{{.Names}}"], check=False)
        return proc.stdout.split()

    def rm(self, name: str) -> None:
        self._run(["rm", "-f", name], check=False)

    def stop(self, name: str) -> None:
        self._run(["stop", name], check=False)

    def start(self, name: str) -> None:
        self._run(["start", name], check=False)

    def exec_ok(self, name: str, args: list[str]) -> tuple[bool, str]:
        proc = self._run(["exec", name, *args], check=False)
        return proc.returncode == 0, (proc.stdout + proc.stderr).strip()

    def passthrough(self, args: list[str]) -> int:
        """Run a container command with inherited stdio (interactive exec)."""
        try:
            return subprocess.run([self.binary, *args]).returncode
        except FileNotFoundError as e:
            raise ContainerError(f"{self.binary} CLI not found on PATH") from e

    # --- images ---------------------------------------------------------------

    def image_exists(self, image: str) -> bool:
        raise NotImplementedError

    def build(self, image: str, dockerfile, context) -> None:
        self._run(["build", "-t", image, "-f", str(dockerfile), str(context)],
                  timeout=600)

    # --- networks ---------------------------------------------------------------

    def network_exists(self, name: str) -> bool:
        raise NotImplementedError

    def network_create(self, name: str) -> None:
        self._run(["network", "create", name], check=False)

    def network_rm(self, name: str) -> None:
        self._run(["network", "rm", name], check=False)

    # --- volumes ----------------------------------------------------------------

    def volume_prune(self) -> None:
        self._run(["volume", "prune", "-f"], check=False)

    # --- runtime state and quirks -----------------------------------------------

    def runtime_state(self) -> str:
        """'running' when the engine is usable, else a short state."""
        raise NotImplementedError

    def host_alias_args(self) -> list[str]:
        """Flags making host.containers.internal resolve from inside
        containers (the canonical base of every deployment)."""
        return []

    def socket_path(self) -> str:
        """The host path of the engine socket (overridable via
        POLIS_CONTAINER_SOCKET)."""
        raise NotImplementedError

    def agent_run_args(self, container_socket: str = "/var/run/docker.sock") -> list[str]:
        """Extra `run` flags the woodpecker agent needs on this runtime."""
        raise NotImplementedError


class PodmanRuntime(ContainerRuntime):
    name = "podman"
    binary = "podman"

    def image_exists(self, image: str) -> bool:
        return self._run(["image", "exists", image], check=False).returncode == 0

    def network_exists(self, name: str) -> bool:
        return self._run(["network", "exists", name], check=False).returncode == 0

    def runtime_state(self) -> str:
        out = self._run(["machine", "inspect", "--format", "{{.State}}"], check=False)
        return out.stdout.strip() or "unknown"

    def socket_path(self) -> str:
        return (os.environ.get("POLIS_CONTAINER_SOCKET")
                or f"/run/user/{os.getuid()}/podman/podman.sock")

    def agent_run_args(self, container_socket: str = "/var/run/docker.sock") -> list[str]:
        # podman-machine on macOS: container root maps to the VM's core user
        # (the socket owner) and CoreOS SELinux would deny the mount without
        # label=disable; the socket is the VM-internal rootless one.
        return [
            "--user", "0:0",
            "--security-opt", "label=disable",
            "-v", f"{self.socket_path()}:{container_socket}",
            "-e", f"DOCKER_HOST=unix://{container_socket}",
        ]


class DockerRuntime(ContainerRuntime):
    name = "docker"
    binary = "docker"

    def host_alias_args(self) -> list[str]:
        # podman resolves host.containers.internal natively; docker only
        # knows host.docker.internal on Desktop and nothing on Engine
        return ["--add-host", "host.containers.internal:host-gateway"]

    def image_exists(self, image: str) -> bool:
        return self._run(["image", "inspect", image], check=False).returncode == 0

    def network_exists(self, name: str) -> bool:
        return self._run(["network", "inspect", name], check=False).returncode == 0

    def runtime_state(self) -> str:
        return ("running" if self._run(["info"], check=False).returncode == 0
                else "not running")

    def socket_path(self) -> str:
        return os.environ.get("POLIS_CONTAINER_SOCKET") or "/var/run/docker.sock"

    def agent_run_args(self, container_socket: str = "/var/run/docker.sock") -> list[str]:
        return [
            "-v", f"{self.socket_path()}:{container_socket}",
            "-e", f"DOCKER_HOST=unix://{container_socket}",
        ]


RUNTIMES: dict[str, type[ContainerRuntime]] = {
    "podman": PodmanRuntime,
    "docker": DockerRuntime,
}

_runtime: ContainerRuntime | None = None


def get_runtime(preferred: str | None = None) -> ContainerRuntime:
    """The runtime in use: explicit argument > POLIS_RUNTIME > auto-detect
    (podman first, then docker)."""
    global _runtime
    want = preferred or os.environ.get("POLIS_RUNTIME")
    if want:
        if want not in RUNTIMES:
            raise ContainerError(
                f"unknown container runtime '{want}' — POLIS_RUNTIME is podman|docker")
        return RUNTIMES[want]()
    if _runtime is not None:
        return _runtime
    for name in ("podman", "docker"):
        if shutil.which(name):
            _runtime = RUNTIMES[name]()
            return _runtime
    raise ContainerError(
        "no container runtime found — install podman or docker, or set POLIS_RUNTIME")


def runtime_name() -> str:
    return get_runtime().name


# --- module-level convenience (the call sites' vocabulary) ----------------------

def _run(args: list[str], check: bool = True,
         timeout: int = 20) -> subprocess.CompletedProcess:
    return get_runtime()._run(args, check=check, timeout=timeout)


def list_containers(all_: bool = True) -> list[dict]:
    return get_runtime().list_containers(all_)


def container(name: str) -> dict | None:
    return get_runtime().container(name)


def container_running(name: str) -> bool:
    return get_runtime().container_running(name)


def container_names() -> list[str]:
    return get_runtime().container_names()


def rm(name: str) -> None:
    get_runtime().rm(name)


def stop(name: str) -> None:
    get_runtime().stop(name)


def start(name: str) -> None:
    get_runtime().start(name)


def exec_ok(name: str, args: list[str]) -> tuple[bool, str]:
    return get_runtime().exec_ok(name, args)


def passthrough(args: list[str]) -> int:
    return get_runtime().passthrough(args)


def image_exists(image: str) -> bool:
    return get_runtime().image_exists(image)


def build(image: str, dockerfile, context) -> None:
    get_runtime().build(image, dockerfile, context)


def network_exists(name: str) -> bool:
    return get_runtime().network_exists(name)


def volume_prune() -> None:
    get_runtime().volume_prune()


def runtime_state() -> str:
    return get_runtime().runtime_state()


def socket_path() -> str:
    return get_runtime().socket_path()


def agent_run_args(container_socket: str = "/var/run/docker.sock") -> list[str]:
    return get_runtime().agent_run_args(container_socket)


# pre-0043 name, kept for callers that still import it
PodmanError = ContainerError
