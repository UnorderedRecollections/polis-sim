@functional
Feature: The provision command group
  Provisioning's contracts that fail fast before any container work.

  Scenario: provisioning without a world fails fast
    Given an isolated federation directory without a world
    When I run polis with "provision up no-world-01"
    Then the command fails
    And the output contains "no world yet"
    And the output does not contain "Traceback"

  Scenario: an unknown platform is refused
    Given an isolated federation is generated
    When I run polis with "provision up unknown-platform-01 --platform bogus"
    Then the command fails
    And the output contains "unknown platform"

  Scenario: destructive provisioning commands need --yes
    Given an isolated federation is generated
    When I run polis with "provision destroy some-sim"
    Then the command fails
    And the output contains "--yes"
    When I run polis with "provision teardown some-sim"
    Then the command fails
    And the output contains "--yes"

  Scenario: unknown sims are clear failures
    Given an isolated federation is generated
    When I run polis with "provision status no-such-sim"
    Then the command fails
    And the output contains "no provisioned sim"
    And the output does not contain "Traceback"
