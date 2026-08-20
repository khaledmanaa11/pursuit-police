"""Plan, build and verify one split repository, end to end (08-10).

A MINIATURE SOURCE REPO, NOT A MOCK. `build_one` is the piece where a mistake is
invisible in review and obvious on disk -- a banner that was never injected, a
provenance file that was written but never staged, a commit that picked up
something the manifest did not list. So these tests build a real git repository,
run the real driver against it, and count what landed. The CLI over this module
is proven in `tests/unit/test_build_split_repos.py`.
"""

from __future__ import annotations

import subprocess

from tests.unit.split_fixtures import mini_source
from tests.unit.submission_gate_helpers import load

driver = load("split_driver")
report_mod = load("split_report")


def test_build_one_produces_a_committed_repository_with_the_banner(tmp_path) -> None:
    source = mini_source(tmp_path)
    plan = driver.plan_build(source)
    built = driver.build_one(source, tmp_path / "out-police", "police", False, plan)
    dest = tmp_path / "out-police"
    assert built["copied"] == 4, built
    assert built["staged"] == 5, "the provenance document must be staged too"
    assert len(built["excluded"]) == 1
    assert built["excluded"][0]["path"] == "config/police/games_played.json"
    assert "<!-- split-repo-banner" in (dest / "README.md").read_text(encoding="utf-8")
    assert (dest / "docs" / "REPO-SPLIT.md").is_file()
    tracked = subprocess.run(["git", "ls-files"], cwd=dest, capture_output=True,
                             text=True, check=True).stdout.splitlines()
    assert len(tracked) == 5
    assert "config/police/games_played.json" not in tracked


def test_the_built_repository_has_one_commit_and_no_remote(tmp_path) -> None:
    source = mini_source(tmp_path)
    driver.build_one(source, tmp_path / "out-thief", "thief", False, driver.plan_build(source))
    dest = tmp_path / "out-thief"
    count = subprocess.run(["git", "rev-list", "--count", "HEAD"], cwd=dest,
                           capture_output=True, text=True, check=True).stdout.strip()
    remote = subprocess.run(["git", "remote"], cwd=dest, capture_output=True,
                            text=True, check=True).stdout.strip()
    assert count == "1"
    assert remote == ""


def test_verify_one_returns_a_row_per_property_and_never_an_empty_list(tmp_path) -> None:
    source = mini_source(tmp_path)
    driver.build_one(source, tmp_path / "out", "police", False, driver.plan_build(source))
    rows = driver.verify_one(tmp_path / "out", source, "police", with_gates=False)
    assert len(rows) == 9
    names = [row.name for row in rows]
    assert len(set(names)) == len(names)
    assert not report_mod.overall(())
