# Repository split — the `police` half

Generated 2026-08-20T15:30:27Z from the development repository at commit `d1ec862` by `scripts/build_split_repos.py`.

## How the file list was derived

`git ls-files` on the source repository, minus the subtractions below. **Never a
directory walk**: the development tree holds an untracked `.env` and an untracked
copy of the course book, and a walk would publish a live credential and a
copyrighted text in one step. The tracked set contains neither, by construction.

**Files in this repository: 1079.**

## What was subtracted, and why

| Path | Reason |
|---|---|
| _(none)_ | the tracked set carried nothing that had to be subtracted |

The live games-played counters (`config/*/games_played*.json`) are the number this
team declares to the league. They are gitignored in the source repository, so they
were never in the tracked set; the build subtracts them BY NAME as well, so a
future force-add cannot carry them here. Misreporting that number is an absolute
disqualification, and a stale copy travelling inside a public repository is a way
to misreport it by accident.

## Both seats' configuration ships

`config/police/` and `config/thief/` are both present. The test suite loads both,
so a repository carrying one could not run its own quality gates. The two agents
are still separate processes with no shared runtime state (rule 2).

## Before your first commit here

```bash
git config core.hooksPath scripts/hooks   # the 150-line + ruff pre-commit gate
uv sync                                   # uv only; there is no requirements file
```
