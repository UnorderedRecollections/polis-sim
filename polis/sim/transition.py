"""The phase transition — the story that codifies the machinery (task 0038).

`transition(run_id)` plays the `phase_transition` story template end to
end through the customary procedure: a petition grieves the customary
machinery; the three authored acts (data/world/legal/transition/) carry
the instruments of the codified machinery into the federal archive —
CODEOWNERS, the branch-protection rules, the Mechanical Magistrate's
pipeline; the Constitutional Council reviews; the Keeper ratifies all
three; the third ratification flips the federation to phase 2 *in the
same transaction* (situation + civil registry + sim slices — the Keeper's
own archival act, never a hand edit).

Requires a gitea-hosted sim (phase-2 proceedings run on gitea). The
federation's phase flips in world.json — an event in the federation's
life, shared by every future sim instance.
"""
from __future__ import annotations

import json
import random
from typing import Any

from .. import config, store
from ..legislation import archive as archive_mod
from ..legislation import bill as bill_mod
from .director import DirectorError, RunConfig, Story, _Cast, _chamber, load_stories, _save_stories
from .journal import Journal, JournalEntry, _utcnow, run_dir
from .norms import load_norm_file
from .runtime import Runtime

# the authored content (task 0036); honors POLIS_DATA_DIR (operator container)
TRANSITION_DIR = config.WORLD_DIR / "legal" / "transition"

# Each act: (act file, title, instrument file, instrument's path in the corpus)
ACTS = [
    ("act-1-assigned-legal-authority.md", "Assigned Legal Authority Act",
     "CODEOWNERS", "CODEOWNERS"),
    ("act-2-constitutional-approval.md", "Constitutional Approval Act",
     "branch-protection.md", "constitution/branch-protection.md"),
    ("act-3-mechanical-magistracy.md", "Mechanical Magistracy Act",
     ".woodpecker.yml", ".woodpecker.yml"),
]

PETITION_TITLE = "Petition for the Codification of the Machinery"
PETITION_BODY = (
    "The customary machinery can no longer carry the burden. The archive "
    "host knows refs and nothing of offices, petitions or approvals; the "
    "constitution is enforced by people alone, and the people are few. "
    "We petition that the machinery be codified: the schedule of assigned "
    "legal authority, the rules of required approval, and the formal "
    "checks of the Mechanical Magistrate."
)

EDITION_NAME = "codified-machinery"
EDITION_MESSAGE = "The codified machinery is promulgated — phase 2 begins."


def _authored_act(act_file: str, origin_city: str, proposer: str) -> str:
    """The authored act text, with casting filled into the front matter."""
    text = (TRANSITION_DIR / act_file).read_text(encoding="utf-8")
    chunk = ("jurisdiction: constitutional\n"
             "# proposer and origin_city are filled by the casting at introduction")
    filled = ("jurisdiction: constitutional\n"
              f"origin_city: {origin_city}\n"
              f"proposer: {proposer}")
    if chunk not in text:
        raise DirectorError(f"{act_file}: expected the casting placeholder in the front matter")
    return text.replace(chunk, filled, 1)


def _require_gitea(run_id: str) -> None:
    # run_dir honors POLIS_SIM_DIR — the check works host-side and inside
    # the operator container (where the sim dir mounts at /sim)
    inv_path = run_dir(run_id) / "provision.json"
    if not inv_path.exists():
        raise DirectorError(
            f"run '{run_id}' is not a provisioned sim — the phase transition "
            "needs a gitea-hosted sim (`polis provision up <sim> --platform gitea`)")
    platform = json.loads(inv_path.read_text(encoding="utf-8")).get("platform") or "gogs"
    if platform != "gitea":
        raise DirectorError(
            f"run '{run_id}' runs on gogs — phase-2 proceedings need gitea; "
            "re-provision with `polis provision up <sim> --platform gitea`")


def _flip_effect(rt: Runtime, run_id: str, act_titles: list[str]) -> Any:
    """The Keeper's third ratification records the new machinery state in
    the same transaction: situation, civil registry, sim slices."""
    def effect() -> dict:
        delta: dict[str, Any] = {"phase": 2, "transition_acts": act_titles}
        if rt.situation is not None:
            rt.situation.federation = {"phase": 2}
            delta["situation"] = "federation.phase = 2"
        world = store.load_world()
        world.federation.phase = 2
        store.save_world(world)
        delta["world"] = "federation.phase = 2"
        slices_dir = run_dir(run_id) / "cities"
        if slices_dir.is_dir():
            flipped = 0
            for sp in slices_dir.glob("*.json"):
                slice_ = json.loads(sp.read_text(encoding="utf-8"))
                if slice_.get("federation", {}).get("phase") != 2:
                    slice_["federation"]["phase"] = 2
                    sp.write_text(json.dumps(slice_, indent=2), encoding="utf-8")
                    flipped += 1
            delta["slices"] = f"{flipped} slices → phase 2"
        return delta
    return effect


def transition(run_id: str) -> Story:
    cfg = RunConfig.load(run_id)
    rd = run_dir(run_id)
    _require_gitea(run_id)
    if store.load_world().federation.phase != 1:
        raise DirectorError(
            "the federation already operates in phase 2 — the transition is "
            "a one-time event")
    stories = load_stories(run_id)
    if any(s.template == "phase_transition" and s.status == "enacted" for s in stories):
        raise DirectorError(
            f"run '{run_id}' has already enacted the phase transition "
            "(a one-time event — see `polis sim stories`)")
    sit_path = rd / "situation.yaml"
    if not sit_path.exists():
        raise DirectorError(f"run '{run_id}' has no situation.yaml — `polis sim new` first")
    rt = Runtime(Journal(run_id), load_norm_file(sit_path), sit_path)
    cast = _Cast()
    n = len(stories)

    # the working clone every chamber shares (the Keeper obtained it at the
    # first drive; ensure it exists if the transition comes first)
    if not (rd / "common-law" / ".git").exists():
        keeper_city = cast.city_of[cast.keeper]
        ch = _chamber(run_id, cast.keeper, keeper_city)
        rt.enact(cast.keeper, "archive.obtain", archive_mod.obtain(ch),
                 params={}, chamber=ch)

    story = Story(id=f"story-{n + 1:04d}", template="phase_transition",
                  status="in_progress", started_at=_utcnow())
    act_titles = [a[1] for a in ACTS]
    story.bindings = {"acts": act_titles, "edition": EDITION_NAME}

    try:
        rng = random.Random(f"{cfg.seed}:transition")
        # only real cities propose — the magistrate's institutional
        # membership is not a city (no legislators there)
        cities = sorted(c.id for c in cast.world.cities)
        proposer_city = rng.choice(cities)
        petitioner = cast.legislator(proposer_city, n)
        jurist = cast.jurist(n)
        keeper = cast.keeper
        story.cast = {"petitioner": petitioner, "jurist": jurist, "keeper": keeper}

        pet_ch = _chamber(run_id, petitioner, proposer_city)
        jur_ch = _chamber(run_id, jurist, cast.city_of[jurist])
        keep_ch = _chamber(run_id, keeper, cast.city_of[keeper])
        keep_ch.origin = pet_ch.origin          # the acts are lodged where developed
        fed = next(o for o in cast.world.offices if o.id == "federal-archivist")
        keep_ch.offices.append(fed.model_dump(mode="json"))

        def seq() -> int:
            return rt.journal.next_seq() - 1

        # --- the grievance ----------------------------------------------------
        res = rt.file_petition(pet_ch, PETITION_TITLE, PETITION_BODY)
        petition_id = res.entry.result.get("id")
        story.entries.append(seq())
        rt.observe("director", "assign_jurisdiction", {"jurisdiction": "constitutional"})
        story.entries.append(seq())

        # --- the three acts of the codified machinery --------------------------
        branches: list[str] = []
        for act_file, title, instrument, instrument_path in ACTS:
            into = "constitution"
            rt.draft_bill(pet_ch, title, kind="act", into=into)
            story.entries.append(seq())
            branch = bill_mod.branch_of(title)
            slug = branch.removeprefix("bill/")
            act_path = f"{into}/{slug}.md"
            (pet_ch.repo_dir / act_path).write_text(
                _authored_act(act_file, proposer_city, petitioner), encoding="utf-8")
            (pet_ch.repo_dir / instrument_path).parent.mkdir(parents=True, exist_ok=True)
            (pet_ch.repo_dir / instrument_path).write_bytes(
                (TRANSITION_DIR / instrument).read_bytes())
            justification = (f"Lodge the {title} and its Schedule 1 (the "
                             f"{instrument} instrument), answering {petition_id}.")
            rt.amend_bill(pet_ch, branch, [act_path, instrument_path], justification)
            story.entries.append(seq())
            rt.introduce_bill(pet_ch, branch, title, justification, answering=petition_id)
            story.entries.append(seq())
            branches.append(branch)

        # --- constitutional review ----------------------------------------------
        for branch in branches:
            rt.scrutinize(jur_ch, branch, "approve",
                          "The codification is consistent with the founding "
                          "constitution (Articles 1–3).")
            story.entries.append(seq())
        rt.observe("director", "approval", {"acts": act_titles})
        story.entries.append(seq())

        # --- ratification: the third act flips the machinery --------------------
        for i, branch in enumerate(branches):
            effect = _flip_effect(rt, run_id, act_titles) if i == len(branches) - 1 else None
            rt.ratify(keep_ch, branch, machinery_effect=effect)
            story.entries.append(seq())

        # --- promulgation --------------------------------------------------------
        # the edition belongs to the federal archive: the Keeper's origin
        # served the ratification fetches — now lodge the tag upstream
        keep_ch.origin = keep_ch.upstream
        rt.enact(keeper, "archive.promulgate",
                 archive_mod.promulgate(keep_ch, EDITION_NAME, EDITION_MESSAGE),
                 params={"name": EDITION_NAME}, chamber=keep_ch)
        story.entries.append(seq())

        story.status = "enacted"
        story.matter = petition_id
    except Exception as e:
        story.status = "failed"
        story.error = str(e)[:500]
        rt.observe("director", f"{story.id} failed", {"error": story.error})
    story.finished_at = _utcnow()
    stories.append(story)
    _save_stories(run_id, stories)

    # the story anchor (links the beats; proof of the transition)
    rt.journal.append(JournalEntry(
        seq=rt.journal.next_seq(), ts=_utcnow(), kind="anchor",
        actor="director", action="story",
        params={"story": story.id, "template": story.template,
                "bindings": story.bindings, "cast": story.cast},
        result={"matter": story.matter, "entries": story.entries},
    ))
    return story
