"""Norms — the rules in force (see docs/design/norms-generalization.md).

SNAPSHOT PRINCIPLE: a norm set is always a YAML document. Seed and evolved
state share one format and one loader — the engine is agnostic about whether
a file is a bootstrap seed or a snapshot. Evolution = load → apply
operations → save; any saved file is a valid bootstrapping point.

The lifecycle operations (enact / supersede / repeal / queries) are pure
functions over NormSet — no git, no platform, no I/O — so they work
identically on a seed, a situation store, or a snapshot.
"""
from __future__ import annotations

from pathlib import Path
from typing import Literal, Optional

import yaml
from pydantic import BaseModel, model_validator

from .. import config
from .legaldata import load_jurisdictions, load_paradigms

NORM_KINDS_FILE = config.WORLD_DIR / "legal" / "ontology" / "norm_kinds.yaml"
NORMS_DIR = config.WORLD_DIR / "legal" / "norms"

NormSource = Literal["custom", "statute", "treaty", "charter"]
NormStatus = Literal["in_force", "superseded", "repealed"]
ObjectType = Literal["resource", "conduct", "status", "flow", "burden", "relationship", "right"]


class NormObject(BaseModel):
    kind: str            # what it is (northern_banks, lending, the tariff regime)
    type: ObjectType     # resource | conduct | status | flow | burden | relationship


class Holder(BaseModel):
    """A party to a holding: either or both of a city and an actor kind
    ("the fishers of Cogswich", "Brasshaven", "any carrier")."""
    city: Optional[str] = None
    actor_kind: Optional[str] = None

    @model_validator(mode="after")
    def _not_empty(self) -> "Holder":
        if not self.city and not self.actor_kind:
            raise ValueError("a holder needs a city and/or an actor_kind")
        return self


class Holding(BaseModel):
    """A durable legal fact linking an actor to an object under a norm
    (docs/design/jurisdiction-requirements.md §2)."""
    id: str                                  # H-0001
    holder: Holder
    object: NormObject
    activity: str = ""                       # the use, for resource holdings
    under: str                               # the norm id it exists under


class Norm(BaseModel):
    id: str                                  # N-0001
    rule_form: str                           # from the jurisdiction's rule_forms
    object: NormObject
    aspect: str                              # the governed aspect (access_right, rate, flow)
    subjects: list[str] = []                 # who is bound
    beneficiaries: list[str] = []            # who gains
    source: NormSource = "custom"
    source_ref: Optional[str] = None         # LegalObject id when source != custom
    status: NormStatus = "in_force"

    @model_validator(mode="after")
    def _source_ref_consistency(self) -> "Norm":
        if self.source == "custom" and self.source_ref is not None:
            raise ValueError(f"{self.id}: custom norms have no source_ref")
        if self.source != "custom" and not self.source_ref:
            raise ValueError(f"{self.id}: source '{self.source}' requires a source_ref")
        return self


class NormSet(BaseModel):
    """A situation document: norms and holdings together (holdings cite the
    norms they exist under and must never drift apart). One format, seed or
    snapshot alike."""
    norms: list[Norm] = []
    holdings: list[Holding] = []
    description: str = ""

    # --- queries -----------------------------------------------------------
    def get(self, norm_id: str) -> Norm:
        for n in self.norms:
            if n.id == norm_id:
                return n
        raise KeyError(f"unknown norm '{norm_id}'")

    def in_force(
        self,
        object_kind: str | None = None,
        aspect: str | None = None,
        jurisdiction_rule_forms: list[str] | None = None,
    ) -> list[Norm]:
        out = [n for n in self.norms if n.status == "in_force"]
        if object_kind:
            out = [n for n in out if n.object.kind == object_kind]
        if aspect:
            out = [n for n in out if n.aspect == aspect]
        if jurisdiction_rule_forms is not None:
            out = [n for n in out if n.rule_form in jurisdiction_rule_forms]
        return out

    # --- lifecycle (pure; see docs/design/norms-generalization.md §7) ------

    def enact(
        self,
        norm_id: str,
        rule_form: str,
        object_: NormObject,
        aspect: str,
        subjects: list[str],
        beneficiaries: list[str],
        source_ref: str,
        source: NormSource = "statute",
    ) -> Norm:
        """A new norm enters by enactment/grant (source_ref = the LegalObject)."""
        norm = Norm(
            id=norm_id, rule_form=rule_form, object=object_, aspect=aspect,
            subjects=subjects, beneficiaries=beneficiaries,
            source=source, source_ref=source_ref,
        )
        self.norms.append(norm)
        return norm

    def supersede(self, old_id: str, new_norm: Norm) -> Norm:
        """The old norm is superseded by a new one (the `supersedes` relation
        made concrete)."""
        old = self.get(old_id)
        old.status = "superseded"
        self.norms.append(new_norm)
        return new_norm

    def repeal(self, norm_id: str, revive_custom: bool = True) -> Norm:
        """Repeal: the norm leaves force. By default the prior custom on the
        same object+aspect revives (phase-1 fiction: repeal restores the
        status quo ante)."""
        norm = self.get(norm_id)
        norm.status = "repealed"
        if revive_custom:
            for n in self.norms:
                if (
                    n is not norm
                    and n.object == norm.object
                    and n.aspect == norm.aspect
                    and n.source == "custom"
                    and n.status != "in_force"
                ):
                    n.status = "in_force"
        return norm

    def contested(self, norm_id: str) -> list[Norm]:
        """Norms in force over the same object+aspect as the given norm —
        the raw material of vested-rights disputes."""
        norm = self.get(norm_id)
        return [
            n for n in self.norms
            if n is not norm and n.status == "in_force"
            and n.object == norm.object and n.aspect == norm.aspect
        ]

    def conflicts(
        self,
        incompatibilities: list | None = None,
        kinds: tuple[str, ...] = ("strict",),
    ) -> list[tuple[Norm, Norm]]:
        """Pairs of in-force norms over the same object+aspect whose rule
        forms are incompatible (docs/design/rule-incompatibility.md).

        `incompatibilities`: IncompatibilityRule objects (with .between/
        .over/.kind) or plain (a, b) tuples (treated as strict, any aspect).
        `kinds`: which degrees to report ("strict", "tension").
        In a healthy situation this returns empty for kinds=("strict",).
        """
        pairs: list[tuple[Norm, Norm]] = []
        if not incompatibilities:
            return pairs
        rules = []
        for r in incompatibilities:
            if isinstance(r, tuple):
                rules.append((frozenset(r), None, "strict"))
            else:
                rules.append((frozenset(r.between), r.over, r.kind))
        rules = [r for r in rules if r[2] in kinds]
        live = self.in_force()
        for i, a in enumerate(live):
            for b in live[i + 1:]:
                if a.object != b.object or a.aspect != b.aspect:
                    continue
                for forms, over, _kind in rules:
                    if frozenset((a.rule_form, b.rule_form)) == forms and (
                            over is None or over == a.aspect):
                        pairs.append((a, b))
        return pairs


# ---------------------------------------------------------------- persistence

def load_norm_file(path: Path) -> NormSet:
    """Load any norm document — seed or snapshot; same format, same rules."""
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return NormSet.model_validate(data)


def save_norm_file(norm_set: NormSet, path: Path, description: str = "") -> Path:
    """Persist a norm set. The saved file is a valid bootstrapping point."""
    if description:
        norm_set.description = description
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(
            norm_set.model_dump(exclude_none=True), f,
            sort_keys=False, allow_unicode=True,
        )
    return path


def load_seed_norms() -> dict[str, NormSet]:
    """The foundational seeds: data/world/legal/norms/<jurisdiction>.yaml."""
    out: dict[str, NormSet] = {}
    if NORMS_DIR.is_dir():
        for path in sorted(NORMS_DIR.glob("*.yaml")):
            out[path.stem] = load_norm_file(path)
    return out


# ---------------------------------------------------------------- validation

def validate_norm_set(norm_set: NormSet, jurisdiction_slug: str) -> list[str]:
    """Cross-validate a norm set against the jurisdiction and paradigm
    registries. Returns a list of problems (empty = valid)."""
    problems: list[str] = []
    jurisdictions = load_jurisdictions()
    paradigms = load_paradigms()
    j = jurisdictions.get(jurisdiction_slug)
    if j is None:
        return [f"unknown jurisdiction '{jurisdiction_slug}'"]
    admitted_types = {
        t for p in j.paradigms for t in paradigms[p].holding_object_types
    } if j.paradigms else set()
    for n in norm_set.norms:
        if n.rule_form not in j.rule_forms:
            problems.append(f"{n.id}: rule_form '{n.rule_form}' not in {jurisdiction_slug}'s rule_forms")
        if admitted_types and n.object.type not in admitted_types:
            problems.append(
                f"{n.id}: object type '{n.object.type}' not admitted by "
                f"{jurisdiction_slug}'s paradigm(s) {sorted(j.paradigms)}")
        if n.object.type == "resource":
            # files are the source of truth; the index is the fallback
            from .resources import load_resources
            on_disk = load_resources().get(jurisdiction_slug, {})
            known = set(on_disk) or set(j.resources)
            if known and n.object.kind not in known:
                problems.append(f"{n.id}: unknown resource '{n.object.kind}' in {jurisdiction_slug}")

    norm_ids = {n.id for n in norm_set.norms}
    from .ontology import actor_type  # noqa: PLC0415 (avoid import cycle at module load)
    for h in norm_set.holdings:
        if h.under not in norm_ids:
            problems.append(f"{h.id}: cites unknown norm '{h.under}'")
        if h.activity and j.activities and h.activity not in j.activity_verbs():
            problems.append(f"{h.id}: activity '{h.activity}' not in {jurisdiction_slug}'s activities")
        try:
            if h.holder.actor_kind:
                actor_type(h.holder.actor_kind)
        except Exception as e:
            problems.append(f"{h.id}: bad holder: {e}")
    return problems
