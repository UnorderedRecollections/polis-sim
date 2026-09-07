"""Client for the woodpecker CI server (the Mechanical Magistrate's engine room).

API base is /api (unversioned); authentication via Bearer token.
"""
from __future__ import annotations

import time
from typing import Any

import httpx

from .. import config


class WoodpeckerError(RuntimeError):
    pass


class WoodpeckerClient:
    name = "woodpecker"

    def __init__(self, token: str | None = None):
        self.http = httpx.Client(
            base_url=config.WOODPECKER_URL,
            headers={"Authorization": f"Bearer {token or config.woodpecker_token()}"},
            timeout=10.0,
        )

    def _request(self, method: str, path: str, **kw: Any) -> httpx.Response:
        try:
            r = self.http.request(method, path, **kw)
        except httpx.HTTPError as e:
            raise WoodpeckerError(f"woodpecker unreachable at {config.WOODPECKER_URL}: {e}") from e
        if r.status_code >= 400:
            raise WoodpeckerError(f"{method} {path} -> {r.status_code}: {r.text[:300]}")
        return r

    def healthz(self) -> bool:
        try:
            return self.http.get("/healthz").status_code == 204
        except httpx.HTTPError:
            return False

    def whoami(self) -> dict:
        return self._request("GET", "/api/user").json()

    def list_agents(self) -> list[dict]:
        return self._request("GET", "/api/agents").json()

    def delete_agent(self, agent_id: int) -> None:
        self._request("DELETE", f"/api/agents/{agent_id}")

    def live_agents(self, max_silence_seconds: int = 300) -> list[dict]:
        """Agents that have contacted the server recently."""
        now = int(time.time())
        return [
            a for a in self.list_agents()
            if a.get("last_contact") and now - a["last_contact"] < max_silence_seconds
        ]
