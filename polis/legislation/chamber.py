"""Chamber — the working context of a legislative act.

Resolves: who acts (a person from the city slice), through which platform
(the provisioned *product* — gogs or gitea; since task 0037 either product
can host phase 1), against which remotes (origin = the city's lodged copy,
upstream = the federal archive), and in which local clone.

Product vs phase (task 0037): `platform` is the provisioned product and
selects client/URL/token; `phase` (1 | 2) is the *procedure* — bills and
the docket dispatch on phase, not product (phase 1 runs matter-store
proceedings even on a gitea host).

Two modes:
  * container mode — POLIS_CITY_CONFIG (or /etc/polis/city.json) present:
    the slice is read directly;
  * operator mode — otherwise: world.json is loaded and --city selects the
    slice; URLs are host-swapped to the locally reachable platform address.

Testing hooks (env): POLIS_PLATFORM_TOKEN overrides the actor's token;
POLIS_ORIGIN_URL / POLIS_UPSTREAM_URL override the slice remotes.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse, urlunparse

from .. import config, store
from ..clients.gitea import GiteaClient
from ..clients.gogs import GogsClient


class ChamberError(RuntimeError):
    pass


@dataclass
class Chamber:
    platform: str            # the provisioned product: "gogs" | "gitea"
    phase: int               # the procedure: 1 customary | 2 codified
    city_id: str
    actor: dict              # person dict from the slice
    origin: str              # remote URL of the city's lodged copy
    upstream: str            # remote URL of the federal archive
    repo_dir: Path
    operator_mode: bool
    token: str | None
    offices: list[dict]      # offices the chamber can see:
                             # container mode -> the city's local offices only;
                             # operator mode -> all world offices (incl. federal,
                             # so the Keeper's merge:main is visible to the orchestrator)

    # --- actor -------------------------------------------------------------
    @property
    def actor_username(self) -> str:
        return self.actor["username"]

    @property
    def actor_label(self) -> str:
        roles = ", ".join(self.actor.get("roles") or self.actor.get("occupies") or [])
        return f"{self.actor['display_name']} ({self.actor_username}{', ' + roles if roles else ''})"

    @property
    def author(self) -> tuple[str, str]:
        git = self.actor["git"]
        return git["author_name"], git["author_email"]

    # --- remotes -------------------------------------------------------------
    @staticmethod
    def owner_repo(url: str) -> tuple[str, str]:
        parts = urlparse(url).path.strip("/").removesuffix(".git").split("/")
        if len(parts) < 2:
            raise ChamberError(f"cannot parse owner/repo from remote URL: {url}")
        return parts[-2], parts[-1]

    def origin_owner_repo(self) -> tuple[str, str]:
        return self.owner_repo(self.origin)

    def upstream_owner_repo(self) -> tuple[str, str]:
        return self.owner_repo(self.upstream)

    def _host_swap(self, url: str) -> str:
        """In operator mode the in-network URL (<platform>:3000) is
        unreachable; swap the host for the locally published one."""
        if not self.operator_mode:
            return url
        platform_url = config.GOGS_URL if self.platform == "gogs" else config.GITEA_URL
        u, p = urlparse(url), urlparse(platform_url)
        return urlunparse(u._replace(scheme=p.scheme, netloc=p.netloc))

    def git_remote_url(self, remote: str, masked: bool = False) -> str:
        """Remote URL usable from here, with the actor's token embedded for
        authentication (masked in --isomorphism output)."""
        url = self._host_swap(self.origin if remote == "origin" else self.upstream)
        if masked or not self.token:
            return url
        u = urlparse(url)
        return urlunparse(u._replace(netloc=f"{self.token}@{u.netloc}"))

    # --- platform client -----------------------------------------------------
    def client(self) -> GogsClient | GiteaClient:
        if not self.token:
            raise ChamberError(
                f"{self.actor_username} has no {self.platform} token yet — "
                "provision the platforms first (or set POLIS_PLATFORM_TOKEN)"
            )
        cls = GogsClient if self.platform == "gogs" else GiteaClient
        if self.operator_mode:
            # host side: config resolves the platform URL (sim secrets etc.)
            return cls(token=self.token)
        # container mode: the in-network host from the slice's origin —
        # config's defaults point at the dev rig, unreachable from here
        u = urlparse(self.origin)
        return cls(token=self.token, base_url=f"{u.scheme}://{u.netloc}")


def _load_slice(city: str | None) -> tuple[dict, bool, list[dict]]:
    cfg = os.environ.get("POLIS_CITY_CONFIG")
    if cfg:
        slice_ = json.loads(Path(cfg).read_text(encoding="utf-8"))
        return slice_, False, slice_.get("local_offices", [])
    etc = Path("/etc/polis/city.json")
    if etc.exists():
        slice_ = json.loads(etc.read_text(encoding="utf-8"))
        return slice_, False, slice_.get("local_offices", [])
    world = store.load_world()
    if not world.cities:
        raise ChamberError("no world yet — run `polis world genesis` first")
    if not city:
        raise ChamberError("operator mode: --city is required (or set POLIS_CITY_CONFIG)")
    # sim context (POLIS_PROVISIONED_SIM): act with the SIM's slice — its
    # remotes, per-sim tokens and provisioned product — not the world slice.
    # Host-swap still applies (operator mode), and config's URLs resolve to
    # the sim's own platform.
    if config.PROVISIONED_SIM:
        sim_slice = (config.DATA_DIR / "sims" / config.PROVISIONED_SIM
                     / "cities" / f"{city}.json")
        if sim_slice.exists():
            slice_ = json.loads(sim_slice.read_text(encoding="utf-8"))
            all_offices = [o.model_dump(mode="json") for o in world.offices]
            return slice_, True, all_offices
        raise ChamberError(
            f"sim '{config.PROVISIONED_SIM}' has no slice for city '{city}' "
            f"(expected {sim_slice})")
    try:
        slice_ = store.city_slice(world, city)
    except KeyError as e:
        raise ChamberError(e.args[0]) from e
    # the operator acts with sight of the whole world, including federal offices —
    # the Keeper of the Federal Rolls never enters a city slice
    all_offices = [o.model_dump(mode="json") for o in world.offices]
    return slice_, True, all_offices


def load_chamber(
    as_user: str,
    city: str | None = None,
    repo_dir: str | None = None,
) -> Chamber:
    slice_, operator_mode, offices = _load_slice(city)
    actor = next(
        (p for p in slice_["citizens"] if p["username"] == as_user), None
    )
    if actor is None:
        raise ChamberError(
            f"'{as_user}' is not a citizen of {slice_['city']['id']} "
            "(officers of the institution act from the operator side)"
        )
    fed = slice_.get("federation", {})
    phase = int(fed.get("phase", 1))
    # the provisioned product (task 0037): slices written by provisioning
    # carry it; world slices fall back to the phase-derived product
    product = fed.get("platform") or ("gitea" if phase == 2 else "gogs")
    remotes = slice_["git"]["remotes"]
    token = (
        (actor.get("credentials", {}).get("api_tokens") or {}).get(product)
        or os.environ.get("POLIS_PLATFORM_TOKEN")
    )
    default_repo = (str(config.DATA_DIR / "sims" / config.PROVISIONED_SIM / "common-law")
                    if config.PROVISIONED_SIM else "./common-law")
    chamber = Chamber(
        platform=product,
        phase=phase,
        city_id=slice_["city"]["id"],
        actor=actor,
        origin=os.environ.get("POLIS_ORIGIN_URL") or remotes["origin"],
        upstream=os.environ.get("POLIS_UPSTREAM_URL") or remotes["upstream"],
        repo_dir=Path(repo_dir or os.environ.get("POLIS_REPO_DIR") or default_repo),
        operator_mode=operator_mode,
        token=token,
        offices=offices,
    )
    # a chamber without its working copy of the corpus is useless; obtain
    # it on first use (idempotent)
    if not chamber.repo_dir.exists() and chamber.origin:
        from . import archive as archive_mod
        archive_mod.obtain(chamber).execute()
    return chamber
