"""GATE-8 criterion 1's PUBLISHED half -- the verdict, and its failure shapes.

Split from `test_gate8_measure.py` at the 150-code-line gate (2026-08-19), when
publication stopped being asserted-absent and started being measured.

WHY THIS VERDICT NEEDED ITS OWN FILE OF FAILURE CASES: the gate it replaces
could only say "nothing is published", which is a fact that stops being
interesting the moment it stops being true. What matters afterwards is the
HALF-published state -- one repository pushed and the other not, from a
different source commit, with one of the two tags missing. That is not
hypothetical: it is what this project did on the day it published.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "scripts"))

import gate8_publication as publication  # noqa: E402
import gate8_report as report  # noqa: E402


def _pub(**overrides) -> dict:
    facts = {"remote_count": 1, "all_remotes_are_https": True, "branch_pushed": True}
    return {"publication": {**facts, **overrides}}


_VERDICTS = {"pending": report.PENDING, "ok": report.PASS, "fail": report.FAIL}


def test_publication_is_pending_before_it_starts_and_passes_when_complete() -> None:
    """PENDING is not a failure: it is the honest pre-08-12 state."""
    nothing = {"police": {"publication": {"remote_count": 0}},
               "thief": {"publication": {"remote_count": 0}}}
    assert publication.published_verdict(nothing, **_VERDICTS) == report.PENDING
    both = {"police": _pub(), "thief": _pub()}
    assert publication.published_verdict(both, **_VERDICTS) == report.PASS


def test_a_half_published_pair_fails_rather_than_reading_as_pending() -> None:
    """THE FAILURE THAT ACTUALLY HAPPENED (2026-08-19).

    One output pushed, the other not -- and worse, from a different source
    commit, with only one of the two tags landing. Half-published is the state
    that costs a submission, so it must be LOUD, never quietly PENDING.
    """
    half = {"police": _pub(), "thief": {"publication": {"remote_count": 0}}}
    assert publication.published_verdict(half, **_VERDICTS) == report.FAIL


def test_every_incomplete_publication_shape_fails() -> None:
    """A verdict that only ever says PASS vouches for nothing."""
    for broken in (
        _pub(branch_pushed=False),
        _pub(remote_count=2),
        _pub(all_remotes_are_https=False),
    ):
        outputs = {"police": _pub(), "thief": broken}
        assert publication.published_verdict(outputs, **_VERDICTS) == report.FAIL
