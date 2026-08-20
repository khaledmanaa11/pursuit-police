"""Materialising one split repository's file tree on disk (08-10, D-76).

NOTHING HERE RUNS GIT AT ALL. This module prepares a destination and copies
files; staging and committing live in `split_commit`, whose every git call is
local. Pushing is 08-12, and it is a human's decision on a human's account.

THE DESTINATION IS CHECKED AGAINST THE SOURCE. `git init` inside the development
working tree gives the new repository the old one's history and its `origin`; a
single reflex `git push` then publishes several hundred private commits to a
public URL. `prepare_destination` refuses any destination at or under the source
root, and the refusal is proven by making it happen in
`tests/unit/test_split_build.py`.
"""

from __future__ import annotations

import os
import shutil
import stat
from pathlib import Path


class UnsafeDestinationError(RuntimeError):
    """The build destination is inside the source repository, or already in use."""


class EmptyBuildError(RuntimeError):
    """A build step was asked to copy, commit or describe ZERO files."""


def _force_writable(func, path, _exc_info) -> None:
    """Retry a failed removal after clearing the read-only bit.

    MEASURED, NOT DEFENSIVE. Git writes every loose object read-only, and on
    Windows `os.unlink` then raises `PermissionError: [WinError 5]` -- the first
    real `--replace` rebuild died part-way through deleting `.git/objects/` and
    left a destination that was neither the old tree nor the new one. A
    half-deleted repository is the worst possible state for something a human is
    about to publish.
    """
    os.chmod(path, stat.S_IWRITE)
    func(path)


def prepare_destination(dest: Path, source_root: Path, replace: bool = False) -> Path:
    """An empty directory OUTSIDE *source_root*, created if it does not exist."""
    dest = Path(dest).resolve()
    source_root = Path(source_root).resolve()
    if dest == source_root or source_root in dest.parents:
        raise UnsafeDestinationError(
            f"{dest} is inside the source repository {source_root}. A split built there "
            "would inherit this repository's history and its remote; one reflex push then "
            "publishes every private commit. Build outside the tree (D-76)."
        )
    if dest.exists() and any(dest.iterdir()):
        if not replace:
            raise UnsafeDestinationError(
                f"{dest} already exists and is not empty. Pass replace=True to rebuild it, "
                "so that a stale tree can never be mistaken for a fresh build."
            )
        shutil.rmtree(dest, onerror=_force_writable)
    dest.mkdir(parents=True, exist_ok=True)
    return dest


def copy_files(source_root: Path, dest_root: Path, paths) -> int:
    """Copy every listed path, byte for byte, and return how many were copied."""
    listed = tuple(paths)
    if not listed:
        raise EmptyBuildError(
            "copy_files was given an empty file list. A repository built from nothing "
            "passes every quality gate by looking at nothing."
        )
    copied = 0
    for relative in listed:
        origin = Path(source_root) / relative
        if not origin.is_file():
            raise FileNotFoundError(
                f"{origin} is in the manifest but not in the source tree. The manifest "
                "comes from `git ls-files`, so this means the working tree is missing a "
                "tracked file -- refusing to build a repository quietly short of one."
            )
        target = Path(dest_root) / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(origin, target)
        copied += 1
    return copied
