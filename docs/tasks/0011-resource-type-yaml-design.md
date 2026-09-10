# 0011: Resource-type YAML files — design document first

- **created:** 2026-09-08T18:51:00Z
- **type:** [simulation]
- **depends-on:** 0007, 0009
- **status:** done

## Description

We need one YAML file per **resource type** per jurisdiction (the concrete
resources stories revolve around — `northern_banks`, `western_commons`, …).
Before writing fifteen-plus files, produce a design document defining:

- the resource schema (identity, jurisdiction, properties with values,
  current norms/holdings referencing it, narrative metadata for
  realization);
- where resource files live (`data/world/legal/resources/`? per-jurisdiction
  subdirs?) and how they relate to the `resources:` lists already in the
  jurisdiction YAMLs (move? link? generate?);
- how resources participate in situation seeds, event candidates and
  dispute generation.

Deliverable: `docs/design/resource-files.md`; the YAML files themselves
become follow-up tasks once the schema is agreed.

## Completion

- **finished:** 2026-09-10T21:48:57Z
- **commit:** a2733f4
