"""Situation generation — scaffold a valid situation.yaml (task 0035).

Hand-authoring situations is the last unwieldy step: this composes one
from the jurisdiction's own data — one norm per resource (rule_forms
cycled for coverage, aspects from the incompatibility table), holdings
from activities × actors × a seeded sample of cities. Output passes
`validate_norm_set` and carries no active strict conflicts by
construction (one norm per resource).
"""
from __future__ import annotations

import random
from typing import Optional

from .legaldata import load_jurisdictions
from .norms import Holder, Holding, Norm, NormObject, NormSet
from .. import store


class SituationError(RuntimeError):
    pass


def _aspect_for(jdata, rule_form: str) -> str:
    for rule in jdata.incompatibilities:
        if rule_form in rule.between and rule.over:
            return rule.over
    return "access_right"


def generate_situation(jurisdiction: str, seed: Optional[int] = None,
                       cities_per_holding: int = 2) -> NormSet:
    from .legaldata import load_paradigms
    jdata = load_jurisdictions().get(jurisdiction)
    if jdata is None:
        raise SituationError(f"unknown jurisdiction '{jurisdiction}'")
    world = store.load_world()
    city_ids = [c.id for c in world.cities]
    if not city_ids:
        raise SituationError("no world yet — run `polis world genesis` first")
    rng = random.Random(seed)
    verbs = [sig for sig in jdata.activities if sig.verb]
    forms = list(jdata.rule_forms)
    offset = rng.randrange(len(forms)) if forms else 0

    paradigms = load_paradigms()
    admitted = {t for p in jdata.paradigms for t in paradigms[p].holding_object_types} \
        if jdata.paradigms else {"resource"}
    if "resource" in admitted:
        return _resource_situation(jdata, verbs, forms, offset, rng,
                                   city_ids, cities_per_holding, jurisdiction, seed)
    return _conduct_situation(jdata, verbs, forms, offset, rng, admitted,
                              city_ids, cities_per_holding, jurisdiction, seed)


def _resource_situation(jdata, verbs, forms, offset, rng, city_ids,
                        cities_per_holding, jurisdiction, seed) -> NormSet:
    all_actors = sorted({a for sig in verbs for a in sig.actors}
                        or set(jdata.actors))
    # norms regulate the resource USERS (depletes/enriches activities), not
    # overseers — if every actor were a subject, all harm would be
    # "allocated by law" and the situation would hold no friction
    users = sorted({a for sig in verbs if sig.impact in ("depletes", "enriches")
                    for a in sig.actors})
    subjects = users or all_actors

    norms: list[Norm] = []
    for i, resource in enumerate(jdata.resources):
        form = forms[(i + offset) % len(forms)] if forms else "custom"
        norms.append(Norm(
            id=f"N-{i + 1:04d}", rule_form=form,
            object=NormObject(kind=resource, type="resource"),
            aspect=_aspect_for(jdata, form),
            subjects=subjects, beneficiaries=subjects,
            source="custom"))

    holdings: list[Holding] = []
    hid = 0
    for resource, norm in zip(jdata.resources, norms):
        for sig in verbs:
            under = norm
            for n in norms:
                if n.object.kind == resource and sig.affects and n.aspect in sig.affects:
                    under = n
                    break
            for actor_kind in sig.actors:
                for city in rng.sample(city_ids,
                                       min(cities_per_holding, len(city_ids))):
                    hid += 1
                    holdings.append(Holding(
                        id=f"H-{hid:04d}",
                        holder=Holder(city=city, actor_kind=actor_kind),
                        object=NormObject(kind=resource, type="resource"),
                        activity=sig.verb, under=under.id))
    return NormSet(norms=norms, holdings=holdings,
                   description=f"generated for {jurisdiction} (seed={seed})")


def _conduct_situation(jdata, verbs, forms, offset, rng, admitted, city_ids,
                       cities_per_holding, jurisdiction, seed) -> NormSet:
    """Non-resource paradigms (conduct-status, political-burden): norms
    govern CONDUCT (one per activity, object kind = the regulated verb —
    the pattern of the existing seeds), holdings attach to the
    jurisdiction's institutions with an admitted type."""
    conduct_type = "conduct" if "conduct" in admitted else sorted(admitted)[0]
    holding_type = next((t for t in ("relationship", "flow", "status", "right")
                         if t in admitted), sorted(admitted)[0])

    norms: list[Norm] = []
    for i, sig in enumerate(verbs):
        form = forms[(i + offset) % len(forms)] if forms else "custom"
        aspect = _aspect_for(jdata, form)
        if aspect == "access_right" and sig.affects:   # fallback misfit for conduct
            aspect = sig.affects[0]
        norms.append(Norm(
            id=f"N-{i + 1:04d}", rule_form=form,
            object=NormObject(kind=sig.verb, type=conduct_type),
            aspect=aspect,
            subjects=list(sig.actors), beneficiaries=list(sig.actors),
            source="custom"))

    holdings: list[Holding] = []
    hid = 0
    for i, sig in enumerate(verbs):
        under = norms[i % len(norms)] if norms else None
        for resource in jdata.resources:
            for actor_kind in sig.actors:
                for city in rng.sample(city_ids,
                                       min(cities_per_holding, len(city_ids))):
                    hid += 1
                    holdings.append(Holding(
                        id=f"H-{hid:04d}",
                        holder=Holder(city=city, actor_kind=actor_kind),
                        object=NormObject(kind=resource, type=holding_type),
                        activity=sig.verb,
                        under=under.id if under else "N-0001"))
    return NormSet(norms=norms, holdings=holdings,
                   description=f"generated for {jurisdiction} (seed={seed})")


def validate_situation(ns: NormSet, jurisdiction: str) -> list[str]:
    """Model validation + registry cross-check + no active strict conflict."""
    from .norms import validate_norm_set
    problems = validate_norm_set(ns, jurisdiction)
    jdata = load_jurisdictions()[jurisdiction]
    for a, b in ns.conflicts(jdata.incompatibilities):
        problems.append(f"active conflict of laws: {a.id} ({a.rule_form}) ⊥ "
                        f"{b.id} ({b.rule_form}) over {a.object.kind}/{a.aspect}")
    return problems
