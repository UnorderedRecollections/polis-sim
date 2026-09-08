"""Extensibility — auditing jurisdictions against the new-jurisdiction
checklist (docs/design/extensibility-api.md §1).

The audit composes the existing validators; it is also the core of the
future `propose_jurisdiction` MCP tool (same checks, run on a candidate
before it is installed).
"""
from __future__ import annotations

from dataclasses import dataclass

from .events import validate_signatures
from .legaldata import load_jurisdictions, load_paradigms
from .norms import load_seed_norms, validate_norm_set
from .resources import load_resources, validate_resources


@dataclass(frozen=True)
class AuditStep:
    step: str
    ok: bool
    detail: str = ""


def audit_jurisdiction(slug: str) -> list[AuditStep]:
    """Run the new-jurisdiction checklist for `slug`; one AuditStep per step."""
    steps: list[AuditStep] = []
    jurisdictions = load_jurisdictions()
    j = jurisdictions.get(slug)

    # 1 — declared
    if j is None:
        return [AuditStep("declared", False, f"no jurisdictions/{slug}.yaml")]
    steps.append(AuditStep("declared", True, slug))

    # 2 — cast
    steps.append(AuditStep("cast defined", bool(j.actors),
                           ", ".join(j.actors) or "no actors"))

    # 3 — grammar
    grammar_ok = bool(j.resource_properties and j.rule_forms and j.disputes)
    steps.append(AuditStep("grammar defined", grammar_ok,
                           f"{len(j.resource_properties)} properties, "
                           f"{len(j.rule_forms)} rule forms, {len(j.disputes)} disputes"))

    # 4 — signatures (impact admitted by paradigm)
    sig_problems = [p for p in validate_signatures() if p.startswith(f"{slug}:")]
    steps.append(AuditStep("activity signatures", not sig_problems,
                           "; ".join(sig_problems) or f"{len(j.activities)} activities"))

    # 5 — incompatibilities (rule_form existence is enforced at load time)
    steps.append(AuditStep("incompatibilities", bool(j.incompatibilities),
                           f"{len(j.incompatibilities)} declared"))

    # 6 — resources (resource-paradigm only)
    if "resource" in j.paradigms:
        res_problems = [p for p in validate_resources() if p.startswith(f"{slug}:")]
        n_files = len(load_resources().get(slug, {}))
        steps.append(AuditStep("resources grounded", not res_problems,
                               "; ".join(res_problems) or f"{n_files} resource files"))
    else:
        steps.append(AuditStep("resources grounded", True, "not a resource paradigm"))

    # 7 — norm seed
    seeds = load_seed_norms()
    ns = seeds.get(slug)
    if ns is None or not ns.norms:
        steps.append(AuditStep("norm seed", False, "no norms seeded"))
    else:
        norm_problems = validate_norm_set(ns, slug)
        steps.append(AuditStep("norm seed", not norm_problems,
                               "; ".join(norm_problems) or f"{len(ns.norms)} norms"))

    # 8 — holdings
    if ns is None or not ns.holdings:
        steps.append(AuditStep("holdings", False, "no holdings seeded"))
    else:
        steps.append(AuditStep("holdings", True, f"{len(ns.holdings)} holdings"))

    # 9 — seed consistency (no active strict conflicts)
    if ns is not None:
        conflicts = ns.conflicts(j.incompatibilities)
        steps.append(AuditStep("seed consistency", not conflicts,
                               "; ".join(f"{a.id} ⊥ {b.id}" for a, b in conflicts)
                               or "no active strict conflicts"))

    # 10 — corpus backing (informational)
    steps.append(AuditStep("corpus backing", True,
                           j.corpus_dir or "no corpus dir (municipal/customary only)"))
    return steps


def audit_all() -> dict[str, list[AuditStep]]:
    return {slug: audit_jurisdiction(slug) for slug in load_jurisdictions()}
