@functional
Feature: The health command group
  Subsystem checks: the host surface stays clean without a rig.

  Scenario: the hosts check runs
    When I run polis with "health hosts"
    Then the command succeeds
    And the output contains "hosts"

  @slow @containers
  Scenario: a provisioned sim passes its health checks
    Given a provisioned sim seeded from "fisheries"
    When I run polis against the sim with "health"
    Then the command succeeds
    And the output contains "sim context"
