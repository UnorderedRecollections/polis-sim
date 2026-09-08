"""Resource files — concrete resources stories revolve around.

Schema and rationale: docs/design/resource-files.md. Files are the single
source of truth for resources; the jurisdiction YAML's `resources:` list is
an index, cross-validated in both directions at load time.
"""
from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel

from .. import config
from .legaldata import load_jurisdictions

RESOURCES_DIR = config.WORLD_DIR / "legal" / "resources"


class ResourceData(BaseModel):
    resource: str                       # slug, matches the filename
    jurisdiction: str                   # owner jurisdiction
    label: str = ""
    object_type: str = "resource"       # always "resource" in these files
    properties: dict[str, object] = {}
    customary_use: list[str] = []
    narrative: str = ""


def _load_one(path: Path) -> ResourceData:
    with path.open(encoding="utf-8") as f:
        data = ResourceData.model_validate(yaml.safe_load(f) or {})
    if data.resource != path.stem:
        raise ValueError(f"{path}: resource '{data.resource}' != filename slug")
    if data.object_type != "resource":
        raise ValueError(f"{path}: object_type must be 'resource'")
    return data


def load_resources() -> dict[str, dict[str, ResourceData]]:
    """All resource files: jurisdiction slug -> resource slug -> data."""
    out: dict[str, dict[str, ResourceData]] = {}
    if not RESOURCES_DIR.is_dir():
        return out
    for jdir in sorted(p for p in RESOURCES_DIR.iterdir() if p.is_dir()):
        out[jdir.name] = {p.stem: _load_one(p) for p in sorted(jdir.glob("*.yaml"))}
    return out


def validate_resources() -> list[str]:
    """Cross-validate resources against the jurisdiction registry:
    bidirectional index↔files, jurisdiction existence, property keys
    restricted to the jurisdiction's declared resource_properties."""
    problems: list[str] = []
    jurisdictions = load_jurisdictions()
    files = load_resources()

    for slug, resources in files.items():
        j = jurisdictions.get(slug)
        if j is None:
            problems.append(f"resources/{slug}: unknown jurisdiction")
            continue
        index, on_disk = set(j.resources), set(resources)
        for missing in sorted(index - on_disk):
            problems.append(f"{slug}: '{missing}' listed in the jurisdiction but has no file")
        for extra in sorted(on_disk - index):
            problems.append(f"{slug}: resource file '{extra}' not listed in the jurisdiction")
        declared = set(j.resource_properties)
        for r in resources.values():
            if r.jurisdiction != slug:
                problems.append(f"{slug}/{r.resource}: jurisdiction field says '{r.jurisdiction}'")
            for key in r.properties:
                if declared and key not in declared:
                    problems.append(
                        f"{slug}/{r.resource}: property '{key}' not declared in "
                        f"{slug}'s resource_properties")
    # resource-paradigm jurisdictions with an index but no files at all —
    # conduct/status jurisdictions list abstract objects that get no files
    for slug, j in jurisdictions.items():
        if "resource" in j.paradigms and j.resources and slug not in files:
            problems.append(f"{slug}: resources listed but no resource files yet")
    return problems


def find_resource(kind: str, jurisdiction: str | None = None) -> ResourceData:
    """One resource by slug (optionally jurisdiction-scoped)."""
    files = load_resources()
    for slug, resources in files.items():
        if jurisdiction and slug != jurisdiction:
            continue
        if kind in resources:
            return resources[kind]
    scope = f" in jurisdiction '{jurisdiction}'" if jurisdiction else ""
    raise KeyError(f"unknown resource '{kind}'{scope}")
