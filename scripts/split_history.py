"""Cloning the development history into a split repository (08-12, D-83).

WHY THIS EXISTS, AND WHY IT REVERSES A DELIBERATE EARLIER CHOICE. 08-10 built
each submission repository with `git init` and one commit, and
`split_build.py`'s own docstring calls an inherited history a hazard: a clone
carries the source's `origin`, so one reflex `git push` publishes several
hundred private commits to a public URL. That reasoning was sound while the
development repository was private and its history unpublished.

Both premises changed. The owner's `origin` is PUBLIC -- so the history is
already published and this module discloses nothing new -- and
`docs/SEGAL_GUIDELINES.md:325` grades "orderly Git history" among the
Extensibility & standards items, judged on the repository that is handed in.
A submission repository with one commit hides 576 commits of TDD from the
one reader they were kept for.

THE HAZARD IS REAL AND IS ANSWERED HERE, NOT WISHED AWAY. `git clone` writes
an `origin` pointing at the source; `clone_history` removes it before
returning and asserts it is gone, so the destination reaches the caller with
zero remotes exactly as the `git init` path does. `split_report.no_remote_row`
then re-checks the same property from the outside. A push in a freshly built
output cannot reach the development repository because there is nothing left
to push to.

WHAT IS CLONED IS `main` AND NOTHING ELSE. `--single-branch` keeps other
branches out, and the source carries no tags (`git tag -l` is empty here by
D-79, which puts the tag on the built artifact instead), so no tag rides along
to be published by accident.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from split_commit import RemoteFoundError, assert_no_remotes

#: The one branch a submission repository carries.
BRANCH = "main"


class HistoryCloneError(RuntimeError):
    """The source history could not be cloned, or arrived in the wrong shape."""


def _run(root: Path, *args: str) -> str:
    done = subprocess.run(
        ["git", *args], cwd=root, capture_output=True, text=True, check=True
    )
    return done.stdout.strip()


def clone_history(source_root: Path, dest: Path, branch: str = BRANCH) -> int:
    """Clone *branch* of *source_root* into *dest*, then drop the inherited remote.

    Returns the number of commits cloned. The destination is left with zero
    remotes, which is asserted here rather than assumed -- an `origin` surviving
    this function is the whole hazard the `git init` path existed to avoid.
    """
    source_root, dest = Path(source_root).resolve(), Path(dest).resolve()
    done = subprocess.run(
        [
            "git", "clone", "--no-hardlinks", "--single-branch",
            "--branch", branch, str(source_root), str(dest),
        ],
        capture_output=True, text=True, check=False,
    )
    if done.returncode != 0:
        raise HistoryCloneError(
            f"cloning {branch} of {source_root} into {dest} failed "
            f"(exit {done.returncode}): {done.stderr.strip()}"
        )
    _drop_origin(dest)
    count = int(_run(dest, "rev-list", "--count", "HEAD") or 0)
    if count < 2:
        raise HistoryCloneError(
            f"{dest} came back with {count} commit(s). This path exists to carry the "
            "development history; a clone that produced one commit has carried none, "
            "and would pass a history check by looking at nothing."
        )
    return count


def _drop_origin(dest: Path) -> None:
    """Remove every remote the clone inherited, and prove none survived."""
    for name in _run(dest, "remote").splitlines():
        if name.strip():
            _run(dest, "remote", "remove", name.strip())
    try:
        assert_no_remotes(dest)
    except RemoteFoundError as exc:  # pragma: no cover -- belt to the loop above
        raise HistoryCloneError(
            f"{dest} still carries a remote after the clone's origin was removed. "
            "Refusing to hand back a destination that a reflex push could publish to."
        ) from exc


def tracked_at_head(dest: Path) -> tuple[str, ...]:
    """Every path the cloned HEAD tracks, in git's own order."""
    return tuple(
        line.strip() for line in _run(dest, "ls-files").splitlines() if line.strip()
    )


def prune_to_manifest(dest: Path, keep) -> tuple[str, ...]:
    """Delete cloned files the manifest does not list. Returns what was removed.

    The manifest is `git ls-files` minus `EXCLUDED_GLOBS`, so on a clean tree
    this removes nothing and returns an empty tuple. It runs anyway: the day an
    exclusion starts matching a tracked file, the difference between the two
    paths must be a deletion in the import commit, not a file that silently
    ships because the history brought it along.
    """
    keeping = set(keep)
    removed = []
    for path in tracked_at_head(dest):
        if path not in keeping:
            _run(dest, "rm", "-q", "--cached", "--", path)
            target = Path(dest) / path
            if target.is_file():
                target.unlink()
            removed.append(path)
    return tuple(removed)
