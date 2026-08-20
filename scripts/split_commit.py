"""Committing exactly what the manifest lists into a built repository (08-10).

NOTHING HERE TOUCHES A REMOTE. Every git call is `init`, `add`, `commit`,
`remote` (a read) or `rev-parse`. There is no `push`, no `remote add`, no
`fetch` and no `tag` anywhere in this module, and `assert_no_remotes` turns
that from an intention into a checked property of the built tree. Pushing is
08-12, and it is a human's decision on a human's account.

FILES ARE STAGED BY EXPLICIT PATHSPEC, never `git add -A`. The list comes from
`split_manifest`, is written to a NUL-separated file and handed to git with
`--pathspec-from-file`, so what is committed is exactly what the manifest said
and a stray file in the destination cannot join the commit by accident. Both
public entry points share `_stage_and_commit`, so the initial-import path and
the onto-history path cannot drift apart in what they stage.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

from split_build import EmptyBuildError

#: `[project] authors = [{ name = "...", email = "..." }]`, for the commit identity.
_AUTHOR = re.compile(r'name\s*=\s*"([^"]+)"\s*,\s*email\s*=\s*"([^"]+)"')


class RemoteFoundError(RuntimeError):
    """A built repository has a remote. It must have none until a human adds one."""


def _run(root: Path, *args: str) -> str:
    done = subprocess.run(
        ["git", *args], cwd=root, capture_output=True, text=True, check=True
    )
    return done.stdout.strip()


def commit_identity(source_root: Path) -> tuple[str, str]:
    """The author declared in `pyproject.toml`, never a literal in this file."""
    text = (source_root / "pyproject.toml").read_text(encoding="utf-8")
    match = _AUTHOR.search(text)
    if not match:
        raise ValueError(
            f"{source_root / 'pyproject.toml'} declares no `authors` entry, so the split "
            "commit has no author to attribute. Refusing to invent one."
        )
    return match.group(1), match.group(2)


def remotes(root: Path) -> tuple[str, ...]:
    """Every configured remote name. Expected to be empty, always, here."""
    listed = _run(root, "remote")
    return tuple(name for name in listed.splitlines() if name.strip())


def assert_no_remotes(root: Path) -> int:
    """0 remotes, or raise. Returns the count so a caller can record the number."""
    found = remotes(root)
    if found:
        raise RemoteFoundError(
            f"{root} has remotes {found}. A split repository must carry none until a "
            "human creates the public repository and adds one (08-12)."
        )
    return 0


def _stage_and_commit(dest_root: Path, listed: tuple[str, ...], message: str,
                      identity: tuple[str, str]) -> str:
    """Stage exactly *listed* by NUL pathspec, commit once, prove zero remotes."""
    name, email = identity
    spec = Path(dest_root) / ".git" / "split-pathspec"
    spec.write_bytes(b"\0".join(path.encode("utf-8") for path in listed))
    _run(dest_root, "add", "--pathspec-from-file", str(spec), "--pathspec-file-nul")
    spec.unlink()
    _run(
        dest_root, "-c", f"user.name={name}", "-c", f"user.email={email}",
        "-c", "commit.gpgsign=false", "commit", "--no-verify", "-m", message,
    )
    assert_no_remotes(dest_root)
    return _run(dest_root, "rev-parse", "HEAD")


def commit_onto_history(dest_root: Path, paths, message: str, source_root: Path) -> str:
    """Commit exactly *paths* on top of an ALREADY-CLONED history (08-12).

    The sibling of `init_and_commit` for the `--with-history` path: no `git
    init`, because the repository already exists and already has commits. Uses
    the same NUL-separated pathspec, so the import commit stages exactly the
    manifest and cannot pick up a stray file the clone left behind. Deletions
    made by `split_history.prune_to_manifest` are already in the index and ride
    along in this commit -- which is the point: a file the manifest drops must
    leave in a commit a reader can see, not vanish between builds.

    `--allow-empty` is deliberately NOT passed. If the injected banner and
    provenance file produced no change, something upstream did not write them,
    and an empty import commit would hide that behind a plausible log entry.
    """
    listed = tuple(paths)
    if not listed:
        raise EmptyBuildError("refusing to add an empty import commit to a history.")
    return _stage_and_commit(dest_root, listed, message, commit_identity(source_root))


def init_and_commit(dest_root: Path, paths, message: str, source_root: Path) -> str:
    """`git init`, stage exactly *paths* by pathspec, commit once, return the hash.

    The identity is read BEFORE `git init`, so a source with no `authors` entry
    refuses while the destination is still exactly as it was found -- never a
    half-initialised repository at a path a human is about to inspect.
    """
    listed = tuple(paths)
    if not listed:
        raise EmptyBuildError("refusing to create a repository with an empty first commit.")
    identity = commit_identity(source_root)
    _run(dest_root, "init", "-b", "main")
    return _stage_and_commit(dest_root, listed, message, identity)
