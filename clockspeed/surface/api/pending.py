"""The endpoints whose published body does not exist yet, answering so.

Owns (BOOTSTRAP.md section 7.1): the wire behaviour of ``/api/advice/<id>/state``,
``/api/audit`` and ``/api/plan`` until the items named in :data:`BLOCKERS` build
what answers them. ``/api/advice`` and ``/api/advice/<id>/derivation`` left this
module when CS-1270 gave the advisor a function building its inputs from a
world; ``clockspeed/surface/api/advice.py`` answers both.

THESE ANSWER HONESTLY RATHER THAN PLAUSIBLY, WHICH IS THE WHOLE MODULE. The
state route has no defended write path (CS-1269), and the audit and plan bodies
are unpublished (CS-1046). An endpoint that
returned ``200`` with ``{"cards": []}`` would be indistinguishable - to a
dashboard, to a client, to an operator reading a log - from a world that
genuinely has no advice to give, and that is non-negotiable 7 at the surface:
"unknown content is flagged and skipped, never fatal, NEVER SILENTLY WRONG". An
empty success body is the silently-wrong branch of that sentence wearing a green
status code. So each returns 501 and NAMES the item that would build it, which
is a machine-readable statement a client can branch on and an operator can act
on.

AND THE REFUSAL CANNOT OUTLIVE ITS REASON. Every value in :data:`BLOCKERS` is
validated by ``contract.not_implemented`` against the closed set of items this
surface still has open, and ``tests/surface/test_contract.py`` pins that set to
the OPEN item lines of ``ROADMAP.md``. When a named item leaves the roadmap that
arm goes red - so these placeholders have to be revisited rather than quietly
outliving the work they point at, which is exactly how CS-500 closing forced
every blame here to be re-pointed. The partition arm in
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
machine with no save, and would turn "this layer is unwritten" into "there is no
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
# a stub of a layer here would be the plausible answer this module exists to
# refuse to give.

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING, Final

from clockspeed.surface.api import contract

if TYPE_CHECKING:
    from collections.abc import Mapping

__all__ = [
    "ADVICE_STATE_ENDPOINT",
    "AUDIT_ENDPOINT",
    "BLOCKERS",
    "METHOD_BOUNDARY",
    "METHOD_GET",
    "METHOD_POST",
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

#: Pillar 5, persistence. Accept, dismiss, snooze or pin one card. MUTATING,
#: hence POST.
ADVICE_STATE_ENDPOINT: Final = "/api/advice/<id>/state"

#: Pillar 3. The whole-world audit against what is actually built.
AUDIT_ENDPOINT: Final = "/api/audit"

#: Pillar 4. Milestone and progression routing against any target.
PLAN_ENDPOINT: Final = "/api/plan"

METHOD_GET: Final = "GET"
METHOD_POST: Final = "POST"

#: The open item each unbacked template names. A BLAME PER TEMPLATE since CS-500
#: closed: the single phase gate that blocked all of them is gone, and what is
#: left is blocked by different items. The advice reads left this table when
#: CS-1270 closed. The state route waits on CS-1269, which records a card state
#: behind a cross-origin refusal - a mutating route on a listener with no such
#: refusal is a write any page in a browser could make. ``/api/audit`` and ``/api/plan`` wait on
#: CS-1046, which publishes their bodies. A ``MappingProxyType`` so nothing
#: holding it can rewrite a blame.
BLOCKERS: Final[Mapping[str, str]] = MappingProxyType(
    {
        ADVICE_STATE_ENDPOINT: "CS-1269",
        AUDIT_ENDPOINT: "CS-1046",
        PLAN_ENDPOINT: "CS-1046",
    }
)

#: Every method-and-template pair with no layer beneath it. The order is the
#: order routes are published in, and it is stable so two runs agree.
UNBACKED: Final[tuple[tuple[str, str], ...]] = (
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
    in :func:`routes` would capture the loop variable by reference, so every
    handler would close over whichever template the loop finished on and every
    refusal would name the same endpoint. Binding through a parameter is what
    makes each closure hold its own value.

    Args:
        endpoint: The route template this handler answers for.

    Returns:
        The handler. It ignores its parameters: there is no request shape that
        would make an unwritten layer answerable, so reading one would only
        create a second way to fail and a place for a caller value to land.
    """
    blocker = BLOCKERS[endpoint]

    def handler(_parameters: Mapping[str, str]) -> contract.Response:
        return contract.not_implemented(endpoint, blocker)

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
    """The unbacked endpoints, one route each, ready to be registered.

    Takes no provider, and that is the point rather than an omission - see the
    module docstring. A refusal that consulted a world first would fail
    differently on a machine with no save.

    ONE ROUTE PER TEMPLATE, AND THE METHOD-BOUNDARY ROUTE IS PUBLISHED
    SEPARATELY. That separation is a seam requirement rather than taste. The
    aggregate route table this project assembles is keyed BY TEMPLATE where it
    is read - ``{route.template: route.method for route in ROUTES}`` in
    ``tests/surface/test_acceptance.py`` - and is asserted to hold exactly the
    templates ``BOOTSTRAP.md`` section 7.1 names, counted before anything
    iterates. A second entry under ``/api/advice/<id>/state`` would be silently
    dropped by that mapping, and which of the two survived would depend on
    iteration order: the aggregate would still hold one entry per published
    template while answering one of them with the wrong verb. Publishing the two
    sets through two accessors makes the assembler state which it wants instead
    of guessing.

    HOW MANY TEMPLATES THAT IS, THIS MODULE DOES NOT SAY (CS-927). The sentence
    above spelled the number until CS-912 published ``/api/registry`` and moved
    it, and because a docstring is not executed nothing went red: the prose and
    the table drifted apart in silence for a phase, each still internally
    consistent. ``health.ENDPOINT_TEMPLATES`` is the one owner of that number -
    ``clockspeed/surface/api/routes.py`` refuses to restate it for the same
    reason - so naming the SET here rather than its SIZE is what keeps this
    paragraph true the next time a route lands.
    ``tests/surface/test_pending_route_count.py`` reddens if a count word
    reappears in front of "templates" anywhere in this module.

    Returns:
        The routes, in a stable order, with pairwise distinct templates.
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
