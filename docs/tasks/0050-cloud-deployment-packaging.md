# 0050: packaging for cloud deployment (GCP, AWS, …)

- **created:** 2026-09-11T16:00:00Z
- **type:** [infrastructure]
- **depends-on:** 0042, 0043, 0047, 0048
- **status:** open

## Description

Package the apparatus so a simulation runs on a cloud host, not just a
developer's machine:

- registry builds (GHCR) for all images; non-root; platform-neutral
  (the macOS-only woodpecker agent hacks disappear with the runner from
  task 0048 or a docker-based agent);
- secrets from environment/secret managers — no `.env` file assumption;
- per-sim stack as manifests: docker-compose (via task 0043) and/or
  kubernetes (one namespace per sim — the naming scheme maps naturally:
  `<sim>-postgres`, `<sim>-forge`, `<sim>-ci`, the operator);
- the proxy (task 0042) as the single ingress for a sim — one stable
  endpoint, TLS termination there;
- a Terraform/Pulumi sketch: network + one sim instance + the proxy,
  teardown mirrors `provision destroy` (including volumes/registry
  cleanup);
- the three stores stay filesystem-based (the isomorphism forbids a
  DB of legal events) — volume/backup strategy documented (snapshot the
  sim dir).

Deliverable: `docs/design/deployment.md` + the manifests/example.

## Completion

<!-- filled in when the task is done:
- **finished:**
- **commit:**
-->
