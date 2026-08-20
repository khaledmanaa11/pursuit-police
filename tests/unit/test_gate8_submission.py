"""GATE-8 criterion 2's own measurement units (08-11).

A MODULE-SCOPE IMPORT IS PART OF THE POINT: `gate8_submission` bootstraps
`tests.unit.readme_contract_checks` at import time, so a heading-table rename
or a broken sys.path shim must fail this file at collection rather than surface
first in a grader-facing CLI run. The report-level verdicts these numbers feed
are exercised in `tests/unit/test_gate8_measure.py`; criterion 3's units are in
`tests/unit/test_gate8_league.py`.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "scripts"))

import gate8_submission as submission  # noqa: E402


def _dest_with_readmes(tmp_path, text: str):
    for role in ("police", "thief"):
        root = tmp_path / f"pursuit-{role}"
        root.mkdir(parents=True)
        (root / "README.md").write_text(text, encoding="utf-8")
    return tmp_path


def test_measure_criterion_2_counts_every_missing_heading_of_a_bare_readme(tmp_path) -> None:
    result = submission.measure_criterion_2(_dest_with_readmes(tmp_path, "# Title\n"))
    for role in ("police", "thief"):
        entry = result["published_readmes"][role]
        assert entry["readme_bytes"] > 0
        assert len(entry["missing_academic_942_headings"]) == entry["academic_sections_expected"]
        assert entry["missing_segal_21_headings"], "a bare README misses the Segal set too"


def test_a_missing_readme_reads_as_zero_bytes_never_a_crash(tmp_path) -> None:
    result = submission.measure_criterion_2(tmp_path)
    for role in ("police", "thief"):
        assert result["published_readmes"][role]["readme_bytes"] == 0


def test_the_screenshot_slots_count_tracked_images_and_stay_pending() -> None:
    slots = submission._screenshot_slots()
    assert slots["tracked_images"] >= slots["non_curve_images"] >= 0
    assert slots["verdict"] == "PENDING"
