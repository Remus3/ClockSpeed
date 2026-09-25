"""CS-811, CS-812, CS-1163 - what the citation guard family can SEE.

WHY THIS MODULE EXISTS AS A SEPARATE FILE. ``tests/test_docs_citations.py`` sits
inside the approach band ``tests/data/test_phase2_gate.py`` holds every file
under ``tests/`` to, and that ceiling is a non-negotiable 2 guard that must not be
raised to fit prose. The relocation seam CS-1066 and CS-1121 established is used
again: the patterns, the arms and the tables stay where they are, and this module
imports them and asserts about them.

THREE BLIND SPOTS, ONE PER ITEM.

* CS-811 - the boundary contract that keeps every judging pattern declared read
  ONE shape: a module-scope ``re.Pattern`` whose name ends ``_RE``. Five other
  shapes escaped it, all measured green. Four are now seen here; the fifth is
  recorded in :data:`ESCAPING_SHAPES` with the reason it cannot be.
* CS-812 - the two de-duplicating arms answered a forgiven citation by its KEY,
  so a second site of an already-forgiven name, and a bare disposition whose
  name had come back to life, were both invisible to the arm itself.
* CS-1163 - the line-pointer shape needs a full ``path.ext:NNN``, so a bare
  continuation - a backticked colon and a line number, written after a full
  pointer in the same sentence - was invisible to every arm.

THE DEPENDENCY RUNS ONE WAY. This module imports the family; nothing in the
family imports it back, which is the same arrangement
``tests/test_disposition_sites.py`` has, and for the same reason.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Final

import pytest

from tests import test_docs_citations
from tests.bare_path_guard import (
    held_patterns,
    module_file,
    module_patterns,
    namespace_closure,
    regex_call_sites,
)
from tests.test_bare_path_citations import WALK_ROOT, family
from tests.test_citation_tables import NEWLINE

# --- CS-811: every shape a judging pattern can be held in -------------------

#: EVERY SHAPE CS-811 MEASURED ESCAPING THE ``*_RE`` WALK, AND HOW EACH IS ANSWERED.
#: A shape is answered either by the arm named, which a planted control below
#: proves live, or by the recorded reason it cannot be caught. The contract
#: after this table asserts every named arm exists in this module, so the record
#: cannot outlive the arm it points at.
ESCAPING_SHAPES: Final[Mapping[str, str]] = {
    "a module-scope pattern named without the _RE suffix": (
        "test_every_pattern_held_anywhere_in_the_family_is_a_declared_shape"
    ),
    "a pattern held inside a module-scope dict": (
        "test_every_pattern_held_anywhere_in_the_family_is_a_declared_shape"
    ),
    "a pattern held inside a module-scope list": (
        "test_every_pattern_held_anywhere_in_the_family_is_a_declared_shape"
    ),
    "a pattern compiled at call time": (
        "test_every_regex_call_site_in_the_family_is_on_the_census"
    ),
    "an arm judging by substring": (
        "RECORDED, NOT CAUGHT. A substring judgement is an `in` test or a str"
        " method call, and Python spells it identically to membership in a set, a"
        " dict or a tuple and to every assertion message check this family makes."
        " The syntax tree carries no operand types, and the needle is as often a"
        " variable as a literal, so no reading of the source can tell a judging"
        " test from a plumbing one. A census of every such site would be bumped on"
        " every unrelated edit, which is a pin nobody keeps - the same reason the"
        " range arm refuses to assert what sits AT a line."
    ),
}

#: How many shapes the CS-811 verifier measured escaping, so the record above
#: cannot quietly lose a row.
_MEASURED_ESCAPING_SHAPES: Final = 5

#: EVERY REGEX CALL SITE IN THE FAMILY'S SOURCE, by module and enclosing scope.
#: AN EQUALITY PIN, so a pattern compiled or matched at call time - which no
#: namespace walk can see, because it is never bound at module scope - is a
#: number in the diff before it can judge anything. ``<module>`` is the top
#: level; a nested scope is dotted. A module with no site has no row.
#:
#: MODULE-SCOPE SITES ARE COUNTED TOO, deliberately. The namespace walk sees a
#: pattern that is BOUND; a top-level ``re.search`` whose Match is used and
#: dropped binds nothing, and only the count sees it.
REGEX_CALL_SITES: Final[Mapping[str, Mapping[str, int]]] = {
    "tests.bare_path_guard": {"<module>": 2},
    "tests.test_bare_path_citations": {
        "test_a_pattern_declared_one_module_over_is_reported_rather_than_unseen": 1,
    },
    "tests.test_docs_citations": {
        "<module>": 7,
        "test_appending_a_non_citation_pattern_spends_its_budget": 2,
    },
}


@pytest.fixture(scope="module")
def walked() -> list[tuple[str, Mapping[str, object]]]:
    """The family the class-closing walks run over, derived exactly as they derive it."""
    return family(namespace_closure([WALK_ROOT]))


_PLANTED: Final = "a-shape-the-boundary-has-never-been-told-about"


def _planted_namespaces() -> dict[str, dict[str, object]]:
    """One synthetic namespace per namespace-held escaping shape, built at call time."""
    return {
        "unsuffixed": {"UNSUFFIXED_SHAPE": re.compile(_PLANTED)},
        "dict": {"PLANTED_TABLE": {"a key": re.compile(_PLANTED)}},
        "list": {"PLANTED_ROWS": ["a string", re.compile(_PLANTED)]},
    }


@pytest.mark.parametrize("shape", ["unsuffixed", "dict", "list"])
def test_a_pattern_held_in_each_escaping_shape_is_seen(shape: str) -> None:
    """The walk sees the pattern in every shape the ``*_RE`` walk was blind to.

    PAIRED WITH THE OLD WALK ON THE SAME INPUT, so the control is not decorative:
    :func:`module_patterns` must still miss it, or the plant is not in an
    escaping shape at all and the positive proves nothing.
    """
    namespace = _planted_namespaces()[shape]

    seen = [pattern.pattern for pattern in held_patterns(namespace).values()]
    old = [pattern.pattern for pattern in module_patterns(namespace).values()]

    assert old == [], f"the plant for {shape} is visible to the old walk, so it escapes nothing"
    assert seen == [_PLANTED], f"the {shape} plant was not seen: {seen}"


def test_a_string_named_like_a_pattern_is_not_held() -> None:
    """The negative, so a walk that returned every value could not pass above."""
    found = held_patterns({"NOT_A_PATTERN_RE": "a string", "ROWS": ("x", {"k": 1})})

    assert found == {}, f"the walk returned non-patterns: {sorted(found)}"


def test_every_pattern_held_anywhere_in_the_family_is_a_declared_shape(
    walked: list[tuple[str, Mapping[str, object]]],
) -> None:
    """THE WIDENED WALK, over the same population the ``*_RE`` walk reads.

    Every compiled pattern a family module holds - under any name, and inside any
    module-scope container at any depth - must be a judged shape or a declared
    non-citation pattern. The tables themselves are containers of patterns and
    are walked too; their members are declared by construction.
    """
    held = {
        f"{dotted}.{name}": pattern
        for dotted, namespace in walked
        for name, pattern in sorted(held_patterns(namespace).items())
    }

    assert held, "no family module holds a pattern, so the walk reads an empty set"
    judged = test_docs_citations.JUDGED_SHAPES
    other = test_docs_citations.NON_CITATION_PATTERNS
    missing = sorted(name for name, value in held.items() if value not in judged + other)
    assert not missing, (
        "patterns held in the family that neither table declares:"
        + NEWLINE
        + NEWLINE.join(f"  {name}" for name in missing)
        + NEWLINE
        + "Name it *_RE at module scope and declare it, or stop judging by it."
    )


_CALL_TIME_SOURCE: Final = (
    "import re\n"
    "import re as rx\n"
    "from re import compile as build\n"
    "TOP_RE = re.compile('x')\n"
    "def judge(text):\n"
    "    return re.search('planted', text)\n"
    "class Arm:\n"
    "    def grade(self, text):\n"
    "        return rx.fullmatch('a', text) or build('b').search(text)\n"
    "def plain(text):\n"
    "    return text.split()\n"
)


def test_a_regex_built_at_call_time_is_counted_by_scope() -> None:
    """Every spelling of a regex call is counted, under the scope that makes it.

    THE ALIASES ARE THE POINT. A census reading only ``re.<name>`` is evaded by
    ``import re as rx`` or by importing the function itself, and both are here.
    A scope with no regex call has no row, so a census that counted every call
    could not pass.
    """
    found = regex_call_sites(_CALL_TIME_SOURCE)

    assert found == {"<module>": 1, "judge": 1, "Arm.grade": 2}, (
        f"the call-site census read {found}"
    )


def test_every_regex_call_site_in_the_family_is_on_the_census(
    walked: list[tuple[str, Mapping[str, object]]],
) -> None:
    """A pattern compiled at call time is a number in the diff before it can judge."""
    measured = {
        dotted: sites
        for dotted, _namespace in walked
        if (sites := regex_call_sites(module_file(dotted).read_text(encoding="utf-8")))
    }

    assert measured, "the family makes no regex call at all, so the census reads nothing"
    pinned = REGEX_CALL_SITES
    drifted = sorted(
        f"  {dotted}: measured {measured.get(dotted, {})}, pinned {pinned.get(dotted, {})}"
        for dotted in set(measured) | set(pinned)
        if measured.get(dotted, {}) != pinned.get(dotted, {})
    )
    assert not drifted, (
        "the family's regex call sites moved under REGEX_CALL_SITES:"
        + NEWLINE
        + NEWLINE.join(drifted)
        + NEWLINE
        + "A new site that judges a citation shape belongs at module scope as a declared"
        " *_RE; a site that does not is recorded here by moving the pin in the same change."
    )


def test_every_escaping_shape_names_a_live_arm_or_records_why_not() -> None:
    """The record of the five shapes cannot point at an arm that is not there."""
    here = globals()
    dangling = sorted(
        shape
        for shape, answer in ESCAPING_SHAPES.items()
        if not answer.startswith("RECORDED, NOT CAUGHT.") and not callable(here.get(answer))
    )

    assert len(ESCAPING_SHAPES) == _MEASURED_ESCAPING_SHAPES, "CS-811 measured five shapes"
    assert not dangling, f"shapes whose answering arm does not exist here: {dangling}"
