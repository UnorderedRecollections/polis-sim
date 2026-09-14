@functional
Feature: The city command group
  The cities: founding, listing and inspection.

  Background:
    Given an isolated federation is generated

  Scenario: the nine cities are listed
    When I run polis with "city list"
    Then the command succeeds
    And the output contains "cogswich"
    And the output contains "Cogswich"

  Scenario: a city is founded and refuses duplication
    When I run polis with "city create --name Testholm"
    Then the command succeeds
    And the output contains "city founded"
    When I run polis with "city list"
    Then the command succeeds
    And the output contains "testholm"
    When I run polis with "city create --name Testholm"
    Then the command fails
    And the output contains "already exists"
    And the output does not contain "Traceback"

  Scenario: a city is inspectable
    When I run polis with "city show cogswich"
    Then the command succeeds
    And the output contains "Cogswich (id=cogswich)"
    And the output contains "Citizens"
    When I run polis with "city show nope"
    Then the command fails
    And the output contains "city not found"

  Scenario: a city without a derivable id is refused
    When I run polis with "city create --name '!!!'"
    Then the command fails
    And the output contains "could not derive a city id"
