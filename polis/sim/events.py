"""Event candidates — friction derivation and charged candidates.

Design: docs/design/activity-signatures.md. A signature declares only its
impact; friction is DERIVED from the current situation (norms + holdings):

    raw harm  = friction table: who else uses this object/aspect
    charged   = raw harm NOT legitimately allocated by a norm in force

A charged candidate is a story seed: actor, action, harmed parties, and the
norms in question. No git, no platform — pure functions over the situation.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional

from .legaldata import ActivitySignature, JurisdictionData, load_jurisdictions
from .norms import Holding, NormSet, load_seed_norms


@dataclass(frozen=True)
class FrictionHit:
    """One harmed holding, with the norms over the affected aspect."""
    holding: Holding
    norms_in_question: tuple[str, ...]      # ids of norms in force over object+aspect


@dataclass(frozen=True)
class Party:
    """A concrete acting party: an actor kind, optionally of a city —
    ("fisher" of Cogswich vs. "fisher" of Brasshaven are different parties)."""
    actor_kind: str
    city: Optional[str] = None

    def label(self) -> str:
        return f"{self.actor_kind} of {self.city}" if self.city else self.actor_kind


@dataclass(frozen=True)
class EventCandidate:
    """A story seed: actor acts, holdings are harmed, norms are in question."""
    actor: Party
    verb: str
    object_kind: str
    affects: tuple[str, ...]
    impact: str
    harmed: tuple[FrictionHit, ...] = field(default_factory=tuple)

    @property
    def charged(self) -> bool:
        return bool(self.harmed)


# ---------------------------------------------------------------- friction table
# who is harmed by each impact kind, as a predicate over a holding
# (sig = the activity signature, h = the potentially harmed holding)

def _same_object(sig: ActivitySignature, h: Holding, object_kind: str) -> bool:
    return h.object.kind == object_kind


_FRICTION: dict[str, Callable[[ActivitySignature, Holding, str], bool]] = {
    "depletes": lambda s, h, obj: _same_object(s, h, obj) and bool(h.activity),
    "blocks": lambda s, h, obj: _same_object(s, h, obj),
    "occupies": lambda s, h, obj: _same_object(s, h, obj),
    "pollutes": lambda s, h, obj: _same_object(s, h, obj),
    "enriches": lambda s, h, obj: False,
    "prohibits": lambda s, h, obj: h.activity == s.verb,
    "requires": lambda s, h, obj: h.activity == s.verb,
    "burdens": lambda s, h, obj: h.activity == s.verb or _same_object(s, h, obj),
    "obliges": lambda s, h, obj: h.activity == s.verb,
    "penalizes": lambda s, h, obj: h.activity == s.verb,
    "confers-status": lambda s, h, obj: h.object.type == "status" and h.object.kind == obj,
    "allocates": lambda s, h, obj: _same_object(s, h, obj),
}


def raw_friction(
    sig: ActivitySignature,
    object_kind: str,
    norm_set: NormSet,
    actor: Party | None = None,
) -> list[FrictionHit]:
    """Every holding harmed by `actor` performing `sig` on `object_kind`,
    with the norms in force over the affected aspects (the legal question).
    A party never harms its own holdings."""
    harmed: list[FrictionHit] = []
    predicate = _FRICTION.get(sig.impact)
    if predicate is None:
        return harmed
    for h in norm_set.holdings:
        if actor and h.holder.actor_kind == actor.actor_kind:
            if h.holder.city is None or h.holder.city == actor.city:
                continue  # the acting party itself
        if predicate(sig, h, object_kind):
            norms = tuple(
                n.id for a in (sig.affects or [""])
                for n in norm_set.in_force(object_kind=object_kind, aspect=a or None)
            )
            harmed.append(FrictionHit(holding=h, norms_in_question=norms))
    return harmed


#: legitimacy hook (docs/design/activity-signatures.md §4.1): harm is
#: allocated — not charged — when a norm in force over the same
#: object+aspect regulates the acting kind. v1 limitation: any regulating
#: norm counts as allocating (intensity, e.g. fishing *beyond* quota,
#: is not yet modeled).
def default_legitimacy(
    sig: ActivitySignature, object_kind: str, norm_set: NormSet, actor_kind: str
) -> bool:
    for n in norm_set.in_force(object_kind=object_kind):
        if sig.affects and n.aspect not in sig.affects:
            continue
        if actor_kind in n.subjects:
            return True
    return False


def _parties(sig: ActivitySignature, norm_set: NormSet) -> list[Party]:
    """The concrete parties who could act: distinct (city, kind) holders of
    the signature's actor kinds, plus a city-less party for kinds that hold
    nothing yet (an outsider can always act)."""
    parties: list[Party] = []
    seen: set[Party] = set()
    for h in norm_set.holdings:
        if h.holder.actor_kind in sig.actors:
            p = Party(actor_kind=h.holder.actor_kind, city=h.holder.city)
            if p not in seen:
                seen.add(p)
                parties.append(p)
    for kind in sig.actors:
        if not any(p.actor_kind == kind for p in parties):
            parties.append(Party(actor_kind=kind))
    return parties


def charged_candidates(
    jurisdiction: JurisdictionData,
    norm_set: NormSet,
    resources: list[str] | None = None,
    legitimacy: Callable[[ActivitySignature, str, NormSet, str], bool] = default_legitimacy,
) -> list[EventCandidate]:
    """All candidates (charged or not) for a jurisdiction against a situation."""
    candidates: list[EventCandidate] = []
    objects = resources or list(jurisdiction.resources)
    for sig in jurisdiction.activities:
        if not sig.impact:
            continue  # bare verbs carry no structure yet
        for actor in _parties(sig, norm_set):
            for obj in objects:
                if not _preconditions_hold(sig, norm_set):
                    continue
                if legitimacy(sig, obj, norm_set, actor.actor_kind):
                    continue  # harm allocated by law — nothing to grieve
                harmed = raw_friction(sig, obj, norm_set, actor=actor)
                candidates.append(EventCandidate(
                    actor=actor, verb=sig.verb, object_kind=obj,
                    affects=tuple(sig.affects), impact=sig.impact,
                    harmed=tuple(harmed),
                ))
    return candidates


def _preconditions_hold(sig: ActivitySignature, norm_set: NormSet) -> bool:
    required_norm = sig.preconditions.get("norm_in_force")
    if required_norm:
        if not any(n.rule_form == required_norm and n.status == "in_force"
                   for n in norm_set.norms):
            return False
    if sig.preconditions.get("holding_required"):
        if not norm_set.holdings:
            return False
    return True


# ---------------------------------------------------------------- convenience

def candidates_for(jurisdiction_slug: str) -> list[EventCandidate]:
    """Charged candidates from the seed, for one jurisdiction."""
    j = load_jurisdictions()[jurisdiction_slug]
    ns = load_seed_norms()[jurisdiction_slug]
    return [c for c in charged_candidates(j, ns) if c.charged]


def validate_signatures() -> list[str]:
    """Paradigm contract: every signature's impact must be one of the
    impact_kinds its jurisdiction's paradigm(s) declare."""
    from .legaldata import load_paradigms

    paradigms = load_paradigms()
    problems: list[str] = []
    for slug, j in load_jurisdictions().items():
        admitted = {k for p in j.paradigms for k in paradigms[p].impact_kinds}
        for sig in j.activities:
            if sig.impact and admitted and sig.impact not in admitted:
                problems.append(
                    f"{slug}: activity '{sig.verb}' has impact '{sig.impact}' "
                    f"not admitted by paradigm(s) {sorted(j.paradigms)} "
                    f"({sorted(admitted)})")
    return problems
