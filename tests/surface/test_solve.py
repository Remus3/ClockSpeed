"""CS-601 slice S4 - /api/solve and /api/optimize over the real solver.

What is covered, and the authority for each arm:

a. THE FIXTURE IS A REAL PRODUCER'S OUTPUT, NEVER A HAND-BUILT LITERAL. Every
   plan and every result graded below comes out of the real
   ``ratio.solve_for_targets`` or ``optimize.optimize_plan`` over the real
   ``tests/solve/synthetic.py`` corpus. A hand-assembled ``ProductionPlan``
   agrees with whatever this module believes the shape is, by construction, and
   would stay green through the exact serializer defect it is meant to catch -
   CONVENTIONS.md section 7.2's "a fixture built parallel to the implementation
   stays green through the real defect", which ``tests/solve/synthetic.py``
   states again in its own docstring.
b. THE EXACT-RATIONAL SPELLING SURVIVES TO THE WIRE. C1's answer is 10/3
   machines, which no float represents - it renders as 3.3333333333333335, a
   perfectly plausible number. Every rate leaves as ``{"num": n, "den": d}``,
   and the arm that proves it reads the RAW ENCODED BYTES rather than the
   Python objects, because the object graph is not what a browser parses. A
   bare JSON number there is read as an IEEE double, which is exactly the float
   non-negotiable 6 keeps out of the answer path.
c. A SOLVER REFUSAL IS ROUTED BY TYPE NAME AND ITS MESSAGE NEVER LEAVES.
   The population is derived from ``__all__`` plus a ``BaseException`` check
   rather than from a name suffix, because five of the twelve carry no
   ``Error`` suffix and a suffix rule would grade seven and call itself
   exhaustive.
   ``UnsolvableChain`` and ``PowerNotComparableError`` both interpolate a
   game-content key into their message, so matching on message text would mean
   holding that text at the surface, and echoing it would publish registry
   content in a response body. Each of the twelve exported solver exceptions is
   raised through both doors and graded on the status, the reason AND the
   absence of its message from the encoded bytes.
d. 503 AND 501 DO NOT COLLAPSE. ``build_registry`` needs a document read from
   the game install, so on a machine with no game there is no registry - a
   working layer with an absent input, which is 503. Answering 501 there would
   report pillar 1 as unwritten when it is written and merely un-fed.
e. THE SURFACE DECIDES NOTHING THE SOLVER COULD DECIDE. An unknown backend
   name, an objective naming no direction and an unsolvable chain are all the
   solver's verdicts, reached by calling it and transcribing what came back.

Test-quality discipline (CONVENTIONS.md section 7.2). Every population size is
bound to a scalar and asserted before it is iterated. Every detector used to
prove an absence - the raw-byte float scan, the bare-number walker - is also run
against a planted POSITIVE and against a control that would false-positive a
naive implementation, so "found nothing" is distinguishable from "looks for
nothing".
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from fractions import Fraction
from typing import TYPE_CHECKING, Final

import pytest

from clockspeed.solve import optimize, ratio
from clockspeed.surface.api import contract, solve
from tests.solve import synthetic

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping
    from types import ModuleType

    from clockspeed.data.registry import Registry

# ---------------------------------------------------------------------------
# Populations, each with the count its sweep asserts before iterating
# ---------------------------------------------------------------------------

#: Every exception class the two solver modules EXPORT, derived the way
#: ``tests/surface/test_contract.py`` derives it: a name in ``__all__`` that
#: resolves to a ``BaseException`` subclass. NOT a name suffix - see the two
#: counts below.
SOLVER_MODULES: Final = (ratio, optimize)

#: What that derivation finds today. Asserted, not assumed.
EXPECTED_SOLVER_EXCEPTIONS: Final = 12

#: MEASURED on this tree, and the reason the derivation is not a name suffix.
#: Five of the twelve carry no ``Error`` suffix at all -
#: ``UnsolvableChain``, ``UnderdeterminedChain``, ``InfeasibleChain``,
#: ``ByproductPolicyRequired`` and ``UnboundedSupply`` - and
#: ``clockspeed/solve/ratio.py:188`` records a coded N818 suppression saying
#: that is deliberate. A ``endswith("Error")`` rule would grade seven of twelve
#: and report itself exhaustive. Both halves are asserted, and their sum is
#: asserted against the whole, so neither can drift alone.
EXPECTED_SUFFIXED_EXCEPTIONS: Final = 7
EXPECTED_UNSUFFIXED_EXCEPTIONS: Final = 5

#: The two doors this slice publishes.
EXPECTED_DOORS: Final = 2

#: A string that appears in every planted exception message and NOWHERE in any
#: legitimate response. Shaped like a game-content key on purpose: that is the
#: class of value the real messages interpolate, and the class of value a
#: response body must never carry.
MESSAGE_SENTINEL: Final = "Desc_S4MessageSentinel_C"

#: The keys ``contract.rational`` spells an exact ratio with.
RATIONAL_KEYS: Final = frozenset({"num", "den"})

#: A JSON string literal, so the number scanner can blank strings out before it
#: looks for a decimal point. Without this the scanner reports every digit
#: inside a recipe key, and a scanner that cannot be trusted is one whose silence
#: means nothing.
JSON_STRING: Final = re.compile(rb'"(?:[^"\\]|\\.)*"')

#: A JSON number token, matched only outside strings.
JSON_NUMBER: Final = re.compile(rb"-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?")


# ---------------------------------------------------------------------------
# Stubs and helpers
# ---------------------------------------------------------------------------


class _StubRegistryProvider:
    """Hands back one registry, or None to stand for a machine with no install.

    A hand-written stub rather than a mock: the protocol has one method, and a
    mock would agree with whatever this module asserted about it.
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


@dataclass(frozen=True)
class Door:
    """One backed endpoint, and the solver call it is a door onto.

    Attributes:
        endpoint: The route template.
        factory: Builds the handler from a registry provider.
        module: The solver module holding the call the handler makes.
        attribute: The name of that call on the module, so a test can replace it.
        parameters: Request parameters that reach the solver on this door.
    """

    endpoint: str
    factory: Callable[[contract.RegistryProvider[Registry]], contract.Handler]
    module: ModuleType
    attribute: str
    parameters: Mapping[str, str]


SOLVE_PARAMETERS: Final[Mapping[str, str]] = {
    "targets": f"{synthetic.SOLVE_ROD_ITEM}=50",
    "recipes": f"{synthetic.ROD_RECIPE},{synthetic.PLATE_RECIPE}",
    "raw_items": synthetic.SOLVE_ORE_ITEM,
    "byproduct_policy": ratio.BYPRODUCT_SINKABLE,
}

OPTIMIZE_PARAMETERS: Final[Mapping[str, str]] = {
    "targets": f"{synthetic.SOLVE_TRINKET_ITEM}=30",
    "candidates": f"{synthetic.ALT_GADGET_RECIPE},{synthetic.STD_GADGET_RECIPE}",
    "unlocked": f"{synthetic.ALT_GADGET_RECIPE},{synthetic.STD_GADGET_RECIPE}",
    "raw_items": synthetic.SOLVE_ORE_ITEM,
    "byproduct_policy": ratio.BYPRODUCT_SINKABLE,
    "objective": f"{optimize.OBJECTIVE_BUILDINGS}=1",
}

DOORS: Final[Mapping[str, Door]] = {
    "solve": Door(
        endpoint=solve.SOLVE_ENDPOINT,
        factory=solve.solve_handler,
        module=ratio,
        attribute="solve_for_targets",
        parameters=SOLVE_PARAMETERS,
    ),
    "optimize": Door(
        endpoint=solve.OPTIMIZE_ENDPOINT,
        factory=solve.optimize_handler,
        module=optimize,
        attribute="optimize_plan",
        parameters=OPTIMIZE_PARAMETERS,
    ),
}


@pytest.fixture(scope="module")
def registry() -> Registry:
    """The synthetic solve corpus, built once through the real seam.

    Returns:
        The registry every arm in this module solves against.
    """
    return synthetic.solve_registry()


def call(door: Door, value: Registry | None, parameters: Mapping[str, str]) -> contract.Response:
    """Run one door's handler against one provider state.

    Args:
        door: The door.
        value: What the registry provider hands back.
        parameters: The request parameters.

    Returns:
        The response.
    """
    return door.factory(_StubRegistryProvider(value))(parameters)


def solver_exception_classes() -> dict[str, type[BaseException]]:
    """Every exception class the two solver modules export, keyed by name.

    Derived rather than listed: a name in ``__all__`` that resolves to a
    ``BaseException`` subclass. A class added to either module tomorrow appears
    here without an edit, which is what makes the exhaustiveness arm mean
    something.

    Returns:
        Class name to class.
    """
    found: dict[str, type[BaseException]] = {}
    for module in SOLVER_MODULES:
        for name in module.__all__:
            member = getattr(module, name)
            if isinstance(member, type) and issubclass(member, BaseException):
                found[name] = member
    return found


def solver_exception_instances() -> dict[str, BaseException]:
    """One real instance of each exported solver exception, message-tagged.

    Constructed through each class's REAL constructor, so a signature change
    goes red here rather than silently producing a different object. The message
    is always the last positional argument and always carries
    :data:`MESSAGE_SENTINEL`.

    Returns:
        Class name to instance.
    """
    tag = MESSAGE_SENTINEL
    return {
        "RatioError": ratio.RatioError(tag),
        "UnsolvableChain": ratio.UnsolvableChain(tag, tag),
        "UnderdeterminedChain": ratio.UnderdeterminedChain((tag,), tag),
        "InfeasibleChain": ratio.InfeasibleChain(tag, Fraction(-1), tag),
        "ByproductPolicyRequired": ratio.ByproductPolicyRequired(tag, tag),
        "UnboundedSupply": ratio.UnboundedSupply(tag),
        "OptimizeError": optimize.OptimizeError(tag),
        "UnknownBackendError": optimize.UnknownBackendError(tag, tag),
        "NoFeasibleSelectionError": optimize.NoFeasibleSelectionError(tag),
        "SearchSpaceTooLargeError": optimize.SearchSpaceTooLargeError(tag),
        "ObjectiveUndefinedError": optimize.ObjectiveUndefinedError(tag),
        "PowerNotComparableError": optimize.PowerNotComparableError(tag, tag),
    }


def number_tokens(raw: bytes) -> tuple[bytes, ...]:
    """Every JSON number token in encoded bytes, ignoring digits inside strings.

    Args:
        raw: The encoded response body.

    Returns:
        The number tokens, in order.
    """
    return tuple(JSON_NUMBER.findall(JSON_STRING.sub(b'""', raw)))


def inexact_tokens(raw: bytes) -> tuple[bytes, ...]:
    """Every number token that is not a plain integer - a float on the wire.

    Args:
        raw: The encoded response body.

    Returns:
        The offending tokens.
    """
    return tuple(token for token in number_tokens(raw) if b"." in token or b"e" in token.lower())


def bare_number_paths(value: object, path: str = "data") -> tuple[str, ...]:
    """Every path at which a number sits OUTSIDE a ``{"num","den"}`` object.

    A rate that reached the wire as a plain JSON number is one a JavaScript
    client reads as an IEEE double. A two-field object cannot be misread that
    way by accident, so every numeric leaf in the serialized model must be
    inside one.

    Args:
        value: Any part of a serialized payload.
        path: What to call the root in a reported path.

    Returns:
        The offending paths.
    """
    if isinstance(value, dict):
        if frozenset(value) == RATIONAL_KEYS:
            return ()
        return tuple(
            offence
            for key, item in value.items()
            for offence in bare_number_paths(item, f"{path}[{key!r}]")
        )
    if isinstance(value, list | tuple):
        return tuple(
            offence
            for index, item in enumerate(value)
            for offence in bare_number_paths(item, f"{path}[{index}]")
        )
    if isinstance(value, bool) or not isinstance(value, int | float):
        return ()
    return (path,)


# ---------------------------------------------------------------------------
# The detectors, graded before anything trusts them
# ---------------------------------------------------------------------------


def test_the_number_scanner_finds_a_planted_float() -> None:
    found = inexact_tokens(b'{"machines":3.3333333333333335}')
    count = len(found)
    assert count == 1


def test_the_number_scanner_ignores_digits_inside_a_string() -> None:
    found = inexact_tokens(b'{"recipe_key":"R_Rod_1.5","note":"3.25"}')
    count = len(found)
    assert count == 0


def test_the_number_scanner_still_sees_the_integers_it_should() -> None:
    found = number_tokens(b'{"num":10,"den":3,"key":"Desc_9_C"}')
    assert found == (b"10", b"3")


def test_the_bare_number_walker_finds_a_planted_bare_rate() -> None:
    found = bare_number_paths({"steps": [{"machines": 3}]})
    count = len(found)
    assert count == 1


def test_the_bare_number_walker_accepts_a_rational_object() -> None:
    found = bare_number_paths({"steps": [{"machines": {"num": 10, "den": 3}}]})
    count = len(found)
    assert count == 0


# ---------------------------------------------------------------------------
# (a) and (b) a real plan, and the exact rational on the wire
# ---------------------------------------------------------------------------


def test_solve_answers_200_with_the_real_c1_plan(registry: Registry) -> None:
    response = call(DOORS["solve"], registry, SOLVE_PARAMETERS)
    status = response.http_status
    problems = contract.contract_problems(response)
    assert status == contract.HTTP_OK
    assert problems == ()

    data = response.payload["data"]
    assert isinstance(data, dict)
    machines = {step["recipe_key"]: step["machines"] for step in data["steps"]}
    assert machines[synthetic.ROD_RECIPE] == contract.rational(synthetic.C1_ROD_MACHINES)
    assert machines[synthetic.PLATE_RECIPE] == contract.rational(synthetic.C1_PLATE_MACHINES)
    assert data["raw_inputs"][synthetic.SOLVE_ORE_ITEM] == contract.rational(
        synthetic.C1_ORE_DEMAND
    )
    assert data["targets"][synthetic.SOLVE_ROD_ITEM] == contract.rational(synthetic.C1_ROD_TARGET)
    assert data["byproduct_policy"] == ratio.BYPRODUCT_SINKABLE


def test_optimize_answers_200_with_the_real_c5_result(registry: Registry) -> None:
    response = call(DOORS["optimize"], registry, OPTIMIZE_PARAMETERS)
    status = response.http_status
    problems = contract.contract_problems(response)
    assert status == contract.HTTP_OK
    assert problems == ()

    data = response.payload["data"]
    assert isinstance(data, dict)
    assert data["selection"] == [synthetic.STD_GADGET_RECIPE]
    assert data["backend"] == optimize.DEFAULT_BACKEND
    machines = {step["recipe_key"]: step["machines"] for step in data["plan"]["steps"]}
    assert machines == {synthetic.STD_GADGET_RECIPE: contract.rational(synthetic.C5_STD_MACHINES)}
    assert data["plan"]["raw_inputs"][synthetic.SOLVE_ORE_ITEM] == contract.rational(
        synthetic.C5_ORE_DEMAND
    )


@pytest.mark.parametrize("door_name", sorted(DOORS))
def test_no_rate_reaches_the_wire_as_a_bare_number(door_name: str, registry: Registry) -> None:
    door = DOORS[door_name]
    response = call(door, registry, door.parameters)
    data = response.payload["data"]
    offences = bare_number_paths(data)
    offence_count = len(offences)
    assert offence_count == 0


@pytest.mark.parametrize("door_name", sorted(DOORS))
def test_the_encoded_bytes_carry_no_float_token(door_name: str, registry: Registry) -> None:
    door = DOORS[door_name]
    raw = contract.encode(call(door, registry, door.parameters).payload)
    offences = inexact_tokens(raw)
    offence_count = len(offences)
    token_count = len(number_tokens(raw))
    assert token_count > 0
    assert offence_count == 0


def test_ten_thirds_does_not_reach_the_wire_as_its_float_rendering(registry: Registry) -> None:
    raw = contract.encode(call(DOORS["solve"], registry, SOLVE_PARAMETERS).payload)
    assert synthetic.C1_ROD_MACHINES_FLOAT_REPR.encode("ascii") not in raw
    assert b'"den":3' in raw
    assert b'"num":10' in raw


def test_a_decimal_target_is_read_exactly_and_never_through_a_float(registry: Registry) -> None:
    parameters = {**SOLVE_PARAMETERS, "targets": f"{synthetic.SOLVE_ROD_ITEM}=0.1"}
    response = call(DOORS["solve"], registry, parameters)
    status = response.http_status
    assert status == contract.HTTP_OK
    data = response.payload["data"]
    assert isinstance(data, dict)
    assert data["targets"][synthetic.SOLVE_ROD_ITEM] == contract.rational(Fraction(1, 10))
    assert data["targets"][synthetic.SOLVE_ROD_ITEM] != contract.rational(Fraction(0.1))


def test_a_ratio_target_is_accepted_in_num_slash_den_form(registry: Registry) -> None:
    parameters = {**SOLVE_PARAMETERS, "targets": f"{synthetic.SOLVE_ROD_ITEM}=10/3"}
    response = call(DOORS["solve"], registry, parameters)
    status = response.http_status
    assert status == contract.HTTP_OK
    data = response.payload["data"]
    assert isinstance(data, dict)
    assert data["targets"][synthetic.SOLVE_ROD_ITEM] == contract.rational(Fraction(10, 3))


# ---------------------------------------------------------------------------
# (c) solver refusals route by type name and their messages never leave
# ---------------------------------------------------------------------------


def test_the_exported_solver_exception_population_is_the_twelve() -> None:
    derived = solver_exception_classes()
    count = len(derived)
    assert count == EXPECTED_SOLVER_EXCEPTIONS
    assert frozenset(derived) == frozenset(contract.SOLVER_REFUSALS)


def test_a_name_suffix_rule_would_miss_five_of_the_twelve() -> None:
    derived = solver_exception_classes()
    count = len(derived)
    assert count == EXPECTED_SOLVER_EXCEPTIONS
    suffixed = len([name for name in derived if name.endswith("Error")])
    unsuffixed = len([name for name in derived if not name.endswith("Error")])
    assert suffixed == EXPECTED_SUFFIXED_EXCEPTIONS
    assert unsuffixed == EXPECTED_UNSUFFIXED_EXCEPTIONS
    assert suffixed + unsuffixed == EXPECTED_SOLVER_EXCEPTIONS


def test_every_exported_solver_exception_has_a_constructed_instance() -> None:
    instances = solver_exception_instances()
    count = len(instances)
    assert count == EXPECTED_SOLVER_EXCEPTIONS
    assert frozenset(instances) == frozenset(solver_exception_classes())


def test_every_planted_instance_really_carries_the_sentinel_in_its_message() -> None:
    instances = solver_exception_instances()
    carrying = [name for name, exc in instances.items() if MESSAGE_SENTINEL in str(exc)]
    count = len(carrying)
    assert count == EXPECTED_SOLVER_EXCEPTIONS


def test_every_planted_instance_is_an_instance_of_its_declared_class() -> None:
    classes = solver_exception_classes()
    instances = solver_exception_instances()
    matching = [name for name, exc in instances.items() if type(exc) is classes[name]]
    count = len(matching)
    assert count == EXPECTED_SOLVER_EXCEPTIONS


@pytest.mark.parametrize("door_name", sorted(DOORS))
@pytest.mark.parametrize("exception_name", sorted(solver_exception_instances()))
def test_a_solver_refusal_routes_by_its_class_name(
    door_name: str,
    exception_name: str,
    registry: Registry,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    door = DOORS[door_name]
    planted = solver_exception_instances()[exception_name]

    def raiser(*_args: object, **_kwargs: object) -> object:
        raise planted

    monkeypatch.setattr(door.module, door.attribute, raiser)
    response = call(door, registry, door.parameters)

    status, reason = contract.SOLVER_REFUSALS[exception_name]
    unavailable = status == contract.STATUS_UNAVAILABLE
    expected_code = contract.HTTP_UNAVAILABLE if unavailable else contract.HTTP_BAD_REQUEST
    observed_code = response.http_status
    observed_reason = response.payload.get("reason")
    problems = contract.contract_problems(response)
    assert observed_code == expected_code
    assert observed_reason == reason
    assert problems == ()


@pytest.mark.parametrize("door_name", sorted(DOORS))
@pytest.mark.parametrize("exception_name", sorted(solver_exception_instances()))
def test_a_solver_refusal_message_never_reaches_the_body(
    door_name: str,
    exception_name: str,
    registry: Registry,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    door = DOORS[door_name]
    planted = solver_exception_instances()[exception_name]

    def raiser(*_args: object, **_kwargs: object) -> object:
        raise planted

    monkeypatch.setattr(door.module, door.attribute, raiser)
    raw = contract.encode(call(door, registry, door.parameters).payload)
    leaked = MESSAGE_SENTINEL.encode("ascii") in raw
    assert leaked is False


def test_the_sentinel_scan_would_catch_a_leak_if_there_were_one() -> None:
    leaked = MESSAGE_SENTINEL.encode("ascii") in contract.encode(
        {"status": contract.STATUS_OK, "endpoint": "/api/solve", "data": {"m": MESSAGE_SENTINEL}}
    )
    assert leaked is True


def test_an_unpublished_solver_subclass_falls_back_to_its_base_row(
    registry: Registry, monkeypatch: pytest.MonkeyPatch
) -> None:
    class _UnpublishedRefusal(ratio.RatioError):
        """A refusal class no version of SOLVER_REFUSALS has ever named."""

    def raiser(*_args: object, **_kwargs: object) -> object:
        raise _UnpublishedRefusal(MESSAGE_SENTINEL)

    monkeypatch.setattr(ratio, "solve_for_targets", raiser)
    response = call(DOORS["solve"], registry, SOLVE_PARAMETERS)
    unpublished = "_UnpublishedRefusal" not in contract.SOLVER_REFUSALS
    status = response.http_status
    reason = response.payload.get("reason")
    leaked = MESSAGE_SENTINEL.encode("ascii") in contract.encode(response.payload)
    assert unpublished is True
    assert status == contract.HTTP_BAD_REQUEST
    assert reason == contract.REASON_RATIO_REFUSED
    assert leaked is False


def test_an_unknown_backend_is_503_through_the_real_solver(registry: Registry) -> None:
    parameters = {**OPTIMIZE_PARAMETERS, "backend": "not-a-backend-this-build-has"}
    response = call(DOORS["optimize"], registry, parameters)
    status = response.http_status
    reason = response.payload.get("reason")
    problems = contract.contract_problems(response)
    assert status == contract.HTTP_UNAVAILABLE
    assert reason == contract.REASON_BACKEND_UNAVAILABLE
    assert problems == ()


def test_an_objective_naming_no_direction_is_the_solvers_verdict(registry: Registry) -> None:
    parameters = {**OPTIMIZE_PARAMETERS, "objective": "not_a_direction=1"}
    response = call(DOORS["optimize"], registry, parameters)
    status = response.http_status
    reason = response.payload.get("reason")
    assert status == contract.HTTP_BAD_REQUEST
    assert reason == contract.REASON_OBJECTIVE_UNDEFINED


def test_an_unsolvable_chain_is_400_through_the_real_solver(registry: Registry) -> None:
    parameters = {
        **SOLVE_PARAMETERS,
        "targets": f"{synthetic.SOLVE_ROD_ITEM}=50",
        "recipes": synthetic.ORPHAN_RECIPE,
    }
    response = call(DOORS["solve"], registry, parameters)
    status = response.http_status
    reason = response.payload.get("reason")
    assert status == contract.HTTP_BAD_REQUEST
    assert reason == contract.REASON_CHAIN_UNSOLVABLE


# ---------------------------------------------------------------------------
# (d) 503 and 501 do not collapse
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("door_name", sorted(DOORS))
def test_no_registry_is_503_and_names_the_absent_install(door_name: str) -> None:
    door = DOORS[door_name]
    response = call(door, None, door.parameters)
    status = response.http_status
    reason = response.payload.get("reason")
    blocker = response.payload.get("blocked_by")
    problems = contract.contract_problems(response)
    assert status == contract.HTTP_UNAVAILABLE
    assert status != contract.HTTP_NOT_IMPLEMENTED
    assert reason == contract.REASON_NO_GAME_INSTALL
    assert blocker is None
    assert problems == ()


@pytest.mark.parametrize("door_name", sorted(DOORS))
def test_no_registry_refuses_before_the_solver_is_reached(
    door_name: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    door = DOORS[door_name]

    def raiser(*_args: object, **_kwargs: object) -> object:
        message = "the solver was reached with no registry"
        raise AssertionError(message)

    monkeypatch.setattr(door.module, door.attribute, raiser)
    status = call(door, None, door.parameters).http_status
    assert status == contract.HTTP_UNAVAILABLE


# ---------------------------------------------------------------------------
# (e) request-shape refusals, from the closed vocabulary and echoing nothing
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("door_name", sorted(DOORS))
def test_an_empty_request_is_400_missing_parameter(door_name: str, registry: Registry) -> None:
    door = DOORS[door_name]
    response = call(door, registry, {})
    status = response.http_status
    reason = response.payload.get("reason")
    assert status == contract.HTTP_BAD_REQUEST
    assert reason == contract.REASON_MISSING_PARAMETER


@pytest.mark.parametrize("door_name", sorted(DOORS))
def test_each_required_parameter_is_individually_required(
    door_name: str, registry: Registry
) -> None:
    door = DOORS[door_name]
    names = sorted(door.parameters)
    count = len(names)
    assert count > 0
    statuses = set()
    for name in names:
        trimmed = {key: value for key, value in door.parameters.items() if key != name}
        response = call(door, registry, trimmed)
        statuses.add((response.http_status, response.payload.get("reason")))
    assert statuses == {(contract.HTTP_BAD_REQUEST, contract.REASON_MISSING_PARAMETER)}


@pytest.mark.parametrize("door_name", sorted(DOORS))
def test_an_unknown_parameter_is_400_unknown_parameter(door_name: str, registry: Registry) -> None:
    door = DOORS[door_name]
    response = call(door, registry, {**door.parameters, "clock_speed": "1"})
    status = response.http_status
    reason = response.payload.get("reason")
    assert status == contract.HTTP_BAD_REQUEST
    assert reason == contract.REASON_UNKNOWN_PARAMETER


@pytest.mark.parametrize(
    "targets",
    [
        "",
        "Desc_SolveRod_C",
        "Desc_SolveRod_C=",
        "Desc_SolveRod_C=fifty",
        "Desc_SolveRod_C=1/0",
        "Desc_SolveRod_C=1e3",
        "Desc_SolveRod_C=0x10",
        "=50",
        "Desc_SolveRod_C=50=60",
    ],
)
def test_a_malformed_targets_value_is_400_invalid_parameter(
    targets: str, registry: Registry
) -> None:
    response = call(DOORS["solve"], registry, {**SOLVE_PARAMETERS, "targets": targets})
    status = response.http_status
    reason = response.payload.get("reason")
    assert status == contract.HTTP_BAD_REQUEST
    assert reason == contract.REASON_INVALID_PARAMETER


def test_a_recipe_key_outside_the_registry_is_400_invalid_parameter(registry: Registry) -> None:
    parameters = {**SOLVE_PARAMETERS, "recipes": "R_NoSuchRecipeInThisRegistry"}
    response = call(DOORS["solve"], registry, parameters)
    status = response.http_status
    reason = response.payload.get("reason")
    assert status == contract.HTTP_BAD_REQUEST
    assert reason == contract.REASON_INVALID_PARAMETER


def test_an_unusable_byproduct_policy_is_the_solvers_verdict(registry: Registry) -> None:
    parameters = {**SOLVE_PARAMETERS, "byproduct_policy": "assume_it_vanishes"}
    response = call(DOORS["solve"], registry, parameters)
    status = response.http_status
    reason = response.payload.get("reason")
    assert status == contract.HTTP_BAD_REQUEST
    assert reason == contract.REASON_BYPRODUCT_POLICY_REQUIRED


@pytest.mark.parametrize("door_name", sorted(DOORS))
def test_a_refusal_body_never_echoes_a_request_value(door_name: str, registry: Registry) -> None:
    door = DOORS[door_name]
    marker = "Desc_S4EchoProbe_C"
    response = call(door, registry, {**door.parameters, "targets": f"{marker}=nope"})
    raw = contract.encode(response.payload)
    status = response.http_status
    assert status == contract.HTTP_BAD_REQUEST
    assert marker.encode("ascii") not in raw


# ---------------------------------------------------------------------------
# The published route table
# ---------------------------------------------------------------------------


def test_solve_publishes_exactly_two_post_routes(registry: Registry) -> None:
    routes = solve.routes(_StubRegistryProvider(registry))
    count = len(routes)
    assert count == EXPECTED_DOORS
    published = sorted((route.method, route.template) for route in routes)
    assert published == [("POST", solve.OPTIMIZE_ENDPOINT), ("POST", solve.SOLVE_ENDPOINT)]


def test_every_published_template_is_spellable_as_an_endpoint(registry: Registry) -> None:
    routes = solve.routes(_StubRegistryProvider(registry))
    count = len(routes)
    assert count == EXPECTED_DOORS
    unspellable = [
        route.template
        for route in routes
        if contract.ENDPOINT_PATTERN.fullmatch(route.template) is None
    ]
    unspellable_count = len(unspellable)
    assert unspellable_count == 0
