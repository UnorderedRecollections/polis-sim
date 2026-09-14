@domain
Feature: The legal domain model
  The seed ontology, the fifteen jurisdictions and their generated
  situations are the simulated legal system's foundations. These checks
  run without containers, on an isolated federation.

  Background:
    Given an isolated federation is generated

  Scenario: the legal seed validates as a whole
    When I run polis with "world legal validate"
    Then the command succeeds
    And the output contains "consistent"

  Scenario: every jurisdiction generates a valid situation
    Then every jurisdiction accepts a generated situation

  Scenario: jurisdictional data is inspectable
    When I run polis with "world jurisdictions show fisheries"
    Then the command succeeds
    And the output contains "fisheries"
    And the output contains "resource"

  Scenario: the municipal registry is populated at genesis
    When I run polis with "city list"
    Then the command succeeds
    And the output contains "Cogswich"
