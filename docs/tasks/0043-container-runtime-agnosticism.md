# 0043: container-runtime agnosticism (podman or docker)

- **created:** 2026-09-11T16:00:00Z
- **type:** [refactoring]
- **depends-on:** none
- **status:** done

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

- **2026-09-13 — resumed and completed.** Scripts converted to the `rt`
  helpers (`proxy/postgres/gogs/gitea/woodpecker/smoke`; the woodpecker
  agent's flags from `rt_agent_flags`, the canonical-host alias from
  `rt_host_alias_flags`); `compose-up/down` prefer the detected runtime's
  provider; `docker-compose.yml` parameterized (`POLIS_CONTAINER_SOCKET`,
  `POLIS_AGENT_USER/SECURITY_OPT`) with `extra_hosts` on gitea/woodpecker;
  `tests/runtime-agnosticism.sh` (docker via a stub CLI, podman live)
  added first in `tests/all.sh`; docs swept (AGENTS.md, README, the user
  guide, testing.md, services, design). Verified: full `tests/all.sh`
  green on podman (10 run, 1 skip) and the stub-verified docker command
  construction. **Caveats:** no docker live test on this machine;
  woodpecker's docker backend has no per-step `extra_hosts`, so phase-2
  pipeline step containers on docker still need the canonical-host
  problem solved (recorded as a known gap for 0050).

## Completion

- **finished:** 2026-09-13T20:30:49Z
- **commit:** ab65e37 (Python boundary) + bc0374c (scripts, compose, checks,
  docs)
