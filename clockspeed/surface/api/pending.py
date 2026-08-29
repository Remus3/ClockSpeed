"""The five endpoints whose computing layer does not exist yet, answering so.

Owns (BOOTSTRAP.md section 7.1): the wire behaviour of ``/api/advice``,
``/api/advice/<id>/derivation``, ``/api/advice/<id>/state``, ``/api/audit`` and
``/api/plan`` until phase 5 builds what sits beneath them.

THESE ANSWER HONESTLY RATHER THAN PLAUSIBLY, WHICH IS THE WHOLE MODULE. There is
no advisor, no whole-world audit and no progression router yet. An endpoint that
returned ``200`` with ``{"cards": []}`` would be indistinguishable - to a
dashboard, to a client, to an operator reading a log - from a world that
genuinely has no advice to give, and that is non-negotiable 7 at the surface:
"unknown content is flagged and skipped, never fatal, NEVER SILENTLY WRONG". An
empty success body is the silently-wrong branch of that sentence wearing a green
status code. So each of the five returns 501 and NAMES the item that would build
it, which is a machine-readable statement a client can branch on and an operator
can act on.

AND THE REFUSAL CANNOT OUTLIVE ITS REASON. :data:`PENDING_BLOCKER` is validated
by ``contract.not_implemented`` against the closed set of items this surface
still has open, and ``tests/surface/test_contract.py`` pins that set to the OPEN
item lines of ``ROADMAP.md``. When phase 5 lands and CS-500 leaves the roadmap,
that arm goes red - so these placeholders have to be revisited rather than
quietly outliving the work they point at. The partition arm in
``tests/surface/test_pending.py`` closes the other direction: a route here that
becomes real must MOVE, because its 501 is asserted rather than merely
tolerated.

WHY THE ADVICE-STATE ROUTE IS A POST, AND WHY A GET ON IT IS 405 RATHER THAN 501.
``/api/advice/<id>/state`` is where a card is accepted, dismissed, snoozed or
pinned, so it MUTATES the per-world advice ledger - a POST, not a GET. The
distinction the 405 protects is real and is not pedantry: 501 says "the layer
beneath this does not exist yet" and 405 says "this path is real, that verb is
not". Answering 501 to a GET would report a route this repository has written as
unwritten, which is the same misinformation as the empty success body, pointed
the other way. The two are published as separate routes so the boundary is
answerable without a running listener and gradeable without one.

THIS MODULE READS NOTHING AND COMPUTES NOTHING, and it needs no provider to say
so. A refusal that had to consult a world before it could refuse would fail on a
machine with no save, and would turn "phase 5 is unwritten" into "there is no
save here" - the 501-versus-503 collapse the envelope exists to prevent.
"""

# SEAM DISCIPLINE (BOOTSTRAP.md section 6).
# Each layer consumes only the layer below it through a stated model.
# solve/ never reads a save. advisor/ never reads the raw docs file.
# surface/ never computes. A layer that reaches past its neighbor is a
# design bug.
#
# There is deliberately nothing below this module to consume. It imports the
# response envelope and the standard library, and that is the complete list -
# an import of clockspeed.advisor here would be an import of a package phase 5
# has not written, and a stub of one would be the plausible answer this module
# exists to refuse to give.

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from clockspeed.surface.api import contract

if TYPE_CHECKING:
    from collections.abc import Mapping

__all__ = [
    "ADVICE_ENDPOINT",
    "ADVICE_STATE_ENDPOINT",
    "AUDIT_ENDPOINT",
    "DERIVATION_ENDPOINT",
    "METHOD_BOUNDARY",
    "METHOD_GET",
    "METHOD_POST",
    "PENDING_BLOCKER",
    "PLAN_ENDPOINT",
    "UNBACKED",
    "method_boundary_routes",
    "method_refusal_handler",
    "not_implemented_handler",
    "routes",
]


# ---------------------------------------------------------------------------
# The route templates
# ---------------------------------------------------------------------------

#: Pillar 5. The ranked advice cards for the current world.
ADVICE_ENDPOINT: Final = "/api/advice"

#: Pillar 5, explain tier 3. Generated from the rule trace, never hand-written
#: (non-negotiable 8) - which is one more reason there is nothing to stub here.
DERIVATION_ENDPOINT: Final = "/api/advice/<id>/derivation"

#: Pillar 5, persistence. Accept, dismiss, snooze or pin one card. MUTATING,
#: hence POST.
ADVICE_STATE_ENDPOINT: Final = "/api/advice/<id>/state"

#: Pillar 3. The whole-world audit against what is actually built.
AUDIT_ENDPOINT: Final = "/api/audit"

#: Pillar 4. Milestone and progression routing against any target.
PLAN_ENDPOINT: Final = "/api/plan"

METHOD_GET: Final = "GET"
METHOD_POST: Final = "POST"

#: The open item that would build every one of these. A single value rather than
#: one per endpoint, because a single phase gate is what actually blocks them:
#: naming a different item on each would imply five independent unlocks and
#: would be four claims this repository cannot support.
PENDING_BLOCKER: Final = "CS-500"

#: Every method-and-template pair with no layer beneath it. The order is the
#: order routes are published in, and it is stable so two runs agree.
UNBACKED: Final[tuple[tuple[str, str], ...]] = (
    (METHOD_GET, ADVICE_ENDPOINT),
    (METHOD_GET, DERIVATION_ENDPOINT),
    (METHOD_POST, ADVICE_STATE_ENDPOINT),
    (METHOD_GET, AUDIT_ENDPOINT),
    (METHOD_GET, PLAN_ENDPOINT),
)

#: Method-and-template pairs that exist ONLY to say the verb is wrong. Published
#: as routes rather than left to a router's fallback so the 405-versus-501
#: boundary is answerable and gradeable without standing up a listener, and so
#: the answer comes from the same constructor either way.
METHOD_BOUNDARY: Final[tuple[tuple[str, str], ...]] = ((METHOD_GET, ADVICE_STATE_ENDPOINT),)


# ---------------------------------------------------------------------------
# The handlers
# ---------------------------------------------------------------------------


def not_implemented_handler(endpoint: str) -> contract.Handler:
    """A handler that refuses, names the blocking item, and reads nothing.

    A FACTORY RATHER THAN A LOOP BODY. Building these inside the comprehension
    in :func:`routes` would capture the loop variable by reference, so all five
    handlers would close over whichever template the loop finished on and every
    refusal would name the same endpoint. Binding through a parameter is what
    makes each closure hold its own value.

    Args:
        endpoint: The route template this handler answers for.

    Returns:
        The handler. It ignores its parameters: there is no request shape that
        would make an unwritten layer answerable, so reading one would only
        create a second way to fail and a place for a caller value to land.
    """

    def handler(_parameters: Mapping[str, str]) -> contract.Response:
        return contract.not_implemented(endpoint, PENDING_BLOCKER)

    return handler


def method_refusal_handler(endpoint: str) -> contract.Handler:
    """A handler that says the path is real and the verb is not.

    Args:
        endpoint: The route template that matched.

    Returns:
        The handler, answering 405. Deliberately NOT 501: the resource exists,
        and only the method is wrong.
    """

    def handler(_parameters: Mapping[str, str]) -> contract.Response:
        return contract.method_not_allowed(endpoint)

    return handler


def routes() -> tuple[contract.Route, ...]:
    """The five unbacked endpoints, one route each, ready to be registered.

    Takes no provider, and that is the point rather than an omission - see the
    module docstring. A refusal that consulted a world first would fail
    differently on a machine with no save.

    ONE ROUTE PER TEMPLATE, AND THE METHOD-BOUNDARY ROUTE IS PUBLISHED
    SEPARATELY. That separation is a seam requirement rather than taste. The
    aggregate route table this project assembles is keyed BY TEMPLATE where it
    is read - ``{route.template: route.method for route in ROUTES}`` in
    ``tests/surface/test_acceptance.py`` - and is asserted to hold exactly the
    nine templates ``BOOTSTRAP.md`` section 7.1 names, counted before anything
    iterates. A second entry under ``/api/advice/<id>/state`` would be silently
    dropped by that mapping, and which of the two survived would depend on
    iteration order: the aggregate would still hold nine templates while
    answering one of them with the wrong verb. Publishing the two sets through
    two accessors makes the assembler state which it wants instead of guessing.

    Returns:
        The five routes, in a stable order, with pairwise distinct templates.
    """
    return tuple(
        contract.Route(method=method, template=template, handler=not_implemented_handler(template))
        for method, template in UNBACKED
    )


def method_boundary_routes() -> tuple[contract.Route, ...]:
    """The routes that exist only to answer 405 rather than 404.

    Published apart from :func:`routes` - see there for why. A server whose
    router synthesises a 405 from a template match needs neither of these; one
    that registers method-and-template pairs verbatim needs both, and gets the
    same answer either way because both go through
    ``contract.method_not_allowed``.

    Returns:
        The method-boundary routes, in a stable order. Every template here also
        appears in :func:`routes` under a different method, which is what makes
        405 rather than 404 the honest answer.
    """
    return tuple(
        contract.Route(method=method, template=template, handler=method_refusal_handler(template))
        for method, template in METHOD_BOUNDARY
    )
