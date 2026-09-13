@phase1 @phase2 @gitea @slow
Feature: The codification of the machinery
  The federation lives by custom until the three acts codify the
  machinery; afterwards the platform itself carries the proceedings.
  This feature drives the whole arc: a phase I story, the explicit
  transition, and a phase II story through real issues, pull requests,
  scrutiny and the Mechanical Magistrate's checks.

  @gitea
  Scenario: the machinery is codified and a bill travels the codified procedure
    Given a provisioned sim seeded from "fisheries"
    When the federation codifies its machinery
    Then the federation operates in phase 2
    And the corpus contains "constitution/branch-protection.md"
    And the corpus contains ".woodpecker.yml"
    And the Mechanical Magistrate's CI is erected

    Given a petition of the fishers of cogswich about the northern banks
    Then the petition is a real issue on the platform
    When the legislator drafts "Northern Banks Codified Access Act" into municipal/cogswich
    Then the bill is a real pull request on the platform
    When the jurist approves the bill
    Then the Mechanical Magistrate approves the bill
    When the Keeper ratifies it with remedy "quota" superseding "N-0001"
    Then the bill's pull request is merged
    And the archive main contains "Northern Banks Codified Access Act"
    And norm "N-0001" is superseded in the situation
