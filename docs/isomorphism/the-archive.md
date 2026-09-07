# The Archive — git as legal memory (§1, §2)

## The legal corpus (§1)

| Git | Legal analogy |
|---|---|
| Repository | Legal archive / body of law |
| File | Statute, constitutional provision, legal document |
| Directory | Legal domain / collection of statutes |
| Repository state | Law as it exists at a point in time |
| Commit | Formal archival act recording a change |
| Commit message | Justification of the legal act |
| Commit hash | Unique archival seal |
| Commit history | Genealogy of the law |
| HEAD | Currently recognized state |
| Tag | Named authoritative edition / legal milestone |

Central idea: the repository is not merely a collection of laws; it is a
**historical record of the evolution of the legal order**.

In the simulation: the corpus lives in `the-archive/common-law`. Its layout
encodes **jurisdiction by path**: `constitution/` (the Council), one directory
per legal domain (`taxation/ maritime/ criminal/ commerce/ civic/
succession/`), and `municipal/<city>/` for city law.

## Distributed political geography (§2)

| Git | Federation analogy |
|---|---|
| Clone | A city obtaining a complete copy of the legal archive |
| Remote | Another recognized archive/polity |
| Fetch | Inspecting another archive's developments |
| Push | Sending your archival changes to another archive |
| Pull | Bringing another archive's developments into yours |
| Fork | Establishing a new legal order from an existing one |
| Upstream | Recognized source/parent legal order |
| Downstream | Legal order derived from another |

The load-bearing distinction:

> **A city is not a branch.** A city possesses an archive; a branch is an
> alternative *line of development within an archive*.

This preserves the separation between **political geography** (who exists)
and **history/procedure** (how law develops).

In the simulation: each city container clones its city's repo (`origin`) and
recognizes the federal archive as `upstream`. `polis archive obtain` performs
exactly these two archival acts (clone + recognize upstream).
