"""The legal ontology — the reusable vocabulary of the simulation's legal DSL.

Fully data-driven: every category is YAML in `data/world/legal/ontology/`
(see docs/design/legal-ontology.md for the concepts). Base classes are
defined here; the loader parses the YAML and **dynamically creates subtypes**
(`ActorPerson`, `ActorCitizen`, …) as a real Python class hierarchy, with
parent relationships coming from the YAML's explicit `parent:` property.

  * Actor          (actors.yaml)          — who can act;
  * LegalObject    (legal_objects.yaml)   — the things law is made of;
  * LegalRelation  (legal_relations.yaml) — how objects relate;
  * ProceduralEvent(procedural_events.yaml)— what can happen to a matter.

Concrete Jurisdiction objects are built at load time by a factory over
`data/world/legal/jurisdictions/*.yaml` (task 0003 metadata).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import yaml

from .. import config
from .legaldata import load_jurisdictions as _load_jurisdiction_data

ONTOLOGY_DIR = config.WORLD_DIR / "legal" / "ontology"


def _read_yaml(name: str) -> dict:
    with (ONTOLOGY_DIR / name).open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _camel(slug: str) -> str:
    return "".join(part.title() for part in slug.replace("_", "-").split("-"))


# ---------------------------------------------------------------- base classes

class Actor:
    """Base class of the actor taxonomy (see ontology/actors.yaml)."""
    kind: str = ""
    label: str = ""
    parent: Optional[str] = None     # the kind this one derives from (explicit in YAML)
    abstract: bool = False
    collective: bool = False


class LegalObject:
    """Base class of legal objects (see ontology/legal_objects.yaml)."""
    kind: str = ""
    label: str = ""
    implemented: bool = False
    note: str = ""


class LegalRelation:
    """Base class of legal relationships (see ontology/legal_relations.yaml)."""
    kind: str = ""
    label: str = ""


class ProceduralEvent:
    """Base class of procedural events (see ontology/procedural_events.yaml)."""
    kind: str = ""
    label: str = ""
    matter_event: Optional[str] = None


class Paradigm:
    """Base class of jurisdiction paradigms (see ontology/paradigms.yaml)."""
    kind: str = ""
    label: str = ""
    description: str = ""
    holding_object_types: list[str] = []
    impact_kinds: list[str] = []


_BASES = {"Actor": Actor, "LegalObject": LegalObject,
          "LegalRelation": LegalRelation, "ProceduralEvent": ProceduralEvent,
          "Paradigm": Paradigm}


def _build_types(filename: str) -> dict[str, type]:
    """Parse a category YAML and dynamically create the subtype hierarchy.

    Every entry becomes a class named `<Base><CamelKind>`; `parent:` (a kind
    declared earlier in the file, or null for the base itself) determines the
    Python base class, so the YAML's parent property is also the real
    inheritance chain.
    """
    spec = _read_yaml(filename)
    base = _BASES[spec["base"]]
    types: dict[str, type] = {}
    for entry in spec.get("kinds", []):
        kind = entry["kind"]
        parent_slug = entry.get("parent")
        parent = base if parent_slug is None else types[parent_slug]  # KeyError = misordered YAML
        attrs = {k: v for k, v in entry.items() if k != "parent"}
        attrs["parent"] = parent_slug
        attrs.setdefault("label", kind.replace("-", " ").replace("_", " ").title())
        types[kind] = type(f"{base.__name__}{_camel(kind)}", (parent,), attrs)
    return types


# ---------------------------------------------------------------- registries

ACTORS: dict[str, type[Actor]] = _build_types("actors.yaml")
LEGAL_OBJECTS: dict[str, type[LegalObject]] = _build_types("legal_objects.yaml")
LEGAL_RELATIONS: dict[str, type[LegalRelation]] = _build_types("legal_relations.yaml")
PROCEDURAL_EVENTS: dict[str, type[ProceduralEvent]] = _build_types("procedural_events.yaml")
PARADIGMS: dict[str, type[Paradigm]] = _build_types("paradigms.yaml")

#: convenient handles on the dynamic classes
ActorPerson = ACTORS["person"]
ActorCitizen = ACTORS["citizen"]
ActorJurisdictional = ACTORS["jurisdictional-actor"]

#: object kinds the machinery can already produce
IMPLEMENTED_OBJECT_TYPES = {k for k, t in LEGAL_OBJECTS.items() if t.implemented}

#: canonical event kind -> matter-store event string (subset with a mapping)
MATTER_EVENT_MAP: dict[str, str] = {
    k: t.matter_event for k, t in PROCEDURAL_EVENTS.items() if t.matter_event
}


def actor_type(kind: str) -> type[Actor]:
    """The class for an actor kind. Unknown kinds (e.g. `harbor-master`,
    `fisher`) are registered on demand as subclasses of ActorJurisdictional."""
    if kind not in ACTORS:
        ACTORS[kind] = type(
            f"Actor{_camel(kind)}", (ActorJurisdictional,),
            {"kind": kind, "label": kind.replace("-", " ").replace("_", " ").title(),
             "parent": ActorJurisdictional.kind, "abstract": False},
        )
    return ACTORS[kind]


def derivation_chain(kind: str) -> list[str]:
    """The actor kind's ancestry, from itself up to a root."""
    chain = []
    cls: type[Actor] | None = actor_type(kind)
    while cls is not None and cls is not Actor:
        chain.append(cls.kind)
        cls = actor_type(cls.parent) if cls.parent else None
    return chain


def is_actor_a(kind: str | type, ancestor: str | type) -> bool:
    """True if `kind` is `ancestor` or derives from it (strings or classes)."""
    cls = kind if isinstance(kind, type) else actor_type(kind)
    anc = ancestor if isinstance(ancestor, type) else actor_type(ancestor)
    return issubclass(cls, anc)


# ---------------------------------------------------------------- jurisdictions

@dataclass(frozen=True)
class ConflictGrammar:
    """What a story generator needs to construct a conflict: the resource,
    who disputes, which properties matter, and which rules could cause or
    settle it (built from the jurisdiction YAML's rule_forms etc.)."""
    resource: str
    actors: list[str]
    resource_properties: list[str]
    possible_rules: list[str]


@dataclass(frozen=True)
class Jurisdiction:
    """A concrete jurisdiction, built at load time by `jurisdiction_factory`."""
    slug: str
    name: str
    corpus_dir: Optional[str]
    paradigms: tuple[str, ...]            # kinds from ontology/paradigms.yaml
    resources: tuple[str, ...]
    actors: tuple[str, ...]               # actor kind slugs
    activities: tuple                     # ActivitySignature objects
    resource_properties: tuple[str, ...]
    rule_forms: tuple[str, ...]
    disputes: tuple[str, ...]

    def actor_types(self) -> list[type[Actor]]:
        return [actor_type(a) for a in self.actors]

    def conflict_grammar(self, resource: str | None = None) -> ConflictGrammar:
        return ConflictGrammar(
            resource=resource or self.resources[0],
            actors=list(self.actors),
            resource_properties=list(self.resource_properties),
            possible_rules=list(self.rule_forms),
        )


def jurisdiction_factory(metadata) -> Jurisdiction:
    """Build a concrete Jurisdiction from a jurisdictions/*.yaml document
    (a legaldata.JurisdictionData), registering its actor kinds."""
    j = Jurisdiction(
        slug=metadata.jurisdiction,
        name=metadata.name,
        corpus_dir=metadata.corpus_dir,
        paradigms=tuple(metadata.paradigms),
        resources=tuple(metadata.resources),
        actors=tuple(metadata.actors),
        activities=tuple(metadata.activities),
        resource_properties=tuple(metadata.resource_properties),
        rule_forms=tuple(metadata.rule_forms),
        disputes=tuple(metadata.disputes),
    )
    for a in j.actors:            # ensure jurisdiction actor kinds are registered
        actor_type(a)
    return j


def load_jurisdictions() -> dict[str, Jurisdiction]:
    """Simulation-startup load: build every concrete jurisdiction from the
    YAML metadata."""
    return {
        slug: jurisdiction_factory(data)
        for slug, data in _load_jurisdiction_data().items()
    }


#: the jurisdiction registry, built at import (simulation startup)
JURISDICTIONS: dict[str, Jurisdiction] = load_jurisdictions()
