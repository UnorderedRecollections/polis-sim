@functional
Feature: The world command group
  Genesis, inspection and the legal seed: the civil registry's surface.

  Background:
    Given an isolated federation is generated

  Scenario: genesis refuses to overwrite and --force recovers
    When I run polis with "world genesis"
    Then the command fails
    And the output contains "already exists"
    And the output does not contain "Traceback"
    When I run polis with "world genesis --force"
    Then the command succeeds
    And the output contains "world created"

  Scenario: an impossible genesis is refused
    When I run polis with "world genesis --force --cities 0"
    Then the command fails
    And the output contains "cities must be 1..24"

  Scenario: the federation is inspectable
    When I run polis with "world show"
    Then the command succeeds
    And the output contains "Concord of the Nine Cities"
    And the output contains "phase 1"

  Scenario: the legal seed validates and jurisdictions are inspectable
    When I run polis with "world legal validate"
    Then the command succeeds
    And the output contains "consistent"
    When I run polis with "world jurisdictions list"
    Then the command succeeds
    And the output contains "fisheries"
    When I run polis with "world jurisdictions show fisheries"
    Then the command succeeds
    And the output contains "Fisheries"
    And the output contains "northern_banks"

  Scenario: an unknown jurisdiction is a clear failure
    When I run polis with "world jurisdictions show bogus"
    Then the command fails
    And the output contains "unknown jurisdiction"
    And the output does not contain "Traceback"

  Scenario: the ontology is inspectable
    When I run polis with "world actors list"
    Then the command succeeds
    And the output contains "city"
    When I run polis with "world paradigms list"
    Then the command succeeds
    And the output contains "resource"
    When I run polis with "world relations list"
    Then the command succeeds
    And the output contains "authorizes"
    When I run polis with "world moves list"
    Then the command succeeds
    And the output contains "file_petition"
    When I run polis with "world legal-objects list"
    Then the command succeeds
    And the output contains "constitution"

  Scenario: seed norms and resources are inspectable
    When I run polis with "world norms list --jurisdiction fisheries"
    Then the command succeeds
    And the output contains "N-0001"
    And the output contains "in_force"
    When I run polis with "world resources list --jurisdiction fisheries"
    Then the command succeeds
    And the output contains "eastern_shoals"

  Scenario: charged events are available for a jurisdiction
    When I run polis with "world events candidates --jurisdiction fisheries"
    Then the command succeeds
    And the output contains "N-0001"
    And the output contains "northern_b"

  Scenario: a situation is generated and refuses to overwrite
    When I run polis with "world situation new fisheries --out {data_dir}/sit.yaml"
    Then the command succeeds
    And the output contains "situation written"
    When I run polis with "world situation new fisheries --out {data_dir}/sit.yaml"
    Then the command fails
    And the output contains "exists"
    When I run polis with "world situation new fisheries --out {data_dir}/sit.yaml --force"
    Then the command succeeds
