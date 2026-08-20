#!/usr/bin/env python
"""Build the two submission repositories from this one, LOCALLY (08-10).

    uv run python scripts/build_split_repos.py --dest C:/somewhere/outside
    uv run python scripts/build_split_repos.py --dest DIR --gates --json out.json

Exit 0 when every row of every built repository passes, 1 when any row fails,
2 when nothing was built or nothing was verified -- `check_submission.py`'s
contract (D-82), because a build that produced no rows must never read as a pass.

THIS COMMAND NEVER TOUCHES A REMOTE. It runs `init`, `add`, `commit` and local
reads. There is no `push`, no `remote add`, no `fetch`, no `tag` in this file or
in any module it imports, and every built repository is asserted to have ZERO
remotes before this returns. Creating the public repositories, adding their
remotes and pushing is 08-12 -- a human, on a human's account.

This file is the CLI; the plan/build/verify machinery is `split_driver`, which
also records WHY both repositories carry the same files (rule 2 vs D-77).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from split_build import UnsafeDestinationError  # noqa: E402
from split_driver import build_one, plan_build, verify_one  # noqa: E402
from split_manifest import ROLES  # noqa: E402
from split_report import overall, render  # noqa: E402

NAME_TEMPLATE = "pursuit-{role}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the two submission repositories")
    parser.add_argument("--dest", type=Path, required=True,
                        help="a directory OUTSIDE this repository to build into")
    parser.add_argument("--roles", nargs="+", default=list(ROLES), choices=list(ROLES))
    parser.add_argument("--replace", action="store_true", help="rebuild over an existing tree")
    parser.add_argument("--gates", action="store_true",
                        help="also run uv sync, ruff and pytest --cov inside each output")
    parser.add_argument("--with-history", action="store_true",
                        help="carry the source's commit history into each output "
                             "(SEGAL Sec17 grades 'orderly Git history'); the clone's "
                             "inherited origin is removed before the build returns")
    parser.add_argument("--json", type=Path, default=None, help="write the evidence here")
    parser.add_argument("--source", type=Path, default=None,
                        help="the repository to split (default: the one this script lives in)")
    args = parser.parse_args(argv)

    source_root = (args.source or Path(__file__).resolve().parent.parent).resolve()
    plan = plan_build(source_root)
    evidence, failures, checked = [], 0, 0
    for role in args.roles:
        try:
            built = build_one(source_root, args.dest / NAME_TEMPLATE.format(role=role),
                              role, args.replace, plan, args.with_history)
        except UnsafeDestinationError as exc:
            print(f"REFUSED: {exc}")
            return 2
        floor = plan.source_commits if args.with_history else None
        rows = verify_one(Path(built["path"]), source_root, role, args.gates, floor)
        checked += len(rows)
        failures += sum(1 for row in rows if not row.ok)
        print(render(role, rows))
        built["rows"] = [row.as_dict() for row in rows]
        built["verdict"] = "pass" if overall(rows) else "FAIL"
        evidence.append(built)

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n",
                             encoding="utf-8", newline="\n")
        print(f"Wrote {args.json}")
    if not evidence or not checked:
        print("NOTHING WAS BUILT OR NOTHING WAS CHECKED -- this is not a pass.")
        return 2
    print(f"{len(evidence)} repository/repositories, {checked} rows, {failures} failing")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
