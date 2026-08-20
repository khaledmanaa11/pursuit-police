"""The rule-49 cross-link block a split repository's README carries (08-10).

THE CROSS-LINK URLS NOW EXIST, AND THE OLD TESTS ASSERTED THEY NEVER WOULD.
Until 08-12 both repositories were unpublished, so every test here asserted the
ABSENCE of a URL-shaped string as hard as the presence of the marker. The owner
published both on 2026-08-19; the banner then still read "not created or pushed
yet" at the top of a README whose body listed the real links, so the file
contradicted itself about the one property rule 49 is about.

WHAT REPLACES THE ABSENCE ASSERTION IS NARROWER, NOT WEAKER. `banner` now takes
the links and renders what it is given, and the tests below assert BOTH
directions: given real URLs it must carry exactly those two and nothing
URL-shaped that was not passed in; given a null slot it must still render
`URL_ABSENT` and invent nothing. The invented-value failure -- a plausible
`https://github.com/<user>/<repo>` that reads as done -- is still refused,
because the generator has no URL literal of its own to fall back on.

INJECTION RAISES WHEN IT CANNOT FIND ITS ANCHOR. A splitter that silently
returns the README unchanged ships a repository with no cross-link at all, and
the build would still report success.
"""

from __future__ import annotations

import ast
import pathlib

import pytest

from tests.unit.submission_gate_helpers import load

docs_mod = load("split_docs")

SHA = "0f6fbf3"
STAMP = "2026-08-17T00:00:00Z"
#: Two links shaped like the real ones, never read from the shipped config: this
#: file tests the RENDERER, and coupling it to `league.json` would make it pass
#: or fail for reasons that have nothing to do with the banner.
LINKS = {
    "police": "https://github.com/example-owner/pursuit-police",
    "thief": "https://github.com/example-owner/pursuit-thief",
}
URL_SHAPES = ("http://", "https://", "github.com", "example.com", "<url>", "TODO")


@pytest.mark.parametrize("role", ["police", "thief"])
def test_the_banner_names_its_own_role_and_its_companion(role: str) -> None:
    text = docs_mod.banner(role, SHA, STAMP)
    other = docs_mod.COMPANION[role]
    assert f"`{role}`" in text
    assert f"`{other}`" in text
    assert SHA in text


@pytest.mark.parametrize("role", ["police", "thief"])
def test_a_banner_given_no_links_states_both_absent_and_invents_neither(role: str) -> None:
    """The pre-publication shape, still reachable and still guarded."""
    text = docs_mod.banner(role, SHA, STAMP)
    assert text.count(docs_mod.URL_ABSENT) == 2, text
    lowered = text.lower()
    for shape in URL_SHAPES:
        assert shape.lower() not in lowered, f"the banner carries a URL-shaped {shape!r}"


@pytest.mark.parametrize("role", ["police", "thief"])
def test_a_banner_given_real_links_carries_exactly_those_two(role: str) -> None:
    text = docs_mod.banner(role, SHA, STAMP, LINKS)
    for url in LINKS.values():
        assert url in text, f"{url} is missing from the {role} banner"
    assert docs_mod.URL_ABSENT not in text, "a published slot still reads as absent"


@pytest.mark.parametrize("role", ["police", "thief"])
def test_one_missing_slot_is_stated_absent_beside_a_real_one(role: str) -> None:
    """The half-published shape: the known link shows, the unknown one does NOT
    borrow its neighbour's value or a plausible-looking guess."""
    half = {"police": LINKS["police"], "thief": docs_mod.URL_ABSENT}
    text = docs_mod.banner(role, SHA, STAMP, half)
    assert text.count(docs_mod.URL_ABSENT) == 1, text
    assert LINKS["police"] in text
    assert LINKS["thief"] not in text


def test_the_generator_holds_no_url_literal_of_its_own() -> None:
    """No URL-shaped STRING CONSTANT in the module's code, so there is nothing to
    fall back on when a slot is empty.

    An AST walk, not a grep over the file: the module docstring quotes
    `https://github.com/<user>/pursuit-cop` as the example of what must never be
    written, and a text scan flags that prose as if it were a hardcoded link --
    a check that fires on a file for saying the right thing. Docstrings are
    subtracted by name, every other constant is examined.
    """
    tree = ast.parse(pathlib.Path(docs_mod.__file__).read_text(encoding="utf-8"))
    docstrings = {
        ast.get_docstring(node, clean=False)
        for node in ast.walk(tree)
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef))
    }
    offenders = [
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and node.value not in docstrings
        and ("github.com" in node.value or "https://" in node.value)
    ]
    assert not offenders, f"split_docs.py carries hardcoded URL literal(s): {offenders}"


def test_the_ast_guard_would_catch_a_planted_literal() -> None:
    """The control. A guard never seen to fire guards nothing -- this proves the
    docstring subtraction did not turn the check above into a vacuous pass."""
    planted = ast.parse('X = "https://github.com/someone/somewhere"')
    found = [
        node.value
        for node in ast.walk(planted)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
        and "github.com" in node.value
    ]
    assert found == ["https://github.com/someone/somewhere"]


def test_the_two_banners_are_not_the_same_document() -> None:
    assert docs_mod.banner("police", SHA, STAMP) != docs_mod.banner("thief", SHA, STAMP)


def test_the_banner_carries_a_machine_checkable_marker() -> None:
    text = docs_mod.banner("police", SHA, STAMP)
    assert docs_mod.MARKER in text
    assert "role=police" in text


def test_injection_places_the_banner_after_the_first_heading() -> None:
    readme = "# Title\n\nintro line\n\n## Installation\n\nbody\n"
    out = docs_mod.inject(readme, docs_mod.banner("thief", SHA, STAMP))
    lines = out.splitlines()
    assert lines[0] == "# Title"
    assert docs_mod.MARKER in out
    assert out.index(docs_mod.MARKER) < out.index("## Installation")
    for original in ("intro line", "## Installation", "body"):
        assert original in out


def test_injection_refuses_a_readme_with_no_top_level_heading() -> None:
    with pytest.raises(docs_mod.MissingAnchorError):
        docs_mod.inject("no heading here\n", docs_mod.banner("police", SHA, STAMP))


def test_injection_refuses_to_run_twice() -> None:
    once = docs_mod.inject("# Title\n\nbody\n", docs_mod.banner("police", SHA, STAMP))
    with pytest.raises(docs_mod.MissingAnchorError):
        docs_mod.inject(once, docs_mod.banner("police", SHA, STAMP))


def test_the_provenance_document_reports_counts_not_adjectives() -> None:
    text = docs_mod.provenance("police", SHA, STAMP, included=907, excluded=(
        ("config/police/games_played.json", "D-77: live rule-37 counter"),
    ))
    assert "907" in text
    assert "config/police/games_played.json" in text
    assert "D-77" in text
    assert "core.hooksPath scripts/hooks" in text
    for shape in URL_SHAPES:
        assert shape.lower() not in text.lower()


def test_the_provenance_document_refuses_a_zero_file_build() -> None:
    with pytest.raises(docs_mod.EmptyBuildError):
        docs_mod.provenance("police", SHA, STAMP, included=0, excluded=())
