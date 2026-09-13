# 0052: authentication for the apparatus (OAuth; JWT vs JWKS assessment)

- **created:** 2026-09-13T15:10:44Z
- **type:** [infrastructure]
- **depends-on:** 0042
- **status:** open

## Description

Add an authentication layer to the apparatus. Once 0042 lands, the proxy
is the only ingress, so access control belongs there (or immediately
behind it) — today every service is reachable by anyone on the host and
each has its own account system.

Questions to settle (the deliverable is a design, then implementation
tasks split from it):

- **identity provider**: the sim's gitea as OAuth2/OIDC provider (it
  already issues OAuth apps and can act as IdP), an external IdP, or a
  small local issuer? The dev rig and each sim need a story; the
  federation's "operator" identity should stay project-owned.
- **enforcement point**: proxy-level forward-auth (caddy + an
  oauth2-proxy-style component) vs per-service native OAuth (gitea,
  woodpecker, gogs has none) vs both; how unauthenticated requests to
  `/gitea`, `/ci`, `/gogs` are handled; machine clients (the operator
  CLI, CI steps, forge webhooks) need non-browser credentials that do
  not ride on a browser session.
- **session vs token**: cookies at the proxy vs propagating bearer
  tokens to backends; do backends trust proxy headers (private network
  only) or re-verify every call?
- **JWT vs JWKS** (the explicit check): do we need either? Likely
  verdict to document: services already mint their own sessions/tokens
  (gitea sessions, woodpecker API JWT); a proxy that owns opaque
  sessions needs neither. JWKS is only needed when an external OIDC
  provider's ID tokens must be verified locally (or if we mint our own
  JWTs for machine auth) — decide, and record why, rather than reaching
  for JWT by default.
- **secrets/topology**: client ids/secrets per sim in `secrets.json`;
  redirect URIs through the proxy (paths under the 0042 canonical
  host); rotation; dev-rig parity.
- **what stays open**: local reproducibility means auth must be
  optional/off by default for demos and CI runs, on by flag for
  "deployed" sims.

Deliverable: `docs/design/auth.md` (threat model, decision, provider,
JWT/JWKS verdict, config surface) plus implementation tasks split once
the design is approved.

## Completion

<!-- filled in when the task is done:
- **finished:**
- **commit:**
-->
