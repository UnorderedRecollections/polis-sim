@functional @slow @containers @gitea
Feature: The gitea command group
  The phase-2 platform's administrative surface, against a gitea-backed
  sim (run with: uv run behave features/gitea.feature --tags @slow).

  @gitea
  Scenario: the sim's gitea answers as the operator
    Given a provisioned sim seeded from "fisheries"
    When I run polis against the sim with "gitea status"
    Then the command succeeds
    And the output contains "orgs:"
    When I run polis against the sim with "gitea users list --query operator"
    Then the command succeeds
    And the output contains "operator"
    When I run polis against the sim with "gitea orgs list"
    Then the command succeeds
    And the output contains "-archive"
