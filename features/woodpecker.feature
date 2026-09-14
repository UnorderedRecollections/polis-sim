@functional @slow @containers @gitea
Feature: The woodpecker command group
  The Mechanical Magistrate's CI surface. Needs the full transition (the
  CI is erected only then): uv run behave features/woodpecker.feature
  --tags @slow — deliberately not part of tests/bdd-phase2.sh.

  @gitea
  Scenario: the Magistrate answers once the CI is erected
    Given a provisioned sim seeded from "fisheries"
    When the federation codifies its machinery
    Then the Mechanical Magistrate's CI is erected
    When I run polis against the sim with "woodpecker whoami"
    Then the command succeeds
    And the output contains "mechanical-magistrate"
