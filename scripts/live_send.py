"""07-10's one supervised live send -- the step the GAME path refuses to take.

WHY THIS FILE EXISTS. `end_of_game_chain.build_reporting_chain` raises
`LIVE_MODE_UNWIRED` when `reporting.mode` is `live` and no sink was injected,
and NOTHING in the agent path injects one -- every `GmailSink` built in this
repository before this file was built by a gate or a unit test around a FAKE
transport. `OAUTH-RUNBOOK.md` Sec4 step 4 nevertheless told the operator to flip
the config and run `dev_launch.py`, which is precisely the shape that refusal
exists to stop. Measured 2026-08-19: that procedure fails twice and sends
nothing. This is the missing half.

THE SHIPPED CONFIG IS NEVER EDITED. `dry_run` ON DISK IS A PRECONDITION and LIVE
is applied to an in-memory copy that is never written back, so no `live` config
ever sits in the working tree waiting to be committed.

IT DOES NOT PLAY A GAME AND IT DOES NOT READ THE LEAGUE CONFIG. `load_league_
config` refuses live mode until all four rule-49 repo URLs are real -- including
the OPPONENT'S TWO, absent until league day -- so routing this through the game
path would make the first real transmission of this project's life happen during
a scored game, with rule 35 zeroing BOTH teams if it went wrong.

`--recipient` IS REQUIRED AND HAS NO DEFAULT, and that is the whole lesson of
this file's first day in service. `reporting.json`'s recipient is the spec's
mandatory address (`docs/PARAMETERS.md:176`, FIXED -- the loader rejects any
other value), so a rehearsal that "just used the config" mailed the LECTURER a
throwaway self-play report. Making the address impossible to supply by accident
is worth more than the keystrokes it costs: to reach the mandatory destination
you now type `--recipient mandatory`, and to rehearse you type your own address.
The GAME path is untouched and still cannot address anything else.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

from live_send_core import live_params, send_once

#: Typed instead of the address itself, so the irreversible choice is a word the
#: operator had to mean, not a string they could paste from a runbook by habit.
MANDATORY_TOKEN = "mandatory"
LECTURER_BANNER = (
    "=== THE MANDATORY DESTINATION: this message goes to the LECTURER's grading\n"
    "=== address ({recipient}). This is the real thing, not a rehearsal."
)
REHEARSAL_BANNER = (
    "=== REHEARSAL: sending to {recipient}, which is NOT the mandatory grading\n"
    "=== address. Nothing about this send reaches the lecturer."
)
SENT_LINE = "=== PURSUIT LIVE SEND: message accepted by Gmail, id={message_id} ==="
NOT_SENT_LINE = "=== PURSUIT LIVE SEND: NOT SENT ({refusal}); nothing was transmitted ==="


def resolve_recipient(value: str, mandatory: str) -> tuple[str, bool]:
    """`(address, is_the_mandatory_destination)` for one `--recipient` value.

    The literal token expands to the spec address; anything else is taken as
    typed, INCLUDING the mandatory address spelled out in full -- someone who
    types it means it just as much as someone who types the token.
    """
    if value == MANDATORY_TOKEN:
        return mandatory, True
    if "@" not in value:
        raise ValueError(
            f"--recipient must be an email address or the literal "
            f"'{MANDATORY_TOKEN}'; got {value!r}"
        )
    return value, value == mandatory


def _parse(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--config-dir", required=True, help="config/police or config/thief")
    parser.add_argument("--result", required=True, help="a result_<game_id>.json to send")
    parser.add_argument(
        "--recipient",
        required=True,
        help=(
            f"your own address to rehearse, or the literal '{MANDATORY_TOKEN}' to "
            f"mail the lecturer's grading address. No default, deliberately."
        ),
    )
    parser.add_argument(
        "--confirm-live-send",
        action="store_true",
        help="required: this transmits a real message and cannot be undone",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse(sys.argv[1:] if argv is None else argv)
    if not args.confirm_live_send:
        print(
            "refusing: pass --confirm-live-send. This sends REAL mail and "
            "cannot be undone (rule 35).",
            file=sys.stderr,
        )
        return 2
    params = live_params(args.config_dir)
    try:
        recipient, is_mandatory = resolve_recipient(args.recipient, params.recipient)
    except ValueError as exc:
        print(f"refusing: {exc}", file=sys.stderr)
        return 2
    banner = LECTURER_BANNER if is_mandatory else REHEARSAL_BANNER
    print(banner.format(recipient=recipient))
    report = json.loads(Path(args.result).read_text(encoding="utf-8"))
    outcome, receipt = asyncio.run(
        send_once(
            report, params, recipient=recipient, work_dir=Path(args.result).parent
        )
    )
    if not outcome.sent:
        print(NOT_SENT_LINE.format(refusal=outcome.refusal), file=sys.stderr)
        return 1
    print(SENT_LINE.format(message_id=receipt.message_id))
    print(f"recipient={recipient}  report={Path(args.result).name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
