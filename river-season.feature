Feature: The river mouth season

  Scenario: spawning season brings a closure
    Given a provisioned sim seeded from "fisheries"
    And a petition of the fishers of vapourmouth about the river mouth
    When the legislator drafts "River Mouth Fishing Season Act" into fisheries
    And the Keeper ratifies it with remedy "seasonal_closure" superseding "N-0002"
    Then the archive main contains "River Mouth Fishing Season Act"
    And norm "N-0002" is superseded in the situation
