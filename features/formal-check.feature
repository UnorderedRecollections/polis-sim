@functional
Feature: The Mechanical Magistrate's formal checks
  The four mechanical checks run against a corpus clone — the same
  tooling the CI pipeline invokes.

  Background:
    Given a throwaway corpus with a changed act

  Scenario: a well-formed act passes all four checks
    When I run polis with "formal-check identify --repo-dir {repo_dir}"
    Then the command succeeds
    And the output contains "formal check passed"
    When I run polis with "formal-check entry-force --repo-dir {repo_dir}"
    Then the command succeeds
    And the output contains "Entry into Force"
    When I run polis with "formal-check references --repo-dir {repo_dir}"
    Then the command succeeds
    And the output contains "all citations resolve"
    When I run polis with "formal-check constitution --repo-dir {repo_dir}"
    Then the command succeeds
    And the output contains "no constitutional change"

  Scenario: an act without front matter fails identification
    Given the changed act loses its front matter
    When I run polis with "formal-check identify --repo-dir {repo_dir}"
    Then the command fails
    And the output contains "no front matter"

  Scenario: an act without an Entry into Force provision fails
    Given the changed act drops the Entry into Force provision
    When I run polis with "formal-check entry-force --repo-dir {repo_dir}"
    Then the command fails
    And the output contains "no Entry into Force provision"

  Scenario: an unresolvable citation fails
    Given the changed act cites a missing document
    When I run polis with "formal-check references --repo-dir {repo_dir}"
    Then the command fails
    And the output contains "is not in the corpus"

  Scenario: a constitutional change without an approval fails
    Given the changed act touches the constitution
    When I run polis with "formal-check constitution --repo-dir {repo_dir}"
    Then the command fails
    And the output contains "no gitea context"
