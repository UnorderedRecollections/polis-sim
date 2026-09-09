"""Locations, endpoints and credentials for the local apparatus.

Secrets live in the project .env file (see .env.example); environment
variables always win over the file. Everything else is likewise overridable
via POLIS_* environment variables so the tool can later be pointed at the
refactored, portable deployment without code changes.
"""
from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
# POLIS_DATA_DIR: inside city containers the legal data is mounted read-only
# (the package itself lives in site-packages there, so no project root exists)
DATA_DIR = Path(os.environ.get("POLIS_DATA_DIR") or (PROJECT_ROOT / "data"))
WORLD_DIR = DATA_DIR / "world"
WORLD_FILE = WORLD_DIR / "world.json"
CITIES_DIR = WORLD_DIR / "cities"
ENV_FILE = PROJECT_ROOT / ".env"

GOGS_URL = os.environ.get("POLIS_GOGS_URL", "http://localhost:10880")
GITEA_URL = os.environ.get("POLIS_GITEA_URL", "http://localhost:3001")
WOODPECKER_URL = os.environ.get("POLIS_WOODPECKER_URL", "http://localhost:10890")

PODMAN_NETWORK = os.environ.get("POLIS_NETWORK", "gogs-local")
POSTGRES_CONTAINER = os.environ.get("POLIS_POSTGRES_CONTAINER", "postgres-gogs")
CITY_CONTAINER_PREFIX = os.environ.get("POLIS_CITY_PREFIX", "polis-city-")


def _load_env_file() -> dict[str, str]:
    values: dict[str, str] = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                values[k.strip()] = v.strip()
    return values


def _secret(env_var: str, env_key: str) -> str:
    """Resolve a secret: POLIS_* env var > process env > .env file."""
    v = os.environ.get(env_var) or os.environ.get(env_key)
    if v:
        return v.strip()
    v = _load_env_file().get(env_key)
    if v:
        return v
    raise RuntimeError(
        f"missing credential: set {env_var} (or {env_key} in {ENV_FILE}) — see .env.example"
    )


def gogs_token() -> str:
    return _secret("POLIS_GOGS_TOKEN", "GOGS_API_KEY")


def gitea_token() -> str:
    return _secret("POLIS_GITEA_TOKEN", "GITEA_API_KEY")


def woodpecker_token() -> str:
    return _secret("POLIS_WOODPECKER_TOKEN", "WOODPECKER_API_KEY")
