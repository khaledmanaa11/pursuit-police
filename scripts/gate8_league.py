"""GATE-8 criterion 3 -- the league half of the submission gate (08-11).

> 3. At least 2 scored league games played against different teams and
>    reported, each game emailing the commit hash it ran on

THE CRITERION CANNOT CLOSE HERE, AND IT IS NOT WRITTEN AS THOUGH IT MIGHT.
Real opponent teams cannot be arranged by an agent, and rule 35 zeroes BOTH
teams when either fails to report. What IS measured is everything underneath:
the ledger's derived count against the Table-18 bounds, and the fact that the
declaration artifact -- the thing that carries the commit hash onto the wire --
has a production caller. A definition is not a caller; three public names with
zero production call sites is exactly what 08-04 found. Criterion 2 lives in
`gate8_submission`.
"""

from __future__ import annotations

import json

from gate8_common import REPO_ROOT, ROLES

from pursuit.services.reporting.league_ledger import read_ledger
from pursuit.services.reporting.league_ledger_fields import (
    MAX_GAMES_PER_TEAM,
    MINIMUM_GAMES,
    count_reading,
    scored_opponents,
)

DECLARATION_EVIDENCE = REPO_ROOT / "docs" / "phases" / "phase-8" / "declaration-evidence"
#: The writer whose production call sites are counted. The module that DEFINES it
#: is excluded, because a definition is not a caller -- that distinction is the
#: whole of what 08-04 found: three public names with zero production callers, so
#: rule 50's declaration artifact had never been written by a real game.
DECLARATION_WRITER = "write_declaration_artifact"
DECLARATION_WRITER_MODULE = "artifact_declaration.py"
#: Where the commit hash actually lives in the artifact -- nested, not top level.
_HASH_PATH = ("declarations", "own", "declaration", "commit_hash")


def _nested(payload: dict, path: tuple[str, ...]) -> object:
    for key in path:
        if not isinstance(payload, dict):
            return None
        payload = payload.get(key)
    return payload


def _call_sites() -> list[str]:
    """Every `src/` module that CALLS the declaration writer, definition excluded."""
    return sorted(
        str(path.relative_to(REPO_ROOT)).replace("\\", "/")
        for path in (REPO_ROOT / "src").rglob("*.py")
        if path.name != DECLARATION_WRITER_MODULE
        and f"{DECLARATION_WRITER}(" in path.read_text(encoding="utf-8")
    )


def _declaration_wiring() -> dict:
    """The commit hash reaches the wire only if a production call site exists."""
    retained = sorted(
        path.name for path in DECLARATION_EVIDENCE.glob("*_declaration_*.json")
    ) if DECLARATION_EVIDENCE.is_dir() else []
    hashes = {}
    for name in retained:
        payload = json.loads((DECLARATION_EVIDENCE / name).read_text(encoding="utf-8"))
        found = _nested(payload, _HASH_PATH)
        if isinstance(found, str) and found.strip():
            hashes[name] = found
    return {
        "declaration_writer": DECLARATION_WRITER,
        "production_call_sites": _call_sites(),
        "call_site_present": bool(_call_sites()),
        "commit_hash_field": ".".join(_HASH_PATH),
        "retained_declaration_artifacts": retained,
        "retained_artifacts_carrying_a_commit_hash": sorted(hashes),
        "commit_hashes_found": sorted(set(hashes.values())),
    }


def measure_criterion_3() -> dict:
    """The ledger's derived count against Table 18's two fixed bounds."""
    ledgers = {}
    for role in ROLES:
        ledger = read_ledger(REPO_ROOT / "config" / role)
        ledgers[role] = {
            "scored_games": count_reading(ledger, scored_only=True),
            "all_games": count_reading(ledger, scored_only=False),
            "distinct_scored_opponents": list(scored_opponents(ledger)),
        }
    return {
        "criterion": "3 -- >=2 scored games vs different teams, reported with the commit hash",
        "ledger": ledgers,
        "bounds": {"minimum_games": MINIMUM_GAMES, "max_games_per_team": MAX_GAMES_PER_TEAM},
        "declaration_wiring": _declaration_wiring(),
        "scored_games_played": {
            "verdict": "PENDING",
            "owner": "08-13 (human, and blocked on 07-10)",
            "why": "real opponent teams cannot be arranged by an agent, and rule 35 zeroes "
                   "BOTH teams when either fails to report -- so no game is played to "
                   "demonstrate a delta",
            "runbook": "docs/phases/phase-8/LEAGUE-RUNBOOK.md",
        },
        "games_played_declaration": {
            "verdict": "PENDING", "owner": "08-14 (human)",
            "open_question": "OQ8-2 -- the rule-38 value is not an agent's to pick",
        },
    }
