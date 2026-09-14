@functional
Feature: The office command group
  Offices: the authorities that grant powers, their inspection and lifecycle.

  Background:
    Given an isolated federation is generated

  Scenario: offices are listed and inspectable
    When I run polis with "office list"
    Then the command succeeds
    And the output contains "federal-archivist"
    When I run polis with "office show federal-archivist"
    Then the command succeeds
    And the output contains "Keeper of the Federal Rolls"
    And the output contains "merge:main"
    And the output contains "occupant: e.vexley"

  Scenario: an office is established and refuses duplication
    When I run polis with "office create --id road-warden --title 'Warden of the Roads' --body 'civic works' --kind juridical --scope federation"
    Then the command succeeds
    And the output contains "office established"
    When I run polis with "office create --id road-warden --title 'Warden Again' --body 'x'"
    Then the command fails
    And the output contains "already exists"
    And the output does not contain "Traceback"

  Scenario: a vacant office is inspectable and cannot be vacated again
    When I run polis with "office create --id road-warden --title 'Warden of the Roads' --body 'civic works'"
    Then the command succeeds
    When I run polis with "office show road-warden"
    Then the output contains "vacant"
    When I run polis with "office vacate road-warden"
    Then the command fails
    And the output contains "already vacant"
