@infrastructure @containers @slow @shared-sim
Feature: Local deployment failures
  The agreed behaviors (docs/design/failure-modes.md): fail fast with a
  remedy, no bare traceback, inspectable state, idempotent recovery.
  One shared sim serves all scenarios; each restores what it broke.

  Scenario: the baseline provisions and status is green
    Given the shared sim is provisioned
    When I ask provision status
    Then provision status is green

  Scenario: a stopped platform is reported and recovers
    Given the gogs platform is stopped
    When I ask provision status
    Then provision status fails
    And provision status reports missing "gogs"
    When I start the sim's containers
    And I ask provision status
    Then provision status is green

  Scenario: a taken proxy port is refused and recovers
    Given the proxy is stopped
    And the proxy port is occupied by another process
    When I provision the sim again with --force
    Then the failure names "already in use"
    When the port is freed
    And I provision the sim again with --force
    Then the command succeeds

  Scenario: a deleted repository is reported and re-created
    Given the archive repository is deleted
    When I ask provision status
    Then provision status fails
    And provision status reports missing "archive/common-law"
    When I provision the sim again with --force
    And I ask provision status
    Then provision status is green

  Scenario: a missing operator degrades the drive and is restored
    Given the operator container is removed
    And a run is started
    When I drive the sim one step
    Then the drive degrades to local execution
    And a story was enacted
    When I provision the sim again with --force
    Then the command succeeds
