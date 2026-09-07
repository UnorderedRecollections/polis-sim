"""Legal document templates — normative documents as structured text.

Per the families-of-legal-documents design: metadata is machine-readable
(YAML-style front matter), the body is human-readable law. Documents do NOT
imitate git; the git operations underneath produce the isomorphism.

Status discipline: the `status:` field is written by the machinery only —
  draft      — set when the document is scaffolded (bill draft)
  proposed   — flipped at introduction (the petition is before the federation)
  enacted    — flipped at ratification (entry into the authoritative corpus)
Humans write the law; the machinery records its lifecycle.
"""
from __future__ import annotations

import re
from pathlib import Path

KINDS = ("act", "amendment", "repeal")

TEMPLATE_DIR = Path(__file__).parent / "templates"


def _load_template(kind: str) -> str:
    path = TEMPLATE_DIR / f"{kind}.md"
    if not path.is_file():
        raise ValueError(f"no template for document kind '{kind}' (expected at {path})")
    return path.read_text(encoding="utf-8")


def _slug(title: str) -> str:
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", title.lower())).strip("-")


def filename_for(title: str) -> str:
    return f"{_slug(title)}.md"


def render_document(
    kind: str,
    *,
    title: str,
    jurisdiction: str,
    origin_city: str,
    proposer: str,
    answering: str | None = None,
    target: str | None = None,
) -> str:
    """A normative document scaffold: front matter + conventional sections."""
    if kind not in KINDS:
        raise ValueError(f"unknown document kind '{kind}' (choose from: {', '.join(KINDS)})")
    fm = [
        "---",
        f"type: {kind}",
        f"title: {title}",
        f"jurisdiction: {jurisdiction}",
        f"origin_city: {origin_city}",
        f"proposer: {proposer}",
    ]
    if answering:
        fm.append(f"originating_petition: {answering}")
    if target:
        fm.append(f"target: {target}")
    fm += ["status: draft", "---", ""]
    body = _load_template(kind).format(title=title, target=target or "<target act>")
    return "\n".join(fm) + "\n" + body


def scaffold(path: Path, kind: str, **meta) -> str:
    """Write a scaffold document; returns the text written."""
    text = render_document(kind, **meta)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return text


_STATUS_RE = re.compile(r"^(---\n(?:(?!^---$).)*?^status:\s*)(\w+)", re.M | re.S)


def flip_status_file(path: Path, new_status: str) -> bool:
    """Rewrite the front-matter status of one document. True if changed.

    Only files that actually begin with front matter and contain a status
    field are touched — prose without metadata is left alone.
    """
    if not path.is_file():
        return False
    text = path.read_text(encoding="utf-8")
    new_text, n = _STATUS_RE.subn(rf"\g<1>{new_status}", text, count=1)
    if n and new_text != text:
        path.write_text(new_text, encoding="utf-8")
        return True
    return False


def flip_status(repo_dir: Path, rel_paths: list[str], new_status: str) -> list[str]:
    """Flip status on every front-matter document among rel_paths; returns
    the paths that changed."""
    changed = []
    for rel in rel_paths:
        if flip_status_file(repo_dir / rel, new_status):
            changed.append(rel)
    return changed
