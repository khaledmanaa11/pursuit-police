"""GATE-8 criterion 1's PUBLISHED half, measured -- and its honest limit.

WHAT CHANGED AND WHY (2026-08-19). 08-11 could not measure publication at all,
so `criterion_1_built_verdict` asserted its ABSENCE instead: `remote_count == 0`
was listed as evidence that nothing had been published from this machine. That
was true and load-bearing right up until the owner published, at which point
the gate reported **BUILT+TAGGED FAIL** -- for a build that was entirely
correct, failing on the one condition the whole phase existed to stop being
true. A gate that fails when its goal is reached is measuring the wrong thing.

So the absence-assertion is replaced by a positive measurement, and the
built/tagged half goes back to describing only the build and the tag.

STILL ZERO REMOTE COMMANDS. Everything here reads refs git already wrote to
disk: `git remote` lists configured remotes, and `refs/remotes/origin/main` is
updated BY the push, so comparing it to local `main` is local evidence that the
branch really went out. No fetch, no ls-remote, no network.

THE ONE THING THIS CANNOT MEASURE, STATED RATHER THAN GUESSED: whether the TAG
reached the remote. Tags get no tracking ref, so locally there is nothing to
compare -- and 2026-08-19 proved the difference matters, when `git push origin
v1.00` failed with `src refspec v1.00 does not match any` while the branch push
beside it succeeded. `tag_push_locally_unverifiable` is therefore reported as a
fact about the MEASUREMENT, never resolved into a verdict about the tag.
"""

from __future__ import annotations

from pathlib import Path

from gate8_common import git_out, lines

#: A published submission repository has exactly one remote. Two would mean the
#: output had been wired somewhere unintended as well.
EXPECTED_REMOTES = 1


def publication_facts(root: Path) -> dict:
    """Remotes and branch-push evidence for one output, from local refs only."""
    remotes = lines(git_out(root, "remote"))
    urls = [git_out(root, "remote", "get-url", name).strip() for name in remotes]
    local = git_out(root, "rev-parse", "main").strip()
    tracking = git_out(root, "rev-parse", "refs/remotes/origin/main").strip()
    return {
        "remote_count": len(remotes),
        "remote_urls": urls,
        "all_remotes_are_https": all(url.startswith("https://") for url in urls) if urls else False,
        "local_main": local,
        "origin_main": tracking,
        "branch_pushed": bool(local) and bool(tracking) and local == tracking,
        "tag_push_locally_unverifiable": True,
    }


def published_verdict(outputs: dict, *, pending: str, ok: str, fail: str) -> str:
    """PASS only when BOTH outputs show one https remote and a pushed branch.

    `pending` when neither output has a remote -- the pre-08-12 state, which is
    not a failure and must never read as one. `fail` when publication was
    STARTED and is wrong: a remote configured but the branch not pushed, or a
    remote count other than one. Half-published is the state that costs a
    submission, so it is the state that gets the loud verdict.
    """
    facts = [output.get("publication", {}) for output in outputs.values()]
    if all(fact.get("remote_count", 0) == 0 for fact in facts):
        return pending
    complete = all(
        fact.get("remote_count") == EXPECTED_REMOTES
        and fact.get("all_remotes_are_https")
        and fact.get("branch_pushed")
        for fact in facts
    )
    return ok if complete else fail
