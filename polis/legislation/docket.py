"""The docket — grievances entering the institutional record (§16).

An issue says "there is a problem"; it proposes no remedy.

Phase 1 (customary): petitions live in the matter store — the institutions
keep their own docket; the mechanical archive (gogs) knows nothing of them.
Phase 2 (codified): the platform gains a docket concept (issues) and the
record moves there.
"""
from __future__ import annotations

import json

from .. import matters as matters_mod
from ..matters import Matter
from .chamber import Chamber, ChamberError
from .plan import Plan


def _get_matter(store: matters_mod.MatterStore, matter_id: str) -> Matter:
    try:
        return store.find(matter_id)
    except KeyError as e:
        raise ChamberError(e.args[0]) from e


# --- phase 1: the matter store -------------------------------------------------

def file_petition(chamber: Chamber, title: str, body: str) -> Plan:
    """A recognized problem, request or dispute enters the docket."""
    if chamber.phase == 2:
        return _platform_file(chamber, title, body)

    def run():
        store = matters_mod.load_matters()
        matter = store.new_matter(
            "petition", title, proposer=chamber.actor_username, city=chamber.city_id
        )
        matter.events.append(matters_mod.MatterEvent(
            event="filed", actor=chamber.actor_username, detail=body
        ))
        matters_mod.save_matters(store)
        return matter

    return Plan(act="file a petition", actor=chamber.actor_label).add(
        machinery=f"matters.json: enter matter (kind=petition, title={json.dumps(title)}, "
                  f"event=filed by {chamber.actor_username})",
        legal="a grievance enters the institutional docket, kept by the "
              "institutions themselves (§16)",
        run=run,
    )


def comment_petition(chamber: Chamber, matter_id: str, body: str) -> Plan:
    if chamber.phase == 2:
        return _platform_comment(chamber, int(matter_id.lstrip("#")), body)

    def run():
        store = matters_mod.load_matters()
        matter = _get_matter(store, matter_id)
        if not matter.is_open:
            raise ChamberError(f"{matter_id} is {matter.status} — the record is closed")
        matter.events.append(matters_mod.MatterEvent(
            event="heard", actor=chamber.actor_username, detail=body
        ))
        if matter.status == "submitted":
            matter.status = "deliberating"
        matters_mod.save_matters(store)
        return matter

    return Plan(act=f"speak on petition {matter_id}", actor=chamber.actor_label).add(
        machinery=f"matters.json: append event (heard, {chamber.actor_username}) to {matter_id}",
        legal="a voice is heard on a docketed grievance; the record grows",
        run=run,
    )


def dismiss_petition(chamber: Chamber, matter_id: str) -> Plan:
    if chamber.phase == 2:
        return _platform_dismiss(chamber, int(matter_id.lstrip("#")))

    def run():
        store = matters_mod.load_matters()
        matter = _get_matter(store, matter_id)
        if not matter.is_open:
            raise ChamberError(f"{matter_id} is already {matter.status}")
        matter.status = "dismissed"
        matter.events.append(matters_mod.MatterEvent(
            event="dismissed", actor=chamber.actor_username
        ))
        matters_mod.save_matters(store)
        return matter

    return Plan(act=f"dismiss petition {matter_id}", actor=chamber.actor_label).add(
        machinery=f"matters.json: {matter_id}.status = dismissed (+ event)",
        legal="the grievance is denied further hearing (the record remains)",
        run=run,
    )


# --- phase 2: the platform docket (issues) --------------------------------------

def _platform_file(chamber: Chamber, title: str, body: str) -> Plan:
    owner, repo = chamber.upstream_owner_repo()
    payload = {"title": title, "body": body}

    def run():
        return chamber.client()._request("POST", f"/api/v1/repos/{owner}/{repo}/issues", json=payload).json()

    return Plan(act="file a petition", actor=chamber.actor_label).add(
        machinery=f"POST /api/v1/repos/{owner}/{repo}/issues  {json.dumps(payload)}",
        legal="a grievance enters the codified docket of the federal archive",
        run=run,
    )


def _platform_comment(chamber: Chamber, number: int, body: str) -> Plan:
    owner, repo = chamber.upstream_owner_repo()

    def run():
        return chamber.client()._request(
            "POST", f"/api/v1/repos/{owner}/{repo}/issues/{number}/comments", json={"body": body}
        ).json()

    return Plan(act=f"speak on petition #{number}", actor=chamber.actor_label).add(
        machinery=f"POST /api/v1/repos/{owner}/{repo}/issues/{number}/comments",
        legal="a voice is heard on a docketed grievance",
        run=run,
    )


def _platform_dismiss(chamber: Chamber, number: int) -> Plan:
    owner, repo = chamber.upstream_owner_repo()

    def run():
        return chamber.client()._request(
            "PATCH", f"/api/v1/repos/{owner}/{repo}/issues/{number}", json={"state": "closed"}
        ).json()

    return Plan(act=f"dismiss petition #{number}", actor=chamber.actor_label).add(
        machinery=f"PATCH /api/v1/repos/{owner}/{repo}/issues/{number}  {{\"state\": \"closed\"}}",
        legal="the grievance is denied further hearing (the record remains)",
        run=run,
    )


# --- inspection -------------------------------------------------------------------

def list_petitions(chamber: Chamber, state: str = "open") -> list[dict]:
    if chamber.phase == 2:
        owner, repo = chamber.upstream_owner_repo()
        return chamber.client()._request(
            "GET", f"/api/v1/repos/{owner}/{repo}/issues", params={"state": state, "type": "issues"}
        ).json()
    store = matters_mod.load_matters()
    petitions = [m for m in store.matters if m.kind == "petition"]
    if state == "open":
        petitions = [m for m in petitions if m.is_open]
    elif state == "closed":
        petitions = [m for m in petitions if not m.is_open]
    return [m.model_dump(mode="json") for m in petitions]


def get_petition(chamber: Chamber, matter_id: str) -> dict:
    if chamber.phase == 2:
        owner, repo = chamber.upstream_owner_repo()
        return chamber.client()._request(
            "GET", f"/api/v1/repos/{owner}/{repo}/issues/{matter_id}"
        ).json()
    store = matters_mod.load_matters()
    return _get_matter(store, matter_id).model_dump(mode="json")
