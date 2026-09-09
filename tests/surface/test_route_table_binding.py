"""The page's route table is bound to the endpoint module's published list.

``clockspeed/surface/api/health.py`` owns ``ENDPOINT_TEMPLATES``, the published
list of route templates, and ``clockspeed/surface/web/app.js`` carries a
``ROUTES`` array that names the same templates a second time so the page can
render a row per route. Two copies of one fact drift, and CLAUDE.md section 4
is explicit that the second copy is the one that goes stale.

WHAT WAS ALREADY BOUND, AND WHAT WAS NOT. ``tests/surface/test_web_assets.py``
already grades two halves of this seam: every published template appears
somewhere in the script's code, and every template the page names carries the
verb its owning module registers. Both are membership-or-better in ONE
direction. Neither notices a row the page carries that nothing publishes,
neither notices the same template written twice, and neither notices the table
reordered - the page's own header comment promises BOOTSTRAP.md section 7.1
order, and no arm held it to that. This module closes the remaining direction
by grading the parsed sequence against the published sequence exactly.

THE ARM THAT GRADES THE ARM. A binding written today is green today, because
the two lists currently agree, and a test that has never been red is a test
about nothing. So :func:`route_binding_faults` is a pure comparator taking both
sequences as arguments, and the second arm feeds it planted pairs in both
directions - agreeing pairs it must accept, divergent pairs it must reject, one
per fault class. The live binding is then one call to a comparator that has
been shown to fire.

The script is read as TEXT and parsed. No JavaScript is executed, and neither
arm needs a game install, a save file or a listening socket.
"""

from __future__ import annotations

import re
from collections import Counter
from typing import TYPE_CHECKING, Final

from clockspeed.surface import config
from clockspeed.surface.api import health

if TYPE_CHECKING:
    from collections.abc import Sequence

#: The script carrying the page's row table.
SCRIPT: Final = "app.js"

#: A JavaScript block comment. Stripped before parsing, because ``app.js``
#: opens with a comment that names the ten routes in section order - parsing
#: prose would let a row deleted from the table still be found in the sentence
#: describing it.
_BLOCK_COMMENT: Final = re.compile(r"/\*[\s\S]*?\*/")

#: The row table's own declaration, from ``var ROUTES = [`` to its closing
#: bracket. Anchored on the array rather than on the file, so a template quoted
#: anywhere else in the script cannot stand in for a row of the table.
_ROUTES_ARRAY: Final = re.compile(r"\bvar\s+ROUTES\s*=\s*\[(?P<body>[^\]]*)\]\s*;")

#: One row's ``template`` field.
_TEMPLATE_FIELD: Final = re.compile(r'\btemplate\s*:\s*"(?P<template>[^"]*)"')


def read_script() -> str:
    """The page script, decoded strictly as ASCII.

    Returns:
        The full text of ``app.js``. Decoding as ASCII rather than as UTF-8 is
        deliberate - a byte above 0x7E raises here rather than becoming a
        character a later comparison has to notice.
    """
    return (config.default_web_dir() / SCRIPT).read_bytes().decode("ascii")


def page_route_templates(script_text: str) -> tuple[str, ...]:
    """The templates the page's row table names, in the order it names them.

    Args:
        script_text: The full text of ``app.js``.

    Returns:
        One entry per row of ``ROUTES``, in source order. Duplicates are kept,
        because a table naming one template twice is a fault this module means
        to report rather than quietly collapse.

    Raises:
        AssertionError: If the script carries no ``ROUTES`` array at all. That
            is a parser failure, not a binding verdict, and reporting it as
            "no templates found" would read as a page missing every route.
    """
    code = _BLOCK_COMMENT.sub(" ", script_text)
    array = _ROUTES_ARRAY.search(code)
    assert array is not None, (
        f"no ROUTES array found in {SCRIPT}; the parser, not the page, is what failed"
    )
    return tuple(match.group("template") for match in _TEMPLATE_FIELD.finditer(array.group("body")))


def route_binding_faults(page: Sequence[str], published: Sequence[str]) -> tuple[str, ...]:
    """Every way the page's row table disagrees with the published list.

    Args:
        page: The templates the page names, in page order.
        published: The templates the endpoint module publishes, in its order.

    Returns:
        One string per fault, sorted within each class and ordered missing,
        surplus, duplicated, then order. Empty means the two agree exactly -
        same members, same multiplicity, same sequence.
    """
    seen = Counter(page)
    expected = Counter(published)

    faults = [
        f"missing: {template} is published but the page's table does not name it"
        for template in sorted(expected - seen)
    ]
    faults += [
        f"surplus: {template} is in the page's table but nothing publishes it"
        for template in sorted(Counter(seen.keys()) - Counter(expected.keys()))
    ]
    faults += [
        f"duplicated: the page's table names {template} {count} times"
        for template, count in sorted(seen.items())
        if count > 1
    ]

    #: ORDER IS GRADED ONLY ONCE MEMBERSHIP AGREES. A page missing a row is
    #: trivially in a different sequence too, and reporting that as a second,
    #: separate fault would bury the one thing a reader has to fix.
    if seen == expected and tuple(page) != tuple(published):
        faults.append(
            f"order: the page's table reads {tuple(page)} "
            f"but the published order is {tuple(published)}"
        )

    return tuple(faults)


# ---------------------------------------------------------------------------
# The live binding
# ---------------------------------------------------------------------------


def test_the_page_route_list_matches_the_health_template_list() -> None:
    """``app.js``'s ``ROUTES`` names exactly the published templates, in order.

    The published sequence is imported from ``health`` rather than restated
    here. A test that hardcoded a third copy of the list would make the drift
    it grades strictly worse - two copies can disagree, three can disagree in
    three ways, and the copy inside the test is the one nobody reads.
    """
    published = health.ENDPOINT_TEMPLATES
    assert published, "health publishes no route templates at all"

    page = page_route_templates(read_script())
    faults = route_binding_faults(page, published)
    total = len(faults)
    assert total == 0, f"{total} route-table binding fault(s): {faults}"


# ---------------------------------------------------------------------------
# The arm that grades the comparator
# ---------------------------------------------------------------------------

#: A stand-in published list. Deliberately NOT the real one: the comparator is
#: a pure function over two sequences, and grading it on synthetic values keeps
#: this arm red-able on a day the real lists happen to agree.
_PUBLISHED: Final = ("/api/alpha", "/api/beta", "/api/gamma")


def test_the_binding_detector_fires_on_a_planted_divergence() -> None:
    """The comparator accepts an agreeing pair and rejects every planted one.

    Both directions, because a comparator that always fires and a comparator
    that never fires are each green against a single-direction arm. The planted
    divergences cover one fault class each - a template the page dropped, one
    it invented, one it wrote twice, and the same members in the wrong order.
    Order is a fault class in its own right: the page renders these as rows in
    sequence, and BOOTSTRAP.md section 7.1 order is what its header promises.
    """
    agreeing = route_binding_faults(_PUBLISHED, _PUBLISHED)
    assert agreeing == (), f"the comparator rejected an identical pair: {agreeing}"

    also_agreeing = route_binding_faults(list(_PUBLISHED), _PUBLISHED)
    assert also_agreeing == (), f"the comparator is sensitive to sequence type: {also_agreeing}"

    #: Fault class -> the page the plant produces, and the word the report for
    #: it must carry. The word is graded too: a comparator that answered every
    #: divergence with one undifferentiated "they differ" would satisfy the
    #: fires-at-all check while telling a reader nothing about what moved.
    planted: Final = {
        "missing": (("/api/alpha", "/api/beta"), "/api/gamma"),
        "surplus": (("/api/alpha", "/api/beta", "/api/gamma", "/api/delta"), "/api/delta"),
        "duplicated": (("/api/alpha", "/api/beta", "/api/beta", "/api/gamma"), "/api/beta"),
        "order": (("/api/beta", "/api/alpha", "/api/gamma"), "order"),
    }

    reported = {
        name: route_binding_faults(page, _PUBLISHED) for name, (page, _word) in planted.items()
    }

    silent = tuple(name for name, faults in sorted(reported.items()) if not faults)
    total = len(silent)
    assert total == 0, f"{total} planted divergence(s) the comparator did not report: {silent}"

    unnamed = tuple(
        f"{name}: {reported[name]}"
        for name, (_page, word) in sorted(planted.items())
        if not any(name in fault and word in fault for fault in reported[name])
    )
    total = len(unnamed)
    assert total == 0, f"{total} divergence(s) reported without naming the fault: {unnamed}"
