"""Persistence of the world state (world.json) and per-city container slices."""
from __future__ import annotations

import json
from pathlib import Path

from . import config
from .models import World


def world_exists() -> bool:
    return config.WORLD_FILE.exists()


def load_world() -> World:
    """Load world.json; return an empty world if none exists yet."""
    if not world_exists():
        return World()
    return World.model_validate_json(config.WORLD_FILE.read_text(encoding="utf-8"))


def save_world(world: World) -> Path:
    config.WORLD_DIR.mkdir(parents=True, exist_ok=True)
    config.WORLD_FILE.write_text(
        world.model_dump_json(indent=2), encoding="utf-8"
    )
    return config.WORLD_FILE


def city_slice(world: World, city_id: str) -> dict:
    """The configuration slice handed to one city container.

    Contains the city's own citizens (with credentials), its locally-scoped
    offices, and the git remotes through which it reaches the apparatus.
    Federal officers' credentials are never included.
    """
    city = world.find_city(city_id)
    fed = world.federation
    host = "gitea" if fed.phase == 2 else "gogs"
    port = 3000  # in-network port of the platform container
    return {
        "city": city.model_dump(mode="json"),
        "federation": {"name": fed.name, "phase": fed.phase},
        "git": {
            "default_branch": "main",
            "remotes": {
                "origin": f"http://{host}:{port}/{city.id}/{fed.repo}.git",
                "upstream": f"http://{host}:{port}/{fed.archive_org}/{fed.repo}.git",
            },
        },
        "citizens": [p.model_dump(mode="json") for p in world.city_persons(city.id)],
        "local_offices": [
            o.model_dump(mode="json") for o in world.offices if o.scope == f"city:{city.id}"
        ],
    }


def export_city(world: World, city_id: str) -> Path:
    config.CITIES_DIR.mkdir(parents=True, exist_ok=True)
    path = config.CITIES_DIR / f"{city_id}.json"
    path.write_text(json.dumps(city_slice(world, city_id), indent=2), encoding="utf-8")
    return path


def export_all_cities(world: World) -> list[Path]:
    return [export_city(world, c.id) for c in world.cities]
