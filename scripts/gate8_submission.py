"""GATE-8 criterion 2 -- the README-and-form half of the submission gate (08-11).

> 2. Academic README with its six mandatory sections (incl. learning curves and
>    `Verified OK` screenshots); submission form filled and saved as PDF,
>    submitted per team member

THE CRITERION CANNOT CLOSE HERE, AND IT IS NOT WRITTEN AS THOUGH IT MIGHT.
The form is a PDF whose location is not recorded anywhere (OQ8-3) and whose
per-member submission is an outward act. What IS measured is everything
underneath: the six section headings in the tree that will be published, and
the screenshot slots that are still empty. Criterion 3 -- the league half --
lives in `gate8_league`.

THE HEADING TABLE IS IMPORTED, NEVER RETYPED. `tests/unit/readme_contract_checks`
owns Sec9.4.2's six section names; a second copy here could pass while the README
contract failed.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from gate8_common import REPO_ROOT, ROLES, split_root

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tests.unit import readme_contract_checks as checks  # noqa: E402

_CURVE_DIR = "artifacts/curves/"


def _readme_of(dest: Path, role: str) -> str:
    path = split_root(dest, role) / "README.md"
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def _screenshot_slots() -> dict:
    """Tracked images that are NOT a training curve. Zero today, and stated so.

    Asked of `git ls-files` across the whole tree, not of one directory. The
    first draft globbed `docs/assets/` only -- a directory that does not exist
    -- and reported `tracked_images: 0` while the audit gate, asking the same
    question properly, was reporting five. A count taken over the wrong set is
    not a smaller count; it is a different question.
    """
    listed = subprocess.run(
        ["git", "ls-files"], cwd=REPO_ROOT, capture_output=True, text=True, check=True,
    ).stdout.split()
    tracked = [path for path in listed
               if path.lower().endswith((".png", ".jpg", ".jpeg", ".gif"))]
    return {
        "tracked_images": len(tracked),
        "non_curve_images": len([p for p in tracked if _CURVE_DIR not in p]),
        "verdict": "PENDING",
        "owner": "07-10 (human -- one live run, then two screenshots)",
        "audit_rows": ["G1-03b", "G5-04"],
        "note": "MARKED-ABSENT SLOTS. 08-06 wrote the slots and refused to fake them.",
    }


def measure_criterion_2(dest: Path) -> dict:
    """The published README's six sections, plus the three human-only halves."""
    per_role = {}
    for role in ROLES:
        text = _readme_of(dest, role)
        per_role[role] = {
            "readme_bytes": len(text),
            "missing_academic_942_headings": checks.missing_headings(
                text, checks.ACADEMIC_942_HEADINGS
            ),
            "missing_segal_21_headings": checks.missing_headings(
                text, checks.SEGAL_21_HEADINGS
            ),
            "academic_sections_expected": len(checks.ACADEMIC_942_HEADINGS),
        }
    return {
        "criterion": "2 -- academic README, screenshots, submission form PDF, per member",
        "published_readmes": per_role,
        "screenshots": _screenshot_slots(),
        "submission_form_pdf": {
            "verdict": "PENDING",
            "owner": "08-14 (human)",
            "open_question": "OQ8-3 -- neither docs/RULES.md nor docs/PARAMETERS.md records "
                             "where the form lives; no location is guessed",
            "runbook": "docs/phases/phase-8/SUBMISSION-RUNBOOK.md",
        },
        "submitted_per_member": {
            "verdict": "PENDING", "owner": "08-14 (human)",
            "team_code": "khm-mn17", "team_size": 1,
        },
        "self_assessment_score": {
            "verdict": "PENDING", "owner": "08-14 (human)",
            "open_question": "OQ8-4 -- a numeric claim about our own work (rule 55)",
            "evidence_table": "docs/SELF-ASSESSMENT.md (drafted by 08-11, score field BLANK)",
        },
    }
