"""The runtime — the enact() transaction facade over the legal machinery.

One call = one legal act = one Plan executed = one journal entry with
before/after anchors. The simulation NEVER touches git stepwise; every
story block goes through here.

The runtime composes what already exists:
  * chamber/legislation (the machinery and its Plans),
  * the matter store (institutional time),
  * a NormSet attached to the run (the situation), with write-back on
    ratification/repeal per norms-generalization §7.

Executor: operator mode (chamber from world.json/slices, POLIS_* env
hooks). ContainerExecutor comes with the city images.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Optional

from ..legislation import archive as archive_mod
from ..legislation import bill as bill_mod
from ..legislation import docket as docket_mod
from ..legislation import gitcmd
from ..legislation.chamber import Chamber, load_chamber
from .journal import Journal, JournalEntry, _utcnow
from .norms import Norm, NormObject, NormSet


def _head(repo_dir: Path, ref: str = "HEAD") -> str:
    try:
        return gitcmd.run(repo_dir, "rev-parse", "--short", ref)
    except Exception:
        return ""


@dataclass
class EnactResult:
    entry: JournalEntry
    outputs: list[Any]                # the Plan steps' results


class Runtime:
    """One simulation run: a journal + an optional situation (NormSet)."""

    def __init__(self, journal: Journal, situation: Optional[NormSet] = None,
                 situation_path: Optional[Path] = None):
        self.journal = journal
        self.situation = situation
        self.situation_path = situation_path

    # --- the transaction facade ---------------------------------------------

    def enact(self, actor: str, action: str, plan, params: dict,
              anchors_extra: Optional[dict] = None,
              chamber: Optional[Chamber] = None,
              write_back: Optional[Callable[[], dict]] = None) -> EnactResult:
        """Execute one legal act as ONE journal entry.

        plan: a legislation Plan (already built for the actor's chamber).
        write_back: optional callable applied after the machinery succeeds,
        returning situation-delta anchors (e.g. norm status transitions).
        """
        before = _head(chamber.repo_dir, "main") if chamber else ""
        outputs = plan.execute()
        after = _head(chamber.repo_dir, "main") if chamber else ""
        anchors: dict[str, Any] = {}
        if chamber:
            anchors["main_before"], anchors["main_after"] = before, after
        if anchors_extra:
            anchors.update(anchors_extra)
        result: dict[str, Any] = {}
        if outputs and outputs[-1] is not None and hasattr(outputs[-1], "id"):
            result["id"] = outputs[-1].id
        if write_back is not None:
            anchors["situation"] = write_back()
            self._save_situation()
        entry = JournalEntry(
            seq=self.journal.next_seq(), ts=_utcnow(),
            kind="action", actor=actor, action=action, params=params,
            result=result, anchors=anchors,
        )
        self.journal.append(entry)
        return EnactResult(entry=entry, outputs=outputs)

    def _save_situation(self) -> None:
        if self.situation is not None and self.situation_path is not None:
            from .norms import save_norm_file
            save_norm_file(self.situation, self.situation_path)

    def observe(self, actor: str, what: str, detail: dict) -> None:
        """Record an assertion/observation (self-auditing journal)."""
        self.journal.append(JournalEntry(
            seq=self.journal.next_seq(),
            ts=_utcnow(),
            kind="observation", actor=actor, action=what, params={}, result=detail,
        ))

    # --- typed moves (each = one legal act) -----------------------------------

    def file_petition(self, chamber: Chamber, title: str, body: str) -> EnactResult:
        return self.enact(
            chamber.actor_username, "docket.file",
            docket_mod.file_petition(chamber, title, body),
            params={"title": title}, chamber=chamber,
        )

    def draft_bill(self, chamber: Chamber, title: str, **draft_kw) -> EnactResult:
        return self.enact(
            chamber.actor_username, "bill.draft",
            bill_mod.draft(chamber, title, **draft_kw),
            params={"title": title, **{k: v for k, v in draft_kw.items() if v}},
            chamber=chamber,
        )

    def amend_bill(self, chamber: Chamber, bill: str, files: list[str],
                   justification: str, all_files: bool = False) -> EnactResult:
        return self.enact(
            chamber.actor_username, "bill.amend",
            bill_mod.amend(chamber, bill, files, justification, all_files),
            params={"bill": bill, "files": files}, chamber=chamber,
        )

    def introduce_bill(self, chamber: Chamber, bill: str, title: str,
                       body: str = "", answering: str | None = None) -> EnactResult:
        res = self.enact(
            chamber.actor_username, "bill.introduce",
            bill_mod.introduce(chamber, bill, title, body, answering=answering),
            params={"bill": bill, "title": title, "answering": answering},
            chamber=chamber,
        )
        matter = res.outputs[-1] if res.outputs else None
        if hasattr(matter, "id"):
            res.entry.anchors["matter"] = matter.id
        return res

    def scrutinize(self, chamber: Chamber, bill: str, verdict: str, body: str = "") -> EnactResult:
        return self.enact(
            chamber.actor_username, "bill.scrutinize",
            bill_mod.scrutinize(chamber, bill, verdict, body),
            params={"bill": bill, "verdict": verdict}, chamber=chamber,
        )

    def ratify(self, chamber: Chamber, bill: str,
               new_norm: Optional[Norm] = None,
               supersedes: Optional[str] = None) -> EnactResult:
        """Enactment + situation write-back: `new_norm` enters (source=statute,
        source_ref=the bill's matter id); `supersedes` marks the old norm."""
        def write_back() -> dict:
            delta: dict[str, Any] = {}
            if self.situation is None:
                return delta
            if supersedes and new_norm is not None:
                old = self.situation.get(supersedes)
                self.situation.supersede(supersedes, new_norm)
                delta["superseded"] = {supersedes: old.rule_form}
                delta["in_force"] = {new_norm.id: new_norm.rule_form}
            elif new_norm is not None:
                self.situation.norms.append(new_norm)
                delta["in_force"] = {new_norm.id: new_norm.rule_form}
            return delta

        res = self.enact(
            chamber.actor_username, "bill.ratify",
            bill_mod.ratify(chamber, bill),
            params={"bill": bill, "supersedes": supersedes,
                    "new_norm": new_norm.id if new_norm else None},
            chamber=chamber, write_back=write_back if self.situation is not None else None,
        )
        return res

    def reject(self, chamber: Chamber, bill: str) -> EnactResult:
        return self.enact(
            chamber.actor_username, "bill.reject",
            bill_mod.reject(chamber, bill),
            params={"bill": bill}, chamber=chamber,
        )

    def repeal(self, chamber: Chamber, norm_id: str, act: str,
               mainline: int | None = None, revive_custom: bool = True) -> EnactResult:
        def write_back() -> dict:
            if self.situation is None:
                return {}
            self.situation.repeal(norm_id, revive_custom=revive_custom)
            return {"repealed": norm_id}

        return self.enact(
            chamber.actor_username, "archive.repeal",
            archive_mod.repeal(chamber, act, mainline=mainline),
            params={"act": act, "norm": norm_id},
            chamber=chamber,
            write_back=write_back if self.situation is not None else None,
        )


def operator_chamber(as_user: str, city: str) -> Chamber:
    """The v1 executor: operator-mode chamber (POLIS_* env hooks apply)."""
    return load_chamber(as_user=as_user, city=city)
