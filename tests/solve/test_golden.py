"""CS-1239: the golden-case corpus for the solve path, exact values only.

Each JSON file under ``golden/`` names a chain of the synthetic solve corpus
(``tests/solve/synthetic.py``, built through the real docs seam) and records the
HAND-DERIVED outputs as fraction strings, with the derivation in each case's
``why``. Nothing here was produced by running the code and pasting its output -
a golden made that way agrees with the implementation by construction and can
never catch it.

Every numeric output is asserted two ways, because ``==`` alone is not evidence
of exactness (``Fraction(1, 2) == 0.5`` is True): ``type(x) is Fraction`` and
then equality with the golden. A golden ``null`` is asserted as ``is None``, so
an absent number can never pass as a zero.

- ``ratio.json``  forwards (targets) and backwards (supply) ratio solves, plus
  the named refusals.
- ``clock.json``  the clamp to the un-sharded base and the unknown ceiling.
- ``power.json``  draws at a clock, the bounded-draw refusal, and plan power
  totals. Away from the reference clock the answer is DEFERRED - an exact
  coefficient beside a symbolic ``clock ** exponent`` term - and the golden
  records that outcome, never a number.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from fractions import Fraction
from pathlib import Path
from typing import Any

import pytest

from clockspeed.data.registry import Registry
from clockspeed.solve import power, ratio
from clockspeed.solve.exact import DeferredPowerTerm, to_exact
from tests.solve import synthetic

GOLDEN_DIR = Path(__file__).resolve().parent / "golden"

_REGISTRIES: Mapping[str, Callable[[], Registry]] = {
    "main": synthetic.solve_registry,
    "rich_recovery": synthetic.rich_recovery_registry,
}

_POLICIES: Mapping[str, str] = {
    "balanced": ratio.BYPRODUCT_BALANCED,
    "sinkable": ratio.BYPRODUCT_SINKABLE,
}

#: Every name a golden may use. Synthetic only - the corpus must never carry a
#: real game content name, and a name outside these sets fails the meta test.
_SYNTHETIC_RECIPES = frozenset(synthetic.SOLVE_RECIPES) | {synthetic.RICH_RECOVER_RECIPE}
_SYNTHETIC_ITEMS = (
    synthetic.SOLVE_PRODUCED
    | synthetic.SOLVE_RAW_ITEMS
    | {
        synthetic.SOLVE_RARE_ITEM,
        synthetic.SOLVE_ORPHAN_ITEM,
    }
)
_SYNTHETIC_BUILDINGS = frozenset(synthetic.SOLVE_BUILDINGS)


def _load(name: str) -> list[dict[str, Any]]:
    """Load one golden file's case list.

    Args:
        name: The file name under ``golden/``.

    Returns:
        The cases, in file order.
    """
    loaded: dict[str, Any] = json.loads((GOLDEN_DIR / name).read_text(encoding="ascii"))
    cases: list[dict[str, Any]] = loaded["cases"]
    return cases


RATIO_CASES = _load("ratio.json")
CLOCK_CASES = _load("clock.json")
POWER_CASES = _load("power.json")


def _ids(cases: list[dict[str, Any]]) -> list[str]:
    return [case["name"] for case in cases]


def _assert_exact(actual: object, golden: str | None, where: str) -> None:
    """Assert one output is exactly a Fraction equal to the golden, or absent.

    Args:
        actual: The value the code returned.
        golden: The hand-derived fraction string, or None for "no number".
        where: How to name the value in a failure.
    """
    if golden is None:
        assert actual is None, f"{where}: expected no number, got {actual!r}"
        return
    assert type(actual) is Fraction, (
        f"{where}: {type(actual).__name__} {actual!r} is not a Fraction"
    )
    assert actual == Fraction(golden), f"{where}: {actual} != golden {golden}"


def _assert_exact_mapping(
    actual: Mapping[str, Fraction], golden: Mapping[str, str], where: str
) -> None:
    assert sorted(actual) == sorted(golden), f"{where}: keys {sorted(actual)} != {sorted(golden)}"
    for key, text in golden.items():
        _assert_exact(actual[key], text, f"{where}[{key}]")


# ---------------------------------------------------------------------------
# Ratio
# ---------------------------------------------------------------------------


def _solve(case: dict[str, Any]) -> ratio.ProductionPlan:
    """Run one ratio golden through the real solver.

    Args:
        case: The golden case.

    Returns:
        The plan.
    """
    registry = _REGISTRIES[case["registry"]]()
    recipes = tuple(case["recipes"])
    raw_items = tuple(case["raw_items"])
    policy = _POLICIES[case["policy"]]
    if case["direction"] == "targets":
        return ratio.solve_for_targets(
            registry,
            ratio.RatioRequest(
                targets={item: to_exact(rate) for item, rate in case["targets"].items()},
                recipes=recipes,
                raw_items=raw_items,
                byproduct_policy=policy,
            ),
        )
    return ratio.solve_for_supply(
        registry,
        ratio.SupplyRequest(
            supply={item: to_exact(rate) for item, rate in case["supply"].items()},
            target_item=case["target_item"],
            recipes=recipes,
            raw_items=raw_items,
            byproduct_policy=policy,
        ),
    )


def _ratio_by_name(name: str) -> dict[str, Any]:
    (case,) = [case for case in RATIO_CASES if case["name"] == name]
    return case


@pytest.mark.parametrize("case", RATIO_CASES, ids=_ids(RATIO_CASES))
def test_ratio_golden(case: dict[str, Any]) -> None:
    if "raises" in case:
        refusal = case["raises"]
        with pytest.raises(getattr(ratio, refusal["type"])) as caught:
            _solve(case)
        assert type(caught.value).__name__ == refusal["type"]
        if "recipe" in refusal:
            assert caught.value.recipe == refusal["recipe"]
        if "machines" in refusal:
            _assert_exact(caught.value.machines, refusal["machines"], "raises.machines")
        if "item" in refusal:
            assert caught.value.item == refusal["item"]
        return

    plan = _solve(case)
    expected = case["expected"]

    assert [step.recipe_key for step in plan.steps] == [key for key, _ in expected["steps"]]
    for step, (key, machines) in zip(plan.steps, expected["steps"], strict=True):
        _assert_exact(step.machines, machines, f"steps[{key}]")
    _assert_exact_mapping(plan.targets, expected["targets"], "targets")
    _assert_exact_mapping(plan.raw_inputs, expected["raw_inputs"], "raw_inputs")
    _assert_exact_mapping(plan.byproducts, expected["byproducts"], "byproducts")


# ---------------------------------------------------------------------------
# Clock
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("case", CLOCK_CASES, ids=_ids(CLOCK_CASES))
def test_clock_golden(case: dict[str, Any]) -> None:
    building = synthetic.solve_registry().buildings[case["building"]]
    expected = case["expected"]

    if case["kind"] == "clamp":
        clamped = power.clamp_to_unsharded_base(building, to_exact(case["clock"]))
        _assert_exact(clamped.clock, expected["clock"], "clock")
        _assert_exact(clamped.base, expected["base"], "base")
        assert clamped.clamped is expected["clamped"]
        return

    ceiling = power.clock_ceiling(building)
    _assert_exact(ceiling.base, expected["base"], "base")
    assert ceiling.slots == expected["slots"]
    assert ceiling.known is expected["known"]


# ---------------------------------------------------------------------------
# Power
# ---------------------------------------------------------------------------


def _assert_deferred(term: DeferredPowerTerm | None, expected: dict[str, Any]) -> None:
    if expected["base"] is None:
        assert term is None, f"expected no deferred term, got {term!r}"
        return
    assert type(term) is DeferredPowerTerm
    _assert_exact(term.base, expected["base"], "deferred.base")
    _assert_exact(term.exponent, expected["exponent"], "deferred.exponent")


def _plan_power(case: dict[str, Any]) -> tuple[str, Fraction, DeferredPowerTerm | None]:
    """Total a golden plan's draw at one clock, keeping a deferred term symbolic.

    Every step must come back with the SAME outcome, and when deferred, the
    same symbolic term, so the exact coefficients add. A plan whose steps
    defer to different terms has no single total, and this refuses it.

    Args:
        case: The power golden, naming a ratio golden as its plan.

    Returns:
        The common outcome, the exact total (megawatts or coefficient), and the
        common deferred term or None.
    """
    registry = synthetic.solve_registry()
    plan = _solve(_ratio_by_name(case["plan"]))
    clock = to_exact(case["clock"])
    outcomes: set[str] = set()
    terms: set[DeferredPowerTerm | None] = set()
    total = Fraction(0)
    for step in plan.steps:
        (building,) = registry.recipes[step.recipe_key].produced_in
        draw = power.draw_at_clock(registry.buildings[building], clock)
        outcomes.add(draw.outcome)
        terms.add(draw.deferred)
        number = draw.megawatts if draw.outcome == power.OUTCOME_EXACT else draw.coefficient
        assert type(number) is Fraction, f"{step.recipe_key}: {number!r}"
        total += step.machines * number
    assert len(outcomes) == 1, outcomes
    assert len(terms) == 1, terms
    return outcomes.pop(), total, terms.pop()


@pytest.mark.parametrize("case", POWER_CASES, ids=_ids(POWER_CASES))
def test_power_golden(case: dict[str, Any]) -> None:
    expected = case["expected"]

    if case["kind"] == "draw":
        building = synthetic.solve_registry().buildings[case["building"]]
        draw = power.draw_at_clock(building, to_exact(case["clock"]))
        assert draw.outcome == expected["outcome"]
        _assert_exact(draw.megawatts, expected["megawatts"], "megawatts")
        _assert_exact(draw.coefficient, expected["coefficient"], "coefficient")
        _assert_deferred(draw.deferred, expected)
        return

    if case["kind"] == "bounded":
        building = synthetic.solve_registry().buildings[case["building"]]
        bounded = power.bounded_draw(building)
        assert bounded.shape == expected["shape"]
        assert bounded.modeled is expected["modeled"]
        assert bounded.source == expected["source"]
        _assert_exact(bounded.minimum, expected["minimum"], "minimum")
        _assert_exact(bounded.maximum, expected["maximum"], "maximum")
        return

    outcome, total, term = _plan_power(case)
    assert outcome == expected["outcome"]
    if outcome == power.OUTCOME_EXACT:
        _assert_exact(total, expected["megawatts"], "plan megawatts")
        assert expected["coefficient"] is None
    else:
        _assert_exact(total, expected["coefficient"], "plan coefficient")
        assert expected["megawatts"] is None
    _assert_deferred(term, expected)


# ---------------------------------------------------------------------------
# The corpus itself
# ---------------------------------------------------------------------------


def _all_cases() -> list[dict[str, Any]]:
    return RATIO_CASES + CLOCK_CASES + POWER_CASES


@pytest.mark.parametrize(
    ("actual", "golden"),
    [(0.5, "1/2"), (2, "2"), (True, "1"), (None, "0"), (Fraction(0), None)],
    ids=["float", "int", "bool", "none-for-zero", "zero-for-none"],
)
def test_the_exactness_check_refuses_an_equal_value_of_the_wrong_type(
    actual: object, golden: str | None
) -> None:
    """``0.5 == Fraction(1, 2)`` is True, so equality alone would pass a float."""
    with pytest.raises(AssertionError):
        _assert_exact(actual, golden, "probe")


def test_every_golden_records_its_hand_derivation() -> None:
    missing = [case["name"] for case in _all_cases() if not case.get("why", "").strip()]
    assert not missing, f"goldens with no recorded derivation: {missing}"


def test_golden_names_are_unique() -> None:
    names = [case["name"] for case in _all_cases()]
    assert len(names) == len(set(names))


def test_the_corpus_names_only_synthetic_content() -> None:
    """Every recipe, item and building a golden names is from the synthetic corpus."""
    for case in RATIO_CASES:
        assert set(case["recipes"]) <= _SYNTHETIC_RECIPES, case["name"]
        named_items = set(case["raw_items"]) | set(case.get("targets", {}))
        named_items |= set(case.get("supply", {})) | {
            case.get("target_item", synthetic.SOLVE_ORE_ITEM)
        }
        if "expected" in case:
            for field in ("targets", "raw_inputs", "byproducts"):
                named_items |= set(case["expected"][field])
        assert named_items <= _SYNTHETIC_ITEMS, case["name"]
    for case in CLOCK_CASES + POWER_CASES:
        if "building" in case:
            assert case["building"] in _SYNTHETIC_BUILDINGS, case["name"]


def test_the_corpus_covers_every_clause() -> None:
    """Both ratio directions, both clock kinds, and at least one deferred power answer."""
    assert {case["direction"] for case in RATIO_CASES} == {"targets", "supply"}
    assert {case["kind"] for case in CLOCK_CASES} == {"clamp", "ceiling"}
    deferred = [
        case for case in POWER_CASES if case["expected"].get("outcome") == power.OUTCOME_DEFERRED
    ]
    assert any(case["kind"] == "draw" for case in deferred)
    assert any(case["kind"] == "plan" for case in deferred)
