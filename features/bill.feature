@functional
Feature: The bill command group
  Bills in phase 1: drafting plans, inspection and clean refusal.

  Background:
    Given an isolated federation is generated

  Scenario: the bill docket is empty at genesis
    When I run polis with "bill list"
    Then the command succeeds
    And the output does not contain "ACT-"

  Scenario: drafting renders a plan without opening a line
    When I run polis with "bill draft --isomorphism --as m.grimsbane --city cogswich --title 'Docks Act' --kind act --into taxation --repo-dir {data_dir}"
    Then the command succeeds
    And the output contains "isomorphism"
    And the output contains "git"
    When I run polis with "bill list"
    Then the command succeeds
    And the output does not contain "ACT-"

  Scenario: amending nothing is refused with a remedy
    When I run polis with "bill amend bill/none --justification 'because' --as m.grimsbane --city cogswich --repo-dir {data_dir}"
    Then the command fails
    And the output contains "nothing to record"
    And the output does not contain "Traceback"
