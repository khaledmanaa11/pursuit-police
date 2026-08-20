"""The provenance document a split repository carries (08-10).

`docs/REPO-SPLIT.md` states what shipped and what did not, in counts and named
reasons, never adjectives. It refuses to describe a zero-file build outright:
an empty repository passes every quality gate by looking at nothing, and a
provenance document that made that look deliberate would certify the vacuity.

NO URL IS EVER WRITTEN HERE. The rule-49 cross-links live in the README banner
(`split_docs`), read from `league.json`; this document only explains the file
list, and `tests/unit/test_split_provenance.py` asserts nothing URL-shaped
appears in its output.
"""

from __future__ import annotations

from split_build import EmptyBuildError


def provenance(role: str, source_commit: str, generated: str, included: int,
               excluded: tuple[tuple[str, str], ...]) -> str:
    """`docs/REPO-SPLIT.md` for the built repository: what shipped, and what did not."""
    if included <= 0:
        raise EmptyBuildError(
            f"provenance asked to describe a build of {included} files. An empty "
            "repository passes every gate by looking at nothing."
        )
    rows = "\n".join(f"| `{path}` | {reason} |" for path, reason in excluded) or \
        "| _(none)_ | the tracked set carried nothing that had to be subtracted |"
    return "\n".join((
        f"# Repository split — the `{role}` half",
        "",
        f"Generated {generated} from the development repository at commit "
        f"`{source_commit}` by `scripts/build_split_repos.py`.",
        "",
        "## How the file list was derived",
        "",
        "`git ls-files` on the source repository, minus the subtractions below. **Never a",
        "directory walk**: the development tree holds an untracked `.env` and an untracked",
        "copy of the course book, and a walk would publish a live credential and a",
        "copyrighted text in one step. The tracked set contains neither, by construction.",
        "",
        f"**Files in this repository: {included}.**",
        "",
        "## What was subtracted, and why",
        "",
        "| Path | Reason |",
        "|---|---|",
        rows,
        "",
        "The live games-played counters (`config/*/games_played*.json`) are the number this",
        "team declares to the league. They are gitignored in the source repository, so they",
        "were never in the tracked set; the build subtracts them BY NAME as well, so a",
        "future force-add cannot carry them here. Misreporting that number is an absolute",
        "disqualification, and a stale copy travelling inside a public repository is a way",
        "to misreport it by accident.",
        "",
        "## Both seats' configuration ships",
        "",
        "`config/police/` and `config/thief/` are both present. The test suite loads both,",
        "so a repository carrying one could not run its own quality gates. The two agents",
        "are still separate processes with no shared runtime state (rule 2).",
        "",
        "## Before your first commit here",
        "",
        "```bash",
        "git config core.hooksPath scripts/hooks   # the 150-line + ruff pre-commit gate",
        "uv sync                                   # uv only; there is no requirements file",
        "```",
        "",
    ))
