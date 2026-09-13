"""The scenario queue — live Gherkin intervention in a running sim (0034b).

A user submits a .feature; it is parsed into beats (scenario.py),
statically validated, and queued under data/sims/<sim>/queues/. Setup
beats execute AT SUBMISSION (they are preconditions; the sim-creation
beat is validated and skipped — the sim already exists). Action and
expectation beats are serviced by the director, one action per drive
step, expectations evaluated as they are reached — a scenario
*scoreboard* recorded as journal observations.

Omniscient narration: beats execute in submission order, whoever they
name (roadmap §1). A failed beat PAUSES the scenario; the sim goes on.
"""
from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Optional

from . import scenario as scenario_mod
from .beats import BeatContext, BeatFailed, SIM_CREATION, execute_beat, match_beat
from .journal import Journal, JournalEntry, _utcnow, run_dir


class QueueError(RuntimeError):
    pass


@dataclass
class BeatState:
    line: int
    kind: str                       # setup | action | expectation
    text: str
    status: str = "pending"         # pending | executed | passed | failed | skipped


@dataclass
class ScenarioState:
    name: str
    slug: str
    submitted_at: str
    status: str = "active"          # active | paused | done
    position: int = 0
    beats: list[BeatState] = field(default_factory=list)
    ctx: dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


def queues_dir(run_id: str) -> Path:
    return run_dir(run_id) / "queues"


def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:40] or "scenario"


def _state_path(run_id: str, slug: str) -> Path:
    return queues_dir(run_id) / f"{slug}.state.json"


def load_state(run_id: str, slug: str) -> ScenarioState:
    path = _state_path(run_id, slug)
    data = json.loads(path.read_text(encoding="utf-8"))
    data["beats"] = [BeatState(**b) for b in data["beats"]]
    return ScenarioState(**data)


def _save_state(run_id: str, st: ScenarioState) -> None:
    data = asdict(st)
    _state_path(run_id, st.slug).write_text(json.dumps(data, indent=2),
                                            encoding="utf-8")


def list_scenarios(run_id: str) -> list[ScenarioState]:
    qd = queues_dir(run_id)
    if not qd.is_dir():
        return []
    out = []
    for p in sorted(qd.glob("*.state.json")):
        data = json.loads(p.read_text(encoding="utf-8"))
        data["beats"] = [BeatState(**b) for b in data["beats"]]
        out.append(ScenarioState(**data))
    return out


# --- submission -----------------------------------------------------------------

def validate(feature: scenario_mod.Feature) -> list[str]:
    """Static checks at submission: every beat must be a USER beat.

    The sim already exists (the provisioning/setup beat is the test
    harness's), and the operator machinery is not the scenario author's
    business — a submitted scenario is legal actions and in-world goals
    only. Returns errors (empty = valid)."""
    errors: list[str] = []
    for sc in feature.scenarios:
        for beat in sc.beats:
            binding, _ = match_beat(beat.text)
            if binding is None:
                templates = "\n  ".join(f"{b.template}  [{b.scope}]"
                                        for b in _templates())
                errors.append(f"{sc.name}:{beat.line} no binding for {beat.text!r}"
                              f"\n  known forms:\n  {templates}")
            elif not binding.is_user:
                errors.append(
                    f"{sc.name}:{beat.line} '{beat.text}' is a "
                    f"{binding.scope}-scoped beat — a submitted scenario uses "
                    "the user vocabulary only (`polis sim steps --scope user`)")
    return errors


def _templates():
    from .beats import BINDINGS
    return BINDINGS


def submit(run_id: str, feature_path: str, name: Optional[str] = None) -> ScenarioState:
    src = Path(feature_path)
    if not src.exists():
        raise QueueError(f"feature file not found: {feature_path}")
    feature = scenario_mod.parse_feature(src)
    if len(feature.scenarios) != 1:
        raise QueueError("v1: exactly one scenario per feature file")
    sc = feature.scenarios[0]
    errors = validate(feature)
    if errors:
        raise QueueError("scenario rejected:\n" + "\n".join(errors))

    st = ScenarioState(
        name=name or sc.name, slug=_slug(name or sc.name),
        submitted_at=_utcnow(),
        beats=[BeatState(line=b.line, kind=b.kind, text=b.text) for b in sc.beats],
    )
    qd = queues_dir(run_id)
    qd.mkdir(parents=True, exist_ok=True)
    (qd / f"{st.slug}.feature").write_text(src.read_text(encoding="utf-8"),
                                           encoding="utf-8")

    # setup beats execute AT SUBMISSION (the sim-creation beat is skipped —
    # the sim exists); a failing setup rejects the submission
    ctx = BeatContext(sim=run_id)
    journal = Journal(run_id)
    for i, beat in enumerate(st.beats):
        if beat.kind != "setup":
            st.position = i
            break
        binding, _ = match_beat(beat.text)
        if binding is SIM_CREATION:
            beat.status = "skipped"
            _record(journal, st, beat, "skipped",
                    "the sim already exists — the setup beat is the harness's")
            continue
        try:
            execute_beat(ctx, beat.text)
            beat.status = "executed"
            _record(journal, st, beat, "executed")
        except Exception as e:
            _record(journal, st, beat, "failed", str(e))
            raise QueueError(f"setup beat failed at line {beat.line}: {e}") from e
    else:
        st.position = len(st.beats)
    st.ctx = {k: v for k, v in vars(ctx).items() if k != "data"}
    st.ctx["data"] = ctx.data
    _save_state(run_id, st)
    return st


def resume(run_id: str, slug: str) -> ScenarioState:
    """Re-activate a paused scenario: the failed beat becomes pending again
    (after the user fixed whatever made it fail)."""
    st = load_state(run_id, slug)
    if st.status != "paused":
        raise QueueError(f"scenario '{slug}' is {st.status}, not paused")
    st.status = "active"
    st.error = None
    for b in st.beats:
        if b.status == "failed":
            b.status = "pending"
    _save_state(run_id, st)
    return st


# --- servicing (called by the director before each story) ------------------------

def service(run_id: str) -> list[ScenarioState]:
    """Advance every active scenario by one action beat (expectations
    evaluated as reached). Returns the states that changed."""
    changed: list[ScenarioState] = []
    journal = Journal(run_id)
    for st in list_scenarios(run_id):
        if st.status != "active":
            continue
        ctx = BeatContext(**{k: v for k, v in st.ctx.items() if k != "data"})
        ctx.data = st.ctx.get("data", {})
        acted = False
        while st.position < len(st.beats):
            beat = st.beats[st.position]
            if beat.kind == "setup":          # already done at submission
                st.position += 1
                continue
            if beat.kind == "expectation" and not acted:
                pass                          # expectations before any action
            elif beat.kind == "action" and acted:
                break                         # one action per service
            try:
                execute_beat(ctx, beat.text)
                beat.status = "executed" if beat.kind != "expectation" else "passed"
                _record(journal, st, beat, beat.status)
            except Exception as e:
                beat.status = "failed"
                st.status = "paused"
                st.error = f"line {beat.line}: {e}"
                _record(journal, st, beat, "failed", str(e))
                break
            st.position += 1
            if beat.kind == "action":
                acted = True
        if st.position >= len(st.beats) and st.status == "active":
            st.status = "done"
            _record(journal, st, None, "done", "the scenario is complete")
        st.ctx = {k: v for k, v in vars(ctx).items() if k != "data"}
        st.ctx["data"] = ctx.data
        _save_state(run_id, st)
        changed.append(st)
    return changed


def _record(journal: Journal, st: ScenarioState, beat: Optional[BeatState],
            status: str, detail: str = "") -> None:
    journal.append(JournalEntry(
        seq=journal.next_seq(), ts=_utcnow(), kind="observation",
        actor="scenario", action=f"{st.slug}"
        + (f":{beat.line}" if beat else ""),
        params={}, result={
            "scenario": st.name, "status": status,
            **({"beat": beat.text, "kind": beat.kind} if beat else {}),
            **({"detail": detail[:300]} if detail else {}),
        }))
