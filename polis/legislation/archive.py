"""Archive operations — the historical record itself (§1, §2, §12–§15).

  obtain          — clone: the city receives a complete copy of the archive (§2)
  receive         — pull: the gazette arrives; federal enactments incorporated (§2)
  lodge           — push: sending archival acts to the lodged copy (§2)
  promulgate      — tag: a named authoritative edition is proclaimed (§1)
  repeal          — revert: a new act undoing an earlier one; history preserved (§12)
  transplant      — cherry-pick: one act imported without its history (§14)
  reconstruct     — rebase: the genealogy of a line of development rewritten (§13)
  replace-history — force push: replacement of the recognized record (§15)

The last four are exceptional archival powers, gated on office powers the
Keeper of the Federal Rolls alone holds (tag:create, revert:main,
branch:manage) — never granted to a city slice.
"""
from __future__ import annotations

from . import gitcmd
from .chamber import Chamber, ChamberError
from .plan import Plan

KEEPER_POWERS = ("tag:create", "revert:main", "branch:manage")


def _actor_powers(chamber: Chamber) -> set[str]:
    held = {o["id"]: o for o in chamber.offices}
    powers: set[str] = set()
    for office_id in chamber.actor.get("occupies", []):
        powers.update((held.get(office_id) or {}).get("powers", []))
    return powers


def _require_power(chamber: Chamber, power: str, act: str) -> None:
    if power not in _actor_powers(chamber):
        raise ChamberError(
            f"{chamber.actor_username} may not {act}: that requires the power "
            f"'{power}', held only by the Keeper of the Federal Rolls"
        )


# --- circulation of the archive (§2) ------------------------------------------

def obtain(chamber: Chamber) -> Plan:
    def _clone():
        if (chamber.repo_dir / ".git").exists():
            return                       # already obtained — idempotent
        gitcmd.run(None, "clone", chamber.git_remote_url("origin"),
                   str(chamber.repo_dir))

    def _add_upstream():
        remotes = gitcmd.run(chamber.repo_dir, "remote")
        if "upstream" not in remotes.split():
            gitcmd.run(chamber.repo_dir, "remote", "add", "upstream",
                       chamber.git_remote_url("upstream"))

    plan = Plan(act="obtain the archive", actor=chamber.actor_label)
    plan.add(
        machinery=gitcmd.cmd_string(None, "clone", chamber.git_remote_url("origin", masked=True),
                                    str(chamber.repo_dir)),
        legal="the city receives a complete copy of the legal archive (§2)",
        run=_clone,
    )
    plan.add(
        machinery=gitcmd.cmd_string(chamber.repo_dir, "remote", "add", "upstream",
                                    chamber.git_remote_url("upstream", masked=True)),
        legal="the federal archive is recognized as the source legal order (upstream)",
        run=_add_upstream,
    )

    def _ensure_main():
        # gogs repos created via the API have HEAD → nonexistent "master";
        # the clone then checks out nothing. Establish local main.
        try:
            gitcmd.run(chamber.repo_dir, "rev-parse", "--verify", "main")
        except Exception:
            gitcmd.run(chamber.repo_dir, "checkout", "-b", "main", "origin/main")

    plan.add(
        machinery=gitcmd.cmd_string(chamber.repo_dir, "checkout", "-b", "main", "origin/main")
                  + "  (if the clone came up empty)",
        legal="the archive's authoritative line (main) is before the archivist's eyes",
        run=_ensure_main,
    )
    return plan


def receive(chamber: Chamber, ref: str = "main") -> Plan:
    plan = Plan(act=f"receive the gazette ({ref})", actor=chamber.actor_label)
    plan.add(
        machinery=gitcmd.cmd_string(chamber.repo_dir, "pull", "upstream", ref),
        legal="federal enactments are brought into the city's archive (§2)",
        run=lambda: gitcmd.run(chamber.repo_dir, "pull", chamber.git_remote_url("upstream"), ref),
    )
    return plan


def lodge(chamber: Chamber, ref: str = "main") -> Plan:
    plan = Plan(act=f"lodge archival acts ({ref})", actor=chamber.actor_label)
    plan.add(
        machinery=f"git -C {chamber.repo_dir} push origin {ref}",
        legal="the city's archival acts are sent to its lodged copy (§2)",
        run=lambda: gitcmd.run(chamber.repo_dir, "push", chamber.git_remote_url("origin"), ref),
    )
    return plan


# --- acts upon the record ------------------------------------------------------

def promulgate(chamber: Chamber, name: str, message: str, ref: str = "main") -> Plan:
    """A named authoritative edition is proclaimed (tag, §1)."""
    author_name, author_email = chamber.author

    def run():
        _require_power(chamber, "tag:create", f"promulgate the edition “{name}”")
        gitcmd.run(chamber.repo_dir,
                   "-c", f"user.name={author_name}", "-c", f"user.email={author_email}",
                   "tag", "-a", name, "-m", message, ref)

    plan = Plan(act=f"promulgate the edition “{name}”", actor=chamber.actor_label)
    plan.add(
        machinery=gitcmd.cmd_string(chamber.repo_dir,
                                    "-c", f"user.name={author_name}",
                                    "-c", f"user.email={author_email}",
                                    "tag", "-a", name, "-m", message, ref),
        legal="a named authoritative edition of the corpus is proclaimed (§1)",
        run=run,
    )
    plan.add(
        machinery=f"git -C {chamber.repo_dir} push origin {name}",
        legal="the edition is entered into the lodged record",
        run=lambda: gitcmd.run(chamber.repo_dir, "push", chamber.git_remote_url("origin"), name),
    )
    return plan


def repeal(chamber: Chamber, act: str, mainline: int | None = None) -> Plan:
    """A new act that reverses the effect of an earlier act (revert, §12).

    Repealing an enactment recorded as a merge requires --mainline 1: the
    repealing act is measured against the authoritative line, not the
    bill's own history."""
    args = ["revert", "--no-edit"]
    if mainline:
        args += ["-m", str(mainline)]
    args.append(act)

    def run():
        _require_power(chamber, "revert:main", f"repeal the act {act}")
        gitcmd.run(chamber.repo_dir, *args)

    plan = Plan(act=f"repeal the act {act}", actor=chamber.actor_label)
    plan.add(
        machinery=gitcmd.cmd_string(chamber.repo_dir, *args),
        legal="a repealing act is recorded — the original act remains in the "
              "historical record (§12)",
        run=run,
    )
    return plan


def transplant(chamber: Chamber, act: str) -> Plan:
    """One act incorporated without its surrounding history (cherry-pick, §14)."""
    def run():
        _require_power(chamber, "branch:manage", f"transplant the act {act}")
        gitcmd.run(chamber.repo_dir, "cherry-pick", act)

    plan = Plan(act=f"transplant the act {act}", actor=chamber.actor_label)
    plan.add(
        machinery=gitcmd.cmd_string(chamber.repo_dir, "cherry-pick", act),
        legal="a legal transplant: one particular act is incorporated into this "
              "line of development without importing its history (§14)",
        run=run,
    )
    return plan


def reconstruct(chamber: Chamber, onto: str) -> Plan:
    """Replaying a line of development on a new foundation (rebase, §13)."""
    def run():
        _require_power(chamber, "branch:manage", f"reconstruct the lineage onto {onto}")
        gitcmd.run(chamber.repo_dir, "rebase", onto)

    plan = Plan(act=f"reconstruct the lineage onto {onto}", actor=chamber.actor_label)
    plan.add(
        machinery=gitcmd.cmd_string(chamber.repo_dir, "rebase", onto),
        legal="archival reconstruction: the genealogy of this line of development "
              "is rewritten upon a different historical foundation (§13)",
        run=run,
    )
    return plan


def replace_history(chamber: Chamber, ref: str = "main") -> Plan:
    """Replacement of the recognized record (force push, §15) — exceptional."""
    def run():
        _require_power(chamber, "branch:manage", f"replace the recognized history of {ref}")
        gitcmd.run(chamber.repo_dir, "push", "--force-with-lease",
                   chamber.git_remote_url("origin"), ref)

    plan = Plan(act=f"replace the recognized history of {ref}", actor=chamber.actor_label)
    plan.add(
        machinery=f"git -C {chamber.repo_dir} push --force-with-lease origin {ref}",
        legal="the lodged archive is commanded to recognize an alternative historical "
              "lineage — an exceptional archival power, not mere addition (§15)",
        run=run,
    )
    return plan


# --- inspection (read-only) ------------------------------------------------------

def editions(chamber: Chamber) -> list[str]:
    """The proclaimed editions (tags)."""
    out = gitcmd.run(chamber.repo_dir, "tag", "--list")
    return [t for t in out.splitlines() if t]


def inspect(chamber: Chamber, limit: int = 20) -> str:
    """The genealogy of the current line (recent archival acts)."""
    return gitcmd.run(chamber.repo_dir, "log", "--oneline", f"-{limit}")
