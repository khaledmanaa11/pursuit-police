"""The live send's machinery: config lift, watchdog, receipt capture, one send.

Split from `live_send.py` at the 150-code-line gate when `--recipient` was added
(2026-08-19). `live_send.py` keeps the CLI -- the argument parsing, the recipient
decision and the banners -- and this file keeps everything that a test can drive
without a command line.

WHY A LIVE SEND NEEDS ITS OWN MACHINERY AT ALL: `build_reporting_chain` refuses
`live` with no injected sink, and nothing in the agent path injects one. See
`live_send.py`'s docstring for the whole argument; it is not repeated here.
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from pursuit.services.reporting.end_of_game import build_reporting_chain
from pursuit.services.reporting.gmail_sink import GmailSink, build_gmail_transport
from pursuit.shared.reporting_config import (
    ReportingMode,
    ReportingParams,
    load_reporting_config,
)

#: Refused rather than "helpfully" accepted: a live config on disk means the
#: flip-and-flip-back procedure is half-done, and finishing it silently here
#: would leave the operator with a live file and no reason to notice.
ALREADY_LIVE = (
    "the config on disk is already 'live'; this script needs the SHIPPED dry_run "
    "config and lifts it in memory. Restore it (git checkout config/<role>/"
    "reporting.json) and run again"
)


class SendWatchdog:
    """`ctx.watchdog`'s surface for a one-shot send: counts, freezes nothing.

    `watchdog_touching` marks activity on entry and in a `finally`; a real
    freeze watchdog's action is `os._exit`, which is not what a supervised
    single send a human is watching should ever do.

    DELIBERATELY NOT `gate7_common.RecordingWatchdog`, whose surface is
    identical. `gate7_common` POPS `PURSUIT_GMAIL_CREDENTIALS_PATH` and
    `PURSUIT_GMAIL_TOKEN_PATH` OUT OF `os.environ` AT IMPORT TIME -- exactly
    right for a gate that must never let a grader's shell become a live API
    call, and fatal here, where the live send IS the point. Importing it for
    these six lines disarmed this script: three runs on 2026-08-19 all died on
    "environment variable PURSUIT_GMAIL_CREDENTIALS_PATH ... is unset" with the
    variable demonstrably set in the calling shell. Six duplicated lines beat
    an import whose documented purpose is to make this file impossible.
    """

    def __init__(self) -> None:
        self.touches = 0

    def touch(self) -> None:
        self.touches += 1


class ReceiptCapturingSink:
    """Wrap the real sink so the id Gmail returned survives the chain.

    `ReportingChain` collapses a success to `SendOutcome(sent=True)` and drops
    the `SendReceipt`. That is right for the GAME path, which only needs to know
    whether it still owes a report -- and useless for THIS step, whose entire
    output is the message id a human checks the mailbox against. Captured by
    wrapping rather than by widening `chain.py`: the game path's return contract
    is not this script's to change.
    """

    def __init__(self, inner) -> None:
        self._inner = inner
        self.receipt = None

    async def send(self, report: dict):
        self.receipt = await self._inner.send(report)
        return self.receipt


def live_params(config_dir: Path | str) -> ReportingParams:
    """The shipped `dry_run` config, lifted to LIVE **in memory only**."""
    params = load_reporting_config(Path(config_dir) / "reporting.json")
    if params.mode is not ReportingMode.DRY_RUN:
        raise ValueError(ALREADY_LIVE)
    return replace(params, mode=ReportingMode.LIVE)


async def send_once(
    report: dict,
    params: ReportingParams,
    *,
    recipient: str,
    work_dir: Path | str,
    transport_builder=build_gmail_transport,
):
    """One report through the SHIPPED chain, with a real `GmailSink` on the end.

    Returns `(outcome, receipt)`. The receipt is `None` on refusal and carries
    the Gmail message id on success -- see `ReceiptCapturingSink` for why it
    cannot simply be read off the outcome.

    `recipient` is passed EXPLICITLY and has no default, rather than being read
    off `params`. `params.recipient` is the spec's mandatory address and nothing
    else -- `load_reporting_config` rejects any other value -- so defaulting to
    it made every rehearsal a message to the lecturer, which is exactly what
    happened on 2026-08-19. The GAME path is untouched and still cannot address
    anything but the mandatory destination; this is an operator tool, and who a
    supervised rehearsal goes to is the operator's to state.

    `transport_builder` is the seam every test drives with a fake, mirroring
    `build_gmail_transport`'s own `credentials_loader`. `work_dir` holds only
    the quota ledger: no artifact is written here, because the report being
    sent was written by the game that produced it.
    """
    capturing = ReceiptCapturingSink(
        GmailSink(transport=transport_builder(params), recipient=recipient)
    )
    chain = build_reporting_chain(
        params,
        watchdog=SendWatchdog(),
        artifact_dir=work_dir,
        quota_dir=work_dir,
        sink=capturing,
    )
    return await chain.send(report), capturing.receipt
