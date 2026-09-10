"""The matter store — pending political/institutional state of the federation.

Third store of the ontology:
  * git history      — the legal archive (what the law is and how it came to be);
  * world/*.json     — the civil registry (who exists: cities, people, offices);
  * matters.json     — the political state (what is pending: petitions, bills,
                       and the procedural record of what happened to them).

Matters live in the institutions, not in the platform: gogs is a merely
mechanical archive and has no concept of petitions, proceedings or approvals.
Recording an event (here) is distinct from enforcing a procedure (which the
constitution leaves to people). Completed matters' event lists are the
procedural record (PROC) of the legal process.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal, Optional

from pydantic import BaseModel, Field

from . import config

MatterKind = Literal["petition", "bill"]

# open = still before the institutions; closed = decided one way or another
OPEN_STATUSES = ("submitted", "deliberating", "scrutinized")
CLOSED_STATUSES = ("ratified", "rejected", "dismissed")

_KIND_PREFIX = {"petition": "PET", "bill": "ACT"}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class MatterEvent(BaseModel):
    date: datetime = Field(default_factory=_utcnow)
    event: str            # filed | debated | scrutinized | enacted | rejected | dismissed | ...
    actor: str            # username
    detail: str = ""


class Matter(BaseModel):
    id: str               # PET-0007 / ACT-0017
    kind: MatterKind
    title: str
    proposer: str         # username
    city: str             # originating city
    status: str           # submitted | deliberating | scrutinized | ratified | rejected | dismissed
    branch: Optional[str] = None    # bills: the line of development
    answering: Optional[str] = None # bills: the petition (PET-…) it answers
    events: list[MatterEvent] = []
    created_at: datetime = Field(default_factory=_utcnow)

    @property
    def is_open(self) -> bool:
        return self.status in OPEN_STATUSES


class MatterStore(BaseModel):
    matters: list[Matter] = []
    counters: dict[str, int] = {}   # per-kind sequence for id allocation

    def new_matter(
        self,
        kind: MatterKind,
        title: str,
        proposer: str,
        city: str,
        branch: str | None = None,
        answering: str | None = None,
    ) -> Matter:
        n = self.counters.get(kind, 0) + 1
        self.counters[kind] = n
        matter = Matter(
            id=f"{_KIND_PREFIX[kind]}-{n:04d}",
            kind=kind, title=title, proposer=proposer, city=city,
            status="submitted", branch=branch, answering=answering,
        )
        self.matters.append(matter)
        return matter

    def find(self, matter_id: str) -> Matter:
        for m in self.matters:
            if m.id == matter_id:
                return m
        raise KeyError(f"unknown matter '{matter_id}'")

    def find_by_branch(self, branch: str) -> Matter | None:
        for m in self.matters:
            if m.kind == "bill" and m.branch == branch and m.is_open:
                return m
        return None


def matters_path() -> Path:
    # POLIS_MATTERS_FILE (explicit) > sim context (POLIS_PROVISIONED_SIM) > world
    if os.environ.get("POLIS_MATTERS_FILE"):
        return Path(os.environ["POLIS_MATTERS_FILE"])
    if config.PROVISIONED_SIM:
        return config.DATA_DIR / "sims" / config.PROVISIONED_SIM / "matters.json"
    return config.WORLD_DIR / "matters.json"


def load_matters() -> MatterStore:
    path = matters_path()
    if not path.exists():
        return MatterStore()
    text = path.read_text(encoding="utf-8").strip()
    if not text:                       # an empty file is an empty docket
        return MatterStore()
    return MatterStore.model_validate_json(text)


def save_matters(store: MatterStore) -> Path:
    path = matters_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(store.model_dump_json(indent=2), encoding="utf-8")
    return path
