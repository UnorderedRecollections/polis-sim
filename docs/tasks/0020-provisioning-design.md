# 0020: Provisioning — design draft

- **created:** 2026-09-09T11:15:00Z
- **type:** [infrastructure]
- **depends-on:** 0019
- **status:** in-progress

## Description

Draft what `polis provision` entails: a high-level command that provisions
gogs (later gitea) with everything the sim needs — repos, accounts, city
containers — above the existing porcelain commands (`polis gogs users …`).

Key requirement: a **human-readable simulation instance id** namespacing
*all* resources (container names, gogs orgs/repos/usernames) so every
resource of one sim instance is identifiable — and cleanly removable.

Deliverable: `docs/design/provisioning.md` — functionality breakdown and
infra dependencies.

## Completion

<!-- filled in when the task is done:
- **finished:**
- **commit:**
-->
