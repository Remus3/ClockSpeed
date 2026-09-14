"""``/api/power`` - the power half of the solve layer, over the real module.

What is covered, and the authority for each arm:

a. THE FIXTURE IS A REAL PRODUCER'S OUTPUT, NEVER A HAND-BUILT LITERAL. Every
   body graded below comes out of the real ``clockspeed/solve/power.py`` over
   the real ``tests/data/synthetic.py`` corpus, built through the real
   ``build_registry``. A hand-assembled ``DeclaredDraw`` agrees with whatever
   this module believes the shape is, by construction, and would stay green
   through the exact serializer defect it exists to catch - CONVENTIONS.md
   section 7.2.
b. THE DEFERRED TERM REACHES THE WIRE UNEVALUATED, AND THAT IS THIS ENDPOINT'S
   WHOLE EXACTNESS PROBLEM. ``clockspeed/solve/power.py`` records that
   ``Fraction(5, 2) ** Fraction('1.321929')`` returns the FLOAT
   3.3577506181236285 on this interpreter, without raising and without warning.
   A surface that rendered ``DeferredPowerTerm`` as a number would reintroduce
   that defect at the one layer with no arithmetic of its own to catch it with,
   so the term leaves as two exact ``{"num","den"}`` pairs and the raw encoded
   bytes are scanned for a float token.
c. FOUR MEASURED SHAPES, AND AN ABSENT DRAW IS NEVER A ZERO. The corpus reaches
   all four, and the arm that says so sweeps the whole building population
   rather than naming one building per shape - the same derivation
   ``tests/solve/test_power.py`` uses, applied to the serialized body.
d. NO CEILING NUMBER EXISTS ANYWHERE IN THE BODY. ADR 0005 establishes that the
   shard slot count is absent from every source on this machine, and
   ``power.ClockCeiling`` has no field that could hold a ceiling. The arm here
   is STRUCTURAL for the same reason that one is: writing a candidate value
   down and asserting it is absent grades one number, while asserting there is
   nowhere to put one grades all of them.
e. THE SURFACE DECIDES NOTHING THE POWER LAYER COULD DECIDE. Every outcome,
   shape and reason string in a body is passed through from
   ``clockspeed/solve/power.py``, and the arms below reconcile the served value
   against a direct call rather than against a string typed here.
f. 503 AND 501 DO NOT COLLAPSE, exactly as on the two solver doors.
   ``build_registry`` needs a document read from the game install, so on a
   machine with no game there is no registry - a written layer with an absent
   input.

Test-quality discipline (CONVENTIONS.md section 7.2). Every population size is
bound to a scalar and asserted before it is iterated, and the float detector is
run against a planted POSITIVE so that "found nothing" is distinguishable from
"looks for nothing".
"""

from __future__ import annotations

import re
from fractions import Fraction
from typing import TYPE_CHECKING, Final

import pytest

from clockspeed.data.registry import build_registry
from clockspeed.solve import power as power_layer
from clockspeed.surface.api import contract, health
from clockspeed.surface.api import power as endpoint
from clockspeed.surface.api import routes as route_table
from tests.data import synthetic as corpus

if TYPE_CHECKING:
    from collections.abc import Mapping

    from clockspeed.data.registry import Registry

# ---------------------------------------------------------------------------
# Populations, each with the count its sweep asserts before iterating
# ---------------------------------------------------------------------------

#: The four measured draw shapes the power layer publishes.
EXPECTED_SHAPES: Final = 4

#: The top-level keys a power body carries.
EXPECTED_DATA_KEYS: Final = 6

#: How many routes this module publishes.
EXPECTED_ROUTES: Final = 1

#: An overclock and an underclock, both away from the reference clock, where the
#: answer is a coefficient beside an unevaluated term rather than a number.
OVERCLOCK: Final = Fraction(3, 2)
UNDERCLOCK: Final = Fraction(1, 2)

#: The float ``Fraction(3, 2) ** Fraction('1.321929')`` degrades to on this
#: interpreter if anything evaluates the deferred term. Computed rather than
#: written down, so it cannot go stale against the corpus exponent.
FLOAT_MARK: Final = "."

#: A JSON string literal, so the number scanner can blank strings out before it
#: looks for a decimal point. Without this the scanner reports every digit
#: inside a building key, and a scanner that cannot be trusted is one whose
#: silence means nothing.
JSON_STRING: Final = re.compile(rb'"(?:[^"\\]|\\.)*"')

#: A JSON number token, matched only outside strings.
JSON_NUMBER: Final = re.compile(rb"-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?")

#: The keys ``contract.rational`` spells an exact value with.
RATIONAL_KEYS: Final = frozenset({"num", "den"})


# ---------------------------------------------------------------------------
# Stubs and helpers
# ---------------------------------------------------------------------------


class _StubRegistryProvider:
    """Hands back one registry, or None for a machine with no install.

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


@pytest.fixture(scope="module")
def registry() -> Registry:
    """The synthetic data corpus, built once through the real seam.

    Returns:
        The registry every arm in this module reads power off.
    """
    return build_registry(corpus.synthetic_document())


def call(value: Registry | None, parameters: Mapping[str, str]) -> contract.Response:
    """Run the endpoint's handler against one provider state.

    Args:
        value: What the registry provider hands back.
        parameters: The request parameters.

    Returns:
        The response.
    """
    return endpoint.make_handler(_StubRegistryProvider(value))(parameters)


def body(value: Registry | None, parameters: Mapping[str, str]) -> Mapping[str, object]:
    """The ``data`` object of one 200 answer.

    Args:
        value: What the registry provider hands back.
        parameters: The request parameters.

    Returns:
        The data object.
    """
    response = call(value, parameters)
    status = response.http_status
    assert status == contract.HTTP_OK, response.payload
    data = response.payload["data"]
    assert isinstance(data, dict)
    return data


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


# ---------------------------------------------------------------------------
# (a) and (e) the served answer is the power layer's own
# ---------------------------------------------------------------------------


def test_a_fixed_draw_building_is_served_as_the_power_layer_reads_it(
    registry: Registry,
) -> None:
    served = body(registry, {"building": corpus.BLENDER_BUILDING})
    direct = power_layer.declared_draw(registry.buildings[corpus.BLENDER_BUILDING])

    declared = served["declared"]
    assert isinstance(declared, dict)
    assert declared["shape"] == direct.shape == power_layer.SHAPE_FIXED
    assert declared["modeled"] is True
    assert direct.megawatts is not None
    assert declared["megawatts"] == contract.rational(direct.megawatts)
    assert declared["reason"] == direct.reason


def test_an_undeclared_draw_is_never_served_as_a_zero(registry: Registry) -> None:
    # None is NOT zero. A confident zero is exactly what a power plan cannot
    # detect, which is why the absent case gets its own shape and a null.
    declared = body(registry, {"building": corpus.CHARGER_BUILDING})["declared"]
    assert isinstance(declared, dict)
    assert declared["shape"] == power_layer.SHAPE_UNDECLARED
    assert declared["modeled"] is False
    assert declared["megawatts"] is None
    assert declared["megawatts"] != contract.rational(Fraction(0))


def test_a_declared_range_is_served_uncollapsed(registry: Registry) -> None:
    # Collapsing the two bounds into a midpoint or into the maximum would
    # publish a scalar the document never stated.
    declared = body(registry, {"building": corpus.RAILCAR_ITEM})["declared"]
    assert isinstance(declared, dict)
    assert declared["shape"] == power_layer.SHAPE_RANGE_ONLY
    assert declared["megawatts"] is None
    assert declared["minimum"] == contract.rational(Fraction(25))
    assert declared["maximum"] == contract.rational(Fraction(110))


def test_every_measured_shape_is_reachable_through_the_endpoint(registry: Registry) -> None:
    # A claim about the model's coverage, checked against what the corpus
    # actually produces through the SERVED body rather than one building at a
    # time - a per-building arm cannot notice a shape the serializer drops.
    shapes = set()
    building_count = len(registry.buildings)
    assert building_count > 0
    for key in registry.buildings:
        declared = body(registry, {"building": key})["declared"]
        assert isinstance(declared, dict)
        shapes.add(declared["shape"])
    shape_count = len(shapes)
    assert shape_count == EXPECTED_SHAPES
    assert shapes == {
        power_layer.SHAPE_FIXED,
        power_layer.SHAPE_RANGE_ONLY,
        power_layer.SHAPE_VARIABLE,
        power_layer.SHAPE_UNDECLARED,
    }


# ---------------------------------------------------------------------------
# (b) the deferred term, never evaluated
# ---------------------------------------------------------------------------


def test_at_the_reference_clock_the_draw_is_exact_and_carries_no_term(
    registry: Registry,
) -> None:
    served = body(
        registry,
        {"building": corpus.BLENDER_BUILDING, "clock": "1"},
    )
    at_clock = served["at_clock"]
    assert isinstance(at_clock, dict)
    direct = power_layer.draw_at_clock(
        registry.buildings[corpus.BLENDER_BUILDING], power_layer.REFERENCE_CLOCK
    )
    assert at_clock["outcome"] == direct.outcome == power_layer.OUTCOME_EXACT
    assert direct.megawatts is not None
    assert at_clock["megawatts"] == contract.rational(direct.megawatts)
    assert at_clock["deferred"] is None
    assert at_clock["coefficient"] is None


@pytest.mark.parametrize("clock", [OVERCLOCK, UNDERCLOCK])
def test_away_from_the_reference_clock_the_term_is_served_symbolically(
    clock: Fraction, registry: Registry
) -> None:
    # The power law has no exact rational value here. The endpoint publishes
    # the exact coefficient beside the two exact operands of the term and
    # applies neither - evaluating it returns a float.
    served = body(
        registry,
        {
            "building": corpus.BLENDER_BUILDING,
            "clock": f"{clock.numerator}/{clock.denominator}",
        },
    )
    at_clock = served["at_clock"]
    assert isinstance(at_clock, dict)
    building = registry.buildings[corpus.BLENDER_BUILDING]
    direct = power_layer.draw_at_clock(building, clock)
    assert at_clock["outcome"] == direct.outcome == power_layer.OUTCOME_DEFERRED
    assert at_clock["megawatts"] is None
    assert direct.coefficient is not None
    assert at_clock["coefficient"] == contract.rational(direct.coefficient)

    deferred = at_clock["deferred"]
    assert isinstance(deferred, dict)
    assert deferred["base"] == contract.rational(clock)
    assert building.power_exponent is not None
    assert deferred["exponent"] == contract.rational(building.power_exponent)


@pytest.mark.parametrize("clock", ["3/2", "1/2", "1", "0", "-1"])
def test_no_power_answer_reaches_the_wire_as_a_float(clock: str, registry: Registry) -> None:
    raw = contract.encode(
        call(
            registry,
            {
                "building": corpus.BLENDER_BUILDING,
                "clock": clock,
                "recipe": corpus.ACCELERATED_RECIPE,
            },
        ).payload
    )
    token_count = len(number_tokens(raw))
    assert token_count > 0
    offences = inexact_tokens(raw)
    offence_count = len(offences)
    assert offence_count == 0


def test_the_float_detector_would_catch_a_leak_if_there_were_one() -> None:
    # The absence above means nothing unless the scanner fires on a positive.
    # This is the exact rendering an evaluated deferred term produces.
    planted = b'{"data": {"at_clock": {"megawatts": 3.3577506181236285}}}'
    offences = inexact_tokens(planted)
    offence_count = len(offences)
    assert offence_count == 1
    assert FLOAT_MARK.encode("ascii") in offences[0]


def test_no_rate_reaches_the_wire_as_a_bare_number(registry: Registry) -> None:
    # A rate that reached the wire as a plain JSON number is one a JavaScript
    # client reads as an IEEE double. Every rate-valued leaf is a two-field
    # object, which cannot be misread that way by accident.
    served = body(
        registry,
        {
            "building": corpus.BLENDER_BUILDING,
            "clock": "3/2",
            "recipe": corpus.ACCELERATED_RECIPE,
        },
    )
    offences = tuple(bare_rate_paths(served))
    offence_count = len(offences)
    assert offence_count == 0


def bare_rate_paths(value: object, path: str = "data") -> tuple[str, ...]:
    """Every path at which a number sits OUTSIDE a ``{"num","den"}`` object.

    ``slots`` is the one deliberate exception and is named rather than inferred:
    it is a COUNT of shard sockets and not a rate, so it is served as a bare
    integer exactly as ``clockspeed/surface/api/registry.py`` serves
    ``sink_points``. Naming it here means a rate that acquired that key by
    accident is still caught everywhere else.

    Args:
        value: The serialized body or a fragment of it.
        path: Where this fragment sits, for the failure message.

    Returns:
        The offending paths.
    """
    if isinstance(value, bool):
        return ()
    if isinstance(value, int):
        return (path,)
    if isinstance(value, dict):
        if set(value) == RATIONAL_KEYS:
            return ()
        found: tuple[str, ...] = ()
        for key, member in value.items():
            if key == "slots":
                continue
            found += bare_rate_paths(member, f"{path}.{key}")
        return found
    if isinstance(value, list):
        found = ()
        for index, member in enumerate(value):
            found += bare_rate_paths(member, f"{path}[{index}]")
        return found
    return ()


def test_the_bare_rate_detector_fires_on_a_planted_number() -> None:
    offences = bare_rate_paths({"declared": {"megawatts": 4}})
    offence_count = len(offences)
    assert offence_count == 1
    assert offences[0] == "data.declared.megawatts"


# ---------------------------------------------------------------------------
# (d) no ceiling number, anywhere
# ---------------------------------------------------------------------------


def test_the_ceiling_is_served_as_unknown_and_publishes_no_number(registry: Registry) -> None:
    ceiling = body(registry, {"building": corpus.BLENDER_BUILDING})["ceiling"]
    assert isinstance(ceiling, dict)
    direct = power_layer.clock_ceiling(registry.buildings[corpus.BLENDER_BUILDING])
    assert ceiling["known"] is False
    assert ceiling["slots"] is None
    assert ceiling["reason"] == direct.reason
    assert direct.base is not None
    assert ceiling["base"] == contract.rational(direct.base)


def test_the_served_ceiling_has_no_key_a_ceiling_number_could_occupy(
    registry: Registry,
) -> None:
    # STRUCTURAL rather than numeric, for the reason ADR 0005 states: writing a
    # candidate value down and asserting its absence grades one number, while
    # asserting there is nowhere to put one grades all of them.
    ceiling = body(registry, {"building": corpus.BLENDER_BUILDING})["ceiling"]
    assert isinstance(ceiling, dict)
    assert set(ceiling) == set(endpoint.CEILING_KEYS)
    assert "ceiling" not in ceiling
    assert "maximum_clock" not in ceiling


def test_a_clamped_clock_says_it_clamped_to_the_unsharded_base(registry: Registry) -> None:
    # ADR 0006's fence, at the surface. A caller reading the base as an
    # achievable ceiling caps every solve at the un-overclocked figure, so the
    # served answer states what it clamped to.
    served = body(registry, {"building": corpus.BLENDER_BUILDING, "clock": "3/2"})
    clamped = served["clamped"]
    assert isinstance(clamped, dict)
    direct = power_layer.clamp_to_unsharded_base(
        registry.buildings[corpus.BLENDER_BUILDING], OVERCLOCK
    )
    assert clamped["clamped"] is True
    assert clamped["clock"] == contract.rational(direct.clock)
    assert clamped["reason"] == direct.reason
    assert "un-sharded base" in str(clamped["reason"])


def test_a_building_with_no_base_is_not_clamped_against_an_invented_one(
    registry: Registry,
) -> None:
    served = body(registry, {"building": corpus.FLOODLIGHT_BUILDING, "clock": "3/2"})
    clamped = served["clamped"]
    assert isinstance(clamped, dict)
    assert clamped["base"] is None
    assert clamped["clamped"] is False
    assert clamped["clock"] == contract.rational(OVERCLOCK)


# ---------------------------------------------------------------------------
# The variable-power operands, with no law applied to them
# ---------------------------------------------------------------------------


def test_the_variable_operands_are_served_uncollapsed_and_unmodeled(
    registry: Registry,
) -> None:
    served = body(
        registry,
        {"building": corpus.ACCELERATOR_BUILDING, "recipe": corpus.ACCELERATED_RECIPE},
    )
    inputs = served["variable_inputs"]
    assert isinstance(inputs, dict)
    direct = power_layer.variable_power_inputs(
        registry.buildings[corpus.ACCELERATOR_BUILDING],
        registry.recipes[corpus.ACCELERATED_RECIPE],
    )
    assert inputs["modeled"] is False
    assert inputs["reason"] == direct.reason
    # This endpoint still serves the operands uncollapsed and applies no law -
    # CS-301 put the law in bounded_draw, and the reason has to name it or a
    # consumer reads "no law here" as "no law anywhere".
    assert "no law is applied here" in str(inputs["reason"])
    assert "bounded_draw" in str(inputs["reason"])
    assert direct.minimum is not None
    assert inputs["minimum"] == contract.rational(direct.minimum)


def test_the_optional_answers_are_absent_until_they_are_asked_for(
    registry: Registry,
) -> None:
    # NULL MEANS "YOU DID NOT ASK", AND IT CANNOT MEAN ANYTHING ELSE: every
    # power-layer answer is a named-outcome object, never a null. The keys are
    # always present so a client never has to tell an absent key from an
    # unknown one.
    served = body(registry, {"building": corpus.ACCELERATOR_BUILDING})
    key_count = len(served)
    assert key_count == EXPECTED_DATA_KEYS
    assert set(served) == set(endpoint.DATA_KEYS)
    assert served["at_clock"] is None
    assert served["clamped"] is None
    assert served["variable_inputs"] is None
    assert served["declared"] is not None
    assert served["ceiling"] is not None


# ---------------------------------------------------------------------------
# The request grammar. Every refusal is a closed-vocabulary code.
# ---------------------------------------------------------------------------


def test_an_empty_request_is_400_missing_parameter(registry: Registry) -> None:
    response = call(registry, {})
    status = response.http_status
    assert status == contract.HTTP_BAD_REQUEST
    assert response.payload["reason"] == contract.REASON_MISSING_PARAMETER


def test_an_unknown_parameter_is_400_unknown_parameter(registry: Registry) -> None:
    response = call(registry, {"building": corpus.BLENDER_BUILDING, "clock_speed": "1"})
    status = response.http_status
    assert status == contract.HTTP_BAD_REQUEST
    assert response.payload["reason"] == contract.REASON_UNKNOWN_PARAMETER


@pytest.mark.parametrize("stated", ["", "Build Blender", "a,b", "1Build", "Build=Blender"])
def test_a_malformed_building_key_is_400_invalid_parameter(stated: str, registry: Registry) -> None:
    response = call(registry, {"building": stated})
    status = response.http_status
    assert status == contract.HTTP_BAD_REQUEST
    assert response.payload["reason"] == contract.REASON_INVALID_PARAMETER


def test_a_building_key_naming_nothing_here_is_400_invalid_parameter(
    registry: Registry,
) -> None:
    response = call(registry, {"building": "Build_NoSuchThing_C"})
    status = response.http_status
    assert status == contract.HTTP_BAD_REQUEST
    assert response.payload["reason"] == contract.REASON_INVALID_PARAMETER


def test_a_recipe_key_naming_nothing_here_is_400_invalid_parameter(
    registry: Registry,
) -> None:
    response = call(
        registry, {"building": corpus.BLENDER_BUILDING, "recipe": "Recipe_NoSuchThing_C"}
    )
    status = response.http_status
    assert status == contract.HTTP_BAD_REQUEST
    assert response.payload["reason"] == contract.REASON_INVALID_PARAMETER


@pytest.mark.parametrize("stated", ["", "fast", "1e3", "0x10", "1/0", "3/2/1", "1.5.0"])
def test_a_clock_that_is_not_an_exact_rational_is_400_invalid_parameter(
    stated: str, registry: Registry
) -> None:
    # THE EXPONENT FORM IS REFUSED OUTRIGHT rather than parsed: ``1e3`` has no
    # reading that does not pass through a binary float, and admitting one shape
    # whose value depends on that reading undoes the whole exactness argument.
    response = call(registry, {"building": corpus.BLENDER_BUILDING, "clock": stated})
    status = response.http_status
    assert status == contract.HTTP_BAD_REQUEST
    assert response.payload["reason"] == contract.REASON_INVALID_PARAMETER


def test_a_decimal_clock_is_read_exactly_and_never_through_a_float(
    registry: Registry,
) -> None:
    # Fraction("0.1") is a tenth; Fraction(float("0.1")) is
    # 3602879701896397/36028797018963968 - an exact reading of the binary
    # approximation and a wrong reading of the decimal.
    served = body(registry, {"building": corpus.BLENDER_BUILDING, "clock": "0.1"})
    at_clock = served["at_clock"]
    assert isinstance(at_clock, dict)
    deferred = at_clock["deferred"]
    assert isinstance(deferred, dict)
    assert deferred["base"] == contract.rational(Fraction(1, 10))
    assert deferred["base"] != contract.rational(Fraction(0.1))


def test_a_negative_clock_is_a_named_outcome_and_not_a_refusal(registry: Registry) -> None:
    # A clock below zero has no real draw. That is an ANSWER the power layer
    # publishes, not a malformed request, so it arrives as a 200 carrying the
    # named outcome rather than as a 400.
    served = body(registry, {"building": corpus.BLENDER_BUILDING, "clock": "-1"})
    at_clock = served["at_clock"]
    assert isinstance(at_clock, dict)
    assert at_clock["outcome"] == power_layer.OUTCOME_UNDEFINED
    assert at_clock["megawatts"] is None


def test_a_refusal_body_never_echoes_a_request_value(registry: Registry) -> None:
    # A caller-supplied string reaches this layer, and on this machine the class
    # of value a message could carry is registry content. The reason comes out
    # of the contract's closed vocabulary whole.
    unknown = "Build_S5EchoSentinel_C"
    raw = contract.encode(call(registry, {"building": unknown}).payload)
    assert unknown.encode("ascii") not in raw


def test_a_bad_request_is_refused_before_the_provider_is_consulted() -> None:
    # Determinism: a malformed request fails identically on a machine with no
    # game as on one with a game, so the grammar is checked first.
    response = call(None, {"building": ""})
    status = response.http_status
    assert status == contract.HTTP_BAD_REQUEST
    assert response.payload["reason"] == contract.REASON_INVALID_PARAMETER


def test_no_registry_is_503_and_names_the_absent_install() -> None:
    # A WRITTEN layer with an ABSENT input, which is a different truth with a
    # different remedy from "this layer has not been built yet". Answering 501
    # would send an operator to a roadmap item instead of to their install.
    response = call(None, {"building": corpus.BLENDER_BUILDING})
    status = response.http_status
    assert status == contract.HTTP_UNAVAILABLE
    assert response.payload["reason"] == contract.REASON_NO_GAME_INSTALL


# ---------------------------------------------------------------------------
# The published route, and its reachability
# ---------------------------------------------------------------------------


def test_the_module_publishes_exactly_one_get_route(registry: Registry) -> None:
    published = endpoint.routes(_StubRegistryProvider(registry))
    count = len(published)
    assert count == EXPECTED_ROUTES
    assert published[0].method == endpoint.METHOD_GET
    assert published[0].template == endpoint.ENDPOINT


def test_the_template_is_spellable_as_an_endpoint() -> None:
    assert contract.ENDPOINT_PATTERN.fullmatch(endpoint.ENDPOINT) is not None


def test_the_endpoint_is_published_by_the_health_body() -> None:
    # THE REACHABILITY ARM. The power layer was written, tested and reachable
    # from NO route at all - a capability that exists and cannot be asked for
    # is one nobody can tell from a capability that does not exist.
    assert endpoint.ENDPOINT in health.ENDPOINT_TEMPLATES


def test_the_endpoint_is_registered_in_the_servers_route_table() -> None:
    templates = tuple(route.template for route in route_table.ROUTES)
    assert endpoint.ENDPOINT in templates
    assert route_table.ENDPOINT_STATUS[endpoint.ENDPOINT] == health.LIVE


def test_the_request_grammar_does_not_drift_from_the_solver_doors() -> None:
    """The two copied patterns are pinned to the ones ``solve.py`` publishes.

    ``clockspeed/surface/api/routes.py`` states that an endpoint module imports
    none of its siblings, so ``power.py`` spells its own ``KEY_PATTERN`` and
    ``RATIONAL_PATTERN`` rather than borrowing them. A duplicated fact is one
    that will drift (CLAUDE.md section 4), and the remedy that rule names is a
    machine check rather than trust - this is that check. Two grammars for one
    wire would mean a clock the solve door accepts and the power door refuses,
    or worse, an exponent form one of them lets through.
    """
    from clockspeed.surface.api import solve  # noqa: PLC0415

    assert endpoint.KEY_PATTERN.pattern == solve.KEY_PATTERN.pattern
    assert endpoint.RATIONAL_PATTERN.pattern == solve.RATIONAL_PATTERN.pattern
