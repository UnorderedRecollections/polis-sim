"""Genesis — generate the founding population of the federation.

Roster (see design discussion):
  * per city: 3 citizen-legislators, 2 local delegates, 1 local archivist;
  * federal superstructure: 6 domain experts, 3 constitutional jurists,
    1 Federal Archivist (a local archivist elevated, dual office),
    1 Mechanical Magistrate (service account, not a person).

Separation rule: no person holds both a political role and a juridical
office. Experts and jurists are citizens of cities, but their citizenship
grants no powers — only their offices do.
"""
from __future__ import annotations

import random

from .models import (
    Agency,
    City,
    Credentials,
    Federation,
    GitIdentity,
    Membership,
    Office,
    Person,
    World,
)
from .names import CITY_NAMES, make_display_name, make_password, make_username

LEGISLATORS_PER_CITY = 3
DELEGATES_PER_CITY = 2

# The Concord of the Nine Cities: the canonical world is the first nine
# names; the pool is longer for scale runs (task 0056).
CANONICAL_CITIES = 9

ARCHIVE_POWERS_FEDERAL = ["merge:main", "revert:main", "tag:create", "branch:manage"]
MAGISTRATE_POWERS = ["execute:formal-checks", "report:commit-status"]


def _expert_powers(domain: str) -> list[str]:
    return [f"review:{domain}/**", f"jurisdiction:{domain}"]


def _local_archivist_powers(city_id: str) -> list[str]:
    return [f"merge:municipal/{city_id}/**", f"maintain:city-archive:{city_id}"]


COUNCIL_POWERS = ["review:required", "veto:incompatibility"]


class _RosterBuilder:
    def __init__(self, seed: int):
        self.rng = random.Random(seed)
        self.taken_names: set[str] = set()
        self.taken_usernames: set[str] = set()
        self.persons: list[Person] = []
        self.offices: list[Office] = []

    def new_person(
        self,
        agency: Agency,
        city_id: str | None,
        roles: list[str] | None = None,
        institution: str | None = None,
    ) -> Person:
        display = make_display_name(self.rng, self.taken_names)
        username = make_username(display, self.taken_usernames)
        if city_id is not None:
            member_of = Membership(type="city", id=city_id)
            email = f"{username}@{city_id}.invalid"
        else:
            member_of = Membership(type="institution", id=institution or "federal-magistracy")
            email = f"{username}@{member_of.id}.invalid"
        person = Person(
            username=username,
            display_name=display,
            email=email,
            agency=agency,
            member_of=member_of,
            roles=roles or [],
            git=GitIdentity(author_name=display, author_email=email),
            credentials=Credentials(password=make_password(self.rng)),
        )
        self.persons.append(person)
        return person

    def new_office(
        self,
        office_id: str,
        title: str,
        body: str,
        kind: str,
        scope: str,
        powers: list[str],
        occupant: Person | None,
    ) -> Office:
        office = Office(
            id=office_id, title=title, body=body, kind=kind,  # type: ignore[arg-type]
            scope=scope, powers=powers,
            occupant=occupant.username if occupant else None,
        )
        self.offices.append(office)
        if occupant is not None:
            occupant.occupies.append(office.id)
        return office


def build_world(seed: int = 42, cities: int | None = None,
                legislators_per_city: int = LEGISLATORS_PER_CITY,
                delegates_per_city: int = DELEGATES_PER_CITY) -> World:
    """The founding population. The defaults are the canonical federation
    (the first nine city names, 3 legislators + 2 delegates per city);
    `cities`, `legislators_per_city` and `delegates_per_city` scale it for
    the performance harness (task 0056). The first nine names and their
    order are fixed — existing seeds depend on them."""
    n = CANONICAL_CITIES if cities is None else cities
    if not 1 <= n <= len(CITY_NAMES):
        raise ValueError(f"cities must be 1..{len(CITY_NAMES)} (the name pool)")
    b = _RosterBuilder(seed)
    cities_ = [City(id=name.lower().replace(" ", ""), display_name=name)
               for name in CITY_NAMES[:n]]

    # --- municipal layer ---------------------------------------------------
    local_archivists: dict[str, Person] = {}
    for city in cities_:
        for _ in range(legislators_per_city):
            b.new_person("political", city.id, roles=["citizen-legislator"])
        for _ in range(delegates_per_city):
            b.new_person("political", city.id, roles=["local-delegate"])
        archivist = b.new_person("juridical", city.id)
        local_archivists[city.id] = archivist
        b.new_office(
            office_id=f"local-archivist-{city.id}",
            title=f"Archivist of {city.display_name}",
            body="local-archive",
            kind="juridical",
            scope=f"city:{city.id}",
            powers=_local_archivist_powers(city.id),
            occupant=archivist,
        )

    # --- federal superstructure --------------------------------------------
    fed = Federation()

    # Domain experts — one per legal domain; citizens of the first six cities
    # at the canonical size, cycling for tiny federations.
    for i, domain in enumerate(fed.domains):
        city = cities_[i % len(cities_)]
        expert = b.new_person("juridical", city.id)
        b.new_office(
            office_id=f"expert-{domain}",
            title=f"Jurisdictional Expert of {domain.title()}",
            body=f"domain:{domain}",
            kind="juridical",
            scope="federal",
            powers=_expert_powers(domain),
            occupant=expert,
        )

    # Constitutional jurists — citizens of the remaining cities, so that
    # every city is home to exactly one federal officer at the canonical
    # size; a tiny federation still seats one.
    jurist_cities = cities_[len(fed.domains):] or [cities_[-1]]
    for i, city in enumerate(jurist_cities, start=1):
        jurist = b.new_person("juridical", city.id)
        b.new_office(
            office_id=f"council-jurist-{i}",
            title=f"Jurist of the Constitutional Council, Seat {i}",
            body="constitutional-council",
            kind="juridical",
            scope="federal",
            powers=list(COUNCIL_POWERS),
            occupant=jurist,
        )

    # Federal Archivist — the first city's local archivist, elevated (dual office).
    b.new_office(
        office_id="federal-archivist",
        title="Keeper of the Federal Rolls",
        body="federal-archive",
        kind="juridical",
        scope="federal",
        powers=list(ARCHIVE_POWERS_FEDERAL),
        occupant=local_archivists[cities_[0].id],
    )

    # The Mechanical Magistrate — software, not a person; belongs to the
    # institution, not to any city. Dormant in phase 1, active in phase 2.
    magistrate = b.new_person("mechanical", None, institution="federal-magistracy")
    magistrate.display_name = "The Mechanical Magistrate"
    magistrate.username = "mechanical-magistrate"
    magistrate.email = "magistrate@federal-magistracy.invalid"
    magistrate.git = GitIdentity(author_name="Mechanical Magistrate", author_email=magistrate.email)
    b.new_office(
        office_id="mechanical-magistrate",
        title="The Mechanical Magistrate",
        body="federal-magistracy",
        kind="mechanical",
        scope="federal",
        powers=list(MAGISTRATE_POWERS),
        occupant=magistrate,
    )

    return World(federation=fed, cities=cities_, offices=b.offices, persons=b.persons)
