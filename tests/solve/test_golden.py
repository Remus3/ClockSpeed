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
- ``strategy.json``  CS-1244 clause 1. One score per named objective over four
  chains, and the strategy badge a plan earns against a named reference. The
  badge cases include the NON-MONOTONE one, which fails a lower rung and clears
  a higher one, because that is the case the ladder exists to describe.

A strategy case names its plan rather than restating the request that builds it:
a plan that already has a ratio golden is REFERENCED by that golden's name, so
the two corpora cannot drift apart on one request. A plan with no ratio golden
carries its own request block in exactly the shape :func:`_solve` consumes.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from fractions import Fraction
from pathlib import Path
from typing import Any

import pytest

from clockspeed.data.registry import Registry
from clockspeed.solve import optimize, power, ratio, strategy
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

_STRATEGY_FILE = "strategy.json"
_STRATEGY_CORPUS: dict[str, Any] = json.loads(
    (GOLDEN_DIR / _STRATEGY_FILE).read_text(encoding="ascii")
)

#: Every plan a strategy case may name, and how to build it. See the module
#: docstring for why a plan with a ratio golden is referenced rather than
#: restated.
STRATEGY_PLANS: Mapping[str, Mapping[str, Any]] = _STRATEGY_CORPUS["plans"]

STRATEGY_CASES: list[dict[str, Any]] = _STRATEGY_CORPUS["cases"]


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
# Strategy - the objective scores and the badge ladder
# ---------------------------------------------------------------------------

#: The weight every objective in this corpus is scored at. One, because a score
#: case grades ONE direction; a weighting would make the golden a statement
#: about the trade-off between directions instead.
STRATEGY_WEIGHT = Fraction(1)

#: The one-direction objective each named objective is graded through, built the
#: same way ``_REGISTRIES`` and ``_POLICIES`` above are keyed. A case naming
#: anything else raises rather than silently scoring something adjacent, and
#: ``test_the_strategy_corpus_can_score_every_modeled_objective`` pins the keys
#: against the shipped tuple so a fourth objective cannot arrive uncovered.
_STRATEGY_OBJECTIVES: Mapping[str, Callable[[], optimize.Objective]] = {
    optimize.OBJECTIVE_RAW: lambda: optimize.weighted_objective(raw=STRATEGY_WEIGHT),
    optimize.OBJECTIVE_BUILDINGS: lambda: optimize.weighted_objective(buildings=STRATEGY_WEIGHT),
    optimize.OBJECTIVE_POWER: lambda: optimize.weighted_objective(power=STRATEGY_WEIGHT),
}


def _strategy_plan(name: str) -> ratio.ProductionPlan:
    """Build one named strategy plan through the real solver.

    Args:
        name: The plan name, a key of the corpus ``plans`` table.

    Returns:
        The solved plan.
    """
    spec = STRATEGY_PLANS[name]
    golden = spec.get("ratio_golden")
    if golden is not None:
        return _solve(_ratio_by_name(golden))
    request: dict[str, Any] = dict(spec["request"])
    return _solve(request)


def _badge_is_non_monotone(case: Mapping[str, Any]) -> bool:
    """Say whether a badge case fails a lower rung and clears a higher one.

    Read off the GOLDEN rather than off a badge the code produced, so the
    property is a statement about the corpus and stays true of it without
    running the module under test.

    Args:
        case: A badge case.

    Returns:
        True when some rung is not cleared and some later rung is.
    """
    flags = [bool(check["cleared"]) for check in case["expected"]["checks"]]
    return any(not flags[index] and any(flags[index + 1 :]) for index in range(len(flags)))


def _strategy_cases_of(kind: str) -> list[dict[str, Any]]:
    """Select the strategy cases of one kind.

    Args:
        kind: ``score`` or ``badge``.

    Returns:
        Those cases, in file order.
    """
    return [case for case in STRATEGY_CASES if case["kind"] == kind]


@pytest.mark.parametrize("case", STRATEGY_CASES, ids=_ids(STRATEGY_CASES))
def test_strategy_golden(case: dict[str, Any]) -> None:
    registry = synthetic.solve_registry()
    expected = case["expected"]

    if case["kind"] == "score":
        objective = _STRATEGY_OBJECTIVES[case["objective"]]()
        score = optimize.score_plan(registry, _strategy_plan(case["plan"]), objective)
        _assert_exact(score, expected["score"], f"score[{case['objective']}]")
        return

    badge = strategy.badge_for(
        registry, _strategy_plan(case["plan"]), _strategy_plan(case["reference"])
    )
    assert badge.strongest == expected["strongest"]
    assert badge.cleared == tuple(expected["cleared"])
    assert [check.strategy for check in badge.checks] == [
        golden["strategy"] for golden in expected["checks"]
    ]
    for check, golden in zip(badge.checks, expected["checks"], strict=True):
        rung = golden["strategy"]
        cleared = check.cleared
        assert cleared is golden["cleared"], f"{rung}: cleared is {cleared}"
        reason = check.reason
        assert reason == golden["reason"], f"{rung}: reason is {reason}"
        _assert_exact(check.score, golden["score"], f"{rung}.score")
        _assert_exact(check.reference, golden["reference"], f"{rung}.reference")
        _assert_exact(check.bound, golden["bound"], f"{rung}.bound")


def test_the_strategy_ladder_order_is_the_order_every_badge_case_records() -> None:
    """A reorder of the shipped ladder reddens here rather than silently passing."""
    shipped = [rung.name for rung in strategy.STRATEGY_LADDER]
    for case in _strategy_cases_of("badge"):
        recorded = [golden["strategy"] for golden in case["expected"]["checks"]]
        assert recorded == shipped, case["name"]


def test_the_strategy_corpus_can_score_every_modeled_objective() -> None:
    """The objective table is keyed by the shipped tuple, not by a hand-kept list."""
    assert sorted(_STRATEGY_OBJECTIVES) == sorted(optimize.OBJECTIVES)


# ---------------------------------------------------------------------------
# The corpus itself
# ---------------------------------------------------------------------------


def _all_cases() -> list[dict[str, Any]]:
    return RATIO_CASES + CLOCK_CASES + POWER_CASES + STRATEGY_CASES


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
    for name, spec in STRATEGY_PLANS.items():
        golden = spec.get("ratio_golden")
        if golden is not None:
            assert golden in {case["name"] for case in RATIO_CASES}, name
            continue
        request = spec["request"]
        assert request["registry"] in _REGISTRIES, name
        assert set(request["recipes"]) <= _SYNTHETIC_RECIPES, name
        named_items = set(request["raw_items"]) | set(request.get("targets", {}))
        named_items |= set(request.get("supply", {}))
        if "target_item" in request:
            named_items.add(request["target_item"])
        assert named_items <= _SYNTHETIC_ITEMS, name
    for case in STRATEGY_CASES:
        assert case["plan"] in STRATEGY_PLANS, case["name"]
        if "reference" in case:
            assert case["reference"] in STRATEGY_PLANS, case["name"]


def test_the_corpus_covers_every_clause() -> None:
    """Both ratio directions, both clock kinds, and at least one deferred power answer."""
    assert {case["direction"] for case in RATIO_CASES} == {"targets", "supply"}
    assert {case["kind"] for case in CLOCK_CASES} == {"clamp", "ceiling"}
    deferred = [
        case for case in POWER_CASES if case["expected"].get("outcome") == power.OUTCOME_DEFERRED
    ]
    assert any(case["kind"] == "draw" for case in deferred)
    assert any(case["kind"] == "plan" for case in deferred)


def test_the_strategy_corpus_scores_every_named_objective() -> None:
    """CS-1244 clause 1: each named objective has golden cases, all three of them."""
    scored = {case["objective"] for case in _strategy_cases_of("score")}
    assert scored == set(optimize.OBJECTIVES)


def test_the_strategy_corpus_carries_a_non_monotone_badge() -> None:
    """Clearance across different objectives is not monotone, and a case proves it.

    Without such a case every badge golden would be satisfied by a
    longest-cleared-PREFIX reading of ``strongest`` as well as by the shipped
    highest-index one, and the corpus would grade the distinction the module
    docstring calls load-bearing not at all.
    """
    badges = _strategy_cases_of("badge")
    graded = [case["name"] for case in badges]
    non_monotone = [case["name"] for case in badges if _badge_is_non_monotone(case)]
    assert non_monotone, f"no badge case fails a lower rung and clears a higher one: {graded}"
    for name in non_monotone:
        (case,) = [entry for entry in badges if entry["name"] == name]
        flags = [bool(check["cleared"]) for check in case["expected"]["checks"]]
        highest = max(index for index, flag in enumerate(flags) if flag)
        strongest = case["expected"]["strongest"]
        assert strongest == case["expected"]["checks"][highest]["strategy"], name
