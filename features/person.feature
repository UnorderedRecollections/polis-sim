@functional
Feature: The person command group
  Persons: the founding roster, creation rules and the agency split.

  Background:
    Given an isolated federation is generated

  Scenario: the founding persons are listed and inspectable
    When I run polis with "person list"
    Then the command succeeds
    And the output contains "m.grimsbane"
    When I run polis with "person show m.grimsbane"
    Then the command succeeds
    And the output contains "political"

  Scenario: a political citizen is created
    When I run polis with "person create --name 'Testa Morrow' --city cogswich --agency political --role citizen-legislator --username t.morrow"
    Then the command succeeds
    And the output contains "person created"
    When I run polis with "person show t.morrow"
    Then the command succeeds
    And the output contains "citizen-legislator"

  Scenario: a mechanical agent belongs to an institution
    When I run polis with "person create --name 'Agent X' --agency mechanical --institution the-archive --username a.x"
    Then the command succeeds
    And the output contains "mechanical"

  Scenario: invalid persons are refused with remedies
    When I run polis with "person create --name 'No City' --agency political --role citizen-legislator --username n.city"
    Then the command fails
    And the output contains "--city is required"
    When I run polis with "person create --name 'No Role' --city cogswich --agency political --username n.role"
    Then the command fails
    And the output contains "needs at least one --role"
    When I run polis with "person create --name 'Bad Role' --city cogswich --agency political --role bogus --username b.role"
    Then the command fails
    And the output contains "unknown political role"
    When I run polis with "person create --name 'Bad Agency' --city cogswich --agency bogus --username b.agency"
    Then the command fails
    And the output contains "unknown agency"
