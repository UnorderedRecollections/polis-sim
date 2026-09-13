"""Queue driver semantics (task 0060) — no containers, no sim.

The scheduling layer (submit → service → pause/resume → done) is tested
against a stub `execute_beat`; the real actions are exercised by the BDD
suites and `tests/scenarios-demo.sh`.

Run: uv run python tests/queue_driver_test.py
"""
from __future__ import annotations

import os
import shutil
import tempfile
import textwrap
from pathlib import Path

RUN = "queue-test"
FAIL = "the docket shows the petition is answered"

tmp = Path(tempfile.mkdtemp(prefix="polis-queue-test-"))
os.environ["POLIS_SIM_DIR"] = str(tmp)

from polis.sim import queue                    # noqa: E402  (env first)
from polis.sim.beats import BeatFailed         # noqa: E402
from polis.sim.journal import Journal          # noqa: E402

calls: list[str] = []
fail_on: set[str] = set()


def fake_execute(ctx, text: str) -> None:
    calls.append(text)
    if text in fail_on:
        raise BeatFailed(f"stubbed failure: {text}")


queue.execute_beat = fake_execute

PASSED = 0


def check(name: str, cond: bool, detail: str = "") -> None:
    global PASSED
    assert cond, f"{name}: {detail}"
    PASSED += 1
    print(f"  ok   {name}")


def feature(text: str, name: str) -> Path:
    p = tmp / name
    p.write_text(textwrap.dedent(text))
    return p


STORY = """\
Feature: paced intervention
  Scenario: a story with two actions and two goals
    Given a petition of the fishers of cogswich about the northern banks
    When the legislator drafts "Paced Act" into fisheries
    Then the docket shows the petition is answered
    When the Keeper ratifies it with remedy "quota" superseding "N-0001"
    Then norm "N-0001" is superseded in the situation
"""

FAILURE = """\
Feature: pause on failure
  Scenario: the goal is not yet true
    Given a petition of the fishers of cogswich about the northern banks
    When the legislator drafts "Doomed Act" into fisheries
    Then the docket shows the petition is answered
    When the Keeper ratifies it with remedy "quota" superseding "N-0001"
"""

OTHER = """\
Feature: the sim goes on
  Scenario: another scenario keeps moving
    Given a petition of the fishers of brasshaven about the northern banks
    When the legislator drafts "Bystander Act" into fisheries
"""

print("queue driver semantics (stub execute_beat)")

# --- submit: Given = precondition, executed now ------------------------------
st = queue.submit(RUN, str(feature(STORY, "story.feature")))
slug = st.slug
check("submit executes the Given precondition",
      calls == ["a petition of the fishers of cogswich about the northern banks"], calls)
check("submit leaves the scenario active at the first When",
      st.status == "active" and st.position == 1, (st.status, st.position))
check("Given beat recorded as executed", st.beats[0].status == "executed")

# --- service: one action per call, goals evaluated as reached ----------------
st = [s for s in queue.service(RUN) if s.slug == slug][0]
check("one action per service, adjacent goal evaluated",
      calls[1:] == ['the legislator drafts "Paced Act" into fisheries',
                    "the docket shows the petition is answered"], calls)
check("position advanced past the goal; still active",
      st.position == 3 and st.status == "active", (st.position, st.status))
check("goal passed", st.beats[2].status == "passed")

st = [s for s in queue.service(RUN) if s.slug == slug][0]
check("the second service completes the scenario", st.status == "done", st.status)
check("all beats executed/passed",
      all(b.status in ("executed", "passed") for b in st.beats),
      [b.status for b in st.beats])

# --- failure pauses; the sim goes on; resume retries -------------------------
calls.clear()
fail_on.add(FAIL)
st = queue.submit(RUN, str(feature(FAILURE, "failure.feature")), name="pauses")
queue.service(RUN)
st = queue.load_state(RUN, "pauses")
check("a failed goal pauses the scenario", st.status == "paused", st.status)
check("the error names the beat",
      st.error and FAIL in st.error, st.error)
check("the failed beat stops the scenario there",
      st.beats[3].status == "pending", [b.status for b in st.beats])

st = queue.submit(RUN, str(feature(OTHER, "other.feature")), name="bystander")
queue.service(RUN)
st = queue.load_state(RUN, "bystander")
check("another scenario keeps moving while one is paused",
      st.status == "done", st.status)

fail_on.clear()
queue.resume(RUN, "pauses")
queue.service(RUN)
st = queue.load_state(RUN, "pauses")
check("resume retries the failed goal to completion", st.status == "done", st.status)
check("the failed beat was retried and passed", st.beats[2].status == "passed")

# --- the journal carries the scoreboard --------------------------------------
observations = [e for e in Journal(RUN).entries() if e.actor == "scenario"]
check("every beat left a scenario observation in the journal",
      len(observations) >= len(st.beats), len(observations))

shutil.rmtree(tmp, ignore_errors=True)
print(f"\nQUEUE DRIVER TESTS PASSED ({PASSED} checks)")
