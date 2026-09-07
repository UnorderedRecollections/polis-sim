"""Client for the gitea instance (phase-2 platform of the apparatus)."""
from __future__ import annotations

from typing import Any

import httpx

from .. import config


class GiteaError(RuntimeError):
    pass


class GiteaClient:
    name = "gitea"

    def __init__(self, token: str | None = None):
        self.http = httpx.Client(
            base_url=config.GITEA_URL,
            headers={"Authorization": f"token {token or config.gitea_token()}"},
            timeout=10.0,
        )

    def _request(self, method: str, path: str, **kw: Any) -> httpx.Response:
        try:
            r = self.http.request(method, path, **kw)
        except httpx.HTTPError as e:
            raise GiteaError(f"gitea unreachable at {config.GITEA_URL}: {e}") from e
        if r.status_code >= 400:
            raise GiteaError(f"{method} {path} -> {r.status_code}: {r.text[:300]}")
        return r

    # --- introspection -----------------------------------------------------
    def version(self) -> str:
        return self._request("GET", "/api/v1/version").json()["version"]

    def whoami(self) -> dict:
        return self._request("GET", "/api/v1/user").json()

    def admin_users(self, limit: int = 200) -> list[dict]:
        return self._request("GET", "/api/v1/admin/users", params={"limit": limit}).json()

    def search_users(self, query: str = "", limit: int = 200) -> list[dict]:
        data = self._request(
            "GET", "/api/v1/users/search", params={"q": query, "limit": limit}
        ).json()
        return data.get("data", []) if isinstance(data, dict) else data

    def list_orgs(self) -> list[dict]:
        return self._request("GET", "/api/v1/user/orgs").json()

    def list_repos(self, limit: int = 200) -> list[dict]:
        data = self._request("GET", "/api/v1/repos/search", params={"limit": limit}).json()
        return data.get("data", []) if isinstance(data, dict) else data

    # --- administration ------------------------------------------------------
    def create_user(self, username: str, email: str, password: str, full_name: str = "") -> dict:
        return self._request(
            "POST",
            "/api/v1/admin/users",
            json={
                "username": username,
                "email": email,
                "password": password,
                "full_name": full_name,
                "must_change_password": False,
                "send_notify": False,
            },
        ).json()

    def delete_user(self, username: str) -> None:
        self._request("DELETE", f"/api/v1/admin/users/{username}")

    def create_org(self, username: str, full_name: str = "") -> dict:
        return self._request(
            "POST", "/api/v1/orgs", json={"username": username, "full_name": full_name}
        ).json()

    def delete_org(self, username: str) -> None:
        self._request("DELETE", f"/api/v1/orgs/{username}")
