"""Beat bindings — the omniscient-narrator vocabulary (task 0034).

ONE table of (pattern → implementation), TWO drivers: behave wraps these
for synchronous tests (features/steps/), the live director's queue
(0034b, polis/sim/queue.py) matches user-submitted scenario beats against
the same patterns.

A binding receives a BeatContext and the regex captures, and raises on
failure (an action that can't be performed, an expectation that doesn't
hold). Expectations return an assertion message on failure instead of
raising when `soft` — no: they raise BeatFailed; the driver decides.
"""
from __future__ import annotations

import json
import re
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional


class BeatFailed(AssertionError):
    pass


@dataclass
class BeatContext:
    """What beats share: the run, plus the story-so-far state."""
    sim: str
    platform: str = "gogs"          # the provisioned product (tags/-D select it)
    petition_id: Optional[str] = None
    bill_branch: Optional[str] = None
    matter_id: Optional[str] = None
    title: Optional[str] = None
    petitioner: Optional[str] = None
    city: Optional[str] = None
    jurisdiction: Optional[str] = None
    data: dict[str, Any] = field(default_factory=dict)


def _runtime(sim: str):
    from .journal import Journal, run_dir
    from .norms import load_norm_file
    from .runtime import Runtime
    sit = run_dir(sim) / "situation.yaml"
    return Runtime(Journal(sim), load_norm_file(sit), sit)


def _chamber(sim: str, username: str):
    import os
    from .. import store
    world = store.load_world()
    city = next(p.member_of.id for p in world.persons if p.username == username)
    if os.environ.get("POLIS_SIM_DIR"):
        # inside an operator container: the sim slices via POLIS_CITY_CONFIG
        from .director import _chamber as director_chamber
        return director_chamber(sim, username, city)
    from ..legislation.chamber import load_chamber
    return load_chamber(as_user=username, city=city)


# --- bindings -----------------------------------------------------------------

def b_provisioned_sim(ctx: BeatContext, jurisdiction: str) -> None:
    """In test mode: provision + seed. In queue mode the sim already
    exists — the queue driver skips this beat after checking the
    jurisdiction matches run.json (see queue.py)."""
    from .. import config, provision
    from .director import RunConfig
    from .journal import new_run, run_dir
    from .norms import load_norm_file, save_norm_file
    provision.up(ctx.sim, platform=ctx.platform)
    new_run(ctx.sim)
    seed = config.WORLD_DIR / "legal" / "norms" / f"{jurisdiction}.yaml"
    save_norm_file(load_norm_file(seed), run_dir(ctx.sim) / "situation.yaml",
                   description=f"bootstrap from {seed.name}")
    RunConfig(run=ctx.sim, jurisdiction=jurisdiction, seed="bdd").save()
    ctx.jurisdiction = jurisdiction


def b_petition(ctx: BeatContext, actor_kind: str, city: str, resource: str) -> None:
    from .director import _Cast
    cast = _Cast()
    petitioner = cast.legislator(city, 0)
    rt = _runtime(ctx.sim)
    ch = _chamber(ctx.sim, petitioner)
    res = rt.file_petition(
        ch, f"Grievance of the {actor_kind}s of {city}",
        f"Our use of the {resource.replace('_', ' ')} is harmed.")
    ctx.petition_id = res.entry.result.get("id")
    ctx.petitioner, ctx.city = petitioner, city
    ctx.data["resource"] = resource
    if not ctx.petition_id:
        raise BeatFailed("the petition was not recorded")


def b_drafts(ctx: BeatContext, title: str, into: str) -> None:
    from ..legislation import bill as bill_mod
    rt = _runtime(ctx.sim)
    ch = _chamber(ctx.sim, ctx.petitioner)
    branch = bill_mod.branch_of(title)
    rt.draft_bill(ch, title, kind="act", into=into)
    slug = branch.removeprefix("bill/")
    rt.amend_bill(ch, branch, [f"{into}/{slug}.md"],
                  f"Answering {ctx.petition_id}.")
    res = rt.introduce_bill(ch, branch, title,
                            f"Answering {ctx.petition_id}.",
                            answering=ctx.petition_id)
    ctx.bill_branch, ctx.title = branch, title
    ctx.matter_id = res.entry.anchors.get("matter")
    if not ctx.matter_id:
        raise BeatFailed("the bill was not introduced")


def b_keeper_ratifies(ctx: BeatContext, remedy: str, norm_id: str) -> None:
    from .director import _Cast, _next_norm_id
    from .norms import Norm
    cast = _Cast()
    rt = _runtime(ctx.sim)
    ch = _chamber(ctx.sim, cast.keeper)
    pet_ch = _chamber(ctx.sim, ctx.petitioner)
    ch.origin = pet_ch.origin
    fed = next(o for o in cast.world.offices if o.id == "federal-archivist")
    ch.offices.append(fed.model_dump(mode="json"))
    contested = rt.situation.get(norm_id)
    new_norm = Norm(
        id=_next_norm_id(rt.situation), rule_form=remedy,
        object=contested.object, aspect=contested.aspect,
        subjects=contested.subjects or ["fisher"],
        beneficiaries=contested.beneficiaries,
        source="statute", source_ref=ctx.matter_id or "")
    rt.ratify(ch, ctx.bill_branch, new_norm=new_norm, supersedes=norm_id)


def b_archive_contains(ctx: BeatContext, text: str) -> None:
    import os
    from .journal import run_dir
    secrets = json.loads((run_dir(ctx.sim) / "secrets.json").read_text())
    platform = secrets.get("platform") or "gogs"
    base = (secrets[f"{platform}_url_internal"] if os.environ.get("POLIS_SIM_DIR")
            else secrets[f"{platform}_url_external"])
    token = secrets.get("admin_token") or ""
    url = base.replace("://", f"://{token}@") + f"/{ctx.sim}-archive/common-law.git"
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(["git", "clone", "-q", "--bare", url, tmp], check=True)
        log = subprocess.run(["git", "-C", tmp, "log", "main"],
                             capture_output=True, text=True).stdout
        names = subprocess.run(["git", "-C", tmp, "show", "--name-only",
                                "--format=", "main"],
                               capture_output=True, text=True).stdout
    if text not in log and text not in names:
        raise BeatFailed(f"'{text}' not found in the archive's main")


def b_norm_superseded(ctx: BeatContext, norm_id: str) -> None:
    from .journal import run_dir
    from .norms import load_norm_file
    ns = load_norm_file(run_dir(ctx.sim) / "situation.yaml")
    status = ns.get(norm_id).status
    if status != "superseded":
        raise BeatFailed(f"{norm_id} is {status}, expected superseded")


def b_petition_answered(ctx: BeatContext) -> None:
    from .. import matters as matters_mod
    store = matters_mod.load_matters()
    bill = next((m for m in store.matters
                 if m.kind == "bill" and m.id == ctx.matter_id), None)
    if bill is None:
        raise BeatFailed("the bill's matter is missing")
    if bill.status != "ratified":
        raise BeatFailed(f"the bill is {bill.status}, expected ratified")
    if ctx.petition_id not in json.dumps(bill.model_dump(mode="json")):
        raise BeatFailed(f"the bill's matter does not link back to {ctx.petition_id}")


# --- the transition arc (task 0053) --------------------------------------------

def b_codify(ctx: BeatContext) -> None:
    """Enact the phase transition (task 0038) and, host-side, erect the
    Mechanical Magistrate's CI (task 0041). The transition is explicit in
    the feature by design — alternate transition scenarios and failures
    can be written against the same vocabulary."""
    import os

    from .. import provision
    from . import transition as transition_mod
    try:
        story = transition_mod.transition(ctx.sim)
    except transition_mod.DirectorError as e:
        raise BeatFailed(str(e)) from e
    if story.status != "enacted":
        raise BeatFailed(f"the transition did not happen: {story.error}")
    if not os.environ.get("POLIS_SIM_DIR"):
        # inside the operator container the host wrapper erects the CI
        try:
            provision.up_woodpecker(ctx.sim)
        except provision.ProvisionError as e:
            raise BeatFailed(f"the CI was not erected: {e}") from e
    ctx.data["edition"] = story.bindings.get("edition")
    ctx.data["transition_acts"] = story.bindings.get("acts")


def b_phase_is(ctx: BeatContext, phase: str) -> None:
    from .. import store
    from .journal import run_dir
    from .norms import load_norm_file
    world_phase = store.load_world().federation.phase
    if str(world_phase) != str(phase):
        raise BeatFailed(f"the civil registry says phase {world_phase}, expected {phase}")
    situation = load_norm_file(run_dir(ctx.sim) / "situation.yaml")
    sit_phase = (situation.federation or {}).get("phase")
    if str(sit_phase) != str(phase):
        raise BeatFailed(f"the situation says phase {sit_phase}, expected {phase}")


def b_corpus_contains(ctx: BeatContext, path: str) -> None:
    from .journal import run_dir
    repo = run_dir(ctx.sim) / "common-law"
    proc = subprocess.run(["git", "-C", str(repo), "cat-file", "-e", f"main:{path}"],
                          capture_output=True, text=True)
    if proc.returncode != 0:
        raise BeatFailed(f"'{path}' is not in the archive's main")


def b_ci_erected(ctx: BeatContext) -> None:
    from .. import provision
    from ..clients import podman
    from ..clients.woodpecker import WoodpeckerClient
    secrets = provision.load_secrets(ctx.sim)
    if not secrets.get("woodpecker_token"):
        raise BeatFailed("the sim's secrets carry no woodpecker token")
    if not podman.container_running(f"{ctx.sim}-woodpecker-server"):
        raise BeatFailed("the woodpecker server is not running")
    base = secrets.get("woodpecker_url_external") or \
        f"http://localhost:{secrets['woodpecker_port']}/ci"
    wc = WoodpeckerClient(token=secrets["woodpecker_token"], base_url=base)
    if wc.lookup_repo(f"{ctx.sim}-archive/common-law") is None:
        raise BeatFailed("the archive repo is not enabled in the CI")


# --- phase-2 platform expectations (gitea serves the request) -------------------

def _platform_repo(ctx: BeatContext):
    """(client, owner, repo) on the federal archive, as the petitioner."""
    user = ctx.petitioner or ctx.data.get("petitioner")
    if not user:
        raise BeatFailed("no petitioner is known — file a petition first")
    ch = _chamber(ctx.sim, user)
    owner, repo = ch.upstream_owner_repo()
    return ch.client(), owner, repo


def _find_pr(client, owner: str, repo: str, branch: Optional[str],
             state: str = "open") -> Optional[dict]:
    prs = client._request("GET", f"/api/v1/repos/{owner}/{repo}/pulls",
                          params={"state": state, "limit": 50}).json()
    for pr in prs if isinstance(prs, list) else []:
        head = pr.get("head") or {}
        if head.get("ref") == branch or str(head.get("label", "")).endswith(f":{branch}"):
            return pr
    return None


def b_petition_is_issue(ctx: BeatContext) -> None:
    if not ctx.petition_id:
        raise BeatFailed("no petition is known — file one first")
    client, owner, repo = _platform_repo(ctx)
    issues = client._request("GET", f"/api/v1/repos/{owner}/{repo}/issues",
                             params={"state": "all", "type": "issues",
                                     "limit": 50}).json()
    if not any(str(i.get("number")) == str(ctx.petition_id)
               for i in issues if isinstance(i, dict)):
        raise BeatFailed(f"petition #{ctx.petition_id} is not a platform issue")


def b_bill_is_pr(ctx: BeatContext) -> None:
    client, owner, repo = _platform_repo(ctx)
    if _find_pr(client, owner, repo, ctx.bill_branch) is None:
        raise BeatFailed(f"no open pull request for '{ctx.bill_branch}'")


def b_bill_pr_merged(ctx: BeatContext) -> None:
    client, owner, repo = _platform_repo(ctx)
    pr = _find_pr(client, owner, repo, ctx.bill_branch, state="all")
    if pr is None:
        raise BeatFailed(f"no pull request was ever opened for '{ctx.bill_branch}'")
    if not pr.get("merged"):
        raise BeatFailed(f"the pull request is not merged (state: {pr.get('state')})")


def b_jurist_approves(ctx: BeatContext) -> None:
    from .director import _Cast
    rt = _runtime(ctx.sim)
    jurist = _Cast().jurist(0)
    ch = _chamber(ctx.sim, jurist)
    rt.scrutinize(ch, ctx.bill_branch, "approve",
                  "Consistent with the codified procedure.")


def _ci_verdict(ctx: BeatContext, expected: str, timeout: int = 300) -> None:
    import time
    client, owner, repo = _platform_repo(ctx)
    deadline = time.time() + timeout
    status: Optional[str] = None
    while time.time() < deadline:
        pr = _find_pr(client, owner, repo, ctx.bill_branch)
        sha = ((pr or {}).get("head") or {}).get("sha")
        if sha:
            st = client._request(
                "GET", f"/api/v1/repos/{owner}/{repo}/commits/{sha}/status").json()
            status = st.get("state")
            if status in ("success", "failure", "error"):
                break
        time.sleep(10)
    if status != expected:
        raise BeatFailed(
            f"the Mechanical Magistrate's verdict is {status!r}, expected {expected!r}")


def b_ci_approves(ctx: BeatContext) -> None:
    _ci_verdict(ctx, "success")


def b_ci_rejects(ctx: BeatContext) -> None:
    _ci_verdict(ctx, "failure")


# --- the table ------------------------------------------------------------------

@dataclass
class Binding:
    pattern: re.Pattern
    fn: Callable
    template: str                       # the human form, for error messages


def _rx(template: str) -> re.Pattern:
    """'"quoted"' and {placeholders} become captures; rest is literal."""
    out, i = [], 0
    for m in re.finditer(r'"[^"]*"|\{(\w+)\}', template):
        out.append(re.escape(template[i:m.start()]))
        out.append("(.+?)")
        i = m.end()
    out.append(re.escape(template[i:]))
    return re.compile("^" + "".join(out) + "$", re.IGNORECASE)


BINDINGS: list[Binding] = [
    Binding(_rx('a provisioned sim seeded from {j}'), b_provisioned_sim,
            'a provisioned sim seeded from "<jurisdiction>"'),
    Binding(_rx('a petition of the {a}s of {c} about the {r}'), b_petition,
            'a petition of the <actor-kind>s of <city> about the <resource>'),
    Binding(_rx('the legislator drafts {t} into {d}'), b_drafts,
            'the legislator drafts "<title>" into <corpus-dir>'),
    Binding(_rx('the Keeper ratifies it with remedy {r} superseding {n}'),
            b_keeper_ratifies,
            'the Keeper ratifies it with remedy "<rule-form>" superseding "<norm-id>"'),
    Binding(_rx('the archive main contains {t}'), b_archive_contains,
            'the archive main contains "<text>"'),
    Binding(_rx('norm {n} is superseded in the situation'), b_norm_superseded,
            'norm "<norm-id>" is superseded in the situation'),
    Binding(_rx('the docket shows the petition is answered'), b_petition_answered,
            'the docket shows the petition is answered'),
    # --- the transition arc (0053) ------------------------------------------
    Binding(_rx('the federation codifies its machinery'), b_codify,
            'the federation codifies its machinery'),
    Binding(_rx('the federation operates in phase {p}'), b_phase_is,
            'the federation operates in phase <1|2>'),
    Binding(_rx('the corpus contains {p}'), b_corpus_contains,
            'the corpus contains "<path>"'),
    Binding(_rx("the Mechanical Magistrate's CI is erected"), b_ci_erected,
            "the Mechanical Magistrate's CI is erected"),
    Binding(_rx('the petition is a real issue on the platform'), b_petition_is_issue,
            'the petition is a real issue on the platform'),
    Binding(_rx('the bill is a real pull request on the platform'), b_bill_is_pr,
            'the bill is a real pull request on the platform'),
    Binding(_rx('the bill\'s pull request is merged'), b_bill_pr_merged,
            "the bill's pull request is merged"),
    Binding(_rx('the jurist approves the bill'), b_jurist_approves,
            'the jurist approves the bill'),
    Binding(_rx('the Mechanical Magistrate approves the bill'), b_ci_approves,
            'the Mechanical Magistrate approves the bill'),
    Binding(_rx('the Mechanical Magistrate rejects the bill'), b_ci_rejects,
            'the Mechanical Magistrate rejects the bill'),
]

SIM_CREATION = BINDINGS[0]      # the queue driver treats this beat specially


def _unquote(s: str) -> str:
    return s[1:-1] if len(s) >= 2 and s[0] == s[-1] and s[0] in "\"'" else s


def match_beat(text: str) -> tuple[Optional[Binding], tuple]:
    for b in BINDINGS:
        m = b.pattern.match(text.strip())
        if m:
            return b, tuple(_unquote(g) for g in m.groups())
    return None, ()


def execute_beat(ctx: BeatContext, text: str) -> None:
    """Match and run one beat; BeatFailed/KeyError/etc. propagate."""
    binding, groups = match_beat(text)
    if binding is None:
        raise BeatFailed(f"no binding for: {text!r}")
    binding.fn(ctx, *groups)
