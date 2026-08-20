"""Miniature source repositories for the split-build test files (08-10).

Shared by `test_split_build`, `test_split_commit`, `test_build_split_repos` and
`test_split_driver`, so the tree a refusal is proven against is one fixture
everywhere rather than four near-copies that can drift apart.
"""

from __future__ import annotations

import subprocess


def git_out(root, *args: str) -> str:
    done = subprocess.run(
        ["git", *args], cwd=root, capture_output=True, text=True, check=True
    )
    return done.stdout.strip()


def tiny_source(tmp_path):
    """A two-file source tree with no git history, for the copy/commit units."""
    source = tmp_path / "source"
    (source / "src").mkdir(parents=True)
    (source / "README.md").write_text("# Title\n\nbody\n", encoding="utf-8")
    (source / "src" / "mod.py").write_text("VALUE = 1\n", encoding="utf-8")
    return source


def mini_source(tmp_path):
    """A committed miniature repository, for the end-to-end driver tests."""
    root = tmp_path / "mini"
    (root / "src").mkdir(parents=True)
    (root / "config" / "police").mkdir(parents=True)
    (root / "README.md").write_text("# Mini\n\nbody\n", encoding="utf-8")
    (root / "src" / "mod.py").write_text("VALUE = 1\n", encoding="utf-8")
    (root / "config" / "police" / "role.json").write_text("{}\n", encoding="utf-8")
    (root / "config" / "police" / "games_played.json").write_text("{}\n", encoding="utf-8")
    (root / "pyproject.toml").write_text(
        '[project]\nauthors = [{ name = "A B", email = "a@b.c" }]\n', encoding="utf-8")
    subprocess.run(["git", "init", "-b", "main"], cwd=root, check=True, capture_output=True)
    subprocess.run(["git", "add", "-A"], cwd=root, check=True, capture_output=True)
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", "commit",
                    "--no-verify", "-m", "seed"], cwd=root, check=True, capture_output=True)
    return root
