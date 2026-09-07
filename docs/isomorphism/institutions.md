# Institutions — the platform as constitutional apparatus

Git provides the machinery of distributed legal history. **The platform
provides a particular constitutional/administrative regime for governing that
machinery** (§18): identity, hosting, petitions, reviews, permissions,
jurisdictional mechanisms, automated checks.

## Issues — the docket (§16)

An issue is a recognized problem, request or dispute entering the
institutional docket — it proposes no remedy. "Article 17 is contradictory."
In the simulation: `polis docket file/list/show/comment/dismiss`.

## Pull requests — legislative petitions (§5)

A PR is a formal petition asking that a proposed line of legal development be
incorporated into the authoritative corpus: proposed changes, their history,
author, discussion, reviews, checks, authorization. The distinction that
matters: **issue = "there is a problem"; PR = "here is a proposed legal
change addressing it."** In the simulation: `polis bill
draft/amend/introduce/debate/…`.

## Review — deliberative institutions (§6)

Code review is institutional scrutiny of proposed legislation; required
reviewers are veto/ratification points. Approvals should represent genuinely
different institutional authorities (originating city + jurisdictional
expert + constitutional review), not "two people click approve." Phase 1
records findings by custom (`polis bill scrutinize` enters them into the
matter's record); phase 2 uses platform reviews.

## CODEOWNERS — jurisdiction (§7)

A machine-readable allocation of legal jurisdiction: who possesses authority
to review changes to particular parts of the corpus. In the simulation,
jurisdiction also lives in **offices and powers** (`merge:municipal/<city>/**`,
`review:taxation/**`), checked in the archivists' own tooling at ratification
— never by the archive host.

## Branch protection — constitutional entrenchment (§8)

Rules restricting how authoritative law may change: no direct alteration,
required reviews, required checks, certain history cannot be rewritten.
Phase-2 machinery.

## CI — automatic constitutional machinery (§9)

CI checks mechanically enforceable rules; humans decide substantive law.

> **CI = automatic formal legality. Review = human institutional judgment.**

The Mechanical Magistrate is the federation's CI office (dormant in phase 1,
erected in phase 2). Its checklist (from the document-families notes, §6):
every act has an ID, jurisdiction, effective date, proposer; an Entry into
Force provision; references to existing legislation resolve; no conflict with
constitutional provisions.

## Merge — formal incorporation (§10)

After petition, scrutiny, jurisdictional approval and checks, the merge is
**enactment**: incorporation into the authoritative history. In the
simulation this is jurisdiction-checked `polis bill ratify` — a local
archivist may enact only within `municipal/<city>/**`; cross-city law
requires the Keeper of the Federal Rolls.
