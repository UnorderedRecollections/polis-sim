# A phase-II scenario: requires a gitea-hosted sim AFTER the machinery has
# been codified (host-side `polis sim transition`, which also erects the
# CI; the service will do both in task 0061). The petition is a real issue,
# the bill a cross-repo PR, the jurist's finding a review, and the
# Mechanical Magistrate's verdict a CI commit-status.
Feature: A bill under the codified procedure

  Scenario: a municipal grievance travels the codified procedure
    Given a petition of the fishers of cogswich about the northern banks
    When the legislator drafts "Codified Banks Access Act" into municipal/cogswich
    And the jurist approves the bill
    And the Mechanical Magistrate approves the bill
    And the Keeper ratifies it with remedy "quota" superseding "N-0001"
    Then the bill's pull request is merged
    And the archive main contains "Codified Banks Access Act"
    And the docket shows the petition is answered
