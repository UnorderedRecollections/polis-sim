@functional @slow @containers
Feature: The gogs command group
  The phase-1 platform's administrative surface, against the sim's own
  gogs (run with: uv run behave features/gogs.feature --tags @slow).

  Scenario: the sim's gogs answers as the operator
    Given a provisioned sim seeded from "fisheries"
    When I run polis against the sim with "gogs whoami"
    Then the command succeeds
    And the output contains "operator"
    When I run polis against the sim with "gogs orgs list"
    Then the command succeeds
    And the output contains "-archive"
    And the output contains "Federal Archive"
