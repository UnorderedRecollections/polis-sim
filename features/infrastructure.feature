@infrastructure
Feature: The container runtime boundary
  The apparatus runs on podman or docker; the runtime boundary owns the
  detection and the runtime-specific quirks. These checks need no
  containers of their own.

  Scenario: a container runtime is available and named
    Then the container runtime is podman or docker

  Scenario: an unknown runtime is rejected with the choices
    Then the container runtime "bogus" is rejected with the choices

  Scenario: the runtime declares its canonical-host handling
    Then the runtime declares its canonical-host handling
