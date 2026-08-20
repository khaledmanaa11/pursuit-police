"""GATE-8 criterion 3's own measurement units (08-11).

THE CALL-SITE SCAN IS THE FINDING 08-04 TURNED INTO A VERDICT: a definition is
not a caller, so the module that DEFINES the declaration writer is excluded
from its own call-site count. The report-level verdicts these numbers feed are
exercised in `tests/unit/test_gate8_measure.py`; this file pins the measurement
itself -- the scan, the nested-hash lookup, and the bounds the ledger count is
judged against.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "scripts"))

import gate8_league as league  # noqa: E402


def test_the_declaration_writer_has_a_production_call_site_that_is_not_its_own_module() -> None:
    sites = league._call_sites()
    assert sites, "write_declaration_artifact has no production caller"
    assert all(league.DECLARATION_WRITER_MODULE not in site for site in sites), sites


def test_the_nested_lookup_dead_ends_to_none_and_never_raises() -> None:
    assert league._nested({"a": {"b": 1}}, ("a", "b")) == 1
    assert league._nested({"declarations": {"own": "not-a-dict"}}, league._HASH_PATH) is None
    assert league._nested({}, league._HASH_PATH) is None


def test_measure_criterion_3_reports_ledger_counts_against_the_table_18_bounds() -> None:
    result = league.measure_criterion_3()
    assert result["bounds"] == {"minimum_games": league.MINIMUM_GAMES,
                                "max_games_per_team": league.MAX_GAMES_PER_TEAM}
    for role in ("police", "thief"):
        assert set(result["ledger"][role]) == {
            "scored_games", "all_games", "distinct_scored_opponents",
        }
    wiring = result["declaration_wiring"]
    assert wiring["call_site_present"] is True
    assert wiring["commit_hash_field"] == ".".join(league._HASH_PATH)
