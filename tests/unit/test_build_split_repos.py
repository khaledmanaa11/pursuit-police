"""The split-build CLI's exit contract, exercised on a miniature repository (08-10).

THE DRIVER'S EXIT CONTRACT IS `check_submission.py`'s (D-82): 0 all rows pass,
1 any row fails, 2 nothing was built or nothing was checked. The refusal path --
a destination inside the source repository -- is asserted to return 2 AND to
leave nothing behind. The plan/build/verify pieces the CLI drives are proven in
`tests/unit/test_split_driver.py`.
"""

from __future__ import annotations

import json

from tests.unit.split_fixtures import mini_source
from tests.unit.submission_gate_helpers import REPO_ROOT, load

driver = load("build_split_repos")


def test_both_outputs_are_built_from_one_manifest_and_one_timestamp(tmp_path) -> None:
    """Re-deriving per role would let a mid-build edit land in one repo only."""
    source = mini_source(tmp_path)
    out = tmp_path / "both"
    code = driver.main(["--dest", str(out), "--source", str(source),
                        "--json", str(tmp_path / "evidence.json")])
    evidence = json.loads((tmp_path / "evidence.json").read_text(encoding="utf-8"))
    assert code == 1, "a miniature source cannot satisfy rule 50 -- an honest FAIL"
    assert [entry["role"] for entry in evidence] == ["police", "thief"]
    assert len({entry["source_commit"] for entry in evidence}) == 1
    assert len({entry["generated"] for entry in evidence}) == 1
    assert len({entry["staged"] for entry in evidence}) == 1
    assert len({entry["commit"] for entry in evidence}) == 2


def test_a_destination_inside_this_repository_exits_2_and_builds_nothing(capsys) -> None:
    target = REPO_ROOT / "should-never-exist"
    assert driver.main(["--dest", str(target)]) == 2
    assert "REFUSED" in capsys.readouterr().out
    assert not target.exists()
