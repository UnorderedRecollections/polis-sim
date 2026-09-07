"""Bills — proposed enactments moving through the legislative machinery.

Life cycle (§3, §5, §6, §10, §11):
  draft      — a branch opens: an alternative line of legal development
  amend      — commits: archival acts recording changes, with justification
  introduce  — a pull request: the formal petition for incorporation
  debate     — comments: deliberation
  scrutinize — reviews: institutional scrutiny (customary, phase 1)
  ratify     — merge: enactment into the authoritative history
  consolidate— squash merge: a messy process codified into one coherent act
  reject     — close unmerged: the petition fails

Ratification is jurisdiction-checked: a Local Archivist may ratify only
bills touching municipal/<city>/**; cross-city bills require the Keeper of
the Federal Rolls.
"""
from __future__ import annotations

import json
import re

from .. import matters as matters_mod
from ..clients.gogs import GogsError
from . import documents, gitcmd
from .chamber import Chamber, ChamberError
from .plan import Plan


def branch_of(title: str) -> str:
    slug = re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", title.lower())).strip("-")
    return f"bill/{slug}"


def _find_pr(chamber: Chamber, branch: str) -> dict | None:
    owner, repo = chamber.upstream_owner_repo()
    prs = chamber.client()._request(
        "GET", f"/api/v1/repos/{owner}/{repo}/pulls", params={"state": "open", "limit": 50}
    ).json()
    for pr in prs if isinstance(prs, list) else []:
        head = pr.get("head") or {}
        if head.get("ref") == branch or str(head.get("label", "")).endswith(f":{branch}"):
            return pr
    return None


def _require_petition(chamber: Chamber, branch: str):
    """The open matter for a bill: a platform PR in phase 2, a matter-store
    entry in phase 1 (the institutions keep their own proceedings)."""
    if chamber.platform == "gitea":
        pr = _find_pr(chamber, branch)
        if pr is None:
            raise ChamberError(f"no open petition found for '{branch}' — has the bill been introduced?")
        return pr
    matter = matters_mod.load_matters().find_by_branch(branch)
    if matter is None:
        raise ChamberError(f"no open petition found for '{branch}' — has the bill been introduced?")
    return matter


def _record_event(chamber: Chamber, matter, event: str, detail: str = "",
                  status: str | None = None) -> None:
    """Enter an event into the matter's record (the proceedings are docketed)."""
    store = matters_mod.load_matters()
    m = store.find(matter.id)
    m.events.append(matters_mod.MatterEvent(
        event=event, actor=chamber.actor_username, detail=detail
    ))
    if status:
        m.status = status
    matters_mod.save_matters(store)


# --- drafting ---------------------------------------------------------------

def draft(chamber: Chamber, title: str, base: str = "main",
          kind: str | None = None, into: str | None = None,
          target: str | None = None, answering: str | None = None) -> Plan:
    branch = branch_of(title)
    plan = Plan(act=f"draft the bill “{title}”", actor=chamber.actor_label)
    plan.add(
        machinery=gitcmd.cmd_string(chamber.repo_dir, "checkout", "-b", branch, base),
        legal="a line of legal development opens — an alternative history diverging "
              "from the recognized corpus (§3)",
        run=lambda: gitcmd.run(chamber.repo_dir, "checkout", "-b", branch, base),
    )
    if kind:
        if not into:
            raise ChamberError("drafting a document requires --into (the jurisdictional directory)")
        if kind not in documents.KINDS:
            raise ChamberError(f"unknown document kind '{kind}' (choose from: {', '.join(documents.KINDS)})")
        path = chamber.repo_dir / into / documents.filename_for(title)

        def run_scaffold():
            documents.scaffold(
                path, kind, title=title, jurisdiction=into,
                origin_city=chamber.city_id, proposer=chamber.actor_username,
                answering=answering, target=target,
            )

        plan.add(
            machinery=f"write {into}/{documents.filename_for(title)} from template {kind}.md "
                      f"(status: draft)",
            legal="the draft takes the form of a legal document — machine-readable "
                  "particulars above, human-readable law below",
            run=run_scaffold,
        )
    return plan


def amend(chamber: Chamber, bill: str, files: list[str], justification: str, all_files: bool = False) -> Plan:
    name, email = chamber.author
    plan = Plan(act=f"amend the bill “{bill}”", actor=chamber.actor_label)
    plan.add(
        machinery=gitcmd.cmd_string(chamber.repo_dir, "checkout", bill),
        legal="return to the bill's line of development",
        run=lambda: gitcmd.run(chamber.repo_dir, "checkout", bill),
    )
    add_args = ("add", "-A") if all_files else ("add", "--", *files)
    plan.add(
        machinery=gitcmd.cmd_string(chamber.repo_dir, *add_args),
        legal="the proposed text is presented for the record",
        run=lambda: gitcmd.run(chamber.repo_dir, *add_args),
    )
    commit_args = ("-c", f"user.name={name}", "-c", f"user.email={email}", "commit", "-m", justification)
    plan.add(
        machinery=gitcmd.cmd_string(chamber.repo_dir, *commit_args),
        legal="a formal archival act records the change, with its justification (§1)",
        run=lambda: gitcmd.run(chamber.repo_dir, *commit_args),
    )
    return plan


# --- petition ---------------------------------------------------------------

def introduce(chamber: Chamber, bill: str, title: str, body: str,
              answering: str | None = None) -> Plan:
    origin_owner, _ = chamber.origin_owner_repo()
    up_owner, up_repo = chamber.upstream_owner_repo()

    def run_push():
        # the machinery records the lifecycle: draft → proposed
        changed = documents.flip_status(chamber.repo_dir, _changed_files(chamber, bill), "proposed")
        if changed:
            name, email = chamber.author
            gitcmd.run(chamber.repo_dir, "add", "--", *changed)
            gitcmd.run(chamber.repo_dir,
                       "-c", f"user.name={name}", "-c", f"user.email={email}",
                       "commit", "-m", f"The petition is entered: {title} stands proposed")
        gitcmd.run(chamber.repo_dir, "push", chamber.git_remote_url("origin"), f"{bill}:{bill}")

    plan = Plan(act=f"introduce the bill “{title}”", actor=chamber.actor_label)
    plan.add(
        machinery=f"git -C {chamber.repo_dir} commit -m '…stands proposed' && push origin {bill}:{bill}",
        legal="the machinery flips status: draft → proposed; "
              "the draft is lodged with the city's archive",
        run=run_push,
    )
    if chamber.platform == "gitea":
        head = bill if origin_owner == up_owner else f"{origin_owner}:{bill}"
        payload = {"head": head, "base": "main", "title": title, "body": body}

        def run_petition():
            return chamber.client()._request(
                "POST", f"/api/v1/repos/{up_owner}/{up_repo}/pulls", json=payload
            ).json()

        plan.add(
            machinery=f"POST /api/v1/repos/{up_owner}/{up_repo}/pulls  {json.dumps(payload)}",
            legal="a formal petition asks that this line of development be incorporated "
                  "into the authoritative legal corpus (§5)",
            run=run_petition,
        )
    else:
        def run_petition():
            store = matters_mod.load_matters()
            if store.find_by_branch(bill):
                raise ChamberError(f"'{bill}' is already before the federation")
            if answering:
                try:
                    store.find(answering)
                except KeyError as e:
                    raise ChamberError(e.args[0]) from e
            matter = store.new_matter(
                "bill", title, proposer=chamber.actor_username,
                city=chamber.city_id, branch=bill, answering=answering,
            )
            matter.events.append(matters_mod.MatterEvent(
                event="introduced", actor=chamber.actor_username, detail=body
            ))
            matters_mod.save_matters(store)
            return matter

        plan.add(
            machinery=f"matters.json: enter matter (kind=bill, branch={bill}, "
                      f"event=introduced by {chamber.actor_username})",
            legal="a formal petition asks that this line of development be incorporated "
                  "into the authoritative legal corpus — the proceedings are docketed "
                  "by the institutions, not by the archive host (§5, phase 1)",
            run=run_petition,
        )
    return plan


def debate(chamber: Chamber, bill: str, body: str) -> Plan:
    def run():
        petition = _require_petition(chamber, bill)
        if chamber.platform == "gitea":
            owner, repo = chamber.upstream_owner_repo()
            return chamber.client()._request(
                "POST", f"/api/v1/repos/{owner}/{repo}/issues/{petition['number']}/comments",
                json={"body": body},
            ).json()
        _record_event(chamber, petition, "debated", detail=body, status="deliberating")
        return petition.id

    machinery = (
        "POST …/issues/<petition>/comments" if chamber.platform == "gitea"
        else f"matters.json: append event (debated, {chamber.actor_username})"
    )
    return Plan(act=f"debate the bill “{bill}”", actor=chamber.actor_label).add(
        machinery=machinery,
        legal="deliberation upon the petition, entered into the record",
        run=run,
    )


def scrutinize(chamber: Chamber, bill: str, verdict: str, body: str) -> Plan:
    """Institutional scrutiny. Phase 1 is customary: the finding is recorded
    as a structured comment (gogs has no formal review machinery — which is
    historically accurate for this era)."""
    if verdict not in ("approve", "request-changes"):
        raise ChamberError("verdict must be 'approve' or 'request-changes'")
    stamp = "SCRUTINY — APPROVED" if verdict == "approve" else "SCRUTINY — CHANGES REQUESTED"
    text = f"{stamp}\n\n{body}" if body else stamp

    def run():
        petition = _require_petition(chamber, bill)
        if chamber.platform == "gitea":
            owner, repo = chamber.upstream_owner_repo()
            return chamber.client()._request(
                "POST", f"/api/v1/repos/{owner}/{repo}/issues/{petition['number']}/comments",
                json={"body": text},
            ).json()
        _record_event(
            chamber, petition,
            "scrutinized: approved" if verdict == "approve" else "scrutinized: changes requested",
            detail=body, status="scrutinized",
        )
        return petition.id

    machinery = (
        f"POST …/issues/<petition>/comments  {json.dumps({'body': text})}"
        if chamber.platform == "gitea"
        else f"matters.json: append event ({stamp.lower()}, {chamber.actor_username})"
    )
    return Plan(act=f"scrutinize the bill “{bill}” ({verdict})", actor=chamber.actor_label).add(
        machinery=machinery,
        legal="institutional scrutiny of the proposed legislation, entered into the record (§6)",
        run=run,
    )


# --- ratification -------------------------------------------------------------

def _merge_powers(chamber: Chamber) -> list[str]:
    """Path patterns the actor may ratify, from the offices they hold."""
    held = {o["id"]: o for o in chamber.offices}
    patterns: list[str] = []
    for office_id in chamber.actor.get("occupies", []):
        for power in (held.get(office_id) or {}).get("powers", []):
            if power == "merge:main":
                patterns.append("**")  # the Keeper may ratify cross-city law
            elif power.startswith("merge:"):
                patterns.append(power.removeprefix("merge:"))
    return patterns


def _check_jurisdiction(chamber: Chamber, changed_files: list[str]) -> None:
    patterns = _merge_powers(chamber)
    if not patterns:
        raise ChamberError(
            f"{chamber.actor_username} holds no archival office — ratification is a "
            "jurisdictional act, not a political one"
        )
    if "**" in patterns:
        return

    def within(path: str) -> bool:
        return any(
            path == p or (p.endswith("/**") and path.startswith(p[:-2]))
            for p in patterns
        )

    for f in changed_files:
        if not within(f):
            raise ChamberError(
                f"ultra vires: '{f}' lies outside the jurisdiction of "
                f"{chamber.actor_username}'s office ({', '.join(patterns)}) — "
                "only the Keeper of the Federal Rolls may ratify cross-city law"
            )


def _changed_files(chamber: Chamber, bill: str) -> list[str]:
    out = gitcmd.run(chamber.repo_dir, "diff", "--name-only", "main..." + bill)
    return [f for f in out.splitlines() if f]


def _merge_via_api(chamber: Chamber, pr_index: int, method: str) -> None:
    owner, repo = chamber.upstream_owner_repo()
    chamber.client()._request(
        "POST", f"/api/v1/repos/{owner}/{repo}/pulls/{pr_index}/merge", json={"Do": method}
    )


def _incorporate_locally(chamber: Chamber, method: str, act_title: str | None = None,
                         changed_files: list[str] | None = None) -> None:
    """The archivist incorporates by their own hand and lodges the new history —
    the customary form of enactment, and the fallback when the platform knows
    no merge route. The machinery then records the lifecycle: proposed → enacted."""
    gitcmd.run(chamber.repo_dir, "checkout", "main")
    name, email = chamber.author
    if method == "squash":
        gitcmd.run(chamber.repo_dir, "merge", "--squash", "FETCH_HEAD")
        if changed_files:
            documents.flip_status(chamber.repo_dir, changed_files, "enacted")
            gitcmd.run(chamber.repo_dir, "add", "-A")
        gitcmd.run(chamber.repo_dir,
                   "-c", f"user.name={name}", "-c", f"user.email={email}",
                   "commit", "-m", act_title or "Consolidated Act")
    else:
        # one archival act: incorporation and the status flip form a single
        # merge commit, so a repeal (revert -m 1) undoes the enactment whole
        gitcmd.run(chamber.repo_dir, "merge", "--no-ff", "--no-commit", "FETCH_HEAD")
        if changed_files:
            flipped = documents.flip_status(chamber.repo_dir, changed_files, "enacted")
            if flipped:
                gitcmd.run(chamber.repo_dir, "add", "--", *flipped)
        gitcmd.run(chamber.repo_dir,
                   "-c", f"user.name={name}", "-c", f"user.email={email}",
                   "commit", "--no-edit")
    gitcmd.run(chamber.repo_dir, "push", chamber.git_remote_url("upstream"), "main")


def _decide(chamber: Chamber, petition, status: str, event: str, detail: str = "") -> str:
    """Enter the order into the record: close the petition as decided."""
    if chamber.platform == "gitea":
        owner, repo = chamber.upstream_owner_repo()
        chamber.client()._request(
            "PATCH", f"/api/v1/repos/{owner}/{repo}/pulls/{petition['number']}",
            json={"state": "closed"},
        )
        return str(petition["number"])
    _record_event(chamber, petition, event, detail=detail, status=status)
    return petition.id


def ratify(chamber: Chamber, bill: str) -> Plan:
    def run():
        gitcmd.run(chamber.repo_dir, "fetch", chamber.git_remote_url("upstream"), "main")
        gitcmd.run(chamber.repo_dir, "fetch", chamber.git_remote_url("origin"), bill)
        changed = _changed_files(chamber, bill)
        _check_jurisdiction(chamber, changed)
        petition = _require_petition(chamber, bill)
        if chamber.platform == "gitea":
            try:
                _merge_via_api(chamber, petition["number"], "merge")
            except GogsError:
                _incorporate_locally(chamber, "merge", changed_files=changed)
        else:
            _incorporate_locally(chamber, "merge", changed_files=changed)
        return _decide(chamber, petition, "ratified", "enacted")

    merge_step = (
        "POST …/pulls/<petition>/merge  {\"Do\": \"merge\"}"
        if chamber.platform == "gitea"
        else "git -C <repo> merge --no-ff FETCH_HEAD && git push upstream main  "
             "(customary incorporation — the apparatus has no merge route)"
    )
    plan = Plan(act=f"ratify the bill “{bill}”", actor=chamber.actor_label)
    plan.add(machinery=f"git -C {chamber.repo_dir} fetch origin {bill} && git fetch upstream main",
             legal="the line of development is examined")
    plan.add(machinery=f"git -C {chamber.repo_dir} diff --name-only main...{bill}",
             legal="jurisdiction is verified: does every amended path lie within the "
                   "archivist's authority?")
    plan.add(machinery=merge_step,
             legal="formal incorporation of the proposed development into the "
                   "authoritative history — enactment (§10)",
             run=run)
    return plan


def consolidate(chamber: Chamber, bill: str, act_title: str) -> Plan:
    def run():
        gitcmd.run(chamber.repo_dir, "fetch", chamber.git_remote_url("upstream"), "main")
        gitcmd.run(chamber.repo_dir, "fetch", chamber.git_remote_url("origin"), bill)
        changed = _changed_files(chamber, bill)
        _check_jurisdiction(chamber, changed)
        petition = _require_petition(chamber, bill)
        if chamber.platform == "gitea":
            try:
                _merge_via_api(chamber, petition["number"], "squash")
            except GogsError:
                _incorporate_locally(chamber, "squash", act_title, changed_files=changed)
        else:
            _incorporate_locally(chamber, "squash", act_title, changed_files=changed)
        return _decide(chamber, petition, "ratified", "enacted",
                       detail=f"codified as “{act_title}”")

    merge_step = (
        "POST …/pulls/<petition>/merge  {\"Do\": \"squash\"}"
        if chamber.platform == "gitea"
        else "git -C <repo> merge --squash FETCH_HEAD && git commit && git push upstream main  "
             "(customary codification — the apparatus has no merge route)"
    )
    plan = Plan(act=f"codify the bill “{bill}” as “{act_title}”", actor=chamber.actor_label)
    plan.add(machinery=merge_step,
             legal="a messy legislative process is consolidated into a single coherent "
                   "legal act — codification (§11)",
             run=run)
    return plan


def reject(chamber: Chamber, bill: str) -> Plan:
    def run():
        petition = _require_petition(chamber, bill)
        return _decide(chamber, petition, "rejected", "rejected")

    machinery = (
        "PATCH …/pulls/<petition>  {\"state\": \"closed\"}"
        if chamber.platform == "gitea"
        else "matters.json: status = rejected (+ event)"
    )
    return Plan(act=f"reject the bill “{bill}”", actor=chamber.actor_label).add(
        machinery=machinery,
        legal="the petition fails; the proposed history is not incorporated",
        run=run,
    )


# --- inspection ---------------------------------------------------------------

def list_bills(chamber: Chamber, state: str = "open") -> list[dict]:
    if chamber.platform == "gitea":
        owner, repo = chamber.upstream_owner_repo()
        prs = chamber.client()._request(
            "GET", f"/api/v1/repos/{owner}/{repo}/pulls", params={"state": state, "limit": 50}
        ).json()
        return prs if isinstance(prs, list) else []
    store = matters_mod.load_matters()
    bills = [m for m in store.matters if m.kind == "bill"]
    if state == "open":
        bills = [m for m in bills if m.is_open]
    elif state == "closed":
        bills = [m for m in bills if not m.is_open]
    return [
        {**m.model_dump(mode="json"), "head": {"ref": m.branch}, "user": {"username": m.proposer}}
        for m in bills
    ]
