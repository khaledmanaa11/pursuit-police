"""D-83: carrying the development history into a submission repository.

THE HAZARD THIS REVERSES IS REAL AND IS TESTED HERE, NOT ASSUMED AWAY.
`split_build.py` refuses to build inside the source tree precisely because a
clone inherits the source's `origin`, and one reflex push then publishes
private history. `--with-history` clones ON PURPOSE, so the inherited-remote
half of that hazard is the first thing asserted below: a destination that
reaches the caller with a remote is the failure, and `test_the_clone_arrives_
with_no_remote` is what stops it shipping.

Every test builds a throwaway git repository in `tmp_path`. None reads the
real development tree, and none touches a network.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from split_history import (  # noqa: E402
    HistoryCloneError,
    clone_history,
    prune_to_manifest,
    tracked_at_head,
)


def _git(root: Path, *args: str) -> str:
    done = subprocess.run(
        ["git", *args], cwd=root, capture_output=True, text=True, check=True
    )
    return done.stdout.strip()


@pytest.fixture
def source(tmp_path: Path) -> Path:
    """A source repository with three commits on `main`."""
    root = tmp_path / "source"
    root.mkdir()
    _git(root, "init", "-b", "main")
    for index in range(3):
        (root / f"file{index}.txt").write_text(f"content {index}\n", encoding="utf-8")
        _git(root, "add", "-A")
        _git(root, "-c", "user.name=T", "-c", "user.email=t@e",
             "-c", "commit.gpgsign=false", "commit", "--no-verify", "-m", f"c{index}")
    return root


def test_the_clone_carries_every_commit(source: Path, tmp_path: Path) -> None:
    dest = tmp_path / "out"
    assert clone_history(source, dest) == 3
    assert _git(dest, "rev-list", "--count", "HEAD") == "3"


def test_the_clone_arrives_with_no_remote(source: Path, tmp_path: Path) -> None:
    """The whole hazard `git init` existed to avoid, closed at the source."""
    dest = tmp_path / "out"
    clone_history(source, dest)
    assert _git(dest, "remote") == "", "the inherited origin survived the clone"


def test_a_single_commit_source_is_refused(tmp_path: Path) -> None:
    """The vacuous pass: a 'history' of one commit has carried no history."""
    root = tmp_path / "thin"
    root.mkdir()
    _git(root, "init", "-b", "main")
    (root / "only.txt").write_text("x\n", encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "-c", "user.name=T", "-c", "user.email=t@e",
         "-c", "commit.gpgsign=false", "commit", "--no-verify", "-m", "one")
    with pytest.raises(HistoryCloneError, match="1 commit"):
        clone_history(root, tmp_path / "out")


def test_a_missing_branch_raises_rather_than_building_nothing(
    source: Path, tmp_path: Path
) -> None:
    with pytest.raises(HistoryCloneError, match="failed"):
        clone_history(source, tmp_path / "out", branch="does-not-exist")


def test_pruning_removes_only_what_the_manifest_omits(
    source: Path, tmp_path: Path
) -> None:
    dest = tmp_path / "out"
    clone_history(source, dest)
    keep = ("file0.txt", "file2.txt")
    assert prune_to_manifest(dest, keep) == ("file1.txt",)
    assert not (dest / "file1.txt").exists()
    assert sorted(tracked_at_head(dest)) == ["file0.txt", "file2.txt"]


def test_pruning_a_complete_manifest_removes_nothing(
    source: Path, tmp_path: Path
) -> None:
    """The clean-tree case: the two paths agree, so the import commit deletes
    nothing. A prune that removed something here would mean the manifest and
    the history disagree about what the project contains."""
    dest = tmp_path / "out"
    clone_history(source, dest)
    assert prune_to_manifest(dest, tracked_at_head(dest)) == ()
