"""The scenario model — a .feature parsed into ordered beats (task 0034).

Gherkin is DATA here, not a test: one model, two drivers. The behave
driver (features/steps/) executes it synchronously; the director's queue
(0034b) will consume it incrementally in a live sim.

Beat kinds by keyword: Given = setup/precondition, When = action,
Then = expectation (scoreboard assertions). And/But inherit the kind of
the previous beat (Gherkin semantics).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class Beat:
    kind: str                       # setup | action | expectation
    keyword: str                    # the raw keyword as written
    text: str
    line: int


@dataclass
class Scenario:
    name: str
    beats: list[Beat] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)


@dataclass
class Feature:
    name: str
    scenarios: list[Scenario] = field(default_factory=list)
    path: Optional[str] = None


_KINDS = {"given": "setup", "when": "action", "then": "expectation"}


def parse_feature(path: str | Path) -> Feature:
    """Parse a .feature into the scenario model (via behave's parser)."""
    from behave.parser import parse_file as behave_parse

    parsed = behave_parse(str(path))
    feature = Feature(name=parsed.name or "", path=str(path))
    for sc in parsed.scenarios:
        scenario = Scenario(name=sc.name or "",
                            tags=[str(t) for t in getattr(sc, "tags", [])])
        current = "setup"
        for step in sc.steps:
            kw = step.keyword.strip().lower()
            if kw in _KINDS:
                current = _KINDS[kw]
            scenario.beats.append(Beat(kind=current, keyword=step.keyword,
                                       text=step.name, line=step.line))
        feature.scenarios.append(scenario)
    return feature


def parse_text(text: str, path: str = "<string>") -> Feature:
    """Parse feature content from a string."""
    from behave.parser import parse as behave_parse

    parsed = behave_parse(text)
    tmp = Path(path)
    # behave's parse() lacks a filename; reuse parse_feature's shaping
    feature = Feature(name=parsed.name or "", path=path)
    for sc in parsed.scenarios:
        scenario = Scenario(name=sc.name or "",
                            tags=[str(t) for t in getattr(sc, "tags", [])])
        current = "setup"
        for step in sc.steps:
            kw = step.keyword.strip().lower()
            if kw in _KINDS:
                current = _KINDS[kw]
            scenario.beats.append(Beat(kind=current, keyword=step.keyword,
                                       text=step.name, line=step.line))
        feature.scenarios.append(scenario)
    return feature
