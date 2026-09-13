"""Performance / scale harness (task 0056).

Builds worlds of a given size, provisions one sim per size, drives a few
director stories and measures the machinery: provisioning time, per-story
drive time, roster/repo counts, record sizes and the archive's git pack
size. The canonical world is snapshotted and restored around the run.

Run:
    uv run python tests/performance_test.py                 # 9 cities, 1 story
    uv run python tests/performance_test.py --cities 9,15,20
    uv run python tests/performance_test.py --legislators-per-city 8 --delegates-per-city 4
"""
from __future__ import annotations

import argparse
import importlib
import json
import os
import shutil
import tempfile
import time
from pathlib import Path

SEED = "42"
JURISDICTION = "fisheries"


def _dir_bytes(path: Path) -> int:
    if path.is_file():
        return path.stat().st_size
    if not path.exists():
        return 0
    return sum(f.stat().st_size for f in path.rglob("*") if f.is_file())


def _backup_world(root: Path) -> Path:
    backup = Path(tempfile.mkdtemp(prefix="polis-perf-world-"))
    src_world, src_cities = root / "world.json", root / "cities"
    if src_world.exists():
        shutil.copy(src_world, backup / "world.json")
    if src_cities.is_dir():
        shutil.copytree(src_cities, backup / "cities")
    return backup


def _restore_world(root: Path, backup: Path) -> None:
    shutil.copy(backup / "world.json", root / "world.json")
    if (backup / "cities").is_dir():
        shutil.rmtree(root / "cities", ignore_errors=True)
        shutil.copytree(backup / "cities", root / "cities")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cities", default="9",
                    help="Comma-separated city counts to measure (default 9).")
    ap.add_argument("--stories", type=int, default=1,
                    help="Director stories per size (default 1).")
    ap.add_argument("--legislators-per-city", type=int, default=3)
    ap.add_argument("--delegates-per-city", type=int, default=2)
    ap.add_argument("--jurisdiction", default=JURISDICTION)
    ap.add_argument("--seed", default=SEED)
    ap.add_argument("--out", type=Path, default=None,
                    help="Write the markdown table here as well.")
    args = ap.parse_args()

    from polis import config, provision, store
    from polis.genesis import build_world
    from polis.sim import situations
    from polis.sim.director import RunConfig, drive, load_stories
    from polis.sim.journal import new_run, run_dir
    from polis.sim.norms import save_norm_file

    world_dir = Path(config.WORLD_FILE).parent
    backup = _backup_world(world_dir)
    rows: list[dict] = []
    try:
        for n in [int(x) for x in args.cities.split(",")]:
            sim = f"perf-{n:02d}"
            try:
                provision.destroy(sim)
            except Exception:
                pass
            shutil.rmtree(Path("data/sims") / sim, ignore_errors=True)

            # a scaled world (in-process: save + export the slices)
            world = build_world(seed=int(args.seed), cities=n,
                                legislators_per_city=args.legislators_per_city,
                                delegates_per_city=args.delegates_per_city)
            store.save_world(world)
            store.export_all_cities(world)

            t0 = time.monotonic()
            provision.up(sim)
            provision_s = time.monotonic() - t0

            os.environ["POLIS_PROVISIONED_SIM"] = sim
            importlib.reload(config)
            new_run(sim)
            ns = situations.generate_situation(args.jurisdiction, seed=int(args.seed))
            save_norm_file(ns, run_dir(sim) / "situation.yaml",
                           description=f"perf seed {args.seed}")
            RunConfig(run=sim, jurisdiction=args.jurisdiction, seed=args.seed).save()

            t0 = time.monotonic()
            drive(sim, args.stories)
            drive_s = time.monotonic() - t0
            stories = load_stories(sim)
            enacted = sum(1 for s in stories if s.status == "enacted")
            failed = next((s for s in stories if s.status != "enacted"), None)

            inv = json.loads((run_dir(sim) / "provision.json").read_text())
            clone_git = run_dir(sim) / "common-law" / ".git"
            row = {
                "cities": n,
                "persons": len(world.persons),
                "repos": len(inv["repos"]),
                "users": len(inv["users"]),
                "provision_s": round(provision_s, 1),
                "drive_s_per_story": round(drive_s / max(args.stories, 1), 1),
                "enacted": f"{enacted}/{args.stories}",
                "journal_b": _dir_bytes(run_dir(sim) / "journal.jsonl"),
                "matters_b": _dir_bytes(run_dir(sim) / "matters.json"),
                "pack_b": _dir_bytes(clone_git),
                "error": (failed.error or failed.status) if failed else "",
            }
            rows.append(row)
            print(f"  n={n:2} persons={row['persons']:4} provision={row['provision_s']:6}s "
                  f"drive/story={row['drive_s_per_story']:6}s enacted={row['enacted']}",
                  flush=True)
            if row["error"]:
                print(f"    first failure: {row['error'][:500]}", flush=True)

            provision.destroy(sim)
            shutil.rmtree(Path("data/sims") / sim, ignore_errors=True)
            os.environ.pop("POLIS_PROVISIONED_SIM", None)
            importlib.reload(config)
    finally:
        _restore_world(world_dir, backup)
        shutil.rmtree(backup, ignore_errors=True)

    header = ("| cities | persons | users | repos | provision s | drive s/story | enacted | "
              "journal B | matters B | git pack B |")
    sep = "|---|---|---|---|---|---|---|---|---|---|"
    table = [header, sep]
    for r in rows:
        table.append("| {cities} | {persons} | {users} | {repos} | {provision_s} | "
                     "{drive_s_per_story} | {enacted} | {journal_b} | {matters_b} | "
                     "{pack_b} |".format(**r))
    report = (f"# Performance measurements (seed {args.seed}, {args.stories} stories, "
              f"jurisdiction {args.jurisdiction})\n\n" + "\n".join(table) + "\n")
    print("\n" + report)
    if args.out:
        args.out.write_text(report, encoding="utf-8")
        print(f"written: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
