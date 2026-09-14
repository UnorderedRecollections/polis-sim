@functional
Feature: The sim command group
  Runs and the journal: start, inspect, and clean failures.

  Background:
    Given an isolated federation is generated

  Scenario: a run is started and inspected
    When I run polis with "world situation new fisheries --out {data_dir}/sit.yaml"
    Then the command succeeds
    When I run polis with "sim new run-01 --situation {data_dir}/sit.yaml"
    Then the command succeeds
    And the output contains "run started"
    When I run polis with "sim list"
    Then the command succeeds
    And the output contains "run-01"
    When I run polis with "sim runtime run-01"
    Then the command succeeds
    And the output contains "journal entries"
    And the output contains "norms in force"

  Scenario: an empty run reports its emptiness clearly
    When I run polis with "sim new bare-01"
    Then the command succeeds
    When I run polis with "sim present bare-01"
    Then the command succeeds
    And the output contains "has no journal entries yet"
    When I run polis with "sim epochs bare-01"
    Then the command succeeds
    And the output contains "no saved epochs"
    When I run polis with "sim stories bare-01"
    Then the command succeeds
    And the output contains "no stories"
    When I run polis with "sim scenarios bare-01"
    Then the command succeeds
    And the output contains "no scenarios queued"

  Scenario: unknown runs and bad scopes are clear failures
    When I run polis with "sim present no-such"
    Then the command fails
    And the output contains "no such run"
    And the output does not contain "Traceback"
    When I run polis with "sim steps --scope bogus"
    Then the command fails
    And the output contains "must be 'user' or 'test'"
    When I run polis with "sim steps --scope user"
    Then the command succeeds
    And the output contains "scenario steps"
