"""CS-927 - the aggregate route-table count, and who is allowed to spell it.

THE DEFECT THIS CLOSES. ``clockspeed/surface/api/pending.py`` recited the size of
the AGGREGATE route table in prose - "the nine templates ``BOOTSTRAP.md`` section
7.1 names" - while ``clockspeed/surface/api/health.py::ENDPOINT_TEMPLATES``, the
one owner of that set, held TEN. The sentence went stale under CS-912, which
published ``/api/registry``, and nothing was watching: a docstring is not
executed, so no arm on this tree could go red when the table moved underneath it.
``clockspeed/surface/api/routes.py`` had already drawn the correct conclusion for
itself - "THE COUNT IS NEVER WRITTEN DOWN IN THIS MODULE, deliberately" - and
``tests/surface/audit_harness.py`` records CS-912 falsifying a third such
sentence elsewhere in this package. This module makes the rule GRADED for
``pending.py`` rather than merely observed.

WHAT IS COVERED, AND THE AUTHORITY FOR EACH ARM:

a. ``pending.py`` DOES NOT SPELL THE AGGREGATE COUNT AT ALL. Not "nine", and not
   "ten" either - a corrected literal is the same defect with a fresher date on
   it, which is CLAUDE.md section 4's "a hardcoded count in a doc is a lie with a
   timestamp on it". The owner of that number is ``health.ENDPOINT_TEMPLATES``,
   and prose that needs it names the owner instead of copying the value.
b. THE DETECTOR IS NOT BLIND. Arm (a) passes by finding nothing, and "found no
   problems" and "looks for no problems" are otherwise the same output
   (CONVENTIONS.md section 7.2). So the same detector is run against PLANTED
   prose - including the exact sentence this item removed, wrapped across a line
   break the way the docstring wrapped it - and the hit is asserted. Every word
   in the vocabulary is planted individually, because a vocabulary spelled as
   data and never swept is one whose members can be deleted one at a time with
   the suite staying green; ``tools/drift_guard.py`` had to repair exactly that
   failure once already.
c. THE BOUNDARY IS PINNED IN THE OTHER DIRECTION TOO. A distributive phrase -
   "ONE ROUTE PER TEMPLATE" - is not a count of templates and must not fire.
   Without that arm, widening the lookahead until arm (a) could never pass would
   go unnoticed.
d. THE AGGREGATE TABLE AND THE PUBLISHED SET ARE THE SAME SET. This is the arm
   the item asks for in so many words: it reddens if ``routes.ROUTES`` and
   ``health.ENDPOINT_TEMPLATES`` ever disagree. ``routes._checked`` already
   refuses such a table AT IMPORT, so in practice the disagreement reaches this
   file as a collection error rather than as a failed assertion. Either way this
   module is red. The assertion is kept so the reason is stated rather than
   inferred from a traceback, and so the guarantee survives a future assembler
   that checks less.
e. THE CLAIM ``pending.py`` ACTUALLY MAKES IS GRADED, NOT MERELY ITS ARITHMETIC.
   That docstring's point is that keying the aggregate BY TEMPLATE would silently
   drop a second entry under ``/api/advice/<id>/state``. So: the shipped table
   does not collapse under that keying, AND folding the method-boundary routes
   back in DOES collapse it. The second half is the non-vacuity control - without
   it "does not collapse" would also pass over a table where collapse was
   impossible, and the separation ``routes.ROUTES`` and
   ``advice.method_boundary_routes`` exist to maintain would be untested. The
   boundary accessor moved from ``pending`` to ``advice`` with CS-1269.

WHAT THIS MODULE DOES NOT COVER, stated as a boundary rather than left implied.
It grades ``pending.py`` ONLY. The same stale sentence lives in
``clockspeed/surface/server.py`` and in ``docs/adr/0012``; both sit outside this
slice's write-list and neither is touched nor asserted here. A green run here
says nothing about either.

Test-quality discipline (CONVENTIONS.md section 7.2). Every population size is
bound to a scalar before it is asserted, so the pytest assertion channel renders
an integer rather than the collection behind it (CS-850). The values these arms
render into a MESSAGE - route templates, and phrases lifted from a tracked source
file - are literals authored in this repository, which is the same reason
``routes.RouteAssemblyError`` is free to name the templates it refuses. No path
from this machine is rendered anywhere.
"""

from __future__ import annotations

import inspect
from typing import Final

import pytest

from clockspeed.surface.api import health, pending, routes

# ---------------------------------------------------------------------------
# The detector
# ---------------------------------------------------------------------------

#: Spelled number words this guard reads as a count. SPELLED AS DATA and swept
#: member by member below, so deleting one cannot leave the suite green.
#:
#: Deliberately NOT ``tools/drift_guard.py``'s ``TIER1_NUMBER_WORDS``. That
#: vocabulary is scoped to CI DURATIONS - it carries "forty-five", "sixty" and
#: "ninety" and omits "thirteen" - and its membership is pinned in both
#: directions by ``tests/test_tier1_budget.py``. Borrowing it would make this
#: guard's meaning change whenever somebody adds a duration spelling, which is a
#: coupling with no upside in either direction.
COUNT_WORDS: Final = (
    "one",
    "two",
    "three",
    "four",
    "five",
    "six",
    "seven",
    "eight",
    "nine",
    "ten",
    "eleven",
    "twelve",
    "thirteen",
    "fourteen",
    "fifteen",
    "sixteen",
    "seventeen",
    "eighteen",
    "nineteen",
    "twenty",
)

#: The noun whose count has exactly one owner. ``pending.py`` is free to state
#: its OWN size - "the five unbacked endpoints" is a fact this module owns - so
#: the guard is scoped to the aggregate's noun rather than to every number in the
#: file. That scoping is why "endpoints" is absent here.
COUNTED_NOUNS: Final = ("template", "templates")

#: How many tokens may sit between the number word and the noun before the pair
#: stops reading as a count. Two, which admits "nine templates" and "nine route
#: templates" while excluding the distributive "one route per template", where
#: the noun lands three tokens out. The exclusion is pinned by its own arm.
LOOKAHEAD: Final = 2


def _tokens(text: str) -> tuple[str, ...]:
    """Reduce text to lowercase alphabetic tokens, one per whitespace-run.

    WHITESPACE IS NORMALIZED ACROSS LINES, and that is the load-bearing part. The
    sentence this item removed wrapped mid-phrase - "hold exactly the" ended one
    line and "nine templates" began the next - so a line-oriented scan reads the
    two halves as unrelated and finds nothing. Splitting the whole source on
    arbitrary whitespace is what makes the wrap invisible to the detector.

    Punctuation and markup are dropped rather than tolerated, so ``TEMPLATE,``
    and ```` ``BOOTSTRAP.md`` ```` reduce to ``template`` and ``bootstrapmd``.
    A token with no letters at all - ``7.1`` - reduces to the empty string and
    can therefore never match a word in either vocabulary.

    Args:
        text: The prose to scan.

    Returns:
        One normalized token per whitespace-separated run, index-aligned with
        ``text.split()`` so a hit can be reported in its original spelling.
    """
    return tuple(
        "".join(character for character in token if character.isalpha()).lower()
        for token in text.split()
    )


def count_phrases(text: str) -> tuple[str, ...]:
    """Every place TEXT spells a count of the counted noun.

    Args:
        text: The prose to scan.

    Returns:
        The offending phrases in their ORIGINAL spelling, one per hit, so a
        failure names what to go and read rather than only how many there were.
    """
    normalized = _tokens(text)
    original = text.split()
    hits = []
    for index, token in enumerate(normalized):
        if token not in COUNT_WORDS:
            continue
        window = normalized[index + 1 : index + 1 + LOOKAHEAD]
        if any(word in COUNTED_NOUNS for word in window):
            hits.append(" ".join(original[index : index + 1 + LOOKAHEAD]))
    return tuple(hits)


# ---------------------------------------------------------------------------
# (b) and (c). The detector is graded BEFORE it is trusted.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("word", COUNT_WORDS)
def test_the_detector_fires_on_every_word_in_its_vocabulary(word: str) -> None:
    planted = f"is asserted to hold exactly the {word} templates section 7.1 names"
    hit_count = len(count_phrases(planted))
    assert hit_count == 1, f"the detector did not fire on a planted count word: {word}"


def test_the_detector_fires_on_the_sentence_this_item_removed() -> None:
    """The plant wraps mid-phrase, which is the shape a line-based scan misses."""
    planted = (
        "and is asserted to hold exactly the\n"
        "    nine templates ``BOOTSTRAP.md`` section 7.1 names, counted before\n"
        "    anything iterates."
    )
    hit_count = len(count_phrases(planted))
    assert hit_count == 1, "the detector missed the wrapped sentence CS-927 removed"


def test_the_detector_fires_on_a_count_split_from_its_noun() -> None:
    hit_count = len(count_phrases("the nine route templates section 7.1 names"))
    assert hit_count == 1, "the detector missed a count one token short of its noun"


def test_the_detector_does_not_fire_on_a_distributive_phrase() -> None:
    """A rate is not a count. Widening the lookahead past this would break (a)."""
    hit_count = len(count_phrases("ONE ROUTE PER TEMPLATE, AND THE BOUNDARY IS PUBLISHED"))
    assert hit_count == 0, "the detector read a distributive phrase as a count"


def test_the_detector_does_not_fire_on_this_modules_own_counted_noun() -> None:
    hit_count = len(count_phrases("with pairwise distinct templates, in a stable order"))
    assert hit_count == 0, "the detector fired on a noun with no count in front of it"


# ---------------------------------------------------------------------------
# (a). The arm this item exists for.
# ---------------------------------------------------------------------------


def test_pending_does_not_spell_the_aggregate_template_count() -> None:
    phrases = count_phrases(inspect.getsource(pending))
    phrase_count = len(phrases)
    assert phrase_count == 0, (
        f"pending.py spells a template count in {phrase_count} place(s) - {list(phrases)} - "
        "and the owner of that number is health.ENDPOINT_TEMPLATES, not this docstring"
    )


# ---------------------------------------------------------------------------
# (d). The two tables agree.
# ---------------------------------------------------------------------------


def test_the_published_template_tuple_holds_no_duplicate() -> None:
    published_count = len(health.ENDPOINT_TEMPLATES)
    distinct_count = len(frozenset(health.ENDPOINT_TEMPLATES))
    assert published_count == distinct_count, (
        "health.ENDPOINT_TEMPLATES names the same template more than once"
    )


def test_the_aggregate_table_names_exactly_the_published_templates() -> None:
    exposed = frozenset(route.template for route in routes.ROUTES)
    published = frozenset(health.ENDPOINT_TEMPLATES)
    published_count = len(published)
    assert published_count > 0, "the published set is empty; this arm would prove nothing"
    disagreement = sorted(exposed ^ published)
    disagreement_count = len(disagreement)
    assert disagreement_count == 0, (
        f"the route table and health.ENDPOINT_TEMPLATES disagree on {disagreement_count} "
        f"template(s): {disagreement}"
    )


def test_every_pending_template_is_one_the_aggregate_publishes() -> None:
    published = frozenset(health.ENDPOINT_TEMPLATES)
    claimed = frozenset(template for _method, template in pending.UNBACKED)
    claimed_count = len(claimed)
    assert claimed_count > 0, "the pending template set is empty; this arm would prove nothing"
    stray = sorted(claimed - published)
    stray_count = len(stray)
    assert stray_count == 0, (
        f"pending names {stray_count} template(s) section 7.1 does not: {stray}"
    )


# ---------------------------------------------------------------------------
# (e). The collapse pending.py warns about is real, and the shipped table avoids it.
# ---------------------------------------------------------------------------


def test_the_aggregate_does_not_collapse_when_keyed_by_template() -> None:
    table_count = len(routes.ROUTES)
    assert table_count > 0, "the route table is empty; this arm would prove nothing"
    keyed_count = len({route.template: route.method for route in routes.ROUTES})
    assert keyed_count == table_count, (
        "keying the route table by template dropped an entry, so one template is "
        "answered by two routes and which one survives depends on iteration order"
    )


def test_folding_the_method_boundary_routes_back_in_does_collapse() -> None:
    """The control that makes the arm above mean something.

    If no template could ever be claimed twice, "does not collapse" would pass on
    a table where the hazard did not exist, and the separation between
    ``routes.ROUTES`` and ``advice.method_boundary_routes`` would be
    untested rather than upheld.
    """
    boundary_count = len(routes.METHOD_BOUNDARY_ROUTES)
    assert boundary_count > 0, "there is no method-boundary route; the control is vacuous"
    combined = routes.ROUTES + routes.METHOD_BOUNDARY_ROUTES
    combined_count = len(combined)
    keyed_count = len({route.template: route.method for route in combined})
    assert keyed_count < combined_count, (
        "folding the method-boundary routes in did not collapse the mapping, so the "
        "hazard pending.py separates them to avoid is not reproduced by this control"
    )
