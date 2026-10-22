"""CS-1244 - the named strategy ladder: thresholds, badges and re-ranking.

Every plan here is built through ``solve_for_targets`` or ``solve_for_supply``,
the ordinary pillar 1 door, over the synthetic solve corpus. Nothing in this
module solves an OPTIMIZE request, because the subject does not either: the
ladder re-SCORES plans it did not choose, and that is the property the third
acceptance clause asks for.

THE DISCRIMINATING CASE IS THE FIRST ARM, and that ordering is deliberate. At
bound one, C5 against C3 gives FALSE, TRUE, TRUE across the three rungs. A
badge built as the longest cleared PREFIX reports nothing cleared on it; a
badge built as the highest-index cleared rung reports ``within-power``. The two
readings of the fourth acceptance clause differ on exactly this plan, so the
arm decides between them rather than demonstrating either.

THE FIGURES ARE RE-DERIVED FROM THE CORPUS CONSTANTS, never written as literals
here. ``tests/solve/synthetic.py`` publishes the ore demand, the machine counts
and the megawatts for each case, and every expectation below is assembled from
those names - so a corpus change moves the expectation with it instead of
leaving a stale number that still passes.

THE RE-SOLVE ARM IS OVER THE AST AND NOT OVER THE TEXT, for the reason
``tests/solve/test_phase3_gate.py`` states at length: the subject module's own
docstring NAMES the three functions it must never call, as the statement of the
property, and a text sweep would flag its own evidence. Under ``ast.parse`` a
docstring is one string constant and its contents are never identifiers.
"""

from __future__ import annotations

import ast
from dataclasses import replace
from fractions import Fraction
from pathlib import Path
from types import MappingProxyType
from typing import Any

import pytest

from clockspeed.data.registry import Registry
from clockspeed.solve import optimize, ratio, strategy
from clockspeed.solve.exact import InexactValueError, audit_exact
from clockspeed.solve.optimize import (
    OBJECTIVE_BUILDINGS,
    OBJECTIVE_POWER,
    OBJECTIVE_RAW,
    OBJECTIVES,
    Objective,
    ObjectiveUndefinedError,
    weighted_objective,
)
from clockspeed.solve.ratio import (
    BYPRODUCT_BALANCED,
    ProductionPlan,
    RatioRequest,
    SupplyRequest,
    solve_for_supply,
    solve_for_targets,
)
from clockspeed.solve.strategy import (
    NOT_CLEARED_OVER_BOUND,
    NOT_CLEARED_UNPRICEABLE,
    RUNG_WITHIN_BUILDINGS,
    RUNG_WITHIN_POWER,
    RUNG_WITHIN_RAW,
    STRATEGY_LADDER,
    Strategy,
    StrategyUndefinedError,
    badge_for,
    check_strategy,
    check_threshold,
    rank_plans,
)
from tests.data.synthetic import (
    KEY_CLASS_NAME,
    KEY_DISPLAY_NAME,
    KEY_DURATION,
    KEY_INGREDIENTS,
    KEY_PRODUCED_IN,
    KEY_PRODUCT,
    amount_blob,
    class_path_blob,
)
from tests.solve.synthetic import (
    C1_ORE_DEMAND,
    C1_PLATE_MACHINES,
    C1_POWER_MW,
    C1_ROD_MACHINES,
    C1_ROD_TARGET,
    C3_FLUID_MACHINES,
    C3_GADGET_MACHINES,
    C3_GADGET_TARGET,
    C3_ORE_DEMAND,
    C3_PLATE_MACHINES,
    C3_POWER_MW,
    C3_RECOVER_MACHINES,
    C4_ORE_CAP,
    C5_ORE_DEMAND,
    C5_POWER_MW,
    C5_STD_MACHINES,
    C5_TRINKET_TARGET,
    FLUID_RECIPE,
    GADGET_RECIPE,
    PLATE_RECIPE,
    RECOVER_RECIPE,
    ROD_RECIPE,
    SOLVE_GADGET_ITEM,
    SOLVE_ORE_ITEM,
    SOLVE_ROD_ITEM,
    SOLVE_TRINKET_ITEM,
    STD_GADGET_RECIPE,
    registry_with,
    solve_registry,
)

UNIT: Fraction = Fraction(1)

#: The C3 loop, as ``tests/solve/test_relax.py`` names it.
C3_LOOP: tuple[str, ...] = (GADGET_RECIPE, RECOVER_RECIPE, FLUID_RECIPE, PLATE_RECIPE)

#: The C1 chain.
C1_CHAIN: tuple[str, ...] = (PLATE_RECIPE, ROD_RECIPE)

#: A recipe produced in no building at all, which is the one shape the power
#: objective cannot price. Mirrors ``tests/solve/test_optimize.py``'s own
#: variant rather than importing it, so neither file's fixture can quietly
#: change what the other one measures.
NO_BUILDING_RECIPE: str = "R_NoBuildingForStrategy"

#: The rate the unpriceable chain is solved at.
NO_BUILDING_TARGET: Fraction = Fraction(30)

#: Its per-machine yield: one Rod per six-second cycle is ten a minute.
NO_BUILDING_PER_MACHINE: Fraction = Fraction(10)

#: The ladder as this module pins it: the rung, its objective and its bound.
#: Reordering :data:`STRATEGY_LADDER` reddens
#: :func:`test_the_ladder_order_is_one_pinned_table`; it also reddens
#: :func:`test_the_badge_records_the_strongest_rung_cleared_and_not_the_longest_prefix`,
#: whose whole point is which index the cleared rungs sit at.
EXPECTED_LADDER: tuple[tuple[str, str, Fraction], ...] = (
    (RUNG_WITHIN_RAW, OBJECTIVE_RAW, UNIT),
    (RUNG_WITHIN_BUILDINGS, OBJECTIVE_BUILDINGS, UNIT),
    (RUNG_WITHIN_POWER, OBJECTIVE_POWER, UNIT),
)

#: The three functions the subject must never reach. Named by identifier, and
#: the arm that uses them reads the subject's AST rather than its text.
FORBIDDEN_SOLVE_NAMES: frozenset[str] = frozenset(
    {"evaluate_selection", "optimize_plan", "solve_for_supply", "solve_for_targets"}
)

#: C1's total machine equivalents, assembled from the corpus rather than stated.
C1_MACHINES: Fraction = C1_ROD_MACHINES + C1_PLATE_MACHINES

#: The rate the C1 chain is solved at to obtain a plan scoring exactly zero on
#: every rung. Zero is a REQUESTED rate like any other and pillar 1 answers it
#: with a real plan - two steps at zero machines, no ore demanded - rather than
#: refusing it. It is the only shipped way to hand
#: :func:`~clockspeed.solve.strategy.check_threshold` a reference whose SCORE is
#: zero, which is where the product form and the quotient form diverge.
ZERO_RATE: Fraction = Fraction(0)

#: C3's, likewise - one published name per step of the loop.
C3_MACHINES: Fraction = (
    C3_GADGET_MACHINES + C3_RECOVER_MACHINES + C3_FLUID_MACHINES + C3_PLATE_MACHINES
)


class RefusedError(Exception):
    """Raised by a stand-in that must never be called."""


def _refuse(*_args: Any, **_kwargs: Any) -> ProductionPlan:
    """Stand in for a solve entry point and refuse to run.

    Args:
        *_args: Ignored.
        **_kwargs: Ignored.

    Returns:
        Never returns.

    Raises:
        RefusedError: Always.
    """
    raise RefusedError("the strategy ladder re-scores plans and must never reach a solve")


def _no_building_entry() -> dict[str, str]:
    """Build a recipe entry produced in no building, as docs text.

    One Ore to one Rod in six seconds, with an EMPTY produced-in blob - a real
    and valid value which the power objective has no draw for.

    Returns:
        The entry mapping, every value a string as in the real document.
    """
    return {
        KEY_CLASS_NAME: NO_BUILDING_RECIPE,
        KEY_DISPLAY_NAME: NO_BUILDING_RECIPE.removeprefix("R_"),
        KEY_DURATION: "6.000000",
        KEY_INGREDIENTS: amount_blob([(SOLVE_ORE_ITEM, 1)]),
        KEY_PRODUCT: amount_blob([(SOLVE_ROD_ITEM, 1)]),
        KEY_PRODUCED_IN: class_path_blob([]),
    }


@pytest.fixture(scope="module")
def registry() -> Registry:
    """Build the synthetic solve registry once for the module.

    Returns:
        The registry.
    """
    return solve_registry()


def _plan(built: Registry, item: str, rate: Fraction, recipes: tuple[str, ...]) -> ProductionPlan:
    """Solve one target rate through pillar 1's forward door.

    Args:
        built: The built registry.
        item: The target item key.
        rate: The requested net rate per minute.
        recipes: The selected recipe keys.

    Returns:
        The plan.
    """
    return solve_for_targets(
        built,
        RatioRequest(
            targets=MappingProxyType({item: rate}),
            recipes=recipes,
            raw_items=(SOLVE_ORE_ITEM,),
            byproduct_policy=BYPRODUCT_BALANCED,
        ),
    )


def _c1(built: Registry) -> ProductionPlan:
    """Build the C1 plan: 50 Rod/min through the plate chain.

    Args:
        built: The built registry.

    Returns:
        The plan.
    """
    return _plan(built, SOLVE_ROD_ITEM, C1_ROD_TARGET, C1_CHAIN)


def _c3(built: Registry) -> ProductionPlan:
    """Build the C3 plan: 20 Gadget/min through the balanced byproduct loop.

    Args:
        built: The built registry.

    Returns:
        The plan.
    """
    return _plan(built, SOLVE_GADGET_ITEM, C3_GADGET_TARGET, C3_LOOP)


def _c4(built: Registry) -> ProductionPlan:
    """Build the C4 plan: the same loop capped at 45 Ore/min of supply.

    Args:
        built: The built registry.

    Returns:
        The plan.
    """
    return solve_for_supply(
        built,
        SupplyRequest(
            supply=MappingProxyType({SOLVE_ORE_ITEM: C4_ORE_CAP}),
            target_item=SOLVE_GADGET_ITEM,
            recipes=C3_LOOP,
            raw_items=(SOLVE_ORE_ITEM,),
            byproduct_policy=BYPRODUCT_BALANCED,
        ),
    )


def _c5(built: Registry) -> ProductionPlan:
    """Build the C5 plan: 30 Trinket/min from the only feasible recipe.

    Args:
        built: The built registry.

    Returns:
        The plan.
    """
    return _plan(built, SOLVE_TRINKET_ITEM, C5_TRINKET_TARGET, (STD_GADGET_RECIPE,))


def _zero_rate(built: Registry) -> ProductionPlan:
    """Build the C1 chain at a requested rate of zero: a real, zero-scored plan.

    Through the same pillar 1 door as every other plan here, with no field
    assembled by hand - the steps are the chain's own, each at zero machines.

    Args:
        built: The built registry.

    Returns:
        The plan. Its score is exactly zero under every rung's objective, which
        :func:`test_the_zero_rate_plan_really_does_score_zero_on_every_rung`
        measures rather than assuming.
    """
    return _plan(built, SOLVE_ROD_ITEM, ZERO_RATE, C1_CHAIN)


def _corpus(built: Registry) -> tuple[ProductionPlan, ...]:
    """The four plans every ranking arm runs over, in a fixed input order.

    Args:
        built: The built registry.

    Returns:
        C1, C3, C4 and C5, in that order. The order is the CALLER's and is
        deliberately not any objective's, so a ranking that merely echoed its
        input would be visible.
    """
    return (_c1(built), _c3(built), _c4(built), _c5(built))


def _places(
    ranked: tuple[strategy.RankedPlan, ...], plans: tuple[ProductionPlan, ...]
) -> list[int]:
    """Map a ranking back onto its input positions, BY IDENTITY.

    Identity rather than equality is the point: it proves each published plan is
    the object that was handed in rather than an equal one rebuilt on the way
    through.

    Args:
        ranked: The ranking.
        plans: The input plans.

    Returns:
        One input index per ranked entry, best first.

    Raises:
        KeyError: A ranked plan is not one of the input objects.
    """
    handed_in = {id(plan): index for index, plan in enumerate(plans)}
    return [handed_in[id(entry.plan)] for entry in ranked]


# ---------------------------------------------------------------------------
# The badge rule - the clause 4 discriminator
# ---------------------------------------------------------------------------


def test_the_badge_records_the_strongest_rung_cleared_and_not_the_longest_prefix(
    registry: Registry,
) -> None:
    """C5 against C3 clears buildings and power but not raw, with a gap at rung 0.

    A longest-prefix badge reports ``strongest is None`` here, so this arm is
    what separates the two readings of the acceptance clause.
    """
    badge = badge_for(registry, _c5(registry), _c3(registry))

    assert badge.cleared == (RUNG_WITHIN_BUILDINGS, RUNG_WITHIN_POWER)
    assert badge.strongest == RUNG_WITHIN_POWER
    assert [check.cleared for check in badge.checks] == [False, True, True]
    assert badge.checks[0].reason == NOT_CLEARED_OVER_BOUND


def test_the_non_monotone_case_compares_the_hand_derived_figures(registry: Registry) -> None:
    """The three (plan, reference) pairs behind the badge above, as exact numbers."""
    checks = badge_for(registry, _c5(registry), _c3(registry)).checks
    measured = [(check.score, check.reference) for check in checks]

    assert measured == [
        (C5_ORE_DEMAND, C3_ORE_DEMAND),
        (C5_STD_MACHINES, C3_MACHINES),
        (C5_POWER_MW, C3_POWER_MW),
    ]
    for check in checks:
        assert type(check.score) is Fraction
        assert type(check.reference) is Fraction


@pytest.mark.parametrize(
    ("plan_of", "reference_of", "expected_cleared", "expected_strongest"),
    [
        (_c5, _c3, (RUNG_WITHIN_BUILDINGS, RUNG_WITHIN_POWER), RUNG_WITHIN_POWER),
        (_c3, _c5, (RUNG_WITHIN_RAW,), RUNG_WITHIN_RAW),
        (_c1, _c3, (RUNG_WITHIN_RAW, RUNG_WITHIN_BUILDINGS, RUNG_WITHIN_POWER), RUNG_WITHIN_POWER),
        (_c3, _c3, (RUNG_WITHIN_RAW, RUNG_WITHIN_BUILDINGS, RUNG_WITHIN_POWER), RUNG_WITHIN_POWER),
    ],
    ids=["c5-against-c3", "c3-against-c5", "c1-against-c3", "c3-against-itself"],
)
def test_the_badge_matches_the_hand_derived_ladder_on_each_pair(
    registry: Registry,
    plan_of: Any,
    reference_of: Any,
    expected_cleared: tuple[str, ...],
    expected_strongest: str,
) -> None:
    """Each pair's cleared set and strongest rung, derived by hand from the corpus."""
    badge = badge_for(registry, plan_of(registry), reference_of(registry))

    assert badge.cleared == expected_cleared
    assert badge.strongest == expected_strongest


def test_a_badge_always_carries_one_check_per_rung_in_ladder_order(registry: Registry) -> None:
    """A rung is never omitted, so a gap in the cleared set stays visible."""
    badge = badge_for(registry, _c5(registry), _c3(registry))

    assert len(badge.checks) == len(STRATEGY_LADDER)
    assert tuple(check.strategy for check in badge.checks) == tuple(
        rung.name for rung in STRATEGY_LADDER
    )


# ---------------------------------------------------------------------------
# The threshold is a PRODUCT and not a quotient - the zero-scored reference
# ---------------------------------------------------------------------------
#
# The subject's module docstring argues at length for
# ``score <= bound * reference`` over ``score / reference <= bound``, and point
# 1 names the consequence that separates them: "a reference score of zero
# clears only a plan score of zero, exactly and by itself". A zero reference
# score is the ONLY input domain on which the two spellings differ, so without
# an arm over it the quotient spelling passes every other arm in this file and
# the documented reason grades nothing. These arms grade the reason rather than
# the spelling: the quotient form cannot return either verdict below, because
# it raises ZeroDivisionError before reaching a comparison.


def test_the_zero_rate_plan_really_does_score_zero_on_every_rung(registry: Registry) -> None:
    """The anti-vacuity control for the two arms below.

    They are about a reference whose SCORE is zero, so an oracle that cannot
    see a zero score would pass them for the wrong reason. Measured here
    through the subject's own scoring path, and the plan is checked to carry
    real steps as well, so the fixture is a solved chain at zero rather than an
    empty plan with nothing in it to score.
    """
    plan = _zero_rate(registry)

    assert tuple(step.recipe_key for step in plan.steps) == C1_CHAIN
    assert all(step.machines == 0 for step in plan.steps)
    for rung in STRATEGY_LADDER:
        score = optimize.score_plan(
            registry,
            plan,
            Objective(weights=MappingProxyType({rung.objective_name: UNIT})),
        )
        assert type(score) is Fraction
        assert score == 0


@pytest.mark.parametrize("rung", STRATEGY_LADDER, ids=[rung.name for rung in STRATEGY_LADDER])
def test_a_zero_scored_reference_clears_a_zero_scored_plan(
    registry: Registry, rung: Strategy
) -> None:
    """Zero within bound times zero: cleared, with both numbers published as zero.

    The product form answers this by itself. The quotient form raises
    ZeroDivisionError on it instead of clearing it.
    """
    plan = _zero_rate(registry)

    check = check_threshold(registry, plan, plan, rung)

    assert check.cleared is True
    assert check.reason == ""
    assert check.score == 0
    assert check.reference == 0
    assert type(check.score) is Fraction
    assert type(check.reference) is Fraction


@pytest.mark.parametrize("rung", STRATEGY_LADDER, ids=[rung.name for rung in STRATEGY_LADDER])
def test_a_zero_scored_reference_clears_nothing_above_zero(
    registry: Registry, rung: Strategy
) -> None:
    """A strictly positive score against a zero reference does not clear, on any rung.

    The other half of the docstring's claim, and the half an ordinary bound
    cannot reach: with the reference at zero the bound is irrelevant and only a
    zero plan is within it. Again ZeroDivisionError under the quotient form.
    """
    reference = _zero_rate(registry)
    plan = _c1(registry)

    check = check_threshold(registry, plan, reference, rung)

    # Bound to a scalar before the comparison: the field is Fraction or None,
    # and the type-identity assertion is what narrows it for the type checker
    # as well as stating the exactness this suite requires everywhere else.
    score = check.score
    assert type(score) is Fraction
    assert score > 0
    assert check.reference == 0
    assert check.cleared is False
    assert check.reason == NOT_CLEARED_OVER_BOUND


def test_a_zero_scored_reference_earns_a_plan_above_zero_no_badge_at_all(
    registry: Registry,
) -> None:
    """The ladder's verdict on the pair, so the consequence is graded end to end."""
    reference = _zero_rate(registry)

    assert badge_for(registry, reference, reference).strongest == RUNG_WITHIN_POWER
    assert badge_for(registry, _c1(registry), reference).strongest is None


# ---------------------------------------------------------------------------
# The table
# ---------------------------------------------------------------------------


def test_the_ladder_order_is_one_pinned_table() -> None:
    """The rung names, their objectives and their bounds, in order, are the pin."""
    measured = tuple((rung.name, rung.objective_name, rung.bound) for rung in STRATEGY_LADDER)

    assert measured == EXPECTED_LADDER


def test_every_rung_names_a_real_objective_and_says_what_it_proves() -> None:
    """A rung's objective is one the optimizer models, and its claim is not empty."""
    for rung in STRATEGY_LADDER:
        assert rung.objective_name in OBJECTIVES
        assert rung.claims.strip()
        assert type(rung.bound) is Fraction


# ---------------------------------------------------------------------------
# Clause 3 - the objective moves the order and nothing else
# ---------------------------------------------------------------------------


def test_switching_the_objective_reorders_but_moves_no_plan_arithmetic(
    registry: Registry,
) -> None:
    """A raw ranking and a power ranking differ in ORDER over the same plan objects."""
    plans = _corpus(registry)

    by_raw = rank_plans(registry, plans, objective=weighted_objective(raw=UNIT))
    by_power = rank_plans(registry, plans, objective=weighted_objective(power=UNIT))

    raw_places = _places(by_raw, plans)
    power_places = _places(by_power, plans)

    assert raw_places != power_places
    assert sorted(raw_places) == sorted(power_places) == list(range(len(plans)))
    assert [entry.plan for entry in by_raw] == [plans[index] for index in raw_places]
    assert [entry.plan for entry in by_power] == [plans[index] for index in power_places]
    assert [entry.rank for entry in by_raw] == list(range(1, len(plans) + 1))


def test_the_ranking_order_is_the_hand_derived_one_under_each_objective(
    registry: Registry,
) -> None:
    """Raw, buildings and power each produce the order the corpus figures imply."""
    plans = _corpus(registry)

    assert _places(rank_plans(registry, plans, objective=weighted_objective(raw=UNIT)), plans) == [
        2,
        0,
        1,
        3,
    ]
    assert _places(
        rank_plans(registry, plans, objective=weighted_objective(power=UNIT)), plans
    ) == [0, 3, 2, 1]
    assert _places(
        rank_plans(registry, plans, objective=weighted_objective(buildings=UNIT)), plans
    ) == [3, 2, 0, 1]


def test_the_top_ranked_member_is_the_reference_every_badge_is_graded_against(
    registry: Registry,
) -> None:
    """The best plan clears every rung, because it is compared against itself."""
    plans = _corpus(registry)

    ranked = rank_plans(registry, plans, objective=weighted_objective(raw=UNIT))

    assert ranked[0].badge.cleared == tuple(rung.name for rung in STRATEGY_LADDER)
    assert ranked[0].badge == badge_for(registry, ranked[0].plan, ranked[0].plan)


def test_a_published_score_and_key_agree_with_the_optimizer(registry: Registry) -> None:
    """Each entry's score is ``score_plan``'s and its key is ``ranking_key``'s."""
    plans = _corpus(registry)
    objective = weighted_objective(raw=UNIT)
    positions = optimize.registry_positions(registry)

    for entry in rank_plans(registry, plans, objective=objective):
        selection = tuple(step.recipe_key for step in entry.plan.steps)
        assert entry.score == optimize.score_plan(registry, entry.plan, objective)
        assert entry.key == optimize.ranking_key(entry.score, selection, positions)


def test_ranking_nothing_publishes_nothing_rather_than_inventing_a_reference(
    registry: Registry,
) -> None:
    """An empty ranking has no top member, so there is no badge to fabricate."""
    assert rank_plans(registry, (), objective=weighted_objective(raw=UNIT)) == ()


# ---------------------------------------------------------------------------
# Re-scoring and never re-solving
# ---------------------------------------------------------------------------


def test_the_subject_module_names_no_solve_entry_point_at_all() -> None:
    """No identifier anywhere in ``strategy.py``'s AST is one of the three.

    Over the tree rather than over the text: the module docstring names all
    three in prose as the statement of the property, and a text sweep would
    flag its own evidence.
    """
    source = Path(strategy.__file__).read_text(encoding="ascii")
    tree = ast.parse(source)
    named = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            named.add(node.id)
        elif isinstance(node, ast.Attribute):
            named.add(node.attr)
        elif isinstance(node, ast.alias):
            named.add(node.name.rpartition(".")[2])

    assert not named & FORBIDDEN_SOLVE_NAMES
    assert "score_plan" in named


def test_ranking_reaches_no_solve_at_runtime_either(
    registry: Registry, monkeypatch: pytest.MonkeyPatch
) -> None:
    """With every solve entry point replaced by a refusal, a ranking still runs."""
    plans = _corpus(registry)
    objective = weighted_objective(raw=UNIT)

    monkeypatch.setattr(ratio, "solve_for_targets", _refuse)
    monkeypatch.setattr(ratio, "solve_for_supply", _refuse)
    monkeypatch.setattr(optimize, "solve_for_targets", _refuse)
    monkeypatch.setattr(optimize, "evaluate_selection", _refuse)
    monkeypatch.setattr(optimize, "optimize_plan", _refuse)

    ranked = rank_plans(registry, plans, objective=objective)

    assert len(ranked) == len(plans)
    assert [entry.plan for entry in ranked] == [plans[index] for index in _places(ranked, plans)]


def test_the_refusal_stand_in_actually_refuses() -> None:
    """The control for the arm above: a stand-in that never fired proves nothing."""
    with pytest.raises(RefusedError):
        _refuse()


# ---------------------------------------------------------------------------
# Non-negotiable 7 - flagged and skipped, and exactly one refusal absorbed
# ---------------------------------------------------------------------------


def test_an_unpriceable_power_term_is_flagged_and_does_not_poison_the_other_rungs() -> None:
    """A recipe produced in no building loses the power rung and keeps the rest."""
    built = registry_with(add=[_no_building_entry()])
    plan = _plan(built, SOLVE_ROD_ITEM, NO_BUILDING_TARGET, (NO_BUILDING_RECIPE,))

    badge = badge_for(built, plan, _c1(built))
    raw_check, buildings_check, power_check = badge.checks

    assert power_check.reason == NOT_CLEARED_UNPRICEABLE
    assert power_check.score is None
    assert power_check.reference is None
    assert power_check.cleared is False
    assert raw_check.score == NO_BUILDING_TARGET
    assert raw_check.reference == C1_ORE_DEMAND
    assert buildings_check.score == NO_BUILDING_TARGET / NO_BUILDING_PER_MACHINE
    assert buildings_check.reference == C1_MACHINES
    assert type(raw_check.score) is Fraction
    assert type(buildings_check.score) is Fraction
    assert badge.cleared == (RUNG_WITHIN_RAW, RUNG_WITHIN_BUILDINGS)
    assert badge.strongest == RUNG_WITHIN_BUILDINGS


def test_an_unpriceable_reference_loses_the_power_rung_too() -> None:
    """The comparison has no exact value whichever side cannot be priced."""
    built = registry_with(add=[_no_building_entry()])
    unpriceable = _plan(built, SOLVE_ROD_ITEM, NO_BUILDING_TARGET, (NO_BUILDING_RECIPE,))

    power_check = badge_for(built, _c1(built), unpriceable).checks[2]

    assert power_check.reason == NOT_CLEARED_UNPRICEABLE
    assert power_check.score is None


def test_the_power_rung_clears_normally_when_both_sides_are_priceable() -> None:
    """The control for the two arms above: the same rung does clear on the corpus."""
    built = solve_registry()

    power_check = badge_for(built, _c1(built), _c3(built)).checks[2]

    assert power_check.cleared is True
    assert power_check.score == C1_POWER_MW
    assert power_check.reference == C3_POWER_MW


def test_a_malformed_objective_is_not_absorbed_as_a_failed_threshold(
    registry: Registry,
) -> None:
    """``ObjectiveUndefinedError`` propagates: a typo is not a threshold verdict."""
    unmodeled = Objective(weights=MappingProxyType({"minimize-belts": UNIT}))

    with pytest.raises(ObjectiveUndefinedError):
        rank_plans(registry, _corpus(registry), objective=unmodeled)


def test_an_objective_with_no_weights_at_all_propagates_too(registry: Registry) -> None:
    """The other shape of the same refusal, on the same route."""
    empty = Objective(weights=MappingProxyType({}))

    with pytest.raises(ObjectiveUndefinedError):
        rank_plans(registry, _corpus(registry), objective=empty)


# ---------------------------------------------------------------------------
# A rung that states no evaluable threshold
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "bound",
    [Fraction(1, 2), Fraction(0), Fraction(-1)],
    ids=["half", "zero", "negative"],
)
def test_a_bound_below_one_is_refused(bound: Fraction) -> None:
    """Below one asks the plan to BEAT the reference, which is a different claim."""
    with pytest.raises(StrategyUndefinedError):
        check_strategy(replace(STRATEGY_LADDER[0], bound=bound))


@pytest.mark.parametrize("bound", [1, True, "1"], ids=["int", "bool", "str"])
def test_a_bound_that_is_not_exactly_a_fraction_is_refused(bound: Any) -> None:
    """Type IDENTITY, not isinstance: an int is exact and still manufactures a float.

    ``isinstance(True, int)`` is True, so the bool case is the one an
    isinstance check would wave through.
    """
    with pytest.raises(StrategyUndefinedError):
        check_strategy(replace(STRATEGY_LADDER[0], bound=bound))


def test_a_rung_naming_an_objective_outside_the_modelled_set_is_refused() -> None:
    """An unmodelled direction has no arithmetic to grade a plan with."""
    rung = Strategy(
        name="within-belts",
        objective_name="belts",
        bound=UNIT,
        claims="nothing, because this objective does not exist",
    )

    with pytest.raises(StrategyUndefinedError):
        check_strategy(rung)


def test_the_rung_check_is_applied_at_the_point_of_use(registry: Registry) -> None:
    """A hand-assembled rung cannot reach the arithmetic unchecked."""
    with pytest.raises(StrategyUndefinedError):
        check_threshold(
            registry,
            _c5(registry),
            _c3(registry),
            replace(STRATEGY_LADDER[0], bound=Fraction(1, 2)),
        )


def test_a_bound_above_one_widens_the_rung_rather_than_being_refused(
    registry: Registry,
) -> None:
    """The control: the bound is a real multiplier, not a constant in disguise.

    C5 fails ``within-raw`` against C3 at bound one and clears it at bound two,
    which is what makes the product form load-bearing rather than decorative.
    """
    plan = _c5(registry)
    reference = _c3(registry)
    widened = replace(STRATEGY_LADDER[0], bound=Fraction(2))

    assert check_threshold(registry, plan, reference, STRATEGY_LADDER[0]).cleared is False
    assert check_threshold(registry, plan, reference, widened).cleared is True


# ---------------------------------------------------------------------------
# Determinism and exactness
# ---------------------------------------------------------------------------


def _cases(built: Registry) -> tuple[Any, ...]:
    """Every published structure this module grades, in one value.

    Args:
        built: The built registry.

    Returns:
        The badges for each hand-derived pair and the rankings under each of
        the three single objectives.
    """
    plans = _corpus(built)
    badges = tuple(badge_for(built, plan, plans[0]) for plan in plans)
    rankings = tuple(
        rank_plans(built, plans, objective=objective)
        for objective in (
            weighted_objective(raw=UNIT),
            weighted_objective(buildings=UNIT),
            weighted_objective(power=UNIT),
        )
    )
    return (badges, rankings)


def test_two_runs_agree(registry: Registry) -> None:
    """Two runs on the same inputs produce equal values with identical reprs."""
    first = _cases(registry)
    second = _cases(registry)

    assert first == second
    assert repr(first) == repr(second)


def test_a_permuted_input_names_the_same_winner(registry: Registry) -> None:
    """The ranking takes its order from the arithmetic, never from the caller."""
    plans = _corpus(registry)
    objective = weighted_objective(raw=UNIT)

    forwards = rank_plans(registry, plans, objective=objective)
    backwards = rank_plans(registry, tuple(reversed(plans)), objective=objective)

    assert [entry.plan for entry in forwards] == [entry.plan for entry in backwards]
    assert [entry.key for entry in forwards] == [entry.key for entry in backwards]


def test_every_numeric_leaf_is_an_exact_fraction(registry: Registry) -> None:
    """``audit_exact`` passes over every badge and every ranking this module builds."""
    badges, rankings = _cases(registry)

    for index, badge in enumerate(badges):
        audit_exact(badge, path=f"badge[{index}]")
    for index, ranking in enumerate(rankings):
        audit_exact(ranking, path=f"ranking[{index}]")


def test_the_exactness_audit_can_still_see_an_inexact_leaf() -> None:
    """The control for the arm above: an audit that reads nothing passes too."""
    planted = replace(STRATEGY_LADDER[0], claims="planted")

    audit_exact(planted, path="planted")

    with pytest.raises(InexactValueError, match="does not admit"):
        audit_exact((UNIT, "ok", object()), path="planted")
