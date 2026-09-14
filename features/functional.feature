@functional
Feature: The polis command surface
  A container-free smoke of the application's command groups, on an
  isolated federation. The per-subcommand suites extend this domain
  (task 0069).

  Background:
    Given an isolated federation is generated

  Scenario: the command groups are listed
    When I run polis with "--help"
    Then the command succeeds
    And the output contains "world"
    And the output contains "docket"
    And the output contains "bill"
    And the output contains "archive"
    And the output contains "sim"
    And the output contains "provision"

  Scenario: the generated world is inspectable
    When I run polis with "city list"
    Then the command succeeds
    And the output contains "Cogswich"
