"""polis formal-check — the Mechanical Magistrate's formal checks.

The four checks of the pipeline (the Mechanical Magistracy Act's
Schedule 1; the checklist in docs/notes/families-of-legal-documents.md
§6). Each check is mechanical: it examines the corpus's form and the
record's marks, never the merits. A check fails by exiting non-zero and
printing its findings; the CI pipeline runs all four on every proposed
change and reports the findings (report:commit-status) — the Magistrate
decides nothing, the offices decide.

The checks operate on a git working clone (--repo-dir, default .): the
documents changed by the proposed line of development, diffed against
the mainline.
"""
from __future__ import annotations

import os
import re
from pathlib import Path

import typer

from ..legislation import gitcmd
from .common import console

app = typer.Typer(no_args_is_help=True,
                  help="The Mechanical Magistrate's formal checks (CI).")

REPO_DIR = typer.Option(".", "--repo-dir", help="Working clone of the corpus.")

_REQUIRED = ("type", "title", "jurisdiction", "proposer", "origin_city")
_VALID_STATUS = ("draft", "proposed", "enacted")


def _changed_docs(repo_dir: Path) -> list[str]:
    """The documents the proposed line of development touches (diffed
    against the mainline)."""
    for base in ("origin/main", "main"):
        try:
            out = gitcmd.run(repo_dir, "diff", "--name-only", f"{base}...HEAD")
            return [f for f in out.splitlines() if f.endswith(".md")]
        except Exception:
            continue
    # no mainline visible (fresh clone?) — every document in the tree
    return [str(p) for p in repo_dir.rglob("*.md")]


def _front_matter(path: Path) -> dict[str, str] | None:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return None
    m = re.match(r"^---\n(.*?)\n---", text, re.S)
    if not m:
        return None
    fm: dict[str, str] = {}
    for line in m.group(1).splitlines():
        if ":" in line and not line.lstrip().startswith("#"):
            k, v = line.split(":", 1)
            fm[k.strip()] = v.strip().strip('"')
    return fm


def _fail(msg: str) -> None:
    console.print(f"[red]FORMAL CHECK FAILED[/red] — {msg}")
    raise typer.Exit(code=1)


def _ok(msg: str) -> None:
    console.print(f"[green]formal check passed[/green] — {msg}")


@app.command()
def identify(repo_dir: str = REPO_DIR) -> None:
    """Every changed act identifies itself: front matter with type, title,
    jurisdiction, proposer and origin_city, and a valid status."""
    rd = Path(repo_dir)
    changed = _changed_docs(rd)
    if not changed:
        _ok("no documents changed — nothing to identify")
        return
    for rel in changed:
        path = rd / rel
        fm = _front_matter(path)
        if fm is None:
            _fail(f"{rel}: a changed legal document has no front matter")
        missing = [k for k in _REQUIRED if not fm.get(k)]
        if missing:
            _fail(f"{rel}: front matter missing {', '.join(missing)}")
        if fm.get("status") not in _VALID_STATUS:
            _fail(f"{rel}: status must be draft|proposed|enacted "
                  f"(got '{fm.get('status')}')")
    _ok(f"{len(changed)} document(s) identified")


@app.command()
def entry_force(repo_dir: str = REPO_DIR) -> None:
    """Every changed act contains an Entry into Force provision."""
    rd = Path(repo_dir)
    changed = _changed_docs(rd)
    acts = [f for f in changed if "entry into force" in
            (rd / f).read_text(encoding="utf-8").lower()]
    missing = [f for f in changed if f not in acts]
    if missing:
        _fail("no Entry into Force provision: " + ", ".join(missing))
    _ok(f"{len(acts)} act(s) carry an Entry into Force provision")


@app.command()
def references(repo_dir: str = REPO_DIR) -> None:
    """Every path a changed act cites resolves to law in the corpus."""
    rd = Path(repo_dir)
    for rel in _changed_docs(rd):
        text = (rd / rel).read_text(encoding="utf-8")
        for cited in re.findall(r"`([\w\-.]+/[\w\-.]+\.\w+)`", text):
            if not (rd / cited).exists():
                _fail(f"{rel}: cites '{cited}', which is not in the corpus")
    _ok("all citations resolve to the corpus")


@app.command()
def constitution(repo_dir: str = REPO_DIR) -> None:
    """A change touching the constitution must carry the Constitutional
    Council's approval: the PR bears a SCRUTINY — APPROVED finding. Reads
    POLIS_GITEA_URL/POLIS_GITEA_TOKEN (injected by the CI)."""
    rd = Path(repo_dir)
    changed = _changed_docs(rd)
    constitutional = [f for f in changed if f.startswith("constitution/")]
    if not constitutional:
        _ok("no constitutional change")
        return
    import httpx
    url = os.environ.get("POLIS_GITEA_URL")
    token = os.environ.get("POLIS_GITEA_TOKEN")
    pr = os.environ.get("CI_COMMIT_PULL_REQUEST") or os.environ.get("CI_PULL_REQUEST")
    owner = os.environ.get("CI_REPO_OWNER")
    repo = os.environ.get("CI_REPO_NAME")
    if not (url and token and pr and owner and repo):
        _fail("constitutional change, but no gitea context to check the Council's "
              "finding (POLIS_GITEA_URL/POLIS_GITEA_TOKEN/CI_* env missing)")
    c = httpx.Client(base_url=url, headers={"Authorization": f"token {token}",
                                            "X-GitHub-Api-Version": "2022-11-28"},
                     timeout=15)
    r = c.get(f"/api/v1/repos/{owner}/{repo}/issues/{pr}/comments")
    if r.status_code >= 400:
        _fail(f"cannot read the petition's record: {r.status_code}")
    approved = any("SCRUTINY — APPROVED" in (x.get("body") or "")
                   for x in r.json())
    if not approved:
        _fail(f"{', '.join(constitutional)}: a constitutional change without the "
              "Council's SCRUTINY — APPROVED finding")
    _ok("the Constitutional Council has approved the change")
