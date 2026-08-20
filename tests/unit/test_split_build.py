"""Materialising one split repository's file tree on disk (08-10, D-76).

TWO REFUSALS ARE THE POINT OF THIS FILE, and each is proven by making the bad
thing happen rather than by reading the code:

* a destination INSIDE the source repository -- `git init` inside a working tree
  is how a split gets an inherited history and, one reflex `git push` later, 486
  private commits on a public URL;
* a build of zero files -- an empty repository passes every quality gate by
  looking at nothing, which is the vacuity `05-18-SUMMARY.md` recorded.

The commit-and-remote refusals moved with the commit machinery: they are proven
in `tests/unit/test_split_commit.py`.
"""

from __future__ import annotations

import stat

import pytest

from tests.unit.split_fixtures import tiny_source
from tests.unit.submission_gate_helpers import REPO_ROOT, load

build_mod = load("split_build")


def test_a_destination_inside_the_source_repository_is_refused(tmp_path) -> None:
    with pytest.raises(build_mod.UnsafeDestinationError):
        build_mod.prepare_destination(REPO_ROOT / "build-here", REPO_ROOT)


def test_a_destination_that_is_the_source_repository_is_refused() -> None:
    with pytest.raises(build_mod.UnsafeDestinationError):
        build_mod.prepare_destination(REPO_ROOT, REPO_ROOT)


def test_an_outside_destination_is_created(tmp_path) -> None:
    dest = build_mod.prepare_destination(tmp_path / "pursuit-police", REPO_ROOT)
    assert dest.is_dir()
    assert not any(dest.iterdir())


def test_an_existing_destination_is_replaced_only_on_request(tmp_path) -> None:
    dest = tmp_path / "pursuit-police"
    dest.mkdir()
    (dest / "stale.txt").write_text("old", encoding="utf-8")
    with pytest.raises(build_mod.UnsafeDestinationError):
        build_mod.prepare_destination(dest, REPO_ROOT, replace=False)
    build_mod.prepare_destination(dest, REPO_ROOT, replace=True)
    assert not (dest / "stale.txt").exists()


def test_replace_removes_a_tree_holding_read_only_files(tmp_path) -> None:
    """Git writes its objects read-only; the first real rebuild died on WinError 5."""
    dest = tmp_path / "pursuit-police"
    (dest / "objects").mkdir(parents=True)
    victim = dest / "objects" / "blob"
    victim.write_text("x", encoding="utf-8")
    victim.chmod(stat.S_IREAD)
    build_mod.prepare_destination(dest, REPO_ROOT, replace=True)
    assert dest.is_dir()
    assert not any(dest.iterdir())


def test_copy_files_copies_every_listed_path_and_counts_them(tmp_path) -> None:
    source = tiny_source(tmp_path)
    dest = tmp_path / "out"
    copied = build_mod.copy_files(source, dest, ("README.md", "src/mod.py"))
    assert copied == 2
    assert (dest / "src" / "mod.py").read_text(encoding="utf-8") == "VALUE = 1\n"
    assert (dest / "README.md").read_text(encoding="utf-8") == "# Title\n\nbody\n"


def test_copy_files_refuses_an_empty_file_list(tmp_path) -> None:
    with pytest.raises(build_mod.EmptyBuildError):
        build_mod.copy_files(tiny_source(tmp_path), tmp_path / "out", ())


def test_copy_files_refuses_a_path_that_is_not_in_the_source(tmp_path) -> None:
    with pytest.raises(FileNotFoundError):
        build_mod.copy_files(tiny_source(tmp_path), tmp_path / "out", ("ghost.py",))
