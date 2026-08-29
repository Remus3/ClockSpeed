"""CS-601 slice S4 - the five unbacked endpoints, and the honesty partition.

What is covered, and the authority for each arm:

a. AN UNBACKED ENDPOINT ANSWERS HONESTLY RATHER THAN PLAUSIBLY. All five of
   ``/api/advice``, ``/api/advice/<id>/derivation``, ``/api/advice/<id>/state``,
   ``/api/audit`` and ``/api/plan`` return 501 naming ``CS-500``. An endpoint
   answering ``200`` with an empty list instead is indistinguishable from a
   world that genuinely has no advice, which is non-negotiable 7 - "unknown
   content is flagged and skipped, never silently wrong" - violated at the
   surface, where an operator is the one being misled.
b. THE RESOURCE EXISTS AND THE METHOD DOES NOT. ``/api/advice/<id>/state``
   mutates the advice ledger, so it is a POST. A GET on it is 405 and NOT 501:
   405 says "this path is real, that verb is not", and answering 501 there
   would report a written route as unwritten.
c. THE PARTITION IS EXACT, IN BOTH DIRECTIONS. The table below is DATA, keyed by
   route identity, and the sweep asserts every published route falls in exactly
   one class and answers the way its class requires. When a phase 5 endpoint
   becomes real, its 501 arm goes RED and forces the builder to move it across;
   equally, a backed route quietly regressing to a placeholder goes red on the
   other side. That "and vice versa" half is the reason the table is an exact
   partition rather than a list of expected 501s.
d. THE SWEEP IS NOT VACUOUS. The published route count is bound to a scalar and
   asserted BEFORE anything iterates, because a sweep over an empty route table
   passes while proving nothing. And the checker the sweep trusts is itself run
   against a PLANTED handler - a 200 carrying an empty ``cards`` list on a
   pending route, which is exactly the plausible-looking lie arm (a) exists to
   forbid - with the rejection asserted. "Found no problems" and "looks for no
   problems" are otherwise the same output (CONVENTIONS.md section 7.2).
e. THE WRONG-BLOCKER CONTROL WIDENS THE VOCABULARY FOR ITS OWN DURATION, and
   that is the arm rather than a shortcut around one. A valid-BUT-WRONG blocker
   needs a member of ``contract.OPEN_BLOCKERS`` that is not the one the five
   name, and nothing guarantees the shipped vocabulary has a spare - it is a
   closed set that shrinks as phases land. Planting an id from OUTSIDE the
   vocabulary instead would grade a different thing: the envelope rejects that
   payload on its own, so the arm would pass with this module's checker
   contributing nothing at all. See the arm's own docstring.

Test-quality discipline (CONVENTIONS.md section 7.2). Every population size is
bound to a scalar and asserted before it is iterated, and every detector used to
prove an absence is also run against a planted positive.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

import pytest

from clockspeed.surface.api import contract, pending, solve
from tests.solve import synthetic

if TYPE_CHECKING:
    from collections.abc import Mapping

    from clockspeed.data.registry import Registry

# ---------------------------------------------------------------------------
# The registry provider stub
# ---------------------------------------------------------------------------


class _StubRegistryProvider:
    """Hands back one registry, or None to stand for a machine with no install.

    A hand-written stub rather than a mock: the protocol has one method, and a
    mock would agree with whatever this test asserted about it.
    """

    def __init__(self, value: Registry | None) -> None:
        """Record what this provider will hand back.

        Args:
            value: The registry, or None for the no-install case.
        """
        self._value = value

    def registry(self) -> Registry | None:
        """The registry this stub was built with.

        Returns:
            The registry, or None.
        """
        return self._value


# ---------------------------------------------------------------------------
# The partition, declared as DATA
# ---------------------------------------------------------------------------

#: Routes with a written layer beneath them. Pillar 1 and pillar 2 both exist,
#: so these answer 200 when the registry is present and 503 when it is not.
#: Never 501: 501 would report written work as unwritten.
BACKED_ROUTES: Final = frozenset(
    {
        ("POST", "/api/solve"),
        ("POST", "/api/optimize"),
    }
)

#: Routes with NO layer beneath them yet. These answer 501 naming CS-500.
PENDING_ROUTES: Final = frozenset(
    {
        ("GET", "/api/advice"),
        ("GET", "/api/advice/<id>/derivation"),
        ("POST", "/api/advice/<id>/state"),
        ("GET", "/api/audit"),
        ("GET", "/api/plan"),
    }
)

#: The one route that exists only to say a verb is wrong. Its own class, because
#: collapsing it into either of the other two loses exactly the distinction
#: arm (b) is about.
METHOD_BOUNDARY_ROUTES: Final = frozenset({("GET", "/api/advice/<id>/state")})

#: What the two modules publish between them today. Asserted BEFORE the sweep
#: iterates: a sweep over an empty route table is green and proves nothing.
EXPECTED_PUBLISHED_ROUTES: Final = 8

#: Just the pending five, for the arm that grades them alone.
EXPECTED_PENDING_ROUTES: Final = 5

#: GET and POST. The advice-state template is published twice - once to do the
#: work phase 5 will build, once to say the other verb is wrong.
EXPECTED_STATE_ROUTE_METHODS: Final = 2

#: A second member for ``contract.OPEN_BLOCKERS``, patched in for one arm and
#: never shipped. Well formed, so the envelope's form check passes it, and a
#: member for the duration, so its membership check passes it too - which is
#: what makes the refusal built from it CONFORMING, and leaves the wrong-blocker
#: fault as the only one anything can find. Deliberately not an id ``ROADMAP.md``
#: names: this arm is about the honesty checker, not about the roadmap, and
#: borrowing a real item would make the control read as a claim about that item.
SECOND_VALID_BLOCKER: Final = "CS-996"

#: The planted blocker and the one the five actually name are two things.
#: Asserted as a SET SIZE rather than as ``a != b``: mypy's ``strict_equality``
#: resolves a ``Final`` string to its literal type and calls the direct
#: comparison non-overlapping, so the honest arm has to be spelled in a form the
#: type checker cannot decide for it. ``tests/surface/test_contract.py`` records
#: the same workaround for the same reason.
TWO_DISTINCT_BLOCKERS: Final = 2

#: The request parameters each backed route needs to reach its solver. Pending
#: routes take none - they refuse before reading anything, which is the point.
BACKED_PARAMETERS: Final[Mapping[tuple[str, str], Mapping[str, str]]] = {
    ("POST", "/api/solve"): {
        "targets": f"{synthetic.SOLVE_ROD_ITEM}=50",
        "recipes": f"{synthetic.ROD_RECIPE},{synthetic.PLATE_RECIPE}",
        "raw_items": synthetic.SOLVE_ORE_ITEM,
        "byproduct_policy": "sinkable",
    },
    ("POST", "/api/optimize"): {
        "targets": f"{synthetic.SOLVE_TRINKET_ITEM}=30",
        "candidates": f"{synthetic.ALT_GADGET_RECIPE},{synthetic.STD_GADGET_RECIPE}",
        "unlocked": f"{synthetic.ALT_GADGET_RECIPE},{synthetic.STD_GADGET_RECIPE}",
        "raw_items": synthetic.SOLVE_ORE_ITEM,
        "byproduct_policy": "sinkable",
        "objective": "buildings=1",
    },
}

# ---------------------------------------------------------------------------
# The honesty checker the sweep trusts, and the codes it can report
# ---------------------------------------------------------------------------

PROBLEM_NOT_A_REFUSAL: Final = "pending-route-did-not-refuse"
PROBLEM_WRONG_BLOCKER: Final = "pending-route-named-the-wrong-blocking-item"
PROBLEM_CONTRACT: Final = "response-disagrees-with-the-envelope-contract"
PROBLEM_BACKED_REFUSED_AS_UNWRITTEN: Final = "backed-route-reported-itself-unwritten"
PROBLEM_WRONG_METHOD_CODE: Final = "method-boundary-route-did-not-answer-405"


def honesty_problems(
    expected: frozenset[tuple[str, str]], route: contract.Route
) -> tuple[str, ...]:
    """Every way this route's answer disagrees with the class it was put in.

    Named and shared rather than inlined into the sweep, because the sweep alone
    cannot tell "this checker found nothing" from "this checker looks for
    nothing". The planted-handler arm runs this same function and asserts a
    non-empty result.

    Args:
        expected: The class the route was declared in - one of
            :data:`BACKED_ROUTES`, :data:`PENDING_ROUTES` or
            :data:`METHOD_BOUNDARY_ROUTES`.
        route: The route to grade. Its handler is called here.

    Returns:
        The problem codes. Empty when the route answers the way its class
        requires.
    """
    identity = (route.method, route.template)
    response = route.handler(BACKED_PARAMETERS.get(identity, {}))
    found: list[str] = [*contract.contract_problems(response)]
    if found:
        found = [PROBLEM_CONTRACT, *found]

    if expected is PENDING_ROUTES:
        if response.http_status != contract.HTTP_NOT_IMPLEMENTED:
            found.append(PROBLEM_NOT_A_REFUSAL)
        elif response.payload.get("blocked_by") != pending.PENDING_BLOCKER:
            found.append(PROBLEM_WRONG_BLOCKER)
    elif expected is METHOD_BOUNDARY_ROUTES:
        if response.http_status != contract.HTTP_METHOD_NOT_ALLOWED:
            found.append(PROBLEM_WRONG_METHOD_CODE)
    elif response.http_status == contract.HTTP_NOT_IMPLEMENTED:
        found.append(PROBLEM_BACKED_REFUSED_AS_UNWRITTEN)

    return tuple(found)


def pending_route(identity: tuple[str, str]) -> contract.Route:
    """The one pending route with this method and template.

    ``next`` without a default on purpose: a missing route raises here rather
    than skipping the arm, and a skipped arm is a gate that reports green having
    graded nothing.

    Args:
        identity: The method and template pair.

    Returns:
        The route.
    """
    published = (*pending.routes(), *pending.method_boundary_routes())
    return next(route for route in published if (route.method, route.template) == identity)


def published_routes(registry: Registry | None) -> tuple[contract.Route, ...]:
    """Every route the two S4 modules publish, with providers already bound.

    Args:
        registry: What the registry provider hands the backed routes.

    Returns:
        The routes.
    """
    return (
        *solve.routes(_StubRegistryProvider(registry)),
        *pending.routes(),
        *pending.method_boundary_routes(),
    )


# ---------------------------------------------------------------------------
# (a) the five refuse honestly
# ---------------------------------------------------------------------------


def test_the_pending_route_table_is_the_declared_five() -> None:
    routes = pending.routes()
    published = frozenset((route.method, route.template) for route in routes)
    count = len(routes)
    assert count == EXPECTED_PENDING_ROUTES
    assert published == PENDING_ROUTES


def test_the_method_boundary_is_published_through_its_own_accessor() -> None:
    routes = pending.method_boundary_routes()
    published = frozenset((route.method, route.template) for route in routes)
    count = len(routes)
    assert count == len(METHOD_BOUNDARY_ROUTES)
    assert published == METHOD_BOUNDARY_ROUTES


def test_a_template_keyed_mapping_over_the_five_loses_nothing() -> None:
    routes = pending.routes()
    count = len(routes)
    assert count == EXPECTED_PENDING_ROUTES
    keyed = {route.template: route.method for route in routes}
    kept = len(keyed)
    assert kept == count


def test_that_check_would_catch_a_template_published_twice() -> None:
    combined = (*pending.routes(), *pending.method_boundary_routes())
    keyed = {route.template: route.method for route in combined}
    kept = len(keyed)
    total = len(combined)
    assert total > kept


@pytest.mark.parametrize("identity", sorted(PENDING_ROUTES))
def test_a_pending_route_refuses_501_naming_cs_500(identity: tuple[str, str]) -> None:
    route = pending_route(identity)
    response = route.handler({})
    status = response.http_status
    blocker = response.payload.get("blocked_by")
    reason = response.payload.get("reason")
    assert status == contract.HTTP_NOT_IMPLEMENTED
    assert blocker == "CS-500"
    assert reason == contract.REASON_NOT_IMPLEMENTED


@pytest.mark.parametrize("identity", sorted(PENDING_ROUTES))
def test_a_pending_route_conforms_to_the_envelope(identity: tuple[str, str]) -> None:
    problems = contract.contract_problems(pending_route(identity).handler({}))
    count = len(problems)
    assert count == 0


@pytest.mark.parametrize("identity", sorted(PENDING_ROUTES))
def test_a_pending_route_never_answers_with_an_empty_collection(identity: tuple[str, str]) -> None:
    route = pending_route(identity)
    response = route.handler({})
    keys = frozenset(response.payload)
    assert keys == contract.PAYLOAD_KEYS_REFUSAL
    assert "data" not in keys


def test_the_blocker_the_five_name_is_one_the_envelope_still_has_open() -> None:
    assert pending.PENDING_BLOCKER in contract.OPEN_BLOCKERS


# ---------------------------------------------------------------------------
# (b) the method boundary
# ---------------------------------------------------------------------------


def test_advice_state_is_a_post_because_it_mutates_the_ledger() -> None:
    published = (*pending.routes(), *pending.method_boundary_routes())
    state = [route for route in published if route.template == "/api/advice/<id>/state"]
    methods = sorted(route.method for route in state)
    count = len(state)
    assert count == EXPECTED_STATE_ROUTE_METHODS
    assert methods == ["GET", "POST"]


def test_get_on_advice_state_is_405_and_not_501() -> None:
    route = pending_route(("GET", "/api/advice/<id>/state"))
    response = route.handler({})
    status = response.http_status
    reason = response.payload.get("reason")
    blocker = response.payload.get("blocked_by")
    assert status == contract.HTTP_METHOD_NOT_ALLOWED
    assert status != contract.HTTP_NOT_IMPLEMENTED
    assert reason == contract.REASON_METHOD_NOT_ALLOWED
    assert blocker is None


def test_post_on_advice_state_is_501_and_not_405() -> None:
    route = pending_route(("POST", "/api/advice/<id>/state"))
    response = route.handler({})
    status = response.http_status
    assert status == contract.HTTP_NOT_IMPLEMENTED


# ---------------------------------------------------------------------------
# (c) and (d) the exact partition, and the controls that stop it being vacuous
# ---------------------------------------------------------------------------


def test_the_three_declared_classes_are_disjoint() -> None:
    overlap = (
        (BACKED_ROUTES & PENDING_ROUTES)
        | (BACKED_ROUTES & METHOD_BOUNDARY_ROUTES)
        | (PENDING_ROUTES & METHOD_BOUNDARY_ROUTES)
    )
    count = len(overlap)
    assert count == 0


def test_the_published_route_set_is_exactly_the_declared_partition() -> None:
    routes = published_routes(synthetic.solve_registry())
    count = len(routes)
    assert count == EXPECTED_PUBLISHED_ROUTES
    published = frozenset((route.method, route.template) for route in routes)
    assert published == BACKED_ROUTES | PENDING_ROUTES | METHOD_BOUNDARY_ROUTES


@pytest.mark.parametrize("with_registry", [True, False])
def test_every_published_route_answers_the_way_its_class_requires(with_registry: bool) -> None:
    routes = published_routes(synthetic.solve_registry() if with_registry else None)
    count = len(routes)
    assert count == EXPECTED_PUBLISHED_ROUTES

    classes = (BACKED_ROUTES, PENDING_ROUTES, METHOD_BOUNDARY_ROUTES)
    graded = 0
    failures: list[str] = []
    for route in routes:
        identity = (route.method, route.template)
        declared = [group for group in classes if identity in group]
        if len(declared) != 1:
            failures.append(PROBLEM_CONTRACT)
            continue
        graded += 1
        failures.extend(honesty_problems(declared[0], route))

    failure_count = len(failures)
    assert graded == EXPECTED_PUBLISHED_ROUTES
    assert failure_count == 0


@pytest.mark.parametrize("with_registry", [True, False])
def test_a_backed_route_answers_200_or_503_and_never_501(with_registry: bool) -> None:
    routes = [
        route
        for route in published_routes(synthetic.solve_registry() if with_registry else None)
        if (route.method, route.template) in BACKED_ROUTES
    ]
    count = len(routes)
    assert count == len(BACKED_ROUTES)

    expected = contract.HTTP_OK if with_registry else contract.HTTP_UNAVAILABLE
    observed = sorted(
        route.handler(BACKED_PARAMETERS[route.method, route.template]).http_status
        for route in routes
    )
    assert observed == [expected] * count


def test_the_honesty_checker_rejects_a_plausible_lie_on_a_pending_route() -> None:
    planted = contract.Route(
        method="GET",
        template="/api/advice",
        handler=lambda _params: contract.ok("/api/advice", {"cards": []}),
    )
    problems = honesty_problems(PENDING_ROUTES, planted)
    count = len(problems)
    assert count > 0
    assert PROBLEM_NOT_A_REFUSAL in problems


def test_the_honesty_checker_rejects_a_pending_route_naming_the_wrong_blocker(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A refusal the ENVELOPE accepts, naming an open item that is the wrong one.

    THE DISCRIMINATION IS VALID-BUT-WRONG, NOT UNKNOWN. Those are two faults and
    two different checkers own them. ``contract.contract_problems`` owns "this
    ``blocked_by`` names nothing the surface has open" and is graded on it in
    ``tests/surface/test_contract.py``. This module owns "this pending route
    named an open item that is not the one blocking it", and the only way to put
    that fault in front of it alone is to hand it a refusal the envelope is
    entirely happy with. Widening the vocabulary for the duration of this arm is
    what buys that, and it makes the arm independent of what the shipped set
    holds: ``contract.not_implemented`` RAISES on any spelling the vocabulary
    does not carry, so an arm that borrowed a real spare member would break the
    day that member's item closed - which is exactly how this arm broke once
    already. A hand-built payload avoids the raise and loses the point instead,
    carrying an envelope fault that passes the assertion below without the
    honesty checker contributing anything.

    THE ASSERTION IS AN EQUALITY OVER THE WHOLE TUPLE for that reason. A
    membership test would also pass on a checker that reports every code it
    knows; the equality says the checker found this fault and no other.
    """
    monkeypatch.setattr(contract, "OPEN_BLOCKERS", contract.OPEN_BLOCKERS | {SECOND_VALID_BLOCKER})
    widened = SECOND_VALID_BLOCKER in contract.OPEN_BLOCKERS
    distinct = len({SECOND_VALID_BLOCKER, pending.PENDING_BLOCKER})
    assert widened, "the vocabulary was not widened, so the refusal below cannot be built"
    assert distinct == TWO_DISTINCT_BLOCKERS, "the planted blocker IS the one the five name"

    planted = contract.Route(
        method="GET",
        template="/api/advice",
        handler=lambda _params: contract.not_implemented("/api/advice", SECOND_VALID_BLOCKER),
    )
    problems = honesty_problems(PENDING_ROUTES, planted)
    count = len(problems)

    assert count > 0
    assert problems == (PROBLEM_WRONG_BLOCKER,), (
        "a conforming 501 that names the wrong open item was graded as something "
        "other than the wrong-blocker fault, or as no fault at all"
    )


def test_the_honesty_checker_rejects_a_backed_route_reporting_itself_unwritten() -> None:
    planted = contract.Route(
        method="POST",
        template="/api/solve",
        handler=lambda _params: contract.not_implemented("/api/solve", "CS-500"),
    )
    problems = honesty_problems(BACKED_ROUTES, planted)
    count = len(problems)
    assert count > 0
    assert PROBLEM_BACKED_REFUSED_AS_UNWRITTEN in problems


def test_the_honesty_checker_rejects_a_method_boundary_route_answering_501() -> None:
    planted = contract.Route(
        method="GET",
        template="/api/advice/<id>/state",
        handler=lambda _params: contract.not_implemented("/api/advice/<id>/state", "CS-500"),
    )
    problems = honesty_problems(METHOD_BOUNDARY_ROUTES, planted)
    count = len(problems)
    assert count > 0
    assert PROBLEM_WRONG_METHOD_CODE in problems


def test_the_honesty_checker_accepts_the_real_pending_routes() -> None:
    routes = [
        route for route in pending.routes() if (route.method, route.template) in PENDING_ROUTES
    ]
    count = len(routes)
    assert count == EXPECTED_PENDING_ROUTES
    failures = [problem for route in routes for problem in honesty_problems(PENDING_ROUTES, route)]
    failure_count = len(failures)
    assert failure_count == 0
