"""Tests for the unit-tagged exact quantity (CS-1248, part 1 of 7: clauses 1 and 2).

Two properties carry this module, and each is here because the defect it
catches is INVISIBLE in ordinary output.

- **A wrong-unit sum is a plausible number.** ``Fraction(3) + Fraction(90)`` is
  ``93``: a per-cycle amount added to a per-minute rate is exact, finite and
  wrong, and nothing downstream can tell. So every refusal below is asserted
  with operands whose RAW VALUES ARE EQUAL where it matters, which proves the
  refusal comes from the unit and not from the value.
- **Exactness is not provable by equality.** ``Fraction(1, 2) == 0.5`` is
  ``True``, so each accepted numeric result is paired with
  ``type(x) is Fraction``.

CS-1248 Acceptance clause 3 (raw and display values are distinct fields wherever
they travel) is graded at the last CS-1248 part, not here (ruling P4F-3).

No tolerance comparison appears anywhere (see ``tests/solve/__init__.py``).
``cast`` is used only to hand an annotated signature a value it forbids, because
the runtime guards exist for values that arrive through an untyped boundary.
"""

from __future__ import annotations

import re
from dataclasses import FrozenInstanceError
from decimal import Decimal
from fractions import Fraction
from typing import cast

import pytest

from clockspeed.advisor.trace import _inexact_reason
from clockspeed.solve.exact import (
    ExactArithmeticError,
    InexactValueError,
    UndefinedRateError,
    audit_exact,
)
from clockspeed.solve.quantity import (
    UNIT_PER_CYCLE,
    UNIT_PER_MINUTE,
    UNITS,
    Quantity,
    UnitMismatchError,
    expect_per_minute,
)


class _LooseFraction(Fraction):
    """A Fraction subclass, which may have overridden the arithmetic the module needs."""


class _LooseStr(str):
    """A str subclass equal to a real unit name, which an isinstance check would admit."""


class _SubQuantity(Quantity):
    """A Quantity subclass, which may have overridden the unit rules this type enforces."""


# ===========================================================================
# Clause 1 - adding two rates of different units is refused
# ===========================================================================


def test_adding_two_rates_of_the_same_unit_is_exact_and_keeps_the_unit() -> None:
    """The accepting half: a refusal test alone passes for a type that refuses everything."""
    total = Quantity.per_minute(Fraction(1, 3)) + Quantity.per_minute(Fraction(1, 6))

    assert total == Quantity.per_minute(Fraction(1, 2))
    assert type(total.value) is Fraction
    assert total.unit == UNIT_PER_MINUTE


def test_subtracting_two_rates_of_the_same_unit_is_exact() -> None:
    """Subtraction shares the unit rule, and a negative rate is a modeled shortfall."""
    gap = Quantity.per_cycle(Fraction(1, 4)) - Quantity.per_cycle(Fraction(1, 2))

    assert gap == Quantity.per_cycle(Fraction(-1, 4))
    assert type(gap.value) is Fraction
    assert gap.unit == UNIT_PER_CYCLE


def test_adding_a_per_cycle_rate_to_a_per_minute_rate_is_refused() -> None:
    """EQUAL raw values, different units: the value cannot be what refuses this."""
    per_minute_rate = Quantity.per_minute(Fraction(3))
    per_cycle_rate = Quantity.per_cycle(Fraction(3))
    assert per_minute_rate.value == per_cycle_rate.value

    # The whole ordered phrase is pinned: both unit names appear in either message, so a bare
    # unit-name match would pass with the operand and the receiver swapped.
    with pytest.raises(
        UnitMismatchError,
        match=re.escape(f"cannot add a {UNIT_PER_CYCLE} quantity and a {UNIT_PER_MINUTE} quantity"),
    ):
        per_minute_rate + per_cycle_rate
    with pytest.raises(
        UnitMismatchError,
        match=re.escape(f"cannot add a {UNIT_PER_MINUTE} quantity and a {UNIT_PER_CYCLE} quantity"),
    ):
        per_cycle_rate + per_minute_rate


def test_subtracting_rates_of_different_units_is_refused() -> None:
    """The refusal is not special to addition: a difference of mixed units is as wrong."""
    with pytest.raises(UnitMismatchError):
        Quantity.per_minute(Fraction(3)) - Quantity.per_cycle(Fraction(3))
    with pytest.raises(UnitMismatchError):
        Quantity.per_cycle(Fraction(3)) - Quantity.per_minute(Fraction(3))


def test_the_mismatch_message_names_both_units() -> None:
    """A refusal nobody can act on is half a refusal: it says which two units met."""
    with pytest.raises(UnitMismatchError) as caught:
        Quantity.per_minute(Fraction(1)) + Quantity.per_cycle(Fraction(1))

    message = str(caught.value)
    assert UNIT_PER_MINUTE in message
    assert UNIT_PER_CYCLE in message


@pytest.mark.parametrize(
    "bare",
    [Fraction(3), 3, 0.5, True, None, "3"],
    ids=["fraction", "int", "float", "bool", "none", "str"],
)
def test_adding_a_bare_number_to_a_quantity_is_refused(bare: object) -> None:
    """A unit-less operand has no unit to match, so it is refused rather than assumed."""
    quantity = Quantity.per_minute(Fraction(3))

    with pytest.raises(UnitMismatchError):
        quantity + cast("Quantity", bare)
    with pytest.raises(UnitMismatchError):
        quantity - cast("Quantity", bare)


def test_a_bare_number_on_the_left_never_yields_a_quantity() -> None:
    """The reflected spelling must not silently coerce either: it raises, it never adds."""
    with pytest.raises(TypeError):
        Fraction(3) + Quantity.per_minute(Fraction(3))  # type: ignore[operator]


def test_the_unit_error_is_not_a_value_error_or_a_type_error() -> None:
    """Same reasoning as InexactValueError: the handler for bad text must not absorb it."""
    assert issubclass(UnitMismatchError, ExactArithmeticError)
    assert not issubclass(UnitMismatchError, ValueError)
    assert not issubclass(UnitMismatchError, TypeError)


# ===========================================================================
# Clause 2 - a per-cycle value fed where per-minute is expected is refused
# ===========================================================================


def test_expect_per_minute_hands_back_the_raw_fraction_of_a_per_minute_rate() -> None:
    """The accepting half of the gate a per-minute consumer calls."""
    raw = expect_per_minute(Quantity.per_minute(Fraction(90)))

    assert raw == Fraction(90)
    assert type(raw) is Fraction


def test_a_per_cycle_value_where_per_minute_is_expected_is_refused() -> None:
    """The measured defect: 3 per cycle read as 3 per minute is 30 times too small here."""
    with pytest.raises(UnitMismatchError, match=UNIT_PER_CYCLE):
        expect_per_minute(Quantity.per_cycle(Fraction(3)))


@pytest.mark.parametrize(
    "bare",
    [Fraction(90), 90, 90.0, None],
    ids=["fraction", "int", "float", "none"],
)
def test_a_bare_number_where_per_minute_is_expected_is_refused(bare: object) -> None:
    """A raw Fraction carries no unit, so a unit-tagged consumer cannot accept it."""
    with pytest.raises(UnitMismatchError):
        expect_per_minute(cast("Quantity", bare))


def test_a_per_cycle_value_converts_to_per_minute_only_through_its_duration() -> None:
    """The one sanctioned route: 3 per 2-second cycle is 90 per minute, exact."""
    converted = Quantity.per_cycle(Fraction(3)).to_per_minute(Fraction(2))

    assert converted == Quantity.per_minute(Fraction(90))
    assert type(converted.value) is Fraction
    assert expect_per_minute(converted) == Fraction(90)


def test_the_conversion_is_exact_where_a_float_route_would_drift() -> None:
    """1 per 3-second cycle is exactly 20 per minute, and 1 per 7 seconds is 60/7."""
    assert Quantity.per_cycle(Fraction(1)).to_per_minute(Fraction(3)).value == Fraction(20)
    seventh = Quantity.per_cycle(Fraction(1)).to_per_minute(Fraction(7)).value
    assert seventh == Fraction(60, 7)
    assert type(seventh) is Fraction


def test_converting_an_already_per_minute_rate_is_refused() -> None:
    """Converting twice is the same defect as never converting, so it is not idempotent."""
    with pytest.raises(UnitMismatchError, match=UNIT_PER_MINUTE):
        Quantity.per_minute(Fraction(90)).to_per_minute(Fraction(2))


def test_converting_over_a_zero_duration_is_undefined_not_unit_error() -> None:
    """per_minute's own refusal propagates; the registry keeps measured zeros."""
    with pytest.raises(UndefinedRateError):
        Quantity.per_cycle(Fraction(3)).to_per_minute(Fraction(0))


@pytest.mark.parametrize("duration", [Fraction(0), Fraction(-2), Fraction(-1, 3)])
def test_converting_over_a_non_positive_duration_is_refused(duration: Fraction) -> None:
    """A cycle takes positive time, so a negative duration is refused as zero is.

    ``per_minute`` alone would return a NEGATIVE rate for a negative duration: exact,
    finite and meaningless. The refusal names the positive-duration rule.
    """
    with pytest.raises(UndefinedRateError, match="positive"):
        Quantity.per_cycle(Fraction(3)).to_per_minute(duration)


def test_converting_over_a_float_duration_is_refused_before_it_poisons_the_rate() -> None:
    """``Fraction(60) / 0.5`` is a float; the conversion refuses its operand first."""
    with pytest.raises(InexactValueError):
        Quantity.per_cycle(Fraction(3)).to_per_minute(cast("Fraction", 0.5))


# ===========================================================================
# Construction - no float, no unit-less quantity
# ===========================================================================


@pytest.mark.parametrize(
    "bad",
    [0.5, 3, True, Decimal("0.5"), _LooseFraction(1, 2), "1/2", None],
    ids=["float", "int", "bool", "decimal", "fraction-subclass", "str", "none"],
)
def test_a_quantity_refuses_any_value_that_is_not_exactly_a_fraction(bad: object) -> None:
    """Identity, not isinstance: an int manufactures a float at the first division."""
    with pytest.raises(InexactValueError):
        Quantity(cast("Fraction", bad), UNIT_PER_MINUTE)
    with pytest.raises(InexactValueError):
        Quantity.per_minute(cast("Fraction", bad))
    with pytest.raises(InexactValueError):
        Quantity.per_cycle(cast("Fraction", bad))


@pytest.mark.parametrize("bad_unit", ["per_second", "", "PER_MINUTE", None, 1, b"per_minute"])
def test_a_quantity_refuses_a_unit_outside_the_closed_vocabulary(bad_unit: object) -> None:
    """A free-text unit would let one unit have two spellings that refuse each other."""
    with pytest.raises(UnitMismatchError):
        Quantity(Fraction(1), cast("str", bad_unit))


def test_a_str_subclass_equal_to_a_unit_name_is_refused() -> None:
    """Exact type, not isinstance, for the unit as for every other check in the module."""
    loose = _LooseStr(UNIT_PER_MINUTE)
    assert loose == UNIT_PER_MINUTE

    with pytest.raises(UnitMismatchError, match="_LooseStr"):
        Quantity(Fraction(1), loose)


def test_the_unit_vocabulary_is_exactly_the_two_published_units() -> None:
    """Pins the closed set and its spellings, so adding a unit is a deliberate edit."""
    assert sorted(UNITS) == ["per_cycle", "per_minute"]


# ===========================================================================
# Pins for the claims the module docstring makes
# ===========================================================================


def test_a_quantity_is_slotted_and_admitted_by_the_advice_trace_walker() -> None:
    """The docstring says a frozen slotted dataclass needs no allowlist entry; prove it.

    The walker admits a dataclass only while frozen, declaring ``__slots__`` itself, and
    with no instance ``__dict__``. Drop ``slots=True`` and all three fail at once.
    """
    quantity = Quantity.per_minute(Fraction(3))

    assert "__slots__" in Quantity.__dict__
    assert not hasattr(quantity, "__dict__")
    assert _inexact_reason(quantity) is None
    assert _inexact_reason((quantity, Quantity.per_cycle(Fraction(1, 3)))) is None


def test_a_quantity_subclass_is_refused_by_add_sub_and_expect_per_minute() -> None:
    """Exact type, not isinstance: a subclass may have overridden the unit rules.

    Refused as the operand and as the receiver is not needed: the receiver is a plain
    Quantity whose own methods run, so only the operand and the gate argument can be one.
    """
    plain = Quantity.per_minute(Fraction(3))
    sub = _SubQuantity(Fraction(3), UNIT_PER_MINUTE)

    with pytest.raises(UnitMismatchError, match="_SubQuantity"):
        plain + sub
    with pytest.raises(UnitMismatchError, match="_SubQuantity"):
        plain - sub
    with pytest.raises(UnitMismatchError, match="_SubQuantity"):
        expect_per_minute(sub)


# ===========================================================================
# Scaling, identity and the exactness audit
# ===========================================================================


def test_scaling_by_a_fraction_keeps_the_unit_and_stays_exact() -> None:
    """A machine count times a per-machine rate is the same unit, never a new one."""
    scaled = Quantity.per_minute(Fraction(30)).scaled(Fraction(5, 2))

    assert scaled == Quantity.per_minute(Fraction(75))
    assert type(scaled.value) is Fraction
    assert scaled.unit == UNIT_PER_MINUTE


@pytest.mark.parametrize("bad", [2, 2.5, True, Decimal(2), None], ids=str)
def test_scaling_by_anything_but_a_fraction_is_refused(bad: object) -> None:
    """A float factor converts the whole rate to a float with nothing raising."""
    with pytest.raises(InexactValueError):
        Quantity.per_minute(Fraction(30)).scaled(cast("Fraction", bad))


def test_equal_values_of_different_units_are_not_equal() -> None:
    """Equality includes the unit: the raw numbers agreeing is the trap, not the answer."""
    assert Quantity.per_minute(Fraction(3)) != Quantity.per_cycle(Fraction(3))
    assert Quantity.per_minute(Fraction(3)) == Quantity.per_minute(Fraction(3))


def test_a_quantity_is_immutable() -> None:
    """A rate that can be retagged in place defeats every refusal above."""
    quantity = Quantity.per_minute(Fraction(3))

    with pytest.raises(FrozenInstanceError):
        quantity.unit = UNIT_PER_CYCLE  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        quantity.value = Fraction(4)  # type: ignore[misc]


def test_audit_exact_admits_a_quantity_and_names_a_poisoned_leaf_inside_one() -> None:
    """A quantity travels inside plan objects, so the no-float audit must walk into it."""
    audit_exact(Quantity.per_minute(Fraction(3)), path="rate")

    poisoned = Quantity.per_minute(Fraction(3))
    object.__setattr__(poisoned, "value", 0.5)
    with pytest.raises(InexactValueError, match=r"rate\.value is float"):
        audit_exact(poisoned, path="rate")
