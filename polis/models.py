"""Domain model of the federation.

Two orthogonal dimensions on every person:
  * member_of  — where the person exists politically (a city), or, for the
                 Mechanical Magistrate, the federal institution it belongs to;
  * occupies   — the offices the person holds; offices grant powers.

Three kinds of agency:
  * political  — citizens who want things (legislators, delegates);
  * juridical  — officers exercising delegated legal authority
                 (experts, jurists, archivists);
  * mechanical — software executing rules (the Mechanical Magistrate).
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal, Optional

from pydantic import BaseModel, Field

Agency = Literal["political", "juridical", "mechanical"]

POLITICAL_ROLES = ("citizen-legislator", "local-delegate")

DEFAULT_DOMAINS = ["taxation", "maritime", "criminal", "commerce", "civic", "succession"]


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Membership(BaseModel):
    type: Literal["city", "institution"]
    id: str  # city slug, or institution body id (e.g. "federal-magistracy")


class GitIdentity(BaseModel):
    author_name: str
    author_email: str


class Credentials(BaseModel):
    password: str
    api_tokens: dict[str, str] = {}  # per-platform tokens, filled at provisioning
    ssh_private_key: Optional[str] = None
    ssh_public_key: Optional[str] = None


class Person(BaseModel):
    username: str
    display_name: str
    email: str
    agency: Agency
    member_of: Membership
    roles: list[str] = []      # political roles (subset of POLITICAL_ROLES)
    occupies: list[str] = []   # office ids
    git: GitIdentity
    credentials: Credentials
    created_at: datetime = Field(default_factory=_utcnow)


class Office(BaseModel):
    id: str                    # e.g. "federal-archivist", "local-archivist-cogswich"
    title: str                 # e.g. "Keeper of the Federal Rolls"
    body: str                  # e.g. "federal-archive", "domain:taxation"
    kind: Literal["juridical", "mechanical"]
    scope: str                 # "federal" or "city:<slug>"
    powers: list[str] = []     # e.g. "merge:main", "merge:municipal/cogswich/**"
    occupant: Optional[str] = None  # username
    created_at: datetime = Field(default_factory=_utcnow)


class City(BaseModel):
    id: str                    # slug, e.g. "cogswich"
    display_name: str
    created_at: datetime = Field(default_factory=_utcnow)


class Federation(BaseModel):
    name: str = "The Concord of the Nine Cities"
    archive_org: str = "the-archive"
    repo: str = "common-law"
    domains: list[str] = Field(default_factory=lambda: list(DEFAULT_DOMAINS))
    phase: int = 1             # 1 = customary machinery (gogs), 2 = automated (gitea+CI)


class World(BaseModel):
    federation: Federation = Field(default_factory=Federation)
    cities: list[City] = []
    offices: list[Office] = []
    persons: list[Person] = []
    created_at: datetime = Field(default_factory=_utcnow)

    # --- lookups -----------------------------------------------------------
    def find_city(self, city_id: str) -> City:
        for c in self.cities:
            if c.id == city_id:
                return c
        raise KeyError(f"unknown city '{city_id}'")

    def find_person(self, username: str) -> Person:
        for p in self.persons:
            if p.username == username:
                return p
        raise KeyError(f"unknown person '{username}'")

    def find_office(self, office_id: str) -> Office:
        for o in self.offices:
            if o.id == office_id:
                return o
        raise KeyError(f"unknown office '{office_id}'")

    def city_persons(self, city_id: str) -> list[Person]:
        return [p for p in self.persons if p.member_of.type == "city" and p.member_of.id == city_id]

    def office_of(self, person: Person, office_id: str) -> Office | None:
        return self.find_office(office_id) if office_id in person.occupies else None
