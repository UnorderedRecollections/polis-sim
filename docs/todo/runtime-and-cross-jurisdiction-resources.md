# TODO: Runtime-created and cross-jurisdiction resources

Surfaced by the question "what if the new jurisdiction defines new
resources?" after task 0014. The new-jurisdiction checklist covers
design-time resources; two cases remain.

## 1. Runtime-created resources

Law can create resources (an enclosure act creates a parcel; a charter
creates a market). Resources are situation objects, so the snapshot
principle already covers their *storage* — but validation does not:

- `norms.validate_norm_set()` checks `object.kind` only against
  design-time resource files (with the jurisdiction index as fallback).
- Needed: a validation-context parameter — run-time validation checks
  against **design files ∪ situation's runtime-added instances**.
- The resource registry itself should likewise be loadable from a situation
  document, not only from `data/world/legal/resources/`.

## 2. Cross-jurisdiction object references

Norms and holdings are per-jurisdiction documents; `object.kind` validates
only within the same jurisdiction. But legal facts cross borders:
river-water's `minimum_flow` constrains what fisheries' `river_mouth`
depends on.

Options:
- **qualified object kinds** — `object: {kind: river-water/irrigation_cuts,
  type: resource}` (preferred: makes the dependency explicit and enables
  cross-jurisdiction friction in event synthesis);
- or `shared: true` in resource files.

Also relates to the river-water `direction:` field (watercourse topology is
inherently cross-object).

## When to address

When the director/executor lands: runtime resource creation matters as soon
as enactments write back to the situation, and cross-jurisdiction
references matter as soon as stories span jurisdictions (river/fisheries is
the canonical candidate).
