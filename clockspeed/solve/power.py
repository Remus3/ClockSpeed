"""Power and clock mathematics: four measured draw shapes, and a ceiling nobody has measured.

Per docs/ARCHITECTURE.md this module owns the power half of the solve layer. It
consumes the normalized model published by ``clockspeed/data/registry.py`` and
the exact primitives in ``clockspeed/solve/exact.py``, and it reaches for
nothing else - not the install locator, not the docs reader. A power figure is
a property of a Building, and a Building is what the layer below hands over.

WHY EVERY ANSWER HERE IS A NAMED OUTCOME RATHER THAN A NUMBER
--------------------------------------------------------------
Almost every failure this module can have produces a plausible megawatt figure
with no error attached, so the outcomes are named and are never collapsed into
"the draw is N". Four of the five ways to be wrong return a number of the right
type:

- a building whose draw is a declared RANGE, averaged into a scalar;
- a building whose declared scalar is a real zero, published as zero;
- a building with no exponent, scaled by a borrowed one;
- a clock above the reference, evaluated through ``**`` into a float.

None of those raises. All four are caught here by refusing to publish a number
at all in the cases where the data does not supply one.

THE FOUR MEASURED POWER SHAPES
-------------------------------
``Building.power_consumption`` is ``Fraction | None`` and None does NOT mean
zero. It means NO SCALAR DRAW WAS DECLARED. Publishing zero for it is the one
unacceptable option, because a confident zero is exactly what a power plan
cannot detect - it balances, it sums, and it is silently missing a building.

1. **Ordinary fixed draw.** A scalar Fraction. This is the only shape with a
   modeled draw, and the scalar is the draw AT THE REFERENCE CLOCK.

2. **A struct range.** One measured entry declares its ``mPowerConsumption`` as
   a ``(Min=...,Max=...)`` struct rather than a decimal. The registry parses the
   bounds into ``estimated_min_power`` / ``estimated_max_power`` and leaves
   ``power_consumption`` None. Both bounds are published here UNCOLLAPSED and
   the shape is reported unmodeled: a midpoint, or the maximum taken as the
   draw, would be a scalar the document never stated.

3. **Variable power.** Three measured buildings declare ``power_consumption`` of
   exactly ``Fraction(0)`` - a REAL declared zero, not an absent key - and carry
   their true draw on the estimated range PLUS a ``variable_power_constant`` and
   ``variable_power_factor`` that live on the RECIPE rather than on the
   building. **The semantics of that constant and factor have never been
   measured by this project.** The registry carries them and nothing interprets
   them, so this module reports the shape as unmodeled and hands the operands
   back verbatim (:func:`variable_power_inputs`). Guessing a linear
   interpolation between the bounds would be inventing a law, and per
   non-negotiable 7 unknown content is flagged and skipped, never silently
   wrong.

4. **A declared maximum of zero is a FIXED-draw building.** ``is_variable_power``
   is True only when ``estimated_max_power`` is ABOVE zero, so the PRESENCE of
   the estimated-maximum key is not the test. One measured entry declares a
   maximum of ``'0.000000'`` beside a real scalar draw, and an implementation
   keyed on key presence reports the whole building unmodeled.

THE CLOCK CEILING, AND THE FENCE AROUND IT
-------------------------------------------
``version.OVERCLOCK_POTENTIAL_SHARD_SLOTS`` is None BY DESIGN. ADR 0005
established that the shard slot count is absent from every source on this
machine: the buildable subsystem is not exported to the docs data at all, and
the shipped headers declare the field ``EditDefaultsOnly`` with no initializer.
So the achievable ceiling is UNKNOWN, and :func:`clock_ceiling` reports it as
unknown rather than assuming one. **No code path in this module returns a
ceiling number in any state**, which is why :class:`ClockCeiling` has no field
that could hold one.

The routes to a ceiling that ADR 0005 forecloses, restated because this is the
module that would take them:

- Do not write the widely-known figure in as a measured value. It is widely
  known and it was never measured from anything on this machine.
- Do not derive it from ``mPowerConsumptionExponent``. The shipped exponent
  sitting within rounding of a log2 relation is a relation between two balance
  values, not a measurement of either.
- Do not invert ``ceiling = base + slots * extra`` from an assumed ceiling to
  recover the slot count. This is the route that FEELS derived, because the
  arithmetic uses only values the game ships. It is not.
- **Do not read ``Building.unsharded_clock_base`` as the achievable ceiling.**
  It is the UN-SHARDED base - the game's own header calls it the maximum not
  accounting for installed power shards - and every shipped entry reports the
  same un-overclocked value. A solver treating it as the ceiling caps every
  solve at the un-overclocked figure and looks correct on every building nobody
  has overclocked, which is invisible in exactly the worlds where testing is
  easiest. ADR 0006 exists for this trap, and its fence is that a caller
  clamping to that value must SAY it is clamping to the un-sharded base.
  :func:`clamp_to_unsharded_base` is that caller, and its result says so.

WHY NO EXPONENT IS EVER DEFAULTED
----------------------------------
``Building.power_exponent`` is None on six measured power-bearing entries, and
that means NOT CLOCK-SCALABLE. It is never defaulted, on the same rule that
governs the un-sharded base: a default publishes a number the game never
shipped, in the right type, indistinguishable from a measured one. A corpus
where other buildings DO carry an exponent is precisely where a defaulting
implementation looks correct, because some exponent is always in scope. The
answer is the named :data:`OUTCOME_NOT_SCALABLE` instead.

WHY THERE IS NO ``**`` IN THIS FILE
------------------------------------
The overclock power law is ``draw * clock ** exponent``. Measured on this
interpreter: ``Fraction(5, 2) ** Fraction('1.321929')`` returns a FLOAT,
``3.3577506181236285``. It does not raise and it does not warn, because the
result is irrational for essentially every rational clock and there is no exact
rational answer to return. The defect is DATA-DEPENDENT -
``Fraction(5, 2) ** Fraction(2, 1)`` returns a Fraction - so a test written with
a whole-number exponent passes while the shipped exponent degrades silently.

So at any clock other than the reference, this module returns
:class:`~clockspeed.solve.exact.DeferredPowerTerm` - the power law held
SYMBOLICALLY, unevaluated - beside the exact Fraction coefficient that
multiplies it. At the reference clock the answer is the declared scalar and no
exponent is applied at all, because a clock of one raised to any power is one.
That is a theorem rather than a balance value, which is why it is the single
clock with an exact rational answer.

WHY THE EXPONENT IS NEVER WRITTEN DOWN HERE (CS-105)
-----------------------------------------------------
The exponent is per building CLASS and two distinct values are measured across
the shipped entries, so a single hardcoded constant is wrong for whichever
entries carry the other one - and wrong quietly, in a number nobody can
eyeball. It is therefore read off the Building on every call and appears
nowhere in this file, under any spelling. ``tests/solve/test_power.py`` enforces
that two ways, because a source scan alone cannot: an integer-pair spelling puts
no exponent-valued constant in the file, so the durable fence is a mutation test
that runs this module over two corpora differing only in one building's
exponent and requires the results to differ.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Final

from clockspeed.data.registry import Building, Recipe
from clockspeed.data.version import OVERCLOCK_POTENTIAL_SHARD_SLOTS
from clockspeed.solve.exact import DeferredPowerTerm, InexactValueError

__all__ = [
    "OUTCOME_DEFERRED",
    "OUTCOME_EXACT",
    "OUTCOME_NOT_SCALABLE",
    "OUTCOME_UNDEFINED",
    "OUTCOME_UNMODELED",
    "REFERENCE_CLOCK",
    "SHAPE_FIXED",
    "SHAPE_RANGE_ONLY",
    "SHAPE_UNDECLARED",
    "SHAPE_VARIABLE",
    "ClampedClock",
    "ClockCeiling",
    "ClockedDraw",
    "DeclaredDraw",
    "VariablePowerInputs",
    "ceiling_reason",
    "clamp_to_unsharded_base",
    "clock_ceiling",
    "declared_draw",
    "draw_at_clock",
    "variable_power_inputs",
]

# ---------------------------------------------------------------------------
# Unit definitions
# ---------------------------------------------------------------------------

#: The clock the shipped draw is stated at. A UNIT DEFINITION and not a balance
#: value: the clock is a potential where the un-overclocked building runs at
#: one, so this is the multiplicative identity of the power law rather than a
#: number a patch can move. It is also the ONLY clock at which the law has an
#: exact rational value, because one raised to any power is one - which is a
#: theorem, and is why no exponent is read on that path.
REFERENCE_CLOCK: Final = Fraction(1)

# ---------------------------------------------------------------------------
# The four measured draw shapes
# ---------------------------------------------------------------------------

#: An ordinary scalar draw. The only shape with a modeled number.
SHAPE_FIXED: Final = "fixed"

#: A declared Min/Max struct and no scalar. Unmodeled; both bounds published.
SHAPE_RANGE_ONLY: Final = "range-only"

#: A declared scalar of a real zero beside an estimated range above zero, with
#: the rest of the law on the recipe. Unmodeled - the law is unmeasured.
SHAPE_VARIABLE: Final = "variable"

#: No readable scalar draw at all. Unmodeled, and NEVER published as zero.
SHAPE_UNDECLARED: Final = "undeclared"

# ---------------------------------------------------------------------------
# Clocked-draw outcomes, never collapsed
# ---------------------------------------------------------------------------

#: The draw is exact and complete. Reachable only at :data:`REFERENCE_CLOCK`.
OUTCOME_EXACT: Final = "exact"

#: The draw is a coefficient times an irrational term, held symbolically.
OUTCOME_DEFERRED: Final = "deferred"

#: The building declares no exponent, so it is not clock-scalable at all. A
#: different fact from an unmodeled draw: the draw may be perfectly well known.
OUTCOME_NOT_SCALABLE: Final = "not-scalable"

#: The draw itself is not modeled, so no clock can be applied to it.
OUTCOME_UNMODELED: Final = "unmodeled"

#: The clock has no real power draw - a clock below zero raises a positive
#: quantity to a power that is not real.
OUTCOME_UNDEFINED: Final = "undefined"

# ---------------------------------------------------------------------------
# Reasons. Every non-answer carries one, because "no number" with no
# explanation is a result nobody can act on.
# ---------------------------------------------------------------------------

_FIXED_REASON: Final = "the entry declares a scalar draw, which is the draw at the reference clock"

_RANGE_ONLY_REASON: Final = (
    "the draw is unmodeled: the entry declares a minimum/maximum struct rather than a "
    "scalar, and collapsing a declared range into one number would publish a draw the "
    "document never stated"
)

_VARIABLE_REASON: Final = (
    "the draw is unmodeled: the declared scalar is a real zero and the true draw is the "
    "estimated range together with a per-recipe constant and factor whose semantics this "
    "project has never measured"
)

_UNDECLARED_REASON: Final = (
    "the draw is unmodeled: the entry declares no readable scalar draw, and absence is not "
    "zero - a confident zero is exactly what a power plan cannot detect"
)

_EXACT_REASON: Final = (
    "at the reference clock the draw is the declared scalar; one raised to any power is "
    "one, so no exponent is applied and no irrational term arises"
)

_DEFERRED_REASON: Final = (
    "away from the reference clock the power law has no exact rational value, so the term "
    "is held symbolically rather than evaluated - evaluating it returns a float"
)

_NOT_SCALABLE_REASON: Final = (
    "the entry declares no exponent, which means it is not clock-scalable; an exponent is "
    "never defaulted, because a default publishes a number the game never shipped"
)

_UNDEFINED_CLOCK_REASON: Final = (
    "a clock below zero has no real power draw; the result would not be a real number, "
    "let alone a rational one"
)

_VARIABLE_INPUTS_REASON: Final = (
    "the variable-power law is unmeasured: the registry carries the per-recipe constant "
    "and factor verbatim and nothing in this project interprets them, so the operands are "
    "handed back uncollapsed and no draw is computed from them"
)

_CEILING_NO_SLOT_COUNT_REASON: Final = (
    "the achievable clock ceiling is unmeasured: it is the un-sharded base plus the "
    "installed shard slot count times the per-shard extra potential, and no source on "
    "this machine carries the slot count"
)

_CEILING_NO_EXTRA_POTENTIAL_REASON: Final = (
    "the achievable clock ceiling is unmeasured here: a slot count alone does not make a "
    "ceiling, the per-shard extra potential is the remaining operand, and this layer does "
    "not carry it - the ADR that records the reading assembles the ceiling, never this "
    "module"
)

_CLAMPED_REASON: Final = (
    "the clock was clamped to the un-sharded base, which is the maximum with no power "
    "shards installed and is not the achievable ceiling"
)

_WITHIN_BASE_REASON: Final = "the clock is at or below the un-sharded base, so nothing was clamped"

_NO_BASE_REASON: Final = (
    "the entry declares no un-sharded base, so there is nothing to clamp against; an "
    "absent base is never defaulted to one"
)


@dataclass(frozen=True)
class DeclaredDraw:
    """What one building's entry actually declares about its power draw.

    Attributes:
        shape: One of :data:`SHAPE_FIXED`, :data:`SHAPE_RANGE_ONLY`,
            :data:`SHAPE_VARIABLE` or :data:`SHAPE_UNDECLARED`. Named rather
            than reduced to a boolean, because the three unmodeled shapes fail
            for three different reasons and a caller renders them differently.
        megawatts: The scalar draw, populated ONLY for :data:`SHAPE_FIXED`.
            None everywhere else, and None is never a stand-in for zero.
        minimum: The low end of a declared range, or None. Published verbatim
            for every shape that has one.
        maximum: The high end of a declared range, or None.
        modeled: True only when :attr:`megawatts` is the whole story. False
            means this module has no draw for the building and says so.
        reason: One line naming why, for the caller to render.
    """

    shape: str
    megawatts: Fraction | None
    minimum: Fraction | None
    maximum: Fraction | None
    modeled: bool
    reason: str


@dataclass(frozen=True)
class ClockedDraw:
    """One building's draw at one clock, with the irrational case never evaluated.

    Attributes:
        outcome: One of the module's ``OUTCOME_*`` constants.
        megawatts: The complete exact draw, populated ONLY for
            :data:`OUTCOME_EXACT`.
        coefficient: The exact Fraction multiplying :attr:`deferred`. Populated
            exactly when :attr:`deferred` is, and never on its own - a
            coefficient with no term is half an answer that looks whole.
        deferred: The symbolic ``clock ** exponent`` term, or None. It carries
            no evaluation method on purpose: there is no exact rational value,
            and a caller that needs a number has to decide - at the presentation
            edge, with the rounding recorded - rather than have this layer
            decide silently.
        reason: One line naming the outcome.
    """

    outcome: str
    megawatts: Fraction | None
    coefficient: Fraction | None
    deferred: DeferredPowerTerm | None
    reason: str


@dataclass(frozen=True)
class ClockCeiling:
    """What is known about a building's clock ceiling, which is not the ceiling.

    There is deliberately NO field here that could hold a ceiling number, and
    that absence is the fence rather than an omission. See the module docstring
    and ADR 0005: the slot count is absent from every source on this machine, so
    a ceiling published from this layer would be assumed rather than measured.

    Attributes:
        base: The building's un-sharded clock base, read from the document, or
            None when the entry declares none. It is NOT the ceiling.
        slots: The shard slot count, from the version pin. None means unmeasured.
        known: Whether the achievable ceiling is known. Always False today, and
            the field exists so a caller has to ASK rather than assume. Even
            once the slot count is measured, the per-shard extra potential is a
            further operand this layer does not carry.
        reason: One line naming exactly what is missing.
    """

    base: Fraction | None
    slots: int | None
    known: bool
    reason: str


@dataclass(frozen=True)
class ClampedClock:
    """A clock limited to the un-sharded base, saying so in as many words.

    ADR 0006 requires that a caller clamping to the un-sharded base state that
    is what it clamped to. This type is how that requirement is met mechanically
    rather than by remembering to mention it.

    Attributes:
        clock: The clock to use - the requested one, or the base when the
            request exceeded it.
        base: The un-sharded base it was compared against, or None.
        clamped: Whether the requested clock was actually reduced.
        reason: One line naming the un-sharded base as what it is.
    """

    clock: Fraction
    base: Fraction | None
    clamped: bool
    reason: str


@dataclass(frozen=True)
class VariablePowerInputs:
    """The operands of the variable-power law, with no law applied to them.

    Attributes:
        constant: ``variable_power_constant`` from the RECIPE, or None.
        factor: ``variable_power_factor`` from the RECIPE, or None.
        minimum: The building's estimated minimum draw, or None.
        maximum: The building's estimated maximum draw, or None.
        modeled: Always False. The semantics of the constant and the factor have
            never been measured by this project, so there is no law to apply and
            no draw to compute.
        reason: One line saying the law is unmeasured.
    """

    constant: Fraction | None
    factor: Fraction | None
    minimum: Fraction | None
    maximum: Fraction | None
    modeled: bool
    reason: str


def _require_exact(value: object, name: str) -> None:
    """Refuse an operand that is not exactly a :class:`~fractions.Fraction`.

    The parameter is typed ``object`` rather than ``Fraction`` deliberately: a
    narrower annotation would let the type checker prove the branch below
    unreachable and delete the one guard that catches an unannotated caller.

    Args:
        value: The operand to check.
        name: What to call it in the message.

    Raises:
        InexactValueError: The value is not exactly a Fraction. Identity, not
            ``isinstance``, so a bool does not arrive by way of int.
    """
    if type(value) is not Fraction:
        raise InexactValueError(
            f"{name} is {type(value).__name__} {value!r}, not a Fraction; one inexact operand "
            "converts every value derived from it while looking entirely correct"
        )


def declared_draw(building: Building) -> DeclaredDraw:
    """Read what a building's entry declares about its draw, in all four shapes.

    The branch order is what makes the four shapes separable, and it is not
    interchangeable. ``is_variable_power`` is tested FIRST because it is the
    registry's own reading of "the estimated maximum is above zero", which is
    the only thing that distinguishes a range-bearing entry from one whose
    declared maximum is a real zero. Only then does the declared scalar decide
    between a struct range (no scalar) and variable power (a scalar of zero).

    Args:
        building: A building as ``build_registry`` published it.

    Returns:
        The declaration. A draw is modeled only when the entry declares a
        readable scalar and is not variable-power; every other shape reports
        unmodeled with both bounds intact, and none of them reports zero.
    """
    scalar = building.power_consumption
    minimum = building.estimated_min_power
    maximum = building.estimated_max_power

    if building.is_variable_power:
        # A scalar beside a real range is the variable-power shape - the scalar
        # is a declared zero and is not the draw. No scalar at all is the struct
        # shape, whose bounds the registry lifted out of the struct string.
        variable = scalar is not None
        return DeclaredDraw(
            shape=SHAPE_VARIABLE if variable else SHAPE_RANGE_ONLY,
            megawatts=None,
            minimum=minimum,
            maximum=maximum,
            modeled=False,
            reason=_VARIABLE_REASON if variable else _RANGE_ONLY_REASON,
        )

    if scalar is None:
        return DeclaredDraw(
            shape=SHAPE_UNDECLARED,
            megawatts=None,
            minimum=minimum,
            maximum=maximum,
            modeled=False,
            reason=_UNDECLARED_REASON,
        )

    return DeclaredDraw(
        shape=SHAPE_FIXED,
        megawatts=scalar,
        minimum=minimum,
        maximum=maximum,
        modeled=True,
        reason=_FIXED_REASON,
    )


def draw_at_clock(building: Building, clock: Fraction) -> ClockedDraw:
    """Compute a building's draw at one clock, deferring the irrational term.

    The exponent is read off the building on every call and appears nowhere in
    this module (CS-105). Two distinct exponents are measured across the shipped
    entries, so a constant here would be wrong for whichever entries carry the
    other one.

    Args:
        building: A building as ``build_registry`` published it.
        clock: The clock as a potential, where :data:`REFERENCE_CLOCK` is the
            un-overclocked building. Must be exactly a Fraction.

    Returns:
        The draw. Exact only at the reference clock; away from it the answer is
        an exact coefficient beside an unevaluated
        :class:`~clockspeed.solve.exact.DeferredPowerTerm`, because
        ``Fraction ** Fraction`` returns a float for the shipped exponent.

    Raises:
        InexactValueError: The clock is not exactly a Fraction.
    """
    _require_exact(clock, "clock")
    draw = declared_draw(building)
    if not draw.modeled or draw.megawatts is None:
        return ClockedDraw(OUTCOME_UNMODELED, None, None, None, draw.reason)

    exponent = building.power_exponent
    if exponent is None:
        # Not clock-scalable. The draw is known and the clock cannot be applied
        # to it, which is a different fact from the draw being unknown.
        return ClockedDraw(OUTCOME_NOT_SCALABLE, None, None, None, _NOT_SCALABLE_REASON)

    if clock == REFERENCE_CLOCK:
        return ClockedDraw(OUTCOME_EXACT, draw.megawatts, None, None, _EXACT_REASON)

    if clock < 0:
        return ClockedDraw(OUTCOME_UNDEFINED, None, None, None, _UNDEFINED_CLOCK_REASON)

    return ClockedDraw(
        outcome=OUTCOME_DEFERRED,
        megawatts=None,
        coefficient=draw.megawatts,
        deferred=DeferredPowerTerm(base=clock, exponent=exponent),
        reason=_DEFERRED_REASON,
    )


def ceiling_reason(slots: int | None) -> str:
    """Name exactly what is missing between here and an achievable ceiling.

    A function rather than one constant because the answer has two states and
    only one of them is reachable from today's data. Stating the second in code
    is what keeps it honest: measuring the slot count does not by itself produce
    a ceiling, and a reader who assumes it does will assemble one from three of
    the four operands.

    Args:
        slots: The shard slot count, or None when it is unmeasured.

    Returns:
        The reason the ceiling is still unmeasured, in either state.
    """
    if slots is None:
        return _CEILING_NO_SLOT_COUNT_REASON
    return _CEILING_NO_EXTRA_POTENTIAL_REASON


def clock_ceiling(building: Building) -> ClockCeiling:
    """Report what is known about a building's clock ceiling - which is not it.

    Publishes NO ceiling number in any state, and :class:`ClockCeiling` has no
    field that could hold one. See ADR 0005: the slot count is absent from every
    source on this machine, and a ceiling assembled from the operands that ARE
    present is the original failure with arithmetic in front of it.

    Args:
        building: A building as ``build_registry`` published it.

    Returns:
        The un-sharded base as the document stated it, the slot count as the
        version pin records it, and ``known`` False with a reason naming what
        is missing.
    """
    slots = OVERCLOCK_POTENTIAL_SHARD_SLOTS
    return ClockCeiling(
        base=building.unsharded_clock_base,
        slots=slots,
        # Never True from this layer. See the class docstring: the field exists
        # so a caller has to ask, and the answer today is no.
        known=False,
        reason=ceiling_reason(slots),
    )


def clamp_to_unsharded_base(building: Building, clock: Fraction) -> ClampedClock:
    """Limit a clock to the un-sharded base, and say that is what was done.

    ADR 0006's fence, mechanically. This is the interim behaviour ADR 0005
    specified - solve at or below the un-sharded base while the ceiling is
    unmeasured - and the result states what it clamped to so that no caller
    reports the base as a ceiling.

    Args:
        building: A building as ``build_registry`` published it.
        clock: The requested clock. Must be exactly a Fraction.

    Returns:
        The clock to use, the base it was compared against, and whether it was
        reduced. A building declaring no base is NOT clamped against an invented
        one - an absent base is never defaulted.

    Raises:
        InexactValueError: The clock is not exactly a Fraction.
    """
    _require_exact(clock, "clock")
    base = building.unsharded_clock_base
    if base is None:
        return ClampedClock(clock=clock, base=None, clamped=False, reason=_NO_BASE_REASON)
    if clock > base:
        return ClampedClock(clock=base, base=base, clamped=True, reason=_CLAMPED_REASON)
    return ClampedClock(clock=clock, base=base, clamped=False, reason=_WITHIN_BASE_REASON)


def variable_power_inputs(building: Building, recipe: Recipe) -> VariablePowerInputs:
    """Gather the variable-power operands without applying a law to them.

    The constant and the factor are per RECIPE while the estimated range is per
    BUILDING, so the operands only exist as a set once both are in hand - which
    is why this takes a pair. What it deliberately does not do is combine them:
    their semantics are unmeasured, and an invented interpolation would produce
    a confident megawatt figure for the hungriest buildings in the game.

    Args:
        building: A building as ``build_registry`` published it.
        recipe: The recipe being run in it.

    Returns:
        The four operands verbatim, ``modeled`` False, and a reason saying the
        law is unmeasured.
    """
    return VariablePowerInputs(
        constant=recipe.variable_power_constant,
        factor=recipe.variable_power_factor,
        minimum=building.estimated_min_power,
        maximum=building.estimated_max_power,
        modeled=False,
        reason=_VARIABLE_INPUTS_REASON,
    )
