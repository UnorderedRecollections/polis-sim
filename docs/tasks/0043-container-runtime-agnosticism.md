# 0043: container-runtime agnosticism (podman or docker)

- **created:** 2026-09-11T16:00:00Z
- **type:** [refactoring]
- **depends-on:** none
- **status:** in-progress

## Description

Make the tooling indifferent to the container runtime. Today everything
assumes podman (`polis/clients/podman.py`, `scripts/infra/*`,
`provision.py`, the macOS-VM-specific woodpecker agent flags
`--user 0:0` / `--security-opt label=disable` / the VM-internal socket).

- A `ContainerRuntime` interface: run/exec/ps/images/volumes/networks,
  with `PodmanRuntime` and `DockerRuntime` behind it; auto-detect
  (`podman` first, then `docker`, then compose providers), overridable
  via `POLIS_RUNTIME`.
- Per-runtime quirks isolated: podman-machine socket path, SELinux
  label, root mapping (the woodpecker agent), volume pruning — none of
  it should leak into provisioning logic.
- The provisioning bring-ups (`_up_postgres`, `_up_gogs`, `_up_gitea`,
  `_up_woodpecker`, operator/city containers) go through the interface;
  `scripts/infra/*` and `docker-compose.yml` keep working on either.
- Enables the deployment work (task 0050): cloud hosts use docker.

## Progress log

- **2026-09-13 — Python side landed; parked for 0059.** Added
  `polis/clients/containers.py`: `ContainerRuntime` with
  `PodmanRuntime`/`DockerRuntime`, auto-detection (`podman` first, then
  `docker`) and `POLIS_RUNTIME`; runtime quirks isolated (image/network
  existence spellings, machine vs `docker info` state, socket path,
  the woodpecker agent's flags, and the canonical-host alias docker
  needs — auto-inserted on every `run`). All Python call sites moved;
  `clients/podman.py` deleted; `polis health runtime` (the old `podman`
  suite name kept as a hidden alias). `scripts/infra/env.sh` gained
  runtime detection and helpers (`rt`, `rt_container_exists/running`,
  `rt_network_exists`, `rt_host_alias_flags`, `rt_socket_path`,
  `rt_agent_flags`). Verified on podman: `polis health runtime`,
  `polis health podman`, fast behave green. **Remaining:** convert the
  scripts to the helpers, compose `extra_hosts` + parameterized agent
  socket/flags, the `tests/runtime-agnosticism.sh` stub check for the
  docker path, docs, full `tests/all.sh`. The docker path is untested
  live (no docker on this machine).

## Completion

<!-- filled in when the task is done:
- **finished:**
- **commit:**
-->
