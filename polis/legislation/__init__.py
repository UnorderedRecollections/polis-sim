"""The legislative machinery: docket, bill and archive operations.

Every operation builds a Plan — a list of machinery steps (git commands,
platform API calls) annotated with their legal meaning. Every CLI command
exposes --isomorphism, which renders the plan instead of executing it.

CONVENTION: all subsequent command families must build Plans and expose
--isomorphism, so the legal act <-> machinery mapping is always inspectable.
"""
