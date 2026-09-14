"""Cross-jurisdiction scenarios (task 0068).

One whole director story per jurisdiction on the shared domain sim: the
situation is generated from the jurisdiction's own data, seeded into a
fresh run and driven to enactment. The seed is fixed (`-D seed=…`, default
41) so failures reproduce — the behave port of
`tests/jurisdictions_test.py` (task 0054).
"""
from __future__ import annotations

from behave import given, then, when

from polis import provision


def _seed(context) -> str:
    return context.config.userdata.get("seed") or "41"


@given("the cross-jurisdiction sim is provisioned")
def shared_sim(context):
    provision.Inventory.load(context.sim)   # provisioned in before_scenario


@given('a run is seeded with a generated "{jurisdiction}" situation')
def seed_run(context, jurisdiction):
    from polis.sim import situations
    from polis.sim.director import RunConfig
    from polis.sim.journal import clear_record, new_run, run_dir
    from polis.sim.norms import save_norm_file

    seed = _seed(context)
    situation = situations.generate_situation(jurisdiction, seed=int(seed))
    problems = situations.validate_situation(situation, jurisdiction)
    if problems:
        raise AssertionError(f"{jurisdiction}: {'; '.join(problems[:3])}")
    clear_record(context.sim)
    new_run(context.sim)
    save_norm_file(situation, run_dir(context.sim) / "situation.yaml",
                   description=f"generated: {jurisdiction} (seed {seed})")
    RunConfig(run=context.sim, jurisdiction=jurisdiction, seed=seed).save()
    context.jurisdiction = jurisdiction


@when("the director drives one story")
def drive_one(context):
    from polis.sim.director import drive
    drive(context.sim, 1)


@then("the story was enacted with a ratification")
def story_enacted(context):
    from polis.sim.director import load_stories
    from polis.sim.journal import Journal

    stories = load_stories(context.sim)
    if not stories:
        raise AssertionError("no story was recorded")
    story = stories[-1]
    if story.status != "enacted":
        raise AssertionError(story.error or f"story status: {story.status}")
    if not any(e.action == "bill.ratify" for e in Journal(context.sim).entries()):
        raise AssertionError("the story enacted but no ratification was recorded")
