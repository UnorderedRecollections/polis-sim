"""The director — drives a simulation run forward (docs/design/director.md).

One drive step = one whole story, end to end:

    situation → charged candidates → seeded selection → casting → remedy
    → execution via runtime.enact() block by block → stories.json + a
    `story` anchor in the journal.

Determinism: all randomness derives from the run's seed (run.json) keyed
by the story index — `rng = Random(f"{seed}:{n}")`. Replay consumes the
journal, never live input.

v1 implements the resource_dispute template and the `seeded` selector;
policies.yaml is read (default: seeded) so per-party policies can land
without redesign.
"""
from __future__ import annotations

import json
import os
import random
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Optional

from .. import store
from ..legislation import archive as archive_mod
from ..legislation.chamber import Chamber, load_chamber
from . import events, legaldata
from .journal import Journal, JournalEntry, _utcnow, run_dir
from .norms import Norm, NormObject, load_norm_file
from .runtime import Runtime


class DirectorError(RuntimeError):
    pass


# --- run config -----------------------------------------------------------------

@dataclass
class RunConfig:
    run: str
    jurisdiction: str
    seed: str
    created_at: str = ""

    @classmethod
    def load(cls, run_id: str) -> "RunConfig":
        path = run_dir(run_id) / "run.json"
        if not path.exists():
            raise DirectorError(
                f"run '{run_id}' has no run.json — create it with "
                "`polis sim new <run> --situation <seed.yaml> [--jurisdiction …]`")
        return cls(**json.loads(path.read_text(encoding="utf-8")))

    def save(self) -> None:
        (run_dir(self.run) / "run.json").write_text(
            json.dumps(asdict(self), indent=2), encoding="utf-8")


# --- story records (stories.json — the mutable story state) ---------------------

@dataclass
class Story:
    id: str
    template: str
    status: str                      # in_progress | enacted | failed | skipped
    bindings: dict[str, Any] = field(default_factory=dict)
    cast: dict[str, str] = field(default_factory=dict)
    matter: Optional[str] = None
    entries: list[int] = field(default_factory=list)
    error: Optional[str] = None
    started_at: str = ""
    finished_at: str = ""


def _stories_path(run_id: str) -> Path:
    return run_dir(run_id) / "stories.json"


def load_stories(run_id: str) -> list[Story]:
    path = _stories_path(run_id)
    if not path.exists():
        return []
    return [Story(**s) for s in json.loads(path.read_text(encoding="utf-8"))]


def _save_stories(run_id: str, stories: list[Story]) -> None:
    _stories_path(run_id).write_text(
        json.dumps([asdict(s) for s in stories], indent=2), encoding="utf-8")


# --- casting (party → person; docs/design/director.md §4) ------------------------

class _Cast:
    """The world's roster as the director needs it (read-only)."""

    def __init__(self):
        world = store.load_world()
        self.world = world
        self.juridical = {o.occupant for o in world.offices
                          if o.kind in ("juridical", "mechanical") and o.occupant}
        self.keeper = next((o.occupant for o in world.offices
                            if o.id == "federal-archivist"), None)
        self.jurists = [o.occupant for o in sorted(world.offices, key=lambda o: o.id)
                        if o.id.startswith("council-jurist-") and o.occupant]
        self.experts = {o.id.removeprefix("expert-"): o.occupant
                        for o in world.offices
                        if o.id.startswith("expert-") and o.occupant}
        self.city_of = {p.username: p.member_of.id for p in world.persons}
        self.citizens: dict[str, list[str]] = {}
        for p in world.persons:
            self.citizens.setdefault(p.member_of.id, []).append(p.username)

    def legislator(self, city: str, story_n: int) -> str:
        """A citizen-legislator of the city (juridical officers excluded),
        rotated by story index."""
        pool = sorted(u for u in self.citizens.get(city, [])
                      if u not in self.juridical)
        if not pool:
            raise DirectorError(f"no free legislator in {city}")
        return pool[story_n % len(pool)]

    def jurist(self, story_n: int) -> str:
        if not self.jurists:
            raise DirectorError("no constitutional jurists seated")
        return self.jurists[story_n % len(self.jurists)]


# --- chambers ---------------------------------------------------------------------

def _chamber(run_id: str, username: str, city: str) -> Chamber:
    """A chamber inside the sim: the sim slice (container mode — no
    host-swap) and the run's shared working clone."""
    rd = run_dir(run_id)
    os.environ["POLIS_CITY_CONFIG"] = str(rd / "cities" / f"{city}.json")
    return load_chamber(as_user=username, city=city,
                        repo_dir=str(rd / "common-law"))


# --- the drive loop -----------------------------------------------------------------

def drive(run_id: str, steps: int = 1) -> list[Story]:
    cfg = RunConfig.load(run_id)
    rd = run_dir(run_id)
    jdata = legaldata.load_jurisdictions().get(cfg.jurisdiction)
    if jdata is None:
        raise DirectorError(f"unknown jurisdiction '{cfg.jurisdiction}'")
    sit_path = rd / "situation.yaml"
    if not sit_path.exists():
        raise DirectorError(f"run '{run_id}' has no situation.yaml")
    rt = Runtime(Journal(run_id), load_norm_file(sit_path), sit_path)
    cast = _Cast()
    stories = load_stories(run_id)
    new: list[Story] = []

    # one-time preamble: the Keeper obtains the archive (the working clone
    # every chamber in this run shares)
    if not (rd / "common-law" / ".git").exists():
        keeper_city = cast.city_of[cast.keeper]
        ch = _chamber(run_id, cast.keeper, keeper_city)
        rt.enact(cast.keeper, "archive.obtain", archive_mod.obtain(ch),
                 params={}, chamber=ch)

    for _ in range(steps):
        # user-submitted scenarios first (0034b): one action beat per
        # scenario per step; the federation's own stories continue around
        # them — and the situation they change
        from . import queue as queue_mod
        queue_mod.service(run_id)

        n = len(stories)
        rng = random.Random(f"{cfg.seed}:{n}")
        story = Story(id=f"story-{n + 1:04d}", template="resource_dispute",
                      status="in_progress", started_at=_utcnow())
        prev = stories[-1] if stories else None
        try:
            _execute_story(rt, cfg, jdata, cast, rng, story, n, prev)
            if story.status == "in_progress":
                story.status = "enacted"
        except Exception as e:                      # a failed story is a true story
            story.status = "failed"
            story.error = str(e)[:500]
            rt.observe("director", f"{story.id} failed", {"error": story.error})
        story.finished_at = _utcnow()
        stories.append(story)
        _save_stories(run_id, stories)
        new.append(story)
        if story.status == "skipped":
            break            # nothing left to grieve — the situation is settled
    return new


def _execute_story(rt: Runtime, cfg: RunConfig, jdata, cast: _Cast,
                   rng: random.Random, story: Story, n: int,
                   prev: Optional[Story] = None) -> None:
    run_id = cfg.run
    situation = rt.situation
    assert situation is not None

    # --- selection (seeded) ------------------------------------------------
    candidates = [c for c in events.charged_candidates(jdata, situation) if c.charged]
    if not candidates:
        story.status = "skipped"
        rt.observe("director", f"{story.id} skipped", {"reason": "no charged candidates"})
        return
    # variety: don't re-tell the immediately previous story if alternatives exist
    if prev and prev.bindings and len(candidates) > 1:
        fresh = [c for c in candidates
                 if (c.actor.label(), c.object_kind, c.verb)
                 != (prev.bindings.get("respondent"), prev.bindings.get("resource"),
                     prev.bindings.get("verb"))]
        if fresh:
            candidates = fresh
    cand = rng.choice(candidates)
    hit = cand.harmed[0]
    claimant = events.Party(actor_kind=hit.holding.holder.actor_kind,
                            city=hit.holding.holder.city)
    respondent = cand.actor
    contested_id = hit.norms_in_question[0] if hit.norms_in_question else None
    contested = situation.get(contested_id) if contested_id else None

    # --- remedy: the rule form incompatible with the contested norm ---------
    remedy, aspect = _pick_remedy(jdata, contested, rng, prev)
    base_title = (f"{cand.object_kind.replace('_', ' ').title()} "
                  f"{remedy.replace('_', ' ').title()} Act")
    story.bindings = {
        "claimant": claimant.label(), "respondent": respondent.label(),
        "resource": cand.object_kind, "verb": cand.verb, "impact": cand.impact,
        "contested_norm": contested_id, "remedy": remedy,
        "rng_key": f"{cfg.seed}:{n}",
    }

    # --- casting -------------------------------------------------------------
    claimant_city = claimant.city or respondent.city
    if not claimant_city:
        raise DirectorError("story has no city to petition from")
    petitioner = cast.legislator(claimant_city, n)
    jurist = cast.jurist(n)
    keeper = cast.keeper
    expert = cast.experts.get(jdata.corpus_dir) if jdata.corpus_dir else None
    story.cast = {"petitioner": petitioner, "jurist": jurist, "keeper": keeper or ""}
    if expert:
        story.cast["expert"] = expert

    pet_ch = _chamber(run_id, petitioner, claimant_city)
    jur_ch = _chamber(run_id, jurist, cast.city_of[jurist])
    keeper_city = cast.city_of[keeper]
    keep_ch = _chamber(run_id, keeper, keeper_city)
    keep_ch.origin = pet_ch.origin   # the bill is lodged where it was developed
    # the Keeper's federal office never enters a city slice (chamber.py §); the
    # container chamber must be told of it explicitly — merge:main is what lets
    # him ratify cross-city law
    fed = next(o for o in cast.world.offices if o.id == "federal-archivist")
    keep_ch.offices.append(fed.model_dump(mode="json"))

    # a remedy may be legislated more than once in an epoch — the second
    # Quota Act is a new act, not a collision. Number the title until the
    # branch is free (same slug rule as the machinery's branch_of).
    from ..legislation import bill as bill_mod
    from ..legislation import gitcmd
    into = jdata.corpus_dir or f"municipal/{claimant_city}"
    title, no = base_title, 2
    while True:
        branch = bill_mod.branch_of(title)
        try:
            remote = gitcmd.run(pet_ch.repo_dir, "ls-remote",
                                pet_ch.git_remote_url("origin"), f"refs/heads/{branch}")
        except Exception:
            remote = ""
        try:
            local = gitcmd.run(pet_ch.repo_dir, "show-ref", "--verify",
                               f"refs/heads/{branch}")
        except Exception:
            local = ""
        if not remote.strip() and not local.strip():
            break
        title, no = f"{base_title} (No. {no})", no + 1
    story.bindings["title"] = title

    def seq() -> int:
        return rt.journal.next_seq() - 1

    # --- the story blocks (template: resource_dispute) ------------------------
    rt.observe(petitioner, "establish_traditional_use",
               {"holding": hit.holding.id, "under": contested_id,
                "party": claimant.label()})
    story.entries.append(seq())
    rt.observe(respondent.label(), "introduce_competing_claim",
               {"verb": cand.verb, "impact": cand.impact, "object": cand.object_kind})
    story.entries.append(seq())

    grievance = (f"Grievance of the {claimant.actor_kind}s of {claimant_city}")
    body = (f"The {respondent.label()}s {cand.verb} the "
            f"{cand.object_kind.replace('_', ' ')} ({cand.impact}); "
            f"our use under {contested_id or 'custom'} is harmed.")
    res = rt.file_petition(pet_ch, grievance, body)
    petition_id = res.entry.result.get("id")
    story.entries.append(seq())
    rt.observe("director", "assign_jurisdiction",
               {"jurisdiction": cfg.jurisdiction, "contested_norm": contested_id})
    story.entries.append(seq())

    rt.draft_bill(pet_ch, title, kind="act", into=into)
    story.entries.append(seq())
    slug = branch.removeprefix("bill/")
    doc = f"{into}/{slug}.md"
    justification = (f"Establish {remedy.replace('_', ' ')} over the "
                     f"{cand.object_kind.replace('_', ' ')}, answering {petition_id}; "
                     f"{contested_id or 'the open custom'} gives way.")
    rt.amend_bill(pet_ch, branch, [doc], justification)
    story.entries.append(seq())
    res = rt.introduce_bill(pet_ch, branch, title,
                            justification, answering=petition_id)
    story.matter = res.entry.anchors.get("matter")
    story.entries.append(seq())

    if expert:
        ex_ch = _chamber(run_id, expert, cast.city_of[expert])
        rt.scrutinize(ex_ch, branch, "approve",
                      f"Within {cfg.jurisdiction} custom, {remedy} is a known remedy.")
        story.entries.append(seq())
    else:
        rt.observe("director", "jurisdictional_review_skipped",
                   {"reason": f"no federal expert exists for {cfg.jurisdiction} "
                              "— its acts are municipal in form"})
        story.entries.append(seq())

    rt.scrutinize(jur_ch, branch, "approve",
                  "The remedy is compatible with the Concord's common law.")
    story.entries.append(seq())
    rt.observe("director", "approval", {"matter": story.matter})
    story.entries.append(seq())

    new_norm = Norm(
        id=_next_norm_id(situation), rule_form=remedy,
        object=NormObject(kind=cand.object_kind, type="resource"),
        aspect=aspect, subjects=[respondent.actor_kind],
        beneficiaries=[claimant.actor_kind],
        source="statute", source_ref=story.matter or "",
    )
    rt.ratify(keep_ch, branch, new_norm=new_norm, supersedes=contested_id)
    story.entries.append(seq())

    # --- the story anchor (kind=anchor — proof, links the beats) --------------
    rt.journal.append(JournalEntry(
        seq=rt.journal.next_seq(), ts=_utcnow(), kind="anchor",
        actor="director", action="story",
        params={"story": story.id, "template": story.template,
                "bindings": story.bindings, "cast": story.cast},
        result={"matter": story.matter, "entries": story.entries},
    ))


def _pick_remedy(jdata, contested: Optional[Norm], rng: random.Random,
                 prev: Optional[Story] = None) -> tuple[str, str]:
    """The harmed party wants the rule form incompatible with the norm that
    hurts them (docs/design/director.md §5). Fallback: any other form.
    Variety: not the immediately previous remedy if alternatives exist."""
    forms: list[str] = []
    aspect = contested.aspect if contested else "access_right"
    if contested is not None:
        for rule in jdata.incompatibilities:
            if contested.rule_form in rule.between:
                others = [f for f in rule.between
                          if f != contested.rule_form and f in jdata.rule_forms]
                forms.extend(others)
                if rule.over:
                    aspect = rule.over
    if not forms:
        pool = [f for f in jdata.rule_forms
                if contested is None or f != contested.rule_form]
        forms = pool
    if not forms:
        raise DirectorError("no remedy available in the jurisdiction's rule forms")
    forms = sorted(set(forms))
    if prev and prev.bindings and len(forms) > 1 and prev.bindings.get("remedy") in forms:
        forms = [f for f in forms if f != prev.bindings["remedy"]]
    return rng.choice(forms), aspect


def _next_norm_id(situation) -> str:
    nums = [int(n.id.split("-")[1]) for n in situation.norms
            if n.id.startswith("N-") and n.id.split("-")[1].isdigit()]
    return f"N-{(max(nums) + 1) if nums else 1:04d}"
