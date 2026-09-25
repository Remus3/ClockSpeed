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
from tests.test_citation_tables import (
    DEEP_ARCHIVE,
    DELIBERATE,
    LEDGER,
    NEWLINE,
    NO_TARGET,
    Disposition,
    bare_path,
    doc_text,
)
from tests.test_citation_tables import tracked as _tracked
from tests.test_docs_citations import (
    bare_name_problems,
    citation_site_identities,
    line_pointer_problems,
    unresolved_citations,
)

# The corpus fixture, rebound under the name pytest resolves it by - an import
# alias alone does not bind a fixture, as tests/test_disposition_sites.py measured.
tracked = _tracked

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
        "<module>": 8,
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


# --- CS-812: the ARM reports what only a contract used to --------------------

#: The doc every CS-812 control keys its disposition on. Any guarded doc would
#: do; this one is scoped whole, so the text the arm reads is the text written.
_DOC: Final = "ROADMAP.md"
_BARE: Final = "test_a_name_that_is_not_bound"


def _full() -> str:
    """A dead ``path::name`` citation, assembled at call time for :func:`bare_path`'s reason."""
    return bare_path("tests", "synthetic", "test_planted.py") + "::" + "test_a_name_thats_out"


def _entry(heading: str) -> str:
    """One ledger-shaped entry spelling the bare name and the full citation once each."""
    return f'## {heading}\n\ngrep -c "{_BARE}" x\nsee `{_full()}`\n\n'


def _forgiving(text: str, cited: str, kind: str = DELIBERATE) -> dict[tuple[str, str], Disposition]:
    """A record forgiving exactly the sites ``cited`` has in ``text`` today."""
    at = citation_site_identities(text, cited)
    return {(_DOC, cited): Disposition(kind, "", "adjudicated as dead", at)}


def test_the_bare_arm_itself_reports_a_second_site_of_a_forgiven_name() -> None:
    """A dead name written again under a NEW heading is a new finding, in the arm.

    The record answers the first entry. Before CS-812 the arm asked only whether
    the NAME was forgiven, so the second entry came back empty from the arm and
    only the module-level site contract noticed it.
    """
    first = _entry("The adjudicated entry")
    table = _forgiving(first, _BARE)
    twice = first + _entry("A later entry nobody adjudicated")

    assert bare_name_problems(_DOC, first, [], [], table) == [], (
        "the record did not forgive the one site it names, so the report below proves nothing"
    )
    reported = [name for name, _why in bare_name_problems(_DOC, twice, [], [], table)]
    assert reported == [_BARE], f"the second site of a forgiven bare name read {reported}"


def test_the_path_arm_itself_reports_a_second_site_of_a_forgiven_citation() -> None:
    """The same arrival, on the ``path::name`` arm, which de-duplicated the same way."""
    first = _entry("The adjudicated entry")
    table = _forgiving(first, _full())
    twice = first + _entry("A later entry nobody adjudicated")

    assert unresolved_citations(_DOC, first, {}, table) == [], (
        "the record did not forgive the one site it names, so the report below proves nothing"
    )
    found = unresolved_citations(_DOC, twice, {}, table)
    reported = [f"{path}::{name}" for path, name, _why in found]
    assert reported == [_full()], f"the second site of a forgiven citation read {reported}"


def test_a_forgiven_site_above_the_first_heading_is_a_finding_not_an_abort() -> None:
    """A site with no identity cannot be named by any record, so the arm reports it.

    Raising would take the whole arm down as an ERROR over one doc; forgiving
    would be the key-only answer CS-812 removed.
    """
    text = f'grep -c "{_BARE}" x\n\n## A heading below the site\n'
    table = {(_DOC, _BARE): Disposition(DELIBERATE, "", "adjudicated as dead", ("x",))}

    found = bare_name_problems(_DOC, text, [], [], table)

    assert [name for name, _why in found] == [_BARE], f"an unanchored forgiven site read {found}"
    assert "above the first heading" in found[0][1], found[0][1]


def test_the_bare_arm_reports_a_forgiven_name_that_has_come_back_to_life() -> None:
    """A bare disposition for a name the tree binds again forgives nothing, and says so.

    THE PRE-EXISTING HALF OF CS-812. The contract's now-resolves branch is gated
    on a path separator in the key, so it never fires for a bare key, and the
    arm skipped every bound name before it looked at the table at all.
    """
    text = _entry("The adjudicated entry")
    table = _forgiving(text, _BARE)

    assert bare_name_problems(_DOC, text, [], [], table) == [], "the control is not clean"
    revived = [name for name, _why in bare_name_problems(_DOC, text, [_BARE], [], table)]
    as_module = [name for name, _why in bare_name_problems(_DOC, text, [], [_BARE], table)]
    assert revived == [_BARE], f"a forgiven name bound again read {revived}"
    assert as_module == [_BARE], f"a forgiven name that became a module read {as_module}"
    assert bare_name_problems(_DOC, text, [_BARE], [], {}) == [], (
        "a live name with no record was reported, so the arm now reports every bound name"
    )


def test_the_path_arm_reports_a_forgiven_citation_that_resolves_again() -> None:
    """The ``path::name`` twin: a record for a citation that resolves is stale in the arm."""
    text = _entry("The adjudicated entry")
    table = _forgiving(text, _full(), NO_TARGET)
    path, _, name = _full().partition("::")
    live = {path: f"def {name}() -> None:\n    pass\n"}

    assert unresolved_citations(_DOC, text, {}, table) == [], "the control is not clean"
    reported = [f"{p}::{n}" for p, n, _why in unresolved_citations(_DOC, text, live, table)]
    assert reported == [_full()], f"a forgiven citation that resolves again read {reported}"
    assert unresolved_citations(_DOC, text, live, {}) == [], (
        "a live citation with no record was reported, so the arm reports every citation"
    )


# --- CS-1163: a bare continuation is a finding, or a pinned declination ------

#: THE CARRIERS THAT MAY NOT BE REPAIRED IN PLACE, AND HOW MANY BARE CONTINUATIONS
#: EACH HOLDS. An EQUALITY pin, measured over the whole file with
#: ``test_docs_citations.BARE_CONTINUATION_RE``. The ledger is append-only and the
#: deep archive is historical, so neither may be edited to discharge its sites;
#: every other tracked markdown file may, and carries none.
#:
#: WHY EQUALITY AND NOT A CEILING. OVER the pin is a NEW bare continuation in a
#: carrier that is still being appended to - write that entry with a full pointer
#: or a ``path::symbol`` citation instead. UNDER it is room banked for the next
#: append; lower the pin in the same change that retires a site.
#:
#: This is the declination CS-1163's acceptance allows, recorded as a number the
#: suite reads rather than as a sentence, so it cannot drift from the corpus.
BARE_CONTINUATIONS_DECLINED: Final[Mapping[str, int]] = {LEDGER: 48, DEEP_ARCHIVE: 5}


def bare_continuation_problems(text: str) -> list[str]:
    """One finding per bare continuation in ``text``, located by line.

    Read with :data:`tests.test_docs_citations.BARE_CONTINUATION_RE`, the judged
    shape the carrier boundary also reads, so the boundary and the arm cannot
    disagree about what a continuation is.

    Args:
        text: A doc's whole text.

    Returns:
        ``line N: <spelling>`` per site, in order.
    """
    return [
        f"line {text.count(NEWLINE, 0, match.start()) + 1}: {match.group(0)}"
        for match in test_docs_citations.BARE_CONTINUATION_RE.finditer(text)
    ]


def pointer_findings(text: str, line_counts: Mapping[str, int]) -> list[str]:
    """Every line-pointer finding in ``text``, in BOTH forms: full and bare continuation.

    The range arm's findings for full ``path.ext:NNN`` pointers, plus one per
    bare continuation. ONE COUNT OVER BOTH FORMS is what lets a single planted
    control prove neither half has stopped matching.
    """
    full, _declined = line_pointer_problems(text, line_counts)
    return full + bare_continuation_problems(text)


def test_a_bare_continuation_beside_a_full_pointer_raises_the_finding_count() -> None:
    """THE PLANT CS-1163 ASKS FOR: the count RISES, and the full pointer is still seen.

    The full pointer is out of range, so it is a finding in both texts - the
    control that the same run still reads the full form. The continuation is
    then the only difference, so a guard blind to it cannot rise, and a guard
    that stopped reading the full form fails the control.
    """
    cited = bare_path("tools", "synthetic", "planted.py")
    counts = {cited: 10}
    alone = f"see `{cited}:900`.\n"
    beside = f"see `{cited}:900` and then `:901`.\n"

    before = pointer_findings(alone, counts)
    after = pointer_findings(beside, counts)

    full_seen = [any(f"{cited}:900" in line for line in run) for run in (before, after)]
    assert full_seen == [True, True], f"the full pointer was not a finding: {before} {after}"
    assert len(after) > len(before), (
        f"a bare continuation beside a full pointer did not raise the count: {after}"
    )


def test_a_ranged_continuation_is_seen_and_a_bare_colon_is_not() -> None:
    """Both spellings the corpus uses are read, and nothing shorter is."""
    found = bare_continuation_problems("at `:990-996`, then `:1094`, not `:` or `:x`\n")

    assert len(found) == 2, f"the continuation shapes read {found}"  # noqa: PLR2004


def test_no_tracked_markdown_file_carries_a_bare_continuation_outside_the_pinned_carriers(
    tracked: list[str],
) -> None:
    """Every tracked markdown file, less the pinned carriers, carries none.

    THE POPULATION IS THE INDEX, not the guarded set: a continuation is a pointer
    whatever doc carries it, and the census that sized this item read every
    tracked markdown file.
    """
    docs = [path for path in tracked if path.endswith(".md")]
    assert set(BARE_CONTINUATIONS_DECLINED) <= set(docs), "a pinned carrier is not tracked"
    found = [
        f"  {doc} {problem}"
        for doc in docs
        if doc not in BARE_CONTINUATIONS_DECLINED
        for problem in bare_continuation_problems(doc_text(doc))
    ]

    assert not found, (
        "bare continuations in a doc that may be edited:"
        + NEWLINE
        + NEWLINE.join(found)
        + NEWLINE
        + "Write the full pointer, or a path::symbol citation for a tracked module."
    )


def test_each_pinned_carrier_holds_exactly_its_pinned_bare_continuations() -> None:
    """The declined carriers are counted, not exempted - in both directions."""
    measured = {
        doc: len(bare_continuation_problems(doc_text(doc))) for doc in BARE_CONTINUATIONS_DECLINED
    }

    assert measured == dict(BARE_CONTINUATIONS_DECLINED), (
        f"measured {measured} against the pin {dict(BARE_CONTINUATIONS_DECLINED)}. OVER is a"
        " new bare continuation in an append-only carrier; UNDER is a pin gone slack."
    )
