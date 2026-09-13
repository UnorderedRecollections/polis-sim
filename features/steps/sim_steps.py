"""behave wrappers around polis.sim.beats — the shared binding table.

All semantics live in polis/sim/beats.py (one binding, two drivers); the
queue driver (0034b) uses the same functions for live intervention.
"""
from __future__ import annotations

import importlib

from behave import given, then, when

from polis.sim import beats
from polis.sim.beats import BeatContext


def _ctx(context) -> BeatContext:
    ctx = BeatContext(sim=context.sim, platform=getattr(context, "platform", "gogs"))
    for k in ("petition_id", "bill_branch", "matter_id", "title",
              "petitioner", "city", "jurisdiction"):
        setattr(ctx, k, getattr(context, k, None))
    return ctx


def _back(context, ctx: BeatContext) -> None:
    for k in ("petition_id", "bill_branch", "matter_id", "title",
              "petitioner", "city", "jurisdiction"):
        setattr(context, k, getattr(ctx, k))


@given('a provisioned sim seeded from "{jurisdiction}"')
def provisioned(context, jurisdiction):
    import polis.config
    beats.b_provisioned_sim(_ctx(context), jurisdiction)
    importlib.reload(polis.config)   # secrets.json now exists → sim endpoints
    context.jurisdiction = jurisdiction


@given('a petition of the {actor_kind}s of {city} about the {resource}')
def petition(context, actor_kind, city, resource):
    ctx = _ctx(context)
    beats.b_petition(ctx, actor_kind, city, resource)
    _back(context, ctx)


@when('the legislator drafts "{title}" into {into}')
def drafts(context, title, into):
    ctx = _ctx(context)
    beats.b_drafts(ctx, title, into)
    _back(context, ctx)


@when('the Keeper ratifies it with remedy "{remedy}" superseding "{norm_id}"')
def ratifies(context, remedy, norm_id):
    ctx = _ctx(context)
    beats.b_keeper_ratifies(ctx, remedy, norm_id)


@then('the archive main contains "{text}"')
def archive_contains(context, text):
    beats.b_archive_contains(_ctx(context), text)


@then('norm "{norm_id}" is superseded in the situation')
def norm_superseded(context, norm_id):
    beats.b_norm_superseded(_ctx(context), norm_id)


@then("the docket shows the petition is answered")
def petition_answered(context):
    beats.b_petition_answered(_ctx(context))


# --- the transition arc (task 0053) -----------------------------------------

@when("the federation codifies its machinery")
def codify(context):
    ctx = _ctx(context)
    beats.b_codify(ctx)
    _back(context, ctx)
    # the transition's machinery effect belongs to the driver, not the
    # scenario: the host erects the Mechanical Magistrate's CI (task 0059)
    import os
    if not os.environ.get("POLIS_SIM_DIR"):
        from polis import provision
        try:
            provision.up_woodpecker(context.sim)
        except provision.ProvisionError as e:
            raise beats.BeatFailed(f"the CI was not erected: {e}") from e


@then("the federation operates in phase {phase}")
def phase(context, phase):
    beats.b_phase_is(_ctx(context), phase)


@then('the corpus contains "{path}"')
def corpus(context, path):
    beats.b_corpus_contains(_ctx(context), path)


@then("the Mechanical Magistrate's CI is erected")
def ci_erected(context):
    beats.b_ci_erected(_ctx(context))


@then("the petition is a real issue on the platform")
def petition_issue(context):
    beats.b_petition_is_issue(_ctx(context))


@then("the bill is a real pull request on the platform")
def bill_pr(context):
    beats.b_bill_is_pr(_ctx(context))


@then("the bill's pull request is merged")
def bill_pr_merged(context):
    beats.b_bill_pr_merged(_ctx(context))


@when("the jurist approves the bill")
def jurist_approves(context):
    beats.b_jurist_approves(_ctx(context))


@then("the Mechanical Magistrate approves the bill")
def ci_approves(context):
    beats.b_ci_approves(_ctx(context))


@then("the Mechanical Magistrate rejects the bill")
def ci_rejects(context):
    beats.b_ci_rejects(_ctx(context))
