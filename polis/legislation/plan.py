"""Plan/Step — the isomorphism engine.

A Plan is the legal act expressed as machinery. Rendering it shows exactly
which git commands and API calls constitute the legal act; executing it
performs them. This is the project's thesis made operational.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from rich.console import Console
from rich.panel import Panel

console = Console()


@dataclass
class Step:
    machinery: str                          # the git/API operation, as a string
    legal: str = ""                         # its meaning in legal language
    run: Optional[Callable[[], Any]] = None  # executor (None = display-only step)


@dataclass
class Plan:
    act: str                       # legal name of the act, e.g. "introduce a bill"
    actor: str                     # who performs it
    steps: list[Step] = field(default_factory=list)

    def add(self, machinery: str, legal: str = "", run: Optional[Callable[[], Any]] = None) -> "Plan":
        self.steps.append(Step(machinery=machinery, legal=legal, run=run))
        return self

    def render_isomorphism(self) -> None:
        lines = []
        for i, s in enumerate(self.steps, 1):
            lines.append(f"[cyan]{i}.[/cyan] [bold]{s.machinery}[/bold]")
            if s.legal:
                lines.append(f"   [dim]{s.legal}[/dim]")
        console.print(Panel(
            "\n".join(lines),
            title=f"isomorphism — {self.act}",
            subtitle=f"performed by: {self.actor}",
            title_align="left",
            subtitle_align="left",
            border_style="cyan",
        ))

    def execute(self) -> list[Any]:
        results = []
        for s in self.steps:
            if s.run is not None:
                results.append(s.run())
        return results
