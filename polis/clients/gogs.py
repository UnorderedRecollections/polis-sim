"""Client for the gogs instance (phase-1 platform of the institutional apparatus).

Note: this gogs build ("next") answers most of the gitea-shaped v1 API, but
some read-only admin routes (e.g. GET /api/v1/admin/users) 404 while the
corresponding POST/DELETE routes work. User listing therefore goes through
/users/search.
"""
from __future__ import annotations

from typing import Any

import httpx

from .. import config


class GogsError(RuntimeError):
    pass


class GogsClient:
    name = "gogs"

    def __init__(self, token: str | None = None):
        self.http = httpx.Client(
            base_url=config.GOGS_URL,
            headers={"Authorization": f"token {token or config.gogs_token()}"},
            timeout=10.0,
        )

    def _request(self, method: str, path: str, **kw: Any) -> httpx.Response:
        try:
            r = self.http.request(method, path, **kw)
        except httpx.HTTPError as e:
            raise GogsError(f"gogs unreachable at {config.GOGS_URL}: {e}") from e
        if r.status_code >= 400:
            raise GogsError(f"{method} {path} -> {r.status_code}: {r.text[:300]}")
        return r

    # --- introspection -----------------------------------------------------
    def whoami(self) -> dict:
        return self._request("GET", "/api/v1/user").json()

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

    def user_exists(self, username: str) -> bool:
        return any(u.get("username") == username for u in self.search_users(username, limit=10))

    def create_token(self, username: str, password: str, name: str = "polis") -> str:
        """A personal token for a user, via their basic auth. This build has
        NO token-delete route and rejects duplicate names, so re-runs use
        suffixed names (teardown deletes users, taking tokens with them)."""
        auth = (username, password)
        last_err = ""
        for attempt in range(20):
            token_name = name if attempt == 0 else f"{name}-{attempt}"
            try:
                r = self.http.post(f"/api/v1/users/{username}/tokens",
                                   auth=auth, json={"name": token_name})
            except httpx.HTTPError as e:
                raise GogsError(f"gogs unreachable at {config.GOGS_URL}: {e}") from e
            if r.status_code < 400:
                return r.json()["sha1"]
            last_err = f"{r.status_code}: {r.text[:200]}"
            if "already exists" not in r.text:
                break
        raise GogsError(f"create token for {username} -> {last_err}")

    def create_repo(self, owner: str, name: str, private: bool = False) -> dict:
        """Repo for a user or org (admin route). auto_init stays false —
        this build fails on auto_init: seed with a push instead."""
        return self._request(
            "POST",
            f"/api/v1/admin/users/{owner}/repos",
            json={"name": name, "private": private, "auto_init": False},
        ).json()

    def delete_repo(self, owner: str, name: str) -> None:
        self._request("DELETE", f"/api/v1/repos/{owner}/{name}")

    def repo_exists(self, owner: str, name: str) -> bool:
        r = self.http.get(f"/api/v1/repos/{owner}/{name}")
        return r.status_code == 200

    def add_collaborator(self, owner: str, repo: str, username: str,
                         permission: str = "write") -> None:
        self._request(
            "PUT",
            f"/api/v1/repos/{owner}/{repo}/collaborators/{username}",
            json={"permission": permission},
        )

    def create_org(self, username: str, full_name: str = "", owner: str | None = None) -> dict:
        # this gogs build has no POST /api/v1/orgs; orgs are created through the
        # admin route, owned by the given (or the authenticated) admin user.
        owner = owner or self.whoami()["login"]
        return self._request(
            "POST",
            f"/api/v1/admin/users/{owner}/orgs",
            json={"username": username, "full_name": full_name},
        ).json()

    def delete_org(self, username: str) -> None:
        raise GogsError(
            "this gogs build exposes no org-deletion route; remove the org via "
            "the web UI or directly in the database"
        )
