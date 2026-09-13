"""Cross-jurisdiction suite (task 0054) — one whole story per jurisdiction.

For each of the 15 jurisdictions: generate and validate a situation from
the jurisdiction's own data (`polis/sim/situations.py`), seed a fresh run
on one provisioned sim, and let the director drive one whole story to
enactment. Per-jurisdiction pass/fail is reported (with the story's
error), so domain bugs surface in a reproducible way (`--seed`).

Run: uv run python tests/jurisdictions_test.py [--seed N]
"""
from __future__ import annotations

import importlib
import os
import shutil
import sys
from pathlib import Path

RUN = "juris-01"
SEED = "41"


def _seed() -> str:
    if "--seed" in sys.argv:
        return sys.argv[sys.argv.index("--seed") + 1]
    return SEED


def _destroy(sim: str) -> None:
    from polis import provision
    try:
        provision.destroy(sim)
    except Exception:
        pass
    shutil.rmtree(Path("data/sims") / sim, ignore_errors=True)


def main() -> int:
    seed = _seed()
    from polis import config, provision, store

    # the suite drives phase-1 stories on a gogs sim
    world = store.load_world()
    if world.federation.phase != 1:
        world.federation.phase = 1
        store.save_world(world)
    print(f"cross-jurisdiction suite (seed={seed}, sim={RUN})", flush=True)
    _destroy(RUN)
    provision.up(RUN)
    os.environ["POLIS_PROVISIONED_SIM"] = RUN
    importlib.reload(config)

    from polis.sim import situations
    from polis.sim.director import DirectorError, RunConfig, drive, load_stories
    from polis.sim.journal import Journal, clear_record, new_run, run_dir
    from polis.sim.norms import save_norm_file

    slugs = sorted(situations.load_jurisdictions())
    results: list[tuple[str, str, str]] = []

    for slug in slugs:
        clear_record(RUN)
        try:
            ns = situations.generate_situation(slug, seed=int(seed))
            problems = situations.validate_situation(ns, slug)
            if problems:
                raise situations.SituationError("; ".join(problems[:3]))
        except Exception as e:
            results.append((slug, "situation", str(e)[:200]))
            print(f"  {slug:22} situation  {str(e)[:70]}", flush=True)
            continue

        new_run(RUN)
        save_norm_file(ns, run_dir(RUN) / "situation.yaml",
                       description=f"generated: {slug} (seed {seed})")
        RunConfig(run=RUN, jurisdiction=slug, seed=seed).save()
        try:
            drive(RUN, 1)
            story = load_stories(RUN)[-1]
            ratified = any(e.action == "bill.ratify" for e in Journal(RUN).entries())
            if story.status != "enacted":
                raise DirectorError(story.error or story.status)
            if not ratified:
                raise DirectorError("the story enacted but no ratification was recorded")
            story_title = story.bindings.get("title", "")
            results.append((slug, "ok", story_title))
            print(f"  {slug:22} ok         {story_title}", flush=True)
        except Exception as e:
            results.append((slug, "story", str(e)[:200]))
            print(f"  {slug:22} story      {str(e)[:70]}", flush=True)

    _destroy(RUN)

    failed = [r for r in results if r[1] != "ok"]
    print(f"\nsummary: {len(results) - len(failed)}/{len(results)} jurisdictions enacted")
    for slug, status, detail in failed:
        print(f"  FAIL {slug:22} {status:9} {detail}")
    if failed:
        print("\nCROSS-JURISDICTION SUITE FAILED")
        return 1
    print("\nCROSS-JURISDICTION SUITE PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
