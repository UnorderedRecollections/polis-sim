@functional
Feature: The docket command group
  Petitions in the matter store (phase 1): filing, inspection, isomorphism.

  Background:
    Given an isolated federation is generated

  Scenario: the docket is empty at genesis
    When I run polis with "docket list"
    Then the command succeeds
    And the output does not contain "PET-"
    When I run polis with "docket show PET-0001"
    Then the command fails
    And the output contains "no such matter"

  Scenario: a petition is filed and inspected
    When I run polis with "docket file --as m.grimsbane --city cogswich --title 'Docks Act' --body 'Repair the docks' --repo-dir {data_dir}"
    Then the command succeeds
    And the output contains "petition filed: PET-0001"
    When I run polis with "docket list"
    Then the command succeeds
    And the output contains "PET-0001"
    When I run polis with "docket show PET-0001"
    Then the command succeeds
    And the output contains "Docks Act"
    And the output contains "m.grimsbane"

  Scenario: a petition is commented and dismissed
    When I run polis with "docket file --as m.grimsbane --city cogswich --title 'Docks Act' --repo-dir {data_dir}"
    Then the command succeeds
    When I run polis with "docket comment PET-0001 --body 'Supporting note' --as m.grimsbane --city cogswich --repo-dir {data_dir}"
    Then the command succeeds
    When I run polis with "docket dismiss PET-0001 --as m.grimsbane --city cogswich --repo-dir {data_dir}"
    Then the command succeeds
    And the output contains "dismissed"
    When I run polis with "docket list --state closed"
    Then the command succeeds
    And the output contains "PET-0001"

  Scenario: the isomorphism renders without recording a petition
    When I run polis with "docket file --isomorphism --as m.grimsbane --city cogswich --title 'Docks Act' --repo-dir {data_dir}"
    Then the command succeeds
    And the output contains "isomorphism"
    And the output contains "matters.json"
    When I run polis with "docket list"
    Then the command succeeds
    And the output does not contain "PET-"

  Scenario: a legislative operation without a city fails clearly
    When I run polis with "docket file --as m.grimsbane --title 'No City' --repo-dir {data_dir}"
    Then the command fails
    And the output contains "--city is required"
    And the output does not contain "Traceback"
