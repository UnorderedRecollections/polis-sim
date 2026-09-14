"""Container-runtime steps (task 0066) — the infrastructure domain.

In-process and container-free: they check the runtime boundary is
available, auto-detects correctly and owns its runtime quirks.
"""
from __future__ import annotations

from behave import then

from polis.clients import containers


@then("the container runtime is podman or docker")
def runtime_named(context):
    runtime = containers.get_runtime()
    assert runtime.name in ("podman", "docker"), runtime.name


@then('the container runtime "{name}" is rejected with the choices')
def runtime_rejected(context, name):
    try:
        containers.get_runtime(name)
    except containers.ContainerError as e:
        assert "podman" in str(e) and "docker" in str(e), str(e)
        return
    raise AssertionError(f"runtime '{name}' was accepted")


@then("the runtime declares its canonical-host handling")
def canonical_host(context):
    runtime = containers.get_runtime()
    args = runtime.host_alias_args()
    if runtime.name == "docker":
        # docker needs the alias injected on every run
        assert "--add-host" in args and any("host.containers.internal" in a for a in args), args
    else:
        # podman resolves host.containers.internal natively
        assert args == [], args

    from polis import provision
    assert provision.CANONICAL_HOST == "host.containers.internal"
