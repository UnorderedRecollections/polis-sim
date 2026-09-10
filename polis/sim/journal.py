"""The journal — the run-scoped replay log (docs/design/simulator.md §2.1).

Append-only JSONL, one file per run: data/sims/<run-id>/journal.jsonl.
Every entry is one legal act with its resulting anchors (git heads, matter
ids, norms touched) — sufficient to re-execute deterministically (--verify,
later) and to re-present step by step (sim present).

Journal seq = simulation time; it references legal time (git) and
institutional time (matter events) but replaces neither. Written by the
runtime, never by hand.
"""
from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from .. import config

SIMS_DIR = config.DATA_DIR / "sims"


def run_dir(run_id: str) -> Path:
    """The run's directory. POLIS_SIM_DIR pins it exactly — the operator
    container mounts one sim's dir at /sim and works nowhere else."""
    pinned = os.environ.get("POLIS_SIM_DIR")
    return Path(pinned) if pinned else SIMS_DIR / run_id


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


@dataclass
class JournalEntry:
    seq: int
    ts: str
    kind: str                        # action | observation | anchor
    actor: str
    action: str                      # e.g. docket.file, bill.ratify
    params: dict[str, Any] = field(default_factory=dict)
    result: dict[str, Any] = field(default_factory=dict)
    anchors: dict[str, Any] = field(default_factory=dict)


class Journal:
    def __init__(self, run_id: str):
        self.run_id = run_id
        self.path = run_dir(run_id) / "journal.jsonl"

    def append(self, entry: JournalEntry) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(entry), ensure_ascii=False) + "\n")

    def entries(self) -> list[JournalEntry]:
        if not self.path.exists():
            return []
        out = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                out.append(JournalEntry(**json.loads(line)))
        return out

    def next_seq(self) -> int:
        entries = self.entries()
        return (entries[-1].seq + 1) if entries else 1


def new_run(run_id: str) -> Journal:
    """Start a run: create its directory and empty journal."""
    j = Journal(run_id)
    j.path.parent.mkdir(parents=True, exist_ok=True)
    j.path.touch(exist_ok=True)
    return j


def list_runs() -> list[str]:
    if not SIMS_DIR.is_dir():
        return []
    return sorted(p.name for p in SIMS_DIR.iterdir() if (p / "journal.jsonl").exists())


# --- epochs: saved records of a run (docs/tasks/0030) -----------------------------
#
# The record = the files the run produces that are NOT the machinery:
# journal, situation, stories, matters, run config. The machinery (platform
# containers, slices, secrets, the git archive) is untouched by epoch ops.

RECORD_FILES = ("journal.jsonl", "situation.yaml", "stories.json",
                "matters.json", "run.json")


def epochs_dir(run_id: str) -> Path:
    return run_dir(run_id) / "epochs"


def save_epoch(run_id: str, name: str) -> Path:
    """Copy the current record aside as a named epoch."""
    rd = run_dir(run_id)
    dest = epochs_dir(run_id) / name
    if dest.exists():
        raise FileExistsError(f"epoch '{name}' already exists for run '{run_id}'")
    dest.mkdir(parents=True)
    moved = 0
    for f in RECORD_FILES:
        src = rd / f
        if src.exists():
            (dest / f).write_bytes(src.read_bytes())
            moved += 1
    if not moved:
        dest.rmdir()
        raise FileNotFoundError(f"run '{run_id}' has no record to save")
    return dest


def clear_record(run_id: str) -> list[str]:
    """Remove the current record files (the machinery is untouched)."""
    rd = run_dir(run_id)
    removed = []
    for f in RECORD_FILES:
        path = rd / f
        if path.exists():
            path.unlink()
            removed.append(f)
    return removed


def list_epochs(run_id: str) -> list[str]:
    ed = epochs_dir(run_id)
    if not ed.is_dir():
        return []
    return sorted(p.name for p in ed.iterdir() if (p / "journal.jsonl").exists())
