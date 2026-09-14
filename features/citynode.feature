@functional @slow @containers
Feature: The citynode command group
  City containers: listed for a sim, not built yet (run with:
  uv run behave features/citynode.feature --tags @slow).

  Scenario: city containers are listed as not created
    Given a provisioned sim seeded from "fisheries"
    When I run polis against the sim with "citynode list"
    Then the command succeeds
    And the output contains "cogswich"
    And the output contains "not created"

  Scenario: a city node status names the missing container
    Given a provisioned sim seeded from "fisheries"
    When I run polis against the sim with "citynode status cogswich"
    Then the command fails
    And the output contains "not created"
    And the output does not contain "Traceback"
