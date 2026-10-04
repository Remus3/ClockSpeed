"""CS-1239: the one display-rounding policy, pinned by golden parity cases.

The solve path is exact end to end and the wire carries rationals, so the ONLY
place a Fraction becomes a rounded decimal is the presentation edge. That edge
gets exactly one function, :func:`clockspeed.solve.exact.display_decimal`, and
its mode is pinned here two ways:

- **Parity.** Every case in ``tests/solve/golden/display.json`` is a hand-derived expected
  string, with every half-step boundary covered positive and negative.
- **The mode is load-bearing.** The same cases are re-run with the module's
  mode flipped to ROUND_HALF_UP, and the specific tie cases the golden marks as
  ``flips`` must then DISAGREE with it. A parity suite that still passed under a
  different mode would be pinning nothing.
"""

from __future__ import annotations

import decimal
import json
from decimal import Decimal
from fractions import Fraction
from pathlib import Path
from typing import Any

import pytest

from clockspeed.solve import exact as exact_module
from clockspeed.solve.exact import InexactValueError, display_decimal

GOLDEN = Path(__file__).resolve().parent / "golden" / "display.json"


def _cases() -> list[dict[str, Any]]:
    """Load the display goldens.

    Returns:
        The case list, in file order.
    """
    loaded: dict[str, Any] = json.loads(GOLDEN.read_text(encoding="ascii"))
    cases: list[dict[str, Any]] = loaded["cases"]
    return cases


_CASES = _cases()
_IDS = [case["name"] for case in _CASES]


def test_the_pinned_mode_is_half_even_in_the_stdlib_spelling() -> None:
    """The mode is named in decimal's own vocabulary, so no reader has to guess."""
    assert exact_module.DISPLAY_ROUNDING == decimal.ROUND_HALF_EVEN


@pytest.mark.parametrize("case", _CASES, ids=_IDS)
def test_display_matches_the_hand_derived_golden(case: dict[str, Any]) -> None:
    assert display_decimal(Fraction(case["value"]), case["places"]) == case["expected"]


@pytest.mark.parametrize("case", _CASES, ids=_IDS)
def test_flipping_the_mode_reddens_exactly_the_named_tie_cases(
    case: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Under ROUND_HALF_UP the flagged cases disagree with the golden; the rest agree.

    Both halves matter. Disagreement on the flagged cases proves the goldens
    discriminate between modes; agreement on the others proves the flip
    touched only ties, so the disagreement is the mode and nothing else.
    """
    monkeypatch.setattr(exact_module, "DISPLAY_ROUNDING", decimal.ROUND_HALF_UP)
    flipped = display_decimal(Fraction(case["value"]), case["places"])

    assert flipped == case["half_up"]
    if case["flips"]:
        assert flipped != case["expected"], case["name"]
    else:
        assert flipped == case["expected"], case["name"]


def test_the_flip_covers_both_signs_and_both_scales() -> None:
    """The flagged set is not a token: positive, negative, whole and fractional ties."""
    flagged = {case["name"] for case in _CASES if case["flips"]}
    assert {"half_at_0", "five_halves_at_0", "minus_five_halves_at_0", "eighth_at_2"} <= flagged
    assert any(case["value"].startswith("-") for case in _CASES if case["flips"])
    assert any(case["places"] > 0 for case in _CASES if case["flips"])


def test_a_mode_outside_the_policy_is_refused_rather_than_ignored(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(exact_module, "DISPLAY_ROUNDING", decimal.ROUND_CEILING)
    with pytest.raises(ValueError, match="ROUND_CEILING"):
        display_decimal(Fraction(1, 2), 0)


@pytest.mark.parametrize(
    "value",
    [0.5, 1, True, Decimal("0.5"), "1/2"],
    ids=["float", "int", "bool", "decimal", "str"],
)
def test_a_value_that_is_not_exactly_a_fraction_is_refused(value: object) -> None:
    """Refused the way to_exact refuses: a float rounded for display hides its drift."""
    with pytest.raises(InexactValueError):
        display_decimal(value, 2)  # type: ignore[arg-type]


@pytest.mark.parametrize("places", [True, 2.0, "2"], ids=["bool", "float", "str"])
def test_places_must_be_exactly_an_int(places: object) -> None:
    with pytest.raises(TypeError):
        display_decimal(Fraction(1, 3), places)  # type: ignore[arg-type]


def test_negative_places_are_refused() -> None:
    with pytest.raises(ValueError, match="places"):
        display_decimal(Fraction(1, 3), -1)


def test_the_result_is_a_plain_ascii_string() -> None:
    rendered = display_decimal(Fraction(-10, 3), 2)
    assert type(rendered) is str
    assert rendered.isascii()
