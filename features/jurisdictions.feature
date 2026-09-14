# The cross-jurisdiction suite (task 0068; ported from
# tests/jurisdictions_test.py, task 0054). Slow: one shared sim, one whole
# director story per jurisdiction. behave.ini hides @slow, so run it as:
#   uv run behave features/ --tags "@domain and @slow"          # seed 41
#   uv run behave features/ --tags "@domain and @slow" -D seed=7
@domain @containers @slow @shared-sim
Feature: One whole story per jurisdiction
  For each of the fifteen jurisdictions a situation is generated from the
  jurisdiction's own data and one whole story is driven to enactment on a
  shared sim. The scenario outline reports per-jurisdiction pass/fail;
  the seed is fixed (-D seed=..., default 41) so failures reproduce.

  Background:
    Given the cross-jurisdiction sim is provisioned

  Scenario Outline: <jurisdiction> enacts a whole story
    Given a run is seeded with a generated "<jurisdiction>" situation
    When the director drives one story
    Then the story was enacted with a ratification

    Examples:
      | jurisdiction         |
      | citizenship          |
      | contract             |
      | criminal             |
      | currency-weights     |
      | environment-resource |
      | fisheries            |
      | foreign-relations    |
      | harbor-navigation    |
      | inheritance          |
      | land-commons         |
      | military-defense     |
      | river-water          |
      | roads-carriage       |
      | taxation             |
      | trade-markets        |
