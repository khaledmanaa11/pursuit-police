"""The git-shape rows of a built split repository, and its report (08-10).

FOUR PROPERTIES THAT ARE ONLY TRUE IF SOMEONE CHECKS THEM.

* ONE commit. Two means the build ran twice into the same tree, or something
  else committed there, and the second commit's provenance is unknown.
* ZERO remotes. This plan builds locally and pushes nothing; the remote is added
  by a human at 08-12 after the public repository exists.
* A history DISJOINT from the source. A split made by cloning, or by `git init`
  inside the working tree, carries several hundred private commits and an
  inherited `origin` -- one reflex `git push` publishes all of them.
* The rule-49 cross-link block present in the README.

`overall(())` IS FALSE, DELIBERATELY. `all(())` is True in Python, so a verifier
built the obvious way reports PASS when its row list came back empty -- the
vacuous pass in its purest form, and the exact failure this phase keeps finding.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from split_docs import MARKER
from split_verify import Check, git_out


def _count(root: Path, *args: str) -> str:
    return git_out(root, *args).strip()


def single_commit_row(dest: Path) -> Check:
    """Exactly one commit -- the initial import, and nothing since."""
    count = _count(dest, "rev-list", "--count", "HEAD")
    return Check("exactly one commit", count == "1", f"rev-list --count HEAD = {count or '?'}")


def preserved_history_row(dest: Path, floor: int) -> Check:
    """The development history arrived, and the import commit sits on top of it.

    `floor` is the source's own commit count, so this cannot be satisfied by a
    shallow or truncated clone: a history that lost commits on the way fails
    here rather than shipping as "orderly" with holes in it.
    """
    count = int(_count(dest, "rev-list", "--count", "HEAD") or 0)
    expected = floor + 1
    return Check(
        "development history preserved",
        count == expected,
        f"rev-list --count HEAD = {count}; expected {expected} "
        f"({floor} from the source, plus the submission import commit)",
    )


def no_remote_row(dest: Path) -> Check:
    """Zero remotes. Nothing in this plan may be pushable by accident."""
    found = [name for name in git_out(dest, "remote").splitlines() if name.strip()]
    return Check("zero remotes", not found, f"{len(found)} remote(s) {found}")


def disjoint_history_row(source_root: Path, sha: str) -> Check:
    """The built commit must exist in NO history the source repository knows."""
    known = subprocess.run(
        ["git", "cat-file", "-e", f"{sha}^{{commit}}"],
        cwd=source_root, capture_output=True, text=True, check=False,
    ).returncode == 0
    return Check(
        "history disjoint from the source repository",
        not known,
        f"commit {sha[:7]} {'IS' if known else 'is not'} an object in the source "
        "repository; a shared commit would mean an inherited history",
    )


def rooted_history_row(source_root: Path, dest: Path) -> Check:
    """HEAD is NEW, its parent is the source's own HEAD. Both halves, or neither.

    The mirror image of `disjoint_history_row`, and deliberately not merely its
    negation. "Some commit is shared" would be satisfied by a stray object; this
    asserts the import commit descends DIRECTLY from the commit the source is
    sitting on, which is the only shape that makes the published log the real
    development history rather than something that merely overlaps it.
    """
    head = _count(dest, "rev-parse", "HEAD")
    parent = _count(dest, "rev-parse", "HEAD~1")
    head_known = _known(source_root, head)
    parent_known = _known(source_root, parent)
    return Check(
        "history rooted in the source repository",
        parent_known and not head_known,
        f"parent {parent[:7]} {'IS' if parent_known else 'is NOT'} known to the source "
        f"and HEAD {head[:7]} {'IS' if head_known else 'is not'} -- the import commit "
        "must be new and must sit directly on the source's history",
    )


def _known(source_root: Path, sha: str) -> bool:
    """Whether *sha* resolves to a commit object in the source repository."""
    return subprocess.run(
        ["git", "cat-file", "-e", f"{sha}^{{commit}}"],
        cwd=source_root, capture_output=True, text=True, check=False,
    ).returncode == 0


def cross_link_row(dest: Path, role: str) -> Check:
    """The rule-49 block, present and naming this repository's own role."""
    readme = Path(dest) / "README.md"
    text = readme.read_text(encoding="utf-8") if readme.is_file() else ""
    ok = MARKER in text and f"role={role}" in text
    return Check(
        "rule-49 cross-link block present",
        ok,
        f"README.md {'carries' if ok else 'does NOT carry'} the split banner for "
        f"role={role} ({len(text)} bytes read)",
    )


def git_rows(dest: Path, source_root: Path, role: str,
             history_floor: int | None = None) -> tuple[Check, ...]:
    """Every git-shape row for one built repository.

    `history_floor` selects which pair of history rows applies and carries the
    number they are checked against. None keeps 08-10's shape (one commit,
    disjoint); an int is the source's commit count for a history-carrying build.
    Two rows change meaning together, never one, because "one commit" and
    "disjoint history" were two statements of the same decision.
    """
    if history_floor is None:
        sha = _count(dest, "rev-parse", "HEAD")
        history = (single_commit_row(dest), disjoint_history_row(source_root, sha))
    else:
        history = (
            preserved_history_row(dest, history_floor),
            rooted_history_row(source_root, dest),
        )
    return (*history, no_remote_row(dest), cross_link_row(dest, role))


def overall(rows) -> bool:
    """True only when there is at least one row and every row passed."""
    listed = tuple(rows)
    return bool(listed) and all(row.ok for row in listed)


def render(role: str, rows) -> str:
    """A plain-text report: one line per row, every count visible."""
    listed = tuple(rows)
    lines = [f"=== split repository: {role} ===", ""]
    lines += [f"[{'PASS' if row.ok else 'FAIL'}] {row.name}: {row.detail}" for row in listed]
    passed = sum(1 for row in listed if row.ok)
    lines += ["", f"{passed}/{len(listed)} rows passed"]
    if not overall(listed):
        lines.append("VERDICT: FAIL")
    else:
        lines.append("VERDICT: pass")
    return "\n".join(lines) + "\n"
