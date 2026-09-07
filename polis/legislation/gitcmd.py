"""Thin git wrapper: every invocation is produced both as a displayable
command string (for --isomorphism) and as an executable call."""
from __future__ import annotations

import shlex
import subprocess
from pathlib import Path


class GitError(RuntimeError):
    pass


def cmd_string(repo_dir: Path | None, *args: str) -> str:
    parts = ["git"]
    if repo_dir is not None:
        parts += ["-C", str(repo_dir)]
    parts += [shlex.quote(a) for a in args]
    return " ".join(parts)


def run(repo_dir: Path | None, *args: str) -> str:
    argv = ["git"]
    if repo_dir is not None:
        argv += ["-C", str(repo_dir)]
    argv += list(args)
    proc = subprocess.run(argv, capture_output=True, text=True)
    if proc.returncode != 0:
        raise GitError(f"{cmd_string(repo_dir, *args)}\n{proc.stderr.strip()}")
    return proc.stdout.strip()
