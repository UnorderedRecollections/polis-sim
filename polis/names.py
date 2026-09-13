"""Fictional name generation — weird-fiction / steampunk flavour."""
from __future__ import annotations

import random
import re
import string

CITY_NAMES = [
    # the canonical nine (their order is fixed: the default world is the
    # first nine, and existing seeds depend on it)
    "Cogswich",
    "Brasshaven",
    "Aetherquay",
    "Thornwick",
    "Cindercog",
    "Gloamingate",
    "Hushpoole",
    "Chimefall",
    "Vapourmouth",
    # the scale pool (task 0056): appended, never reordered
    "Saltmarch",
    "Ravenmoor",
    "Gildenford",
    "Mistvale",
    "Ashenbridge",
    "Coldharbour",
    "Foxglove",
    "Dunhollow",
    "Emberwick",
    "Greyfen",
    "Highwater",
    "Ironhall",
    "Larkspur",
    "Marrowgate",
    "Ninewells",
]

FIRST_NAMES = [
    "Ambrose", "Edwina", "Thaddeus", "Morwen", "Septimus", "Odile",
    "Bartholomew", "Ingrid", "Casimir", "Vera", "Ezekiel", "Honoria",
    "Silas", "Petronella", "Reginald", "Drusilla", "Obadiah", "Thomasina",
    "Ephraim", "Leonora", "Gideon", "Ursula", "Phineas", "Millicent",
    "Tobias", "Wilhelmina", "Cornelius", "Beatrice", "Josiah", "Evadne",
    "Roderick", "Clementine", "Algernon", "Mercy", "Eustace", "Ophelia",
    "Barnaby", "Temperance", "Leopold", "Hester", "Maximilian", "Prudence",
    "Nathaniel", "Georgiana", "Percival", "Rowena", "Ebenezer", "Sophronia",
    "Archibald", "Lavinia", "Horace", "Emmeline",
]

LAST_NAMES = [
    "Vane", "Morrow", "Cogswell", "Brassington", "Quill", "Featherstone",
    "Halloway", "Grimsbane", "Thistledown", "Marrowbone", "Kettleblack",
    "Sallow", "Nightingale", "Ashcroft", "Bellwether", "Crankshaw",
    "Duskwater", "Emberly", "Fallowfield", "Grimshaw", "Hartwell",
    "Ironmonger", "Jackdaw", "Kestrel", "Lovelace", "Munderby",
    "Nettlebed", "Oxbow", "Pargeter", "Rookwood", "Sable", "Tallow",
    "Underhill", "Vexley", "Wormwood", "Yarborough", "Zelwick",
    "Thackery", "Pembleton", "Starling", "Goodenough", "Hollowfax",
    "Marlborough", "Dreever",
]


def slugify(text: str) -> str:
    """'Aether Quay' -> 'aetherquay'; keeps only lowercase ascii letters/digits."""
    return re.sub(r"[^a-z0-9]+", "", text.lower())


def make_display_name(rng: random.Random, taken: set[str]) -> str:
    for _ in range(1000):
        name = f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}"
        if name not in taken:
            taken.add(name)
            return name
    raise RuntimeError("name pool exhausted")


def make_username(display_name: str, taken: set[str]) -> str:
    """'Edwina Vane' -> 'e.vane' (digits appended on collision)."""
    parts = display_name.split()
    base = f"{parts[0][0].lower()}.{slugify(parts[-1])}"
    username = base
    n = 2
    while username in taken:
        username = f"{base}{n}"
        n += 1
    taken.add(username)
    return username


def make_password(rng: random.Random, length: int = 18) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(rng.choices(alphabet, k=length))
