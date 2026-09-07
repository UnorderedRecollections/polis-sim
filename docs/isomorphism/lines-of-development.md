# Lines of Development — branches and the life of legal history

## Branch — an alternative legal history (§3)

An independently developing trajectory from a shared legal past. Two branches
can explore different answers to the same legal question without either
becoming authoritative. Bills in the simulation are branches (`bill/<slug>`);
`polis bill draft` opens one.

## Merge — reconciliation of legal histories (§4)

Combining two legitimate trajectories into a new state. A **merge conflict**
is a conflict of laws: git identifies textual incompatibility; humans decide
which substantive law is preferable.

## Squash — codification (§11)

Consolidating a messy legislative process (draft → amendment → correction →
review changes → …) into a single coherent legal act: *The Consolidated
Reform Act*. `polis bill consolidate`.

## Revert — repeal (§12)

A new legal act that reverses the effect of an earlier act. The original act
**remains in the historical record**: "this happened, and subsequently the
law was changed to undo its effect." `polis archive repeal` (repealing an
enactment recorded as a merge takes `--mainline 1`).

In the simulation, repeal exists twice by design: the Keeper's exceptional
correction (`archive repeal`, a bare revert) and repeal-as-bill
(`bill draft --kind repeal`, a repeal document through the ordinary
legislative flow).

## Rebase — reconstruction of legal lineage (§13)

Replaying a sequence of legal developments on top of a different historical
foundation. The changes may be substantively similar, but their ancestry is
rewritten. Merge *preserves and reconciles* divergent histories; rebase
*rewrites* one to appear descended from a different foundation.
`polis archive reconstruct`.

## Cherry-pick — legal transplant (§14)

One particular act imported into another line of development without its
surrounding history: City B wants one reform from City A but not the rest of
City A's development. `polis archive transplant`.

## Force push — replacement of recognized history (§15)

Normal push: "here are additional historical acts." Force push: "**replace
the history you recognize with this alternative lineage.**" An exceptional
archival power — constitutional reconstruction — not inherently illegitimate,
but guarded. `polis archive replace-history` requires `--yes` and the
`branch:manage` office power.

## Enactment is one archival act (project convention)

Ratification merges with `--no-commit`, flips the document's `status:` to
`enacted`, and commits a **single merge** — so a later repeal
(`revert -m 1`) undoes the enactment whole. The lifecycle statuses
(`draft → proposed → enacted`) are written **only by the machinery**, never
by hand.
