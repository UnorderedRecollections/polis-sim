@functional
Feature: The assign command group
  Membership and authority: citizenship, office, and the separation of powers.

  Background:
    Given an isolated federation is generated

  Scenario: citizenship is assigned
    When I run polis with "person create --name 'Jurist Vale' --agency juridical --institution the-archive --username j.vale"
    Then the command succeeds
    When I run polis with "assign citizenship j.vale cogswich"
    Then the command succeeds
    And the output contains "now a citizen of cogswich"

  Scenario: an office is occupied, vacated and re-occupied
    When I run polis with "office create --id road-warden --title 'Warden of the Roads' --body 'civic works'"
    Then the command succeeds
    When I run polis with "person create --name 'Jurist Vale' --agency juridical --institution the-archive --username j.vale"
    Then the command succeeds
    When I run polis with "assign office j.vale road-warden"
    Then the command succeeds
    And the output contains "now holds"
    When I run polis with "person create --name 'Jurist Wren' --agency juridical --institution the-archive --username j.wren"
    Then the command succeeds
    When I run polis with "assign office j.wren road-warden"
    Then the command fails
    And the output contains "is occupied by"
    When I run polis with "office vacate road-warden"
    Then the command succeeds
    When I run polis with "assign office j.wren road-warden"
    Then the command succeeds

  Scenario: political agency may not occupy an office
    When I run polis with "person create --name 'Polly Tician' --city cogswich --agency political --role citizen-legislator --username p.tician"
    Then the command succeeds
    When I run polis with "office create --id road-warden --title 'Warden of the Roads' --body 'civic works'"
    Then the command succeeds
    When I run polis with "assign office p.tician road-warden"
    Then the command fails
    And the output contains "may not occupy an office"
    And the output does not contain "Traceback"

  Scenario: mechanical agents and mechanical offices are separated too
    When I run polis with "person create --name 'Agent X' --agency mechanical --institution the-archive --username a.x"
    Then the command succeeds
    When I run polis with "assign citizenship a.x cogswich"
    Then the command fails
    And the output contains "belongs to an institution"
    When I run polis with "person create --name 'Jurist Vale' --agency juridical --institution the-archive --username j.vale"
    Then the command succeeds
    When I run polis with "office create --id crier --title 'Crier' --body 'notices' --kind mechanical"
    Then the command succeeds
    When I run polis with "assign office j.vale crier"
    Then the command fails
    And the output contains "belongs to software"
