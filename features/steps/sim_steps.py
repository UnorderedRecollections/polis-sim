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
    ctx = BeatContext(sim=context.sim)
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
