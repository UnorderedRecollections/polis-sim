# The Three Stores — the project's ontology

Three stores, each sovereign over a different kind of truth:

| Store | Holds | In the fiction |
|---|---|---|
| git history | the legal corpus and its genealogy | the **legal archive** |
| `data/world/world.json` + `cities/*.json` | who exists: cities, people, offices, powers | the **civil registry** |
| `data/world/matters.json` | what is pending: petitions, bills, and the procedural record of what happened to them | the **political state** |

## No database — deliberately

A database of legal events would be a *competing source of truth* and break
the isomorphism: git history **is** the record of legal acts. The civil
registry and the matter store are small, single-writer, human-inspectable
JSON files; if concurrent mutation ever arrives (a simulation service), the
matter store goes behind an interface — see
`docs/todo/simulation-service-requirements.md`.

## Recording ≠ enforcing

**Recording an event is distinct from enforcing a procedure.** The archive
host (gogs) records refs and knows nothing of petitions, approvals or
constitutional checks. The constitution is enforced by people; jurisdiction
checks run in the archivists' *own tooling* (`polis bill ratify`), never in
the archive host. Nothing in gogs prevents a rogue push — exactly as nothing
in an archive building prevents a rogue clerk. That is the correct model of
a self-managed commons: the legitimacy of a merge comes from the
institution, not from the software.

## Matters and the procedural record

A matter (`PET-0007` / `ACT-0017`) has a status
(`submitted → deliberating → scrutinized → ratified | rejected | dismissed`)
and an **event list**: filed, heard, introduced, debated, scrutinized,
enacted… The event list *is* the procedural record (the "minutes of
proceedings"). Completed matters never touch the repository — the corpus
contains law, not process.

## The two clocks

- **git history = legal time** (when acts entered the corpus);
- **matter events = institutional time** (when proceedings advanced).

A future simulation service should correlate them for stepping/replay, but
never merge them.
