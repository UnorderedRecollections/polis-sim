@functional
Feature: The archive command group
  The Keeper's machinery: plans render and the guards hold.

  Background:
    Given an isolated federation is generated

  Scenario: obtaining the archive renders a plan
    When I run polis with "archive obtain --isomorphism --as m.grimsbane --city cogswich --repo-dir {data_dir}"
    Then the command succeeds
    And the output contains "isomorphism"
    And the output contains "git clone"

  Scenario: promulgating renders a plan
    When I run polis with "archive promulgate --isomorphism --as m.grimsbane --city cogswich --name 'Docks Act' --message 'merges the act' --repo-dir {data_dir}"
    Then the command succeeds
    And the output contains "isomorphism"
    And the output contains "Docks Act"

  Scenario: replacing the recognized history needs --yes, but rendering is free
    When I run polis with "archive replace-history --as m.grimsbane --city cogswich --repo-dir {data_dir}"
    Then the command fails
    And the output contains "requires --yes"
    And the output does not contain "Traceback"
    When I run polis with "archive replace-history --isomorphism --as m.grimsbane --city cogswich --repo-dir {data_dir}"
    Then the command succeeds
    And the output contains "isomorphism"
