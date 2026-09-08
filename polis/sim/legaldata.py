"""Loader for the legal-design YAML data (data/world/legal/).

The story generator is data-driven: jurisdiction files, the legal-move
vocabulary and story templates are YAML (readable by non-technical people);
this module validates them into pydantic models. Schema rationale:
docs/design/story-data-model.md.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel

from .. import config

LEGAL_DIR = config.WORLD_DIR / "legal"
JURISDICTIONS_DIR = LEGAL_DIR / "jurisdictions"
TEMPLATES_DIR = LEGAL_DIR / "templates"


class ParadigmData(BaseModel):
    kind: str                             # resource | conduct-status | political-burden
    label: str
    description: str = ""
    holding_object_types: list[str] = []
    impact_kinds: list[str] = []


class JurisdictionData(BaseModel):
    jurisdiction: str                     # slug, matches the filename
    name: str
    corpus_dir: Optional[str] = None
    paradigms: list[str] = []             # kinds from ontology/paradigms.yaml
    resources: list[str]
    actors: list[str]                     # derive from JurisdictionalActor
    activities: list[str]                 # domain verbs (NOT legal moves)
    resource_properties: list[str]
    rule_forms: list[str]
    disputes: list[str]


class MovesData(BaseModel):
    legal_moves: list[str]
    machinery_aliases: dict[str, str] = {}


class StoryTemplate(BaseModel):
    story_type: str
    participants: dict[str, str]
    sequence: list[str]


def _load_yaml(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_paradigms() -> dict[str, ParadigmData]:
    spec = _load_yaml(LEGAL_DIR / "ontology" / "paradigms.yaml")
    return {
        k["kind"]: ParadigmData.model_validate(k)
        for k in spec.get("kinds", [])
    }


def load_jurisdictions() -> dict[str, JurisdictionData]:
    known = load_paradigms()
    out: dict[str, JurisdictionData] = {}
    for path in sorted(JURISDICTIONS_DIR.glob("*.yaml")):
        data = JurisdictionData.model_validate(_load_yaml(path))
        if data.jurisdiction != path.stem:
            raise ValueError(f"{path.name}: jurisdiction '{data.jurisdiction}' != filename slug")
        unknown = set(data.paradigms) - set(known)
        if unknown:
            raise ValueError(f"{path.name}: unknown paradigm(s) {sorted(unknown)} "
                             f"(known: {sorted(known)})")
        out[data.jurisdiction] = data
    return out


def load_moves() -> MovesData:
    return MovesData.model_validate(_load_yaml(LEGAL_DIR / "moves.yaml"))


def load_templates() -> dict[str, StoryTemplate]:
    out: dict[str, StoryTemplate] = {}
    for path in sorted(TEMPLATES_DIR.glob("*.yaml")):
        tpl = StoryTemplate.model_validate(_load_yaml(path))
        out[tpl.story_type] = tpl
    return out
