"""Client for the woodpecker CI server (the Mechanical Magistrate's engine room).

API base is /api (unversioned); authentication via Bearer token. Per-sim
instances (task 0041) point base_url at the sim's published port.
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

    def __init__(self, token: str | None = None, base_url: str | None = None):
        self.http = httpx.Client(
            base_url=base_url or config.WOODPECKER_URL,
            headers={"Authorization": f"Bearer {token or config.woodpecker_token()}"},
            timeout=10.0,
        )

    def _request(self, method: str, path: str, **kw: Any) -> httpx.Response:
        try:
            r = self.http.request(method, path, **kw)
        except httpx.HTTPError as e:
            raise WoodpeckerError(f"woodpecker unreachable at {self.http.base_url}: {e}") from e
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

    # --- CI bring-up (task 0041) ----------------------------------------------

    def enable_repo(self, forge_remote_id: int, owner: str, name: str) -> dict:
        """Enable a forge repo for builds (admin operation). Tolerates an
        already-active repo (idempotent re-runs over a persistent DB)."""
        try:
            return self._request(
                "POST", f"/api/repos?forge_remote_id={forge_remote_id}",
                json={"owner": owner, "name": name},
            ).json()
        except WoodpeckerError as e:
            if "already active" not in str(e):
                raise
            repo = self.lookup_repo(f"{owner}/{name}")
            if repo is None:
                raise
            return repo

    def lookup_repo(self, full_name: str) -> dict | None:
        r = self.http.get(f"/api/repos/lookup/{full_name}")
        return r.json() if r.status_code == 200 else None

    def repo_pipelines(self, repo_id: int, per_page: int = 5) -> list[dict]:
        return self._request(
            "GET", f"/api/repos/{repo_id}/pipelines", params={"per_page": per_page}
        ).json()

    def create_global_secret(self, name: str, value: str, events: list[str]) -> None:
        self._request("POST", "/api/secrets",
                      json={"name": name, "value": value, "events": events,
                            "images": [], "plugins_only": False})
