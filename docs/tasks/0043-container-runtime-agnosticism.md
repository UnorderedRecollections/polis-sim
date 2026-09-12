# 0043: container-runtime agnosticism (podman or docker)

- **created:** 2026-09-11T16:00:00Z
- **type:** [refactoring]
- **depends-on:** none
- **status:** open

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

## Completion

<!-- filled in when the task is done:
- **finished:**
- **commit:**
-->
