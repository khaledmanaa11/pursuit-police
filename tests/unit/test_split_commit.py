"""Committing a materialised split repository (08-10, D-76).

THE NO-REMOTE GUARD IS PROVEN BY MAKING IT FIRE. This plan builds locally and
pushes nothing, so `assert_no_remotes` is asserted against a planted remote --
an all-clear from a guard never seen to fire is not an all-clear. The git
assertions are counts (`rev-list --count`, `ls-files | len`), never exit codes,
so an empty repository cannot pass by being looked at and found empty.

Both public entry points refuse a zero-file commit outright: an empty commit is
the vacuous pass `05-18-SUMMARY.md` recorded, wearing a plausible log entry.
"""

from __future__ import annotations

import subprocess

import pytest

from tests.unit.split_fixtures import git_out, tiny_source
from tests.unit.submission_gate_helpers import REPO_ROOT, load

build_mod = load("split_build")
commit_mod = load("split_commit")


def test_the_built_repository_has_one_commit_and_no_remote(tmp_path) -> None:
    source = tiny_source(tmp_path)
    dest = tmp_path / "out"
    build_mod.copy_files(source, dest, ("README.md", "src/mod.py"))
    sha = commit_mod.init_and_commit(dest, ("README.md", "src/mod.py"), "initial", REPO_ROOT)
    assert len(sha) >= 7
    assert git_out(dest, "rev-list", "--count", "HEAD") == "1"
    assert git_out(dest, "remote") == ""
    assert len(git_out(dest, "ls-files").splitlines()) == 2


def test_init_and_commit_refuses_an_empty_file_list(tmp_path) -> None:
    with pytest.raises(commit_mod.EmptyBuildError):
        commit_mod.init_and_commit(tmp_path / "out", (), "initial", REPO_ROOT)


def test_commit_onto_history_refuses_an_empty_file_list(tmp_path) -> None:
    with pytest.raises(commit_mod.EmptyBuildError):
        commit_mod.commit_onto_history(tmp_path / "out", (), "import", REPO_ROOT)


def test_an_authorless_source_refuses_before_git_init_touches_the_destination(tmp_path) -> None:
    """The identity is read first, so the refusal leaves the destination untouched."""
    source = tmp_path / "authorless"
    source.mkdir()
    (source / "pyproject.toml").write_text('[project]\nname = "x"\n', encoding="utf-8")
    dest = tmp_path / "out"
    dest.mkdir()
    with pytest.raises(ValueError):
        commit_mod.init_and_commit(dest, ("README.md",), "initial", source)
    assert not (dest / ".git").exists()


def test_the_no_remote_guard_fires_on_a_planted_remote(tmp_path) -> None:
    source = tiny_source(tmp_path)
    dest = tmp_path / "out"
    build_mod.copy_files(source, dest, ("README.md",))
    commit_mod.init_and_commit(dest, ("README.md",), "initial", REPO_ROOT)
    subprocess.run(
        ["git", "remote", "add", "origin", "../elsewhere.git"],
        cwd=dest, check=True, capture_output=True,
    )
    assert commit_mod.remotes(dest) == ("origin",)
    with pytest.raises(commit_mod.RemoteFoundError):
        commit_mod.assert_no_remotes(dest)


def test_the_no_remote_guard_passes_on_the_freshly_built_tree(tmp_path) -> None:
    source = tiny_source(tmp_path)
    dest = tmp_path / "out"
    build_mod.copy_files(source, dest, ("README.md",))
    commit_mod.init_and_commit(dest, ("README.md",), "initial", REPO_ROOT)
    assert commit_mod.remotes(dest) == ()
    assert commit_mod.assert_no_remotes(dest) == 0


def test_the_commit_identity_is_read_from_the_project_metadata() -> None:
    name, email = commit_mod.commit_identity(REPO_ROOT)
    declared = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert name and email
    assert name in declared
    assert email in declared
