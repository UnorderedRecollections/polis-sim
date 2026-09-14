"""formal-check scenarios (task 0069): a throwaway corpus in a git repo.

The checks diff the proposal against the mainline and read the changed
documents — so the fixture is a tiny corpus with one changed act on a
`proposal` branch. Variants edit that act before the check runs.
"""
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from behave import given

BASE = """---
type: constitution
title: Founding
jurisdiction: federation
proposer: convention
origin_city: cogswich
status: enacted
---

# Founding

Entry into Force

The founding cites `constitution/founding.md`.
"""

ACT = """---
type: act
title: Test Act
jurisdiction: taxation
proposer: m.grimsbane
origin_city: cogswich
status: draft
---

# Test Act

Entry into Force

The act cites `constitution/founding.md`.
"""


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True,
                   capture_output=True, text=True)


def _act(context) -> Path:
    return Path(context.repo_dir) / "taxation" / "test-act.md"


@given("a throwaway corpus with a changed act")
def corpus(context):
    repo = Path(tempfile.mkdtemp(prefix="polis-bdd-corpus-"))
    context.repo_dir = str(repo)
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.email", "corpus@bdd.invalid")
    _git(repo, "config", "user.name", "Corpus Fixture")
    (repo / "constitution").mkdir()
    (repo / "constitution" / "founding.md").write_text(BASE, encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-m", "founding")
    _git(repo, "checkout", "-b", "proposal")
    (repo / "taxation").mkdir()
    _act(context).write_text(ACT, encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-m", "test act")


@given("the changed act loses its front matter")
def loses_front_matter(context):
    _act(context).write_text("# Test Act\n\nEntry into Force\n", encoding="utf-8")


@given("the changed act drops the Entry into Force provision")
def drops_entry_force(context):
    text = _act(context).read_text(encoding="utf-8")
    _act(context).write_text(text.replace("Entry into Force", "Commencement"),
                             encoding="utf-8")


@given("the changed act cites a missing document")
def bad_citation(context):
    text = _act(context).read_text(encoding="utf-8")
    _act(context).write_text(text.replace("constitution/founding.md",
                                          "taxation/does-not-exist.md"),
                             encoding="utf-8")


@given("the changed act touches the constitution")
def constitutional_change(context):
    p = Path(context.repo_dir) / "constitution" / "amendment.md"
    p.write_text(ACT.replace("taxation", "constitution"), encoding="utf-8")
    _git(Path(context.repo_dir), "add", "-A")
    _git(Path(context.repo_dir), "commit", "-m", "amendment")
