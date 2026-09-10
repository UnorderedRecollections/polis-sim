Feature: The northern banks dispute
  The fishers of Brasshaven watch Cogswich boats empty the northern
  banks; a petition, a bill, and the Keeper's enactment bring a quota.

  Scenario: overfishing leads to a quota
    Given a provisioned sim seeded from "fisheries"
    And a petition of the fishers of brasshaven about the northern banks
    When the legislator drafts "Northern Banks Quota Act" into fisheries
    And the Keeper ratifies it with remedy "quota" superseding "N-0001"
    Then the archive main contains "Northern Banks Quota Act"
    And norm "N-0001" is superseded in the situation
    And the docket shows the petition is answered
