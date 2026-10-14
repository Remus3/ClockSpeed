"""``/api/power``: the power and clock half of the solve layer, serialized.

Owns (BOOTSTRAP.md section 7.1): the request grammar for the power door, the
JSON spelling of the five records ``clockspeed/solve/power.py`` publishes, and
the transcription of a missing building into the frozen envelope.

THE POWER LAYER WAS WRITTEN, TESTED AND REACHABLE FROM NO ROUTE AT ALL, and this
module exists because that is indistinguishable from not having been written.
``declared_draw``, ``draw_at_clock``, ``clock_ceiling``,
``clamp_to_unsharded_base`` and ``variable_power_inputs`` are all published
below, so the whole of that module's answer is askable rather than half of it.
``/api/power`` is the third route to arrive under section 7.1's word "minimum",
after ``/api/registry`` (CS-912) and ``/api/map`` (CS-977).

THE DEFERRED TERM LEAVES UNEVALUATED, AND THAT IS THIS DOOR'S WHOLE EXACTNESS
PROBLEM. ``clockspeed/solve/power.py`` records the measurement: with
``exponent`` a shipped NON-INTEGER exponent (the pin in
``clockspeed/data/version.py`` owns the values),
``Fraction(5, 2) ** Fraction(exponent)`` returns the FLOAT
3.3577506181236285 on this interpreter for one of them, without raising and
without warning,
because the result is irrational for essentially every rational clock. So away
from the reference clock the answer is an exact coefficient beside a
``DeferredPowerTerm``, and this module renders that term as its two exact
OPERANDS - base and exponent, each a ``{"num","den"}`` pair - and applies
neither. A surface that evaluated it would reintroduce the defect at the one
layer with no arithmetic of its own to catch it with, which is non-negotiable 6
given away at the last possible moment.

EVERY RATE LEAVES AS ``{"num": n, "den": d}``, exactly as
``clockspeed/surface/api/solve.py`` states at length. ``slots`` is the ONE bare
integer in a body and it is not a rate - it is a COUNT of shard sockets, served
the way ``clockspeed/surface/api/registry.py`` serves ``sink_points``. It is
also None today and by design: ADR 0005 establishes that no source on this
machine carries it.

NO CEILING NUMBER IS PUBLISHED IN ANY STATE, and :data:`CEILING_KEYS` is the
fence rather than a listing. ``power.ClockCeiling`` deliberately has no field
that could hold one, so a body built from its fields cannot carry one either.
The un-sharded base IS served, and it is served under the name the game's own
header gives it, because ADR 0006's requirement is that a caller clamping to
that value SAY it is clamping to the un-sharded base - which the served
``clamped`` record does, in the power layer's own words.

NOTHING HERE INTERPRETS AN OUTCOME. Every ``shape``, ``outcome`` and ``reason``
is a closed-vocabulary string the power layer authored, passed through whole. A
surface that translated one would hold a second copy of a vocabulary its
neighbour owns, and the copy is the one that goes stale (CLAUDE.md section 4).

WHY A BUILDING KEY IS LOOKED UP HERE AND WHY THAT IS NOT COMPUTATION.
``clockspeed/solve/power.py`` takes a ``Building`` and a ``Recipe``, not their
keys, so somebody has to turn a key into the model. That is a mapping read
against the registry - the same read ``clockspeed/surface/api/registry.py``
already publishes the vocabulary FOR - and it decides nothing about power. What
this module must not do, and does not, is answer a question about a building the
registry does not hold: an absent key is refused, never defaulted and never
answered with a zero draw.

THE REFUSAL NAMES NO KEY. A caller-supplied string reaches this layer, and the
class of value it can carry is game content. The reason comes out of
``contract.REASONS`` whole and the offending key is never interpolated, on the
rule ``clockspeed/surface/api/solve.py`` states for a solver message.

THE 501/503 SPLIT DOES NOT COLLAPSE HERE EITHER. ``build_registry`` needs a
document read from the game install, so on a machine with no game there is no
registry: a WRITTEN layer with an ABSENT input, which is 503 and a different
truth with a different remedy from "this layer has not been built yet".

WHY A MALFORMED REQUEST IS REFUSED BEFORE THE PROVIDER IS CONSULTED. A request
that does not satisfy the grammar fails identically on every machine, and saying
so does not depend on any machine state. Consulting the provider first would
make the answer to one bad request depend on whether a game happens to be
installed, which is the determinism property (CLAUDE.md section 1) given away
for nothing.
"""

# SEAM DISCIPLINE (BOOTSTRAP.md section 6).
# Each layer consumes only the layer below it through a stated model.
# solve/ never reads a save. advisor/ never reads the raw docs file.
# surface/ never computes. A layer that reaches past its neighbor is a
# design bug.
#
# Below this module is clockspeed.solve.power, and that is the ONLY layer it
# names at runtime for an ANSWER. The registry's provenance (CS-1315) comes
# through clockspeed/surface/api/provenance.py, a helper that publishes no route
# and copies the audit layer's registry check. It opens no file: not a save, not
# the raw docs, not the game install. The registry arrives from a provider the SERVER bound into the
# handler by closure, so this module never imports the server and never learns
# how a registry was obtained.
#
# IT IMPORTS NO SIBLING ENDPOINT MODULE, which is why the two request-grammar
# patterns below are spelled here rather than borrowed from
# clockspeed/surface/api/solve.py. clockspeed/surface/api/routes.py states the
# rule: "Every module beside it publishes its own routes and imports none of its
# siblings, so each stays gradeable on its own." A duplicated fact is one that
# will drift, so the duplication is MACHINE-CHECKED rather than trusted -
# tests/surface/test_power.py pins both patterns equal to solve.py's, and a
# divergence goes red there instead of shipping two grammars for one wire.

from __future__ import annotations

import re
from dataclasses import dataclass, field
from fractions import Fraction
from typing import TYPE_CHECKING, Final

from clockspeed.solve import power
from clockspeed.surface.api import contract, provenance

if TYPE_CHECKING:
    from collections.abc import Mapping

    from clockspeed.data.registry import Building, Recipe, Registry
    from clockspeed.solve.exact import DeferredPowerTerm

__all__ = [
    "AT_CLOCK_KEYS",
    "CEILING_KEYS",
    "CLAMPED_KEYS",
    "DATA_KEYS",
    "DECLARED_KEYS",
    "ENDPOINT",
    "KEY_PATTERN",
    "METHOD_GET",
    "OPTIONAL",
    "PARAM_BUILDING",
    "PARAM_CLOCK",
    "PARAM_RECIPE",
    "RATIONAL_PATTERN",
    "REQUIRED",
    "TERM_KEYS",
    "VARIABLE_KEYS",
    "make_handler",
    "routes",
]


# ---------------------------------------------------------------------------
# The route template and the request grammar
# ---------------------------------------------------------------------------

#: The route template this endpoint answers. A literal authored here, never a
#: path read off a request line.
ENDPOINT: Final = "/api/power"

#: The verb this route answers, spelled HERE because a module that owns an
#: endpoint owns its method too - the rule
#: ``clockspeed/surface/api/registry.py`` states and
#: ``clockspeed/surface/api/solve.py`` already follows.
#:
#: A GET AND NOT A POST, WHICH IS THE OPPOSITE CHOICE FROM THE SOLVER DOORS AND
#: IS MADE ON THEIR OWN STATED GROUND. Those two answer with a POST because a
#: request carries a target BASKET, a candidate set and an objective - a body
#: rather than something to spell in a URL. A power request carries one building
#: identifier, at most one recipe identifier and at most one clock: it is a
#: lookup, like ``/api/registry`` and ``/api/plan?target=<milestone>`` beside it,
#: and nothing about it is a basket.
METHOD_GET: Final = "GET"

PARAM_BUILDING: Final = "building"
PARAM_CLOCK: Final = "clock"
PARAM_RECIPE: Final = "recipe"

#: Exactly what ``/api/power`` requires: the building, and nothing else. Two of
#: the five power-layer answers need no further input, so the cheapest useful
#: question is one parameter long.
REQUIRED: Final = frozenset({PARAM_BUILDING})

#: The two parameters that unlock the clock-dependent and recipe-dependent
#: answers. OPTIONAL rather than required because a caller who wants only the
#: declared draw should not have to invent a clock to ask for it - and an
#: invented clock is exactly the kind of value that later reads as measured.
#: Anything outside both sets is REFUSED rather than ignored, on the rule
#: ``clockspeed/solve/optimize.py`` states for an unknown objective weight: an
#: ignored parameter is one the caller believes is in force and is not.
OPTIONAL: Final = frozenset({PARAM_CLOCK, PARAM_RECIPE})

#: An item, recipe or building ClassName. Permissive enough for the namespaced
#: identifiers mod content uses (BOOTSTRAP.md section 11). PINNED EQUAL TO
#: ``clockspeed/surface/api/solve.py``'s by ``tests/surface/test_power.py`` - see
#: the seam note above on why it is copied rather than imported.
KEY_PATTERN: Final = re.compile(r"[A-Za-z_][A-Za-z0-9_.-]*")

#: An exact clock: an integer, an exact decimal, or ``num/den``. THE EXPONENT
#: FORM IS ABSENT ON PURPOSE. ``1e3`` has no reading that does not pass through
#: a binary float, and admitting one shape whose value depends on that reading
#: would undo the whole exactness argument for the sake of a spelling nobody
#: needs. Applied with ``fullmatch``, so a trailing newline cannot smuggle
#: anything past it. Pinned equal to solve.py's, as above.
RATIONAL_PATTERN: Final = re.compile(r"-?\d+(?:\.\d+|/\d+)?")


# ---------------------------------------------------------------------------
# The body shape. Every tuple below mirrors a power-layer dataclass exactly.
# ---------------------------------------------------------------------------

#: Exactly the top-level keys a success body carries. TOTAL: the three
#: conditional answers are always PRESENT and are null when the caller did not
#: ask for them, so a client never has to tell an absent key from an unknown
#: one. Null cannot be mistaken for an answer, because every power-layer answer
#: is a named-outcome object and none of them is ever null. The last two are
#: ``provenance.DATA_KEYS`` (CS-1315): whether the registry every draw here is
#: priced from was verified against the pinned docs, and the audit's code when
#: it was not.
DATA_KEYS: Final = (
    "building_key",
    "declared",
    "ceiling",
    "at_clock",
    "clamped",
    "variable_inputs",
    *provenance.DATA_KEYS,
)

#: ``power.DeclaredDraw``'s fields, in its own order.
DECLARED_KEYS: Final = ("shape", "megawatts", "minimum", "maximum", "modeled", "reason")

#: ``power.ClockedDraw``'s fields, in its own order.
AT_CLOCK_KEYS: Final = ("outcome", "megawatts", "coefficient", "deferred", "reason")

#: ``exact.DeferredPowerTerm``'s fields. TWO OPERANDS AND NO VALUE, which is the
#: whole point of the type - it carries no evaluation method because there is no
#: exact rational value to evaluate to.
TERM_KEYS: Final = ("base", "exponent")

#: ``power.ClockCeiling``'s fields. THERE IS NO CEILING KEY HERE and there is
#: nowhere for one to go, which is ADR 0005's fence rather than an omission.
CEILING_KEYS: Final = ("base", "slots", "known", "reason")

#: ``power.ClampedClock``'s fields.
CLAMPED_KEYS: Final = ("clock", "base", "clamped", "reason")

#: ``power.VariablePowerInputs``'s fields, in its own order.
VARIABLE_KEYS: Final = ("constant", "factor", "minimum", "maximum", "modeled", "reason")


class _PowerParameterError(Exception):
    """One request-shape refusal, carrying a REASON CODE and no caller text.

    A code rather than a message, which is the anti-echo rule applied to this
    module's own internals: an exception that carried the offending value would
    put that value one ``str(exc)`` away from a response body. The rendered line
    comes out of ``contract.REASONS`` whole.

    THE NAME CARRIES THIS MODULE'S PREFIX, AND PRIVACY IS NOT WHY. It was
    ``_ParameterError``, which is what ``clockspeed/surface/api/solve.py``
    already calls its own, and ``tests/test_exception_messages.py`` refuses a
    class name a derivation resolves to more than one module. The leading
    underscore does not make a name unambiguous - it makes it unimported, which
    is a different property, and the arm that caught this reads the whole tree
    rather than one module's public surface. The seam note at the head of this
    file is what produced the collision: an endpoint module imports no sibling,
    so it re-declares rather than shares, and every name it re-declares has to
    be unambiguous tree-wide. A module added beside this one owes the same debt.

    Attributes:
        reason: A key of ``contract.REASONS`` whose status is
            ``contract.STATUS_ERROR``.
    """

    def __init__(self, reason: str) -> None:
        """Record the reason code.

        Args:
            reason: The closed-vocabulary reason code, authored in the contract
                module and never built from caller text.
        """
        super().__init__(reason)
        self.reason = reason


# ---------------------------------------------------------------------------
# Parsing. Every refusal is a closed-vocabulary code and quotes nothing.
# ---------------------------------------------------------------------------


def _check_names(parameters: Mapping[str, str]) -> None:
    """Refuse a request whose parameter NAMES are not the ones this door takes.

    Args:
        parameters: The request parameters.

    Raises:
        _PowerParameterError: A required name is absent, or a name outside both sets
            is present.
    """
    offered = frozenset(parameters)
    if REQUIRED - offered:
        raise _PowerParameterError(contract.REASON_MISSING_PARAMETER)
    if offered - REQUIRED - OPTIONAL:
        raise _PowerParameterError(contract.REASON_UNKNOWN_PARAMETER)


def _key(text: str) -> str:
    """Read a parameter that is one bare identifier and nothing else.

    Args:
        text: The verbatim parameter text.

    Returns:
        The identifier, unchanged.

    Raises:
        _PowerParameterError: The text is empty or is not a well-formed key.
    """
    if KEY_PATTERN.fullmatch(text) is None:
        raise _PowerParameterError(contract.REASON_INVALID_PARAMETER)
    return text


def _clock(text: str) -> Fraction:
    """Read one exact clock, never through a float.

    Args:
        text: The verbatim parameter text.

    Returns:
        The exact value. The string is handed to ``Fraction`` UNMODIFIED, which
        is what keeps ``0.1`` reading as 1/10 rather than as the binary
        approximation ``float("0.1")`` substitutes - an exact reading of the
        wrong number, and exact-and-wrong is invisible to every downstream
        exactness check.

    Raises:
        _PowerParameterError: The text is not a shape :data:`RATIONAL_PATTERN`
            admits, or is a ratio with a zero denominator.
    """
    if RATIONAL_PATTERN.fullmatch(text) is None:
        raise _PowerParameterError(contract.REASON_INVALID_PARAMETER)
    try:
        return Fraction(text)
    except (ValueError, ZeroDivisionError) as exc:
        raise _PowerParameterError(contract.REASON_INVALID_PARAMETER) from exc


@dataclass(frozen=True)
class _Shaped:
    """One request, read as far as it can be read with no registry in hand.

    THE SPLIT THIS TYPE MARKS IS THE DETERMINISM RULE, NOT A TIDINESS ONE. A
    malformed identifier and an unreadable clock fail identically on every
    machine, so they are refused before the provider is consulted; whether a
    well-formed key names anything is a question only a registry can answer, so
    that necessarily follows it. Without the split, a caller who typed an empty
    building name would get 400 on a machine with a game and 503 on one without
    - the same request, two answers, decided by something that has nothing to do
    with the request.

    Attributes:
        building_key: A well-formed identifier. Not yet known to name anything.
        clock: The exact clock, or None when the caller asked for none.
        recipe_key: A well-formed identifier, or None when none was stated.
    """

    # CS-1024: both keys are caller-typed text and are withheld from the repr.
    building_key: str = field(repr=False)
    clock: Fraction | None
    recipe_key: str | None = field(repr=False)


def _shaped(parameters: Mapping[str, str]) -> _Shaped:
    """Read every value whose shape can be judged with no registry.

    Args:
        parameters: The request parameters, names already checked.

    Returns:
        The request, shape-checked and no further.

    Raises:
        _PowerParameterError: An identifier is malformed, or the clock is not an
            exact rational this grammar admits.
    """
    stated_clock = parameters.get(PARAM_CLOCK)
    stated_recipe = parameters.get(PARAM_RECIPE)
    return _Shaped(
        building_key=_key(parameters[PARAM_BUILDING]),
        clock=None if stated_clock is None else _clock(stated_clock),
        recipe_key=None if stated_recipe is None else _key(stated_recipe),
    )


# ---------------------------------------------------------------------------
# Serialization. Transcription only - nothing here computes.
# ---------------------------------------------------------------------------


def _optional_rational(value: Fraction | None) -> dict[str, int] | None:
    """Render an optional exact measurement, keeping ABSENT distinct from zero.

    Args:
        value: The exact measurement, or None when the layer below has none.

    Returns:
        The two integers, or None. None is NEVER replaced by a zero: the power
        layer states at length that an absent draw and a declared zero are
        different facts, and a confident zero is the one failure a power plan
        cannot detect.
    """
    if value is None:
        return None
    return contract.rational(value)


def _term(value: DeferredPowerTerm | None) -> dict[str, object] | None:
    """Render the symbolic power term as its two exact operands.

    Args:
        value: The unevaluated term, or None at the reference clock and in
            every outcome that has no term.

    Returns:
        The operands, keyed by :data:`TERM_KEYS`, or None. NOTHING IS RAISED TO
        ANYTHING HERE. The exponent is an operand and is exact; the RESULT of
        applying it is what has no exact value, which is why the term arrives
        unevaluated and leaves the same way.
    """
    if value is None:
        return None
    return {"base": contract.rational(value.base), "exponent": contract.rational(value.exponent)}


def _declared(draw: power.DeclaredDraw) -> dict[str, object]:
    """Render what a building's entry declares about its draw.

    Field names mirror the dataclass exactly. A renamed field on the wire would
    be a second name for one fact, and the two would drift.

    Args:
        draw: The declaration, straight from the power layer.

    Returns:
        The object, keyed by :data:`DECLARED_KEYS`.
    """
    return {
        "shape": draw.shape,
        "megawatts": _optional_rational(draw.megawatts),
        "minimum": _optional_rational(draw.minimum),
        "maximum": _optional_rational(draw.maximum),
        "modeled": draw.modeled,
        "reason": draw.reason,
    }


def _at_clock(drawn: power.ClockedDraw) -> dict[str, object]:
    """Render one building's draw at one clock, term and all.

    Args:
        drawn: The clocked draw, straight from the power layer.

    Returns:
        The object, keyed by :data:`AT_CLOCK_KEYS`. The coefficient and the term
        are populated together or not at all, exactly as the dataclass
        publishes them - a coefficient with no term is half an answer that looks
        whole.
    """
    return {
        "outcome": drawn.outcome,
        "megawatts": _optional_rational(drawn.megawatts),
        "coefficient": _optional_rational(drawn.coefficient),
        "deferred": _term(drawn.deferred),
        "reason": drawn.reason,
    }


def _ceiling(ceiling: power.ClockCeiling) -> dict[str, object]:
    """Render what is known about a clock ceiling - which is not the ceiling.

    Args:
        ceiling: The record, straight from the power layer.

    Returns:
        The object, keyed by :data:`CEILING_KEYS`. ``slots`` is a COUNT and is
        served as a bare integer, the way
        ``clockspeed/surface/api/registry.py`` serves ``sink_points``; it is
        None today, and ADR 0005 records why.
    """
    return {
        "base": _optional_rational(ceiling.base),
        "slots": ceiling.slots,
        "known": ceiling.known,
        "reason": ceiling.reason,
    }


def _clamped(clamped: power.ClampedClock) -> dict[str, object]:
    """Render a clock limited to the un-sharded base, saying so in as many words.

    Args:
        clamped: The record, straight from the power layer.

    Returns:
        The object, keyed by :data:`CLAMPED_KEYS`. The reason is the power
        layer's own line and names the un-sharded base as what it is, which is
        how ADR 0006's requirement is met mechanically rather than by
        remembering to mention it.
    """
    return {
        "clock": contract.rational(clamped.clock),
        "base": _optional_rational(clamped.base),
        "clamped": clamped.clamped,
        "reason": clamped.reason,
    }


def _variable(inputs: power.VariablePowerInputs) -> dict[str, object]:
    """Render the variable-power operands, with no law applied to them.

    Args:
        inputs: The record, straight from the power layer.

    Returns:
        The object, keyed by :data:`VARIABLE_KEYS`. The four operands are
        UNCOLLAPSED and NO LAW IS APPLIED HERE. ADR 0021 measured the law, and
        ``clockspeed/solve/power.py`` owns it in ``bounded_draw``, which answers
        this shape with two exact bounds. This endpoint does not serve those
        bounds yet - that is CS-1065, and until it does, a consumer reading "no
        law here" as "no law anywhere" is the failure this paragraph exists to
        stop. What stays refused either way is a SCALAR: the cycle average rides
        a power-consumption curve the shipped document does not carry, so an
        interpolation here would produce a confident megawatt figure for the
        hungriest buildings in the game.
    """
    return {
        "constant": _optional_rational(inputs.constant),
        "factor": _optional_rational(inputs.factor),
        "minimum": _optional_rational(inputs.minimum),
        "maximum": _optional_rational(inputs.maximum),
        "modeled": inputs.modeled,
        "reason": inputs.reason,
    }


def _body(registry: Registry, request: _Shaped) -> dict[str, object]:
    """Answer the whole question this request asked, and nothing it did not.

    Args:
        registry: The built registry.
        request: The shape-checked request.

    Returns:
        The data object, keyed by :data:`DATA_KEYS`. Every key is present; the
        three that depend on an optional parameter are null when it was not
        stated, and the registry's provenance is copied from
        :func:`provenance.registry_state`.

    Raises:
        _PowerParameterError: An identifier names nothing in this registry. NOT
            defaulted and NOT answered with an undeclared draw: "this registry
            holds no such building" and "this building declares no draw" are
            different facts, and collapsing them would report a typo as a
            measurement.
    """
    building: Building | None = registry.buildings.get(request.building_key)
    if building is None:
        raise _PowerParameterError(contract.REASON_INVALID_PARAMETER)

    recipe: Recipe | None = None
    if request.recipe_key is not None:
        recipe = registry.recipes.get(request.recipe_key)
        if recipe is None:
            raise _PowerParameterError(contract.REASON_INVALID_PARAMETER)

    clock = request.clock
    return {
        "building_key": building.key,
        "declared": _declared(power.declared_draw(building)),
        "ceiling": _ceiling(power.clock_ceiling(building)),
        "at_clock": None if clock is None else _at_clock(power.draw_at_clock(building, clock)),
        "clamped": (
            None if clock is None else _clamped(power.clamp_to_unsharded_base(building, clock))
        ),
        "variable_inputs": (
            None if recipe is None else _variable(power.variable_power_inputs(building, recipe))
        ),
        **provenance.registry_state(registry),
    }


# ---------------------------------------------------------------------------
# The handler
# ---------------------------------------------------------------------------


def make_handler(registries: contract.RegistryProvider[Registry]) -> contract.Handler:
    """Build the ``/api/power`` handler around a bound registry provider.

    Args:
        registries: Whatever hands this endpoint the registry. Bound by the
            server before registration, so this module never imports the server
            and stays testable without an HTTPS listener.

    Returns:
        The handler.
    """

    def handle(parameters: Mapping[str, str]) -> contract.Response:
        """Answer one request.

        Args:
            parameters: The parsed query parameters.

        Returns:
            The 200 with the power answer, the 503 when this machine has no
            game installed, or the 400 for a request this door does not take.
        """
        # EVERYTHING MACHINE-INDEPENDENT IS DECIDED BEFORE THE PROVIDER IS
        # CONSULTED - see _Shaped for why the boundary sits exactly there.
        try:
            _check_names(parameters)
            request = _shaped(parameters)
        except _PowerParameterError as exc:
            return contract.bad_request(ENDPOINT, exc.reason)

        registry = registries.registry()
        if registry is None:
            return contract.unavailable(ENDPOINT, contract.REASON_NO_GAME_INSTALL)

        try:
            data = _body(registry, request)
        except _PowerParameterError as exc:
            return contract.bad_request(ENDPOINT, exc.reason)

        return contract.ok(ENDPOINT, data)

    return handle


def routes(registries: contract.RegistryProvider[Registry]) -> tuple[contract.Route, ...]:
    """Every route this module publishes, with the provider already bound.

    Args:
        registries: Whatever hands this endpoint the registry.

    Returns:
        The one GET route.
    """
    return (contract.Route(method=METHOD_GET, template=ENDPOINT, handler=make_handler(registries)),)
