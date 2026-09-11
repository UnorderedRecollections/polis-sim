"""Client for the gitea instance (the codified-machinery platform; also a
valid host for phase-1 sims since the platform abstraction, task 0037).

Quirks probed against this build (v1.27):
  * POST /users/{username}/tokens requires scopes on the request body when
    the authenticating principal has no token scopes (basic auth works);
  * org repos are created via POST /orgs/{org}/repos (the admin users route
    covers users only); an org cannot be deleted while it owns repos.
"""
from __future__ import annotations

from typing import Any

import httpx

from .. import config


class GiteaError(RuntimeError):
    pass


class GiteaClient:
    name = "gitea"

    def __init__(self, token: str | None = None, base_url: str | None = None):
        self.http = httpx.Client(
            base_url=base_url or config.GITEA_URL,
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

    def user_exists(self, username: str) -> bool:
        return any(u.get("login", u.get("username")) == username
                   for u in self.search_users(username, limit=10))

    def create_token(self, username: str, password: str, name: str = "polis") -> str:
        """A personal token for a user, via their basic auth. Gitea requires
        scopes on the request body when the authenticating principal carries
        none — request all scopes (the user's slice token feeds git + API).
        Token names are unique per user — re-runs use suffixed names (same
        rule as gogs; teardown deletes users, taking tokens with them)."""
        import base64
        auth = "Basic " + base64.b64encode(f"{username}:{password}".encode()).decode()
        last_err = ""
        for attempt in range(20):
            token_name = name if attempt == 0 else f"{name}-{attempt}"
            r = self.http.post(
                f"/api/v1/users/{username}/tokens",
                headers={"Authorization": auth},
                json={"name": token_name, "scopes": ["all"]},
            )
            if r.status_code < 400:
                return r.json()["sha1"]
            last_err = f"{r.status_code}: {r.text[:200]}"
            if "has been used" not in r.text:
                break
        raise GiteaError(f"create token for {username} -> {last_err}")

    def create_org(self, username: str, full_name: str = "", owner: str | None = None) -> dict:
        return self._request(
            "POST", "/api/v1/orgs", json={"username": username, "full_name": full_name}
        ).json()

    def delete_org(self, username: str) -> None:
        # an org with repos refuses deletion (500) — remove repos first
        self._request("DELETE", f"/api/v1/orgs/{username}")

    def org_exists(self, username: str) -> bool:
        r = self.http.get(f"/api/v1/orgs/{username}")
        return r.status_code == 200

    def create_repo(self, owner: str, name: str, private: bool = False) -> dict:
        """Repo for a user (admin users route) or an org (orgs route).
        auto_init stays false — seed with a push (same rule as gogs)."""
        if self.user_exists(owner):
            path = f"/api/v1/admin/users/{owner}/repos"
        else:
            path = f"/api/v1/orgs/{owner}/repos"
        return self._request(
            "POST", path, json={"name": name, "private": private, "auto_init": False}
        ).json()

    def create_fork(self, owner: str, repo: str, organization: str) -> dict:
        """Fork a repo into an organization (cross-repo PRs require the head
        repo to be a real fork of the base — the city archives are forks of
        the federal archive)."""
        return self._request(
            "POST", f"/api/v1/repos/{owner}/{repo}/forks",
            json={"organization": organization},
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
