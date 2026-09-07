# Families of Legal Documents

For the simulation, we should **not model legal documents as arbitrary prose files**.
We want enough structure that the Git history can represent a recognizable legal process, while still being readable by non-technical people.
A useful starting point is to distinguish **legal acts**, **petitions**, and **procedural records**.
For this purpose we need a templating system to reuse standard legal documents.

## 1. Three families of documents

### A. Normative documents — things that become law

These are the things that ultimately enter the authoritative legal corpus:

* Constitution
* statute / act
* amendment
* regulation
* treaty
* ordinance
* repeal
* emergency measure

A statute could have a structure like:

```text
ACT OF THE FEDERATION
Act No. 17/42

Title: An Act Concerning Inter-City Trade

Preamble

Article 1 — Purpose

Article 2 — Definitions

Article 3 — Rights and Obligations

Article 4 — Administration

Article 5 — Enforcement

Article 6 — Relation to Existing Law

Article 7 — Entry into Force

Article 8 — Final Provisions
```

The important part for the simulation is that **the document itself doesn't say that it is law merely because somebody committed it**, but has an explicit **lifecycle**:

```text
draft
  ↓
petition / proposal
  ↓
review
  ↓
approval
  ↓
enactment
  ↓
authoritative corpus
```

That's analogous to the distinction between a commit existing and a commit being accepted into the authoritative branch.



# 2. Petitions are different

A petition is fundamentally a **request for institutional action**, rather than a piece of law.
Every petition a standard header:

```yaml
type: petition
petition_id: PET-0042

petitioner:
  name: "Mara of City B"
  city: "City B"

submitted: 1842-03-17

jurisdiction: federal

subject: "Inter-city grain trade"

request:
  type: legislation
  target: "common-law/trade"

status: submitted
```

followed by human-readable prose:

```text
# Petition Concerning Inter-City Grain Trade

## To

The Federal Council of the Confederation

## Petition

We, the undersigned citizens of City B, petition the
Council to establish a common rule governing...

## Grounds

...

## Proposed Action

We request that the Council consider the attached
Act Concerning Inter-City Grain Trade.

## Signatories

...
```

This gives a useful distinction between
    **Petition = "Please do something."**
and
    **Proposed Act = "Here is the thing we propose you do."**


# 3. A proposed law should probably be its own document

**Proposed law** should not be placed directly into the petition.

Instead they should be split both from the 'domain' perspective and from an implementation perspective:

```text
petitions/
    PET-0042.md

proposals/
    ACT-0017.md
```

The petition references the proposal:

```yaml
petition_id: PET-0042

request:
  type: legislation
  proposal: ACT-0017
```

And the proposal contains:

```yaml
type: act
id: ACT-0017
title: "Inter-City Grain Trade Act"

origin:
  city: "City B"
  petition: PET-0042

jurisdiction: federal

status: proposed
```

This becomes extremely useful later because you can demonstrate **references between legal objects**.

# 4. Amendments should be first-class objects

An **amendment** is particularly interesting in Git because it maps naturally onto a change to an existing text:

```yaml
type: amendment
id: AMD-0081

target:
  act: ACT-0017
  article: 4
  paragraph: 2

proposer:
  city: City D
  person: "Lucius"

status: proposed
```

Then:

```text
## Proposed Amendment

Replace Article 4 §2 with:

> Grain transported between member cities shall...
```

Git provides the *mechanical* representation of the textual change, while the document provides the **legal meaning of the change**.
That's an important distinction to preserve.


# 5. There is also a need for procedural documents

These are neither law nor petitions. They record **what happened to a legal proposal**.

For example:

```text
procedures/
    PR-0042/
        submission.md
        jurisdiction.md
        reviews.md
        decision.md
```

Or, more simply, one document:

```yaml
type: procedural_record
id: PROC-0042

matter: ACT-0017

events:

  - date: 1842-03-18
    event: submitted
    actor: "Mara"

  - date: 1842-03-19
    event: jurisdiction_assigned
    jurisdiction: federal_trade
    actor: "Archivist Bob"

  - date: 1842-03-21
    event: constitutional_review
    result: approved
    actor: "Jurist Helena"

  - date: 1842-03-22
    event: enacted
    actor: "Federal Archivist"
```

This is where the analogy to **court/session records** becomes particularly powerful.
A normal merge commit is the Git-level history while the **procedural record** explains **what that merge meant institutionally**.


# 6. We need to separate metadata from the legal text

This is probably the most important design decision.
Use a format like Markdown with YAML front matter:

```markdown

type: act
id: ACT-0017
title: Inter-City Grain Trade Act

jurisdiction: federal
origin_city: City B

status: enacted

introduced_by:
  name: Mara
  city: City B

effective_date: 1842-04-01


# Inter-City Grain Trade Act

## Preamble

...

## Article 1 — Definitions

...

## Article 2 — Duties

...

## Article 3 — Enforcement

...

## Article 4 — Entry into Force

...
```

Following from this are two basic priciples on which the design rests:
- the **metadata is machine-readable**.
- the **body is human-readable law**.

The bonus is that it gives your CI system something to work with, for example, the Mechanical Magistrate can check:
```text
Does every Act have an ID?
Does it specify a jurisdiction?
Does it have an effective date?
Does it identify its proposer?
Does it contain an Entry into Force provision?
Does it reference existing legislation correctly?
Does the cited legislation actually exist?
Does it conflict with constitutional provisions?
```

That's much more interesting than simply running `pytest` on some arbitrary text.

# 7. The need to establish a legal directory structure

Something like:

```text
law/
│
├── constitution/
│   ├── constitution.md
│   └── amendments/
│
├── statutes/
│   ├── trade/
│   ├── taxation/
│   ├── citizenship/
│   └── infrastructure/
│
├── treaties/
│
├── regulations/
│
└── repealed/
```

Then separate the **procedural material**:

```text
petitions/
proposals/
amendments/
proceedings/
```

So the repository becomes conceptually:

```text
                    REPOSITORY
                         │
       ┌─────────────────┴─────────────────┐
       │                                   │
   LEGAL CORPUS                       LEGAL PROCESS
       │                                   │
 constitution                         petitions
 statutes                             proposals
 treaties                             amendments
 regulations                          proceedings
```

This is a useful distinction because **Git history records the evolution of the corpus**, while the process documents explain *why* and *under what authority* it changed.

# 8. What templates are needed in the first iteraton ?

Start small, with perhaps **six templates**:

### `petition.md`

```text
PETITION
ID:
PETITIONER:
CITY:
JURISDICTION:
SUBJECT:
REQUEST:

GROUNDS:

PROPOSED ACTION:

ATTACHMENTS:
```

### `act.md`

```text
ACT
ID:
TITLE:
JURISDICTION:
PROPONENT:
ORIGINATING PETITION:

PREAMBLE

ARTICLE 1 — ...

ARTICLE 2 — ...

ENFORCEMENT

RELATION TO EXISTING LAW

ENTRY INTO FORCE

FINAL PROVISIONS
```

### `amendment.md`

```text
AMENDMENT
ID:
TARGET:
PROPONENT:

PROVISION TO BE CHANGED:

CURRENT TEXT:

PROPOSED TEXT:

RATIONALE:
```

### `treaty.md`

```text
TREATY
ID:
PARTIES:
SUBJECT:

PREAMBLE

ARTICLE 1 — ...

ARTICLE 2 — ...

OBLIGATIONS

DISPUTE RESOLUTION

TERMINATION

ENTRY INTO FORCE
```

### `repeal.md`

```text
REPEAL
ID:
TARGET LAW:

PROVISION REPEALED:

EFFECTIVE DATE:

TRANSITIONAL PROVISIONS:
```

### `procedural-record.md`

```text
PROCEDURAL RECORD
MATTER:
JURISDICTION:

SUBMITTED:
ASSIGNED:
REVIEWS:
DECISION:
ENACTMENT:

ACTORS:
```

## 9. And there's a very nice Git mapping here

Once these templates exist, the simulation can make the Git vocabulary almost self-explanatory:

| Legal process                          | Git operation         |
| -- |  |
| Drafting a proposal                    | Working tree          |
| Save a draft                           | Commit                |
| Submit proposal                        | Push                  |
| Create legislative proceeding          | Pull Request          |
| Request another jurisdiction's opinion | Review                |
| Amend proposal                         | New commit            |
| Incorporate another proposal           | Cherry-pick           |
| Combine divergent legal histories      | Merge                 |
| Rewrite the draft's history            | Rebase                |
| Consolidate drafting history           | Squash                |
| Undo enacted provision                 | Revert                |
| Publish authoritative corpus           | Merge to `main` + tag |
| Historical edition of law              | Git tag               |
| Copy the federation's law to a city    | Clone                 |
| City-specific legal corpus             | Branch                |
| Automated constitutional review        | CI                    |
| Required constitutional approval       | Branch protection     |
| Assigned legal authority               | CODEOWNERS            |

And this suggests an important principle for the simulation:

> **Don't make the legal documents imitate Git. Make them look like plausible legal documents, and let the actual Git operations underneath them produce the isomorphism.**

That way, when a non-technical participant sees:

```text
PET-0042
   ↓
ACT-0017
   ↓
PR #17
   ↓
3 reviews
   ↓
Constitutional test ✓
   ↓
Federal Archivist
   ↓
merge
   ↓
ACT-0017 becomes part of common law
```

they aren't being asked to understand an artificially constructed metaphor. **They can see the same institutional process expressed simultaneously in legal language and in Git mechanics.**


## Final notes:

All these domain objects should be first-class objects in the python implementation.

There should be specific sub-commands to inspect petition , create petition, log procedural_record etc.

### Procedural Records language:

| What your simulation does                    | Legal term(s)                                            | Meaning                                                    |
| -------------------------------------------- | -------------------------------------------------------- | ---------------------------------------------------------- |
| Put a document into the official case record | **file** / **filing**                                    | Formally submit a document to an authority                 |
| Add an event/document to the official record | **enter into the record**                                | Make something part of the authoritative procedural record |
| Record a procedural event                    | **make an entry on the record**                          | Create a formal record of what happened                    |
| Record proceedings chronologically           | **docket** / **docketing**                               | Enter matters/events into an official register             |
| Maintain the official record                 | **keep/maintain the record**                             | Custodial function                                         |
| Record what happened during a proceeding     | **minutes** / **minutes of proceedings**                 | Formal account of proceedings                              |
| Make an official determination               | **enter an order**                                       | Formally record a decision/order                           |
| Add supporting material                      | **file an exhibit** / **enter an exhibit into evidence** | Put evidentiary material into the record                   |
| Refer to something already recorded          | **cite the record** / **refer to the record**            | Invoke existing procedural material                        |
| Correct the record                           | **correct/amend the record**                             | Alter an erroneous procedural entry                        |
| Seal material                                | **seal the record**                                      | Restrict access to part of the record                      |
| Publish the result                           | **promulgate / publish / gazette**                       | Give an official public form to an act                     |


**Thoughts on terminology:**

"Filing" is probably your best verb for commits.
"Docketing" is particularly interesting. (NB: this is already implemented)
Petitioners file petitions.
Legislators introduce acts.
Committees consider them.
Jurists review them.
The proceedings are docketed.
Orders and decisions are entered into the record.
The Archivist maintains the record.
The enacted law is promulgated.

