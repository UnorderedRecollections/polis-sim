# A phase-I scenario (gogs or gitea sim, before the codification).
#
# The fishers grieve an overfished bank; the legislator drafts a quota act
# and the Keeper enacts it. Submit to a running sim:
#
#   uv run polis sim submit scenarios/northern-banks-quota.feature
#   uv run polis sim drive --steps 3
Feature: The northern banks quota

  Scenario: overfishing leads to a quota
    Given a petition of the fishers of brasshaven about the northern banks
    When the legislator drafts "Northern Banks Quota Act" into fisheries
    And the Keeper ratifies it with remedy "quota" superseding "N-0001"
    Then the archive main contains "Northern Banks Quota Act"
    And norm "N-0001" is superseded in the situation
    And the docket shows the petition is answered
