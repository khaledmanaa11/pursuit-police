"""The two generated documents a split repository carries (08-10).

RULE 49 WANTS TWO REAL, CROSS-LINKED REPOSITORY LINKS, AND THE BANNER NOW READS
THEM RATHER THAN ASSERTING THEY DO NOT EXIST. Until 08-12 they genuinely did
not, so both were written as a STATED-ABSENT marker. The owner created and
pushed both repositories on 2026-08-19; a banner that kept saying "not created
or pushed yet" put a FALSE rule-49 claim at the top of the file whose body
listed the real URLs three screens down. The same README contradicted itself
about the one property rule 49 is about.

THE LINKS COME FROM `config/<role>/league.json`, NEVER FROM A LITERAL HERE.
`repo_links` reads `repo_urls.own_cop` / `own_thief` out of the shipped config,
so the banner, the config and the loader that refuses a placeholder in live mode
all answer to ONE value. A URL typed into this module would be a second source
that could drift from the first without anything noticing.

A PLACEHOLDER WOULD STILL BE WORSE THAN A HOLE, and `URL_ABSENT` is kept for
exactly that. `https://github.com/<user>/pursuit-cop` reads as done to every
human and every grep that goes looking. A slot that is null in `league.json` --
the opponent's two, before league day -- still renders as a stated absence. This
is the discipline 08-04 applied to `league.json`, whose loader refuses a
placeholder outright when `reporting.mode = live` (D-81).

THE INJECTION ANCHOR IS CHECKED, NOT ASSUMED. A splitter that cannot find the
README's H1 and returns the text unchanged produces a repository with no
cross-link while reporting success -- so `inject` raises, both when the anchor is
missing and when the banner is already there.
"""

from __future__ import annotations

#: Each role's companion repository.
COMPANION = {"police": "thief", "thief": "police"}
#: How each role's agent is named in prose.
ROLE_NOUN = {"police": "cop", "thief": "thief"}
#: The machine-checkable marker `split_verify` looks for in a built README.
MARKER = "<!-- split-repo-banner"
#: The stated-absent value, for a slot `league.json` really does leave null.
URL_ABSENT = "**NOT ASSIGNED — no URL is recorded in `league.json` for this slot**"
#: `league.json` slot names, per role, for the two repositories WE publish.
OWN_SLOT = {"police": "own_cop", "thief": "own_thief"}


class MissingAnchorError(RuntimeError):
    """The README has no `# ` heading, or already carries a banner."""


class EmptyBuildError(RuntimeError):
    """A provenance document was asked to describe a zero-file build."""


def repo_links(source_root) -> dict:
    """Both roles' published URLs, read from the shipped `league.json`.

    One source of truth. A slot that is null, empty or missing comes back as
    `URL_ABSENT`, so the banner states an absence rather than inventing a link.
    """
    import json
    from pathlib import Path

    links = {}
    for role, slot in OWN_SLOT.items():
        path = Path(source_root) / "config" / role / "league.json"
        value = None
        if path.is_file():
            data = json.loads(path.read_text(encoding="utf-8"))
            value = (data.get("league", data).get("repo_urls") or {}).get(slot)
        links[role] = value.strip() if isinstance(value, str) and value.strip() else URL_ABSENT
    return links


def banner(role: str, source_commit: str, generated: str, links: dict | None = None) -> str:
    """The rule-49 cross-link block for *role*, carrying both published URLs.

    *links* maps each role to its URL or to `URL_ABSENT`; omitting it states both
    absent, which is what a caller with no config to read should say.
    """
    other = COMPANION[role]
    links = links or {"police": URL_ABSENT, "thief": URL_ABSENT}
    mine, theirs = links.get(role, URL_ABSENT), links.get(other, URL_ABSENT)
    absent = URL_ABSENT in (mine, theirs)
    note = (
        [
            "> **A link shown as NOT ASSIGNED is stated absent, never filled with a",
            "> plausible-looking value.** Inventing one would read as done to every human",
            f"> and every search that went looking for it. `config/{role}/league.json` is the",
            "> single source these are read from; its loader refuses a placeholder when",
            "> reporting runs live.",
        ]
        if absent
        else [
            f"> Both links are read from `config/{role}/league.json` at build time, never",
            "> typed into the generator, so the banner, the config and the loader that",
            "> refuses a placeholder in live mode cannot drift apart.",
        ]
    )
    return "\n".join((
        f"{MARKER} role={role} source={source_commit} -->",
        "",
        f"> **This is the `{role}` repository — the {ROLE_NOUN[role]} agent — one half of a",
        "> two-repository submission (rule 49).** It is generated from the development",
        f"> repository at commit `{source_commit}` on {generated} by",
        "> `scripts/build_split_repos.py`, from `git ls-files` and nothing else.",
        ">",
        "> | Rule-49 link | Value |",
        "> |---|---|",
        f"> | This repository (`{role}`) | {mine} |",
        f"> | Companion repository (`{other}`) | {theirs} |",
        ">",
        *note,
        ">",
        "> Both `config/police/` and `config/thief/` ship here: the test suite loads both",
        "> seats, so a repository carrying one of them could not run its own gates. The two",
        "> agents remain separate PROCESSES with no shared runtime state (rule 2); these are",
        "> two static directories of JSON.",
        ">",
        "> The live games-played counters are deliberately absent — see",
        "> `docs/REPO-SPLIT.md`.",
        "",
    ))


def inject(readme_text: str, banner_text: str) -> str:
    """Place *banner_text* immediately after the README's first `# ` heading."""
    if MARKER in readme_text:
        raise MissingAnchorError(
            "this README already carries a split banner; injecting a second one would "
            "ship two contradictory rule-49 blocks."
        )
    lines = readme_text.splitlines()
    for index, line in enumerate(lines):
        if line.startswith("# "):
            head = lines[: index + 1]
            tail = lines[index + 1:]
            return "\n".join([*head, "", banner_text.rstrip("\n"), *tail]) + "\n"
    raise MissingAnchorError(
        "the README has no top-level `# ` heading, so the rule-49 cross-link block has "
        "nowhere to go. Refusing to return the README unchanged: a split repository "
        "without its cross-link is the defect this build exists to prevent."
    )


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
