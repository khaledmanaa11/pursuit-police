"""Plan, build and verify one submission repository (08-10, 08-12).

WHY BOTH REPOSITORIES CARRY THE SAME FILES. The two agents are separate
PROCESSES, and rule 2 forbids sharing runtime state between them. It does not
forbid the two publishable repositories from carrying the same static library
and the same two configuration directories -- and the test suite loads BOTH
seats, so a repository holding one of them could not run its own quality gates
and therefore could not be shown to meet Table 5 inside its own tree (D-77).

NOTHING HERE TOUCHES A REMOTE. The git this module reaches runs through
`split_commit` (`init`, `add`, `commit`, local reads) and, on the
`--with-history` path, `split_history` -- whose `git clone` copies a LOCAL
source path and whose `remote remove` / `rm --cached` strip the clone's
inherited origin and the manifest-dropped files before the build returns.
Pushing is 08-12, a human, on a human's account.
`scripts/build_split_repos.py` is the CLI over this module.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from split_build import copy_files, prepare_destination
from split_commit import commit_onto_history, init_and_commit
from split_docs import banner, inject, repo_links
from split_gates import (
    RUFF,
    SUITE,
    SYNC,
    coverage_floor,
    run_gate,
    simple_row,
    suite_row,
)
from split_history import clone_history, prune_to_manifest
from split_manifest import manifest_for
from split_provenance import provenance
from split_report import git_rows
from split_verify import (
    absence_row,
    config_row,
    git_out,
    line_limit_row,
    rule50_row,
    workflow_row,
)

PROVENANCE = "docs/REPO-SPLIT.md"


@dataclass(frozen=True)
class BuildPlan:
    """One file list, one source commit, one timestamp -- shared by BOTH outputs.

    DERIVED ONCE, ON PURPOSE. Re-deriving the manifest per role reads the working
    tree twice, minutes apart with a full `pytest --cov` in between; anything that
    changed in the gap would land in the second repository and not the first, and
    two submission repositories that disagree about their own contents is a defect
    no reader could diagnose from either one.
    """

    manifest: object
    source_commit: str
    stamp: str
    #: The source's own commit count -- the floor a preserved history is checked
    #: against, read once with the manifest so both outputs answer to one number.
    source_commits: int = 0


def plan_build(source_root: Path) -> BuildPlan:
    """The single manifest, commit and timestamp every output is built from."""
    return BuildPlan(
        manifest_for(source_root),
        git_out(source_root, "rev-parse", "--short", "HEAD").strip(),
        datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        int(git_out(source_root, "rev-list", "--count", "HEAD").strip() or 0),
    )


def build_one(source_root: Path, dest_root: Path, role: str, replace: bool,
              plan: BuildPlan, with_history: bool = False) -> dict:
    """Materialise one role's repository and return what was built, in numbers."""
    manifest, source_commit, stamp = plan.manifest, plan.source_commit, plan.stamp
    dest = prepare_destination(dest_root, source_root, replace=replace)
    cloned, pruned = 0, ()
    if with_history:
        cloned = clone_history(source_root, dest)
        pruned = prune_to_manifest(dest, manifest.included)
    copied = copy_files(source_root, dest, manifest.included)

    readme = dest / "README.md"
    readme.write_text(
        inject(
            readme.read_text(encoding="utf-8"),
            banner(role, source_commit, stamp, repo_links(source_root)),
        ),
        encoding="utf-8", newline="\n",
    )
    (dest / PROVENANCE).parent.mkdir(parents=True, exist_ok=True)
    (dest / PROVENANCE).write_text(
        provenance(role, source_commit, stamp, manifest.count, manifest.excluded),
        encoding="utf-8", newline="\n",
    )
    staged = (*manifest.included, PROVENANCE)
    verb = "submission import" if with_history else "initial import"
    message = (
        f"chore: {verb} of the {role} submission repository "
        f"(split from {source_commit}, {manifest.count} tracked files)"
    )
    sha = (commit_onto_history if with_history else init_and_commit)(
        dest, staged, message, source_root
    )
    return {
        "role": role, "path": str(dest), "commit": sha, "source_commit": source_commit,
        "generated": stamp, "copied": copied, "staged": len(staged),
        "history": {"carried": with_history, "cloned_commits": cloned,
                    "pruned": list(pruned)},
        "excluded": [{"path": path, "reason": reason} for path, reason in manifest.excluded],
    }


def verify_one(dest: Path, source_root: Path, role: str, with_gates: bool,
               history_floor: int | None = None) -> list:
    """Every row for one built repository, structural first, gates last."""
    rows = [
        *git_rows(dest, source_root, role, history_floor),
        line_limit_row(dest), absence_row(dest), config_row(dest),
        rule50_row(dest), workflow_row(dest),
    ]
    if with_gates:
        rows.append(simple_row("uv sync", *run_gate(dest, SYNC)))
        rows.append(simple_row("ruff check .", *run_gate(dest, RUFF)))
        code, output = run_gate(dest, SUITE)
        rows.append(suite_row(code, output, coverage_floor(dest)))
    return rows
