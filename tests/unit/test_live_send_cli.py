"""The live send CLI's contract -- above all, WHO a message can reach.

THE INCIDENT THIS FILE PINS (2026-08-19). `--recipient` did not exist and the
address was read off `reporting.json`, which by spec holds the LECTURER's
grading address and nothing else (`docs/PARAMETERS.md:176`, FIXED; the loader
rejects any other value). So the very first rehearsal mailed a throwaway
self-play report to the person who grades the project. Nothing was technically
wrong -- every test passed, the send worked exactly as designed, and the design
was to mail the lecturer.

Hence: no default. To reach the mandatory destination you type
`--recipient mandatory`; to rehearse you type your own address. These tests
assert that a bare invocation CANNOT reach the lecturer, which is the property
that was missing, not the property that was broken.

Nothing here sends: every path asserted stops before any transport is built.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "scripts"))

import live_send  # noqa: E402

from pursuit.shared.reporting_config import load_reporting_config  # noqa: E402

SHIPPED_POLICE = REPO_ROOT / "config" / "police"
MANDATORY = load_reporting_config(SHIPPED_POLICE / "reporting.json").recipient
REHEARSAL_ADDRESS = "khaled.mnaa43@gmail.com"


def test_the_shipped_config_really_does_hold_the_lecturers_address():
    """The premise of this whole file, checked rather than assumed."""
    assert MANDATORY == "rmisegal+uoh26finalgame@gmail.com"


def test_the_literal_token_is_the_only_shorthand_for_the_lecturer():
    address, is_mandatory = live_send.resolve_recipient(live_send.MANDATORY_TOKEN, MANDATORY)
    assert (address, is_mandatory) == (MANDATORY, True)


def test_a_rehearsal_address_is_taken_as_typed_and_flagged_as_not_mandatory():
    address, is_mandatory = live_send.resolve_recipient(REHEARSAL_ADDRESS, MANDATORY)
    assert address == REHEARSAL_ADDRESS
    assert is_mandatory is False


def test_the_mandatory_address_typed_in_full_still_counts_as_mandatory():
    """Someone who spells it out means it as much as someone who types the token."""
    _, is_mandatory = live_send.resolve_recipient(MANDATORY, MANDATORY)
    assert is_mandatory is True


def test_a_value_that_is_not_an_address_is_refused():
    with pytest.raises(ValueError, match="email address"):
        live_send.resolve_recipient("me", MANDATORY)


def test_recipient_is_required_so_a_bare_run_cannot_reach_the_lecturer(tmp_path):
    """The incident, as an assertion: omitting it must FAIL, never default."""
    with pytest.raises(SystemExit) as exit_info:
        live_send.main(
            [
                "--config-dir", str(SHIPPED_POLICE),
                "--result", str(tmp_path / "result_x.json"),
                "--confirm-live-send",
            ]
        )
    assert exit_info.value.code != 0


def test_the_cli_refuses_without_the_confirmation_flag(tmp_path, capsys):
    code = live_send.main(
        [
            "--config-dir", str(SHIPPED_POLICE),
            "--result", str(tmp_path / "result_x.json"),
            "--recipient", REHEARSAL_ADDRESS,
        ]
    )
    assert code != 0
    assert "--confirm-live-send" in capsys.readouterr().err


def test_the_two_banners_cannot_be_mistaken_for_each_other():
    lecturer = live_send.LECTURER_BANNER.format(recipient=MANDATORY)
    rehearsal = live_send.REHEARSAL_BANNER.format(recipient=REHEARSAL_ADDRESS)
    assert "LECTURER" in lecturer and "REHEARSAL" not in lecturer
    assert "REHEARSAL" in rehearsal and "LECTURER" not in rehearsal
    assert MANDATORY not in rehearsal, "a rehearsal banner must not show the real address"


def test_the_cli_does_not_import_gate7_common_either():
    """`live_send_core` carries this guard too; the CLI is the other half.

    `gate7_common` clears the Gmail credential variables at import, which would
    disarm the send from this side just as effectively.
    """
    tree = ast.parse(Path(live_send.__file__).read_text(encoding="utf-8"))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.add(node.module or "")
    assert "gate7_common" not in imported
    assert "live_send_core" in imported, "the control: the CLI DOES use the core"
