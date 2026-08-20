"""The provenance document a split repository carries (08-10).

`docs/REPO-SPLIT.md` reports counts and named reasons, never adjectives, and
refuses to describe a zero-file build -- an empty repository passes every gate
by looking at nothing. Nothing URL-shaped may appear in its output: the rule-49
cross-links live in the README banner and nowhere else.
"""

from __future__ import annotations

import pytest

from tests.unit.submission_gate_helpers import load
from tests.unit.test_split_docs import SHA, STAMP, URL_SHAPES

prov_mod = load("split_provenance")


def test_the_provenance_document_reports_counts_not_adjectives() -> None:
    text = prov_mod.provenance("police", SHA, STAMP, included=907, excluded=(
        ("config/police/games_played.json", "D-77: live rule-37 counter"),
    ))
    assert "907" in text
    assert "config/police/games_played.json" in text
    assert "D-77" in text
    assert "core.hooksPath scripts/hooks" in text
    for shape in URL_SHAPES:
        assert shape.lower() not in text.lower()


def test_the_provenance_document_refuses_a_zero_file_build() -> None:
    with pytest.raises(prov_mod.EmptyBuildError):
        prov_mod.provenance("police", SHA, STAMP, included=0, excluded=())


def test_a_build_with_no_exclusions_states_none_rather_than_inventing_rows() -> None:
    text = prov_mod.provenance("police", SHA, STAMP, included=907, excluded=())
    assert "_(none)_" in text
    for shape in URL_SHAPES:
        assert shape.lower() not in text.lower()
