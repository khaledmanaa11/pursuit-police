"""The two git rows that INVERT when a submission repository carries history.

08-10 asserted "exactly one commit" and "history disjoint from the source".
Both were true, both were load-bearing, and both stated the same decision: keep
private working history out of a public artifact. D-83 reverses that decision
because the source is already public and SEGAL Sec17 grades orderly Git history
on the repository handed in.

A REVERSED CHECK IS THE EASIEST PLACE TO HIDE A VACUOUS PASS. "Not disjoint" is
satisfied by any shared object; "more than one commit" by any clone that kept
two. So the replacements are SPECIFIC: the count must equal the source's own
count plus exactly one, and the import commit must descend DIRECTLY from the
commit the source is sitting on. Each test below drives the failing shape too,
because a row never seen to fail guards nothing.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from split_history import clone_history  # noqa: E402
from split_report import (  # noqa: E402
    preserved_history_row,
    rooted_history_row,
)

SOURCE_COMMITS = 3


def _git(root: Path, *args: str) -> str:
    done = subprocess.run(
        ["git", *args], cwd=root, capture_output=True, text=True, check=True
    )
    return done.stdout.strip()


def _commit(root: Path, message: str) -> None:
    _git(root, "add", "-A")
    _git(root, "-c", "user.name=T", "-c", "user.email=t@e",
         "-c", "commit.gpgsign=false", "commit", "--no-verify", "-m", message)


@pytest.fixture
def source(tmp_path: Path) -> Path:
    root = tmp_path / "source"
    root.mkdir()
    _git(root, "init", "-b", "main")
    for index in range(SOURCE_COMMITS):
        (root / f"f{index}.txt").write_text(f"{index}\n", encoding="utf-8")
        _commit(root, f"c{index}")
    return root


@pytest.fixture
def built(source: Path, tmp_path: Path) -> Path:
    """A clone with the import commit on top -- the shape a real build makes."""
    dest = tmp_path / "out"
    clone_history(source, dest)
    (dest / "README.md").write_text("banner\n", encoding="utf-8")
    _commit(dest, "chore: submission import")
    return dest


def test_the_preserved_history_row_passes_at_exactly_source_plus_one(
    built: Path,
) -> None:
    row = preserved_history_row(built, SOURCE_COMMITS)
    assert row.ok, row.detail
    assert str(SOURCE_COMMITS + 1) in row.detail


def test_a_truncated_history_fails_rather_than_shipping_with_holes(
    built: Path,
) -> None:
    """A shallow clone would satisfy 'more than one commit'. Not this row."""
    assert not preserved_history_row(built, SOURCE_COMMITS + 5).ok


def test_a_missing_import_commit_fails_the_count(
    source: Path, tmp_path: Path
) -> None:
    dest = tmp_path / "bare"
    clone_history(source, dest)
    assert not preserved_history_row(dest, SOURCE_COMMITS).ok


def test_the_rooted_row_passes_when_the_parent_is_the_sources_head(
    source: Path, built: Path
) -> None:
    row = rooted_history_row(source, built)
    assert row.ok, row.detail


def test_a_build_that_forgot_its_import_commit_is_not_rooted(
    source: Path, tmp_path: Path
) -> None:
    """HEAD would then BE the source's HEAD -- shared, not descended from it."""
    dest = tmp_path / "bare"
    clone_history(source, dest)
    assert not rooted_history_row(source, dest).ok


def test_a_history_from_somewhere_else_is_not_rooted(
    built: Path, tmp_path: Path
) -> None:
    """The control: a repository whose commits the source has never seen."""
    stranger = tmp_path / "stranger"
    stranger.mkdir()
    _git(stranger, "init", "-b", "main")
    (stranger / "x.txt").write_text("x\n", encoding="utf-8")
    _commit(stranger, "unrelated")
    assert not rooted_history_row(stranger, built).ok
