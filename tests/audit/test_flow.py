"""CS-1235: the nominal item flow of a built world, per item, exact.

Every recipe here comes from the hand-authored synthetic SOLVER corpus,
``tests/solve/synthetic.py``, built through the real ``docs_extract`` and
``build_registry`` seam. Every machine is a synthetic ``MachineState`` literal
authored in this module. Nothing opens a save, a docs file or the install.

THE RATES ARE RE-DERIVED HERE FROM THE CORPUS CONSTANTS, never read back out
of the module under test: R_Plate turns one ore into one plate every
``PLATE_DURATION_S`` seconds, so one machine at clock one moves
``60 / PLATE_DURATION_S`` of each per minute.

THE CONFIDENT ZERO IS THE DEFECT GRADED HARDEST. A machine whose recipe the
mapping does not carry, or whose clock never read, contributes NOTHING to any
item - and an implementation that read the absent clock as one, or dropped the
unknown machine without trace, would publish a flow that looks measured and is
not. Each such machine lands in a NAMED gap with a count and a WARN code, and
the buckets conserve against the population.
"""

from __future__ import annotations

from fractions import Fraction
from typing import cast

import pytest

from clockspeed.audit import flow
from clockspeed.audit.machines import MachineState, WorldMachines
from clockspeed.data.registry import Recipe
from clockspeed.solve import exact
from tests.solve import synthetic

_SMELTER = synthetic.SOLVE_SMELTER_BUILDING
_PLATE = synthetic.SOLVE_PLATE_ITEM
_ROD = synthetic.SOLVE_ROD_ITEM
_ORE = synthetic.SOLVE_ORE_ITEM

#: One R_Plate machine at clock one, per minute - derived from the corpus.
_PLATE_RATE = Fraction(synthetic.SECONDS_PER_MINUTE) / synthetic.PLATE_DURATION_S
#: One R_Rod machine at clock one, per minute.
_ROD_RATE = Fraction(synthetic.SECONDS_PER_MINUTE) / synthetic.ROD_DURATION_S

_UNKNOWN_RECIPE = "R_SolveNeverAuthored"

_ZERO = Fraction(0)

#: Machine counts used by more than one arm.
_FOUR = 4
_TWO = 2


@pytest.fixture(name="recipes", scope="module")
def recipes_fixture() -> dict[str, Recipe]:
    """The corpus recipes, keyed by class name the way a caller supplies them.

    Returns:
        A plain dict, so the module under test is shown to need only a Mapping.
    """
    return dict(synthetic.solve_registry().recipes)


def _machine(recipe: str | None, clock: Fraction | None = Fraction(1)) -> MachineState:
    """Build one synthetic machine.

    Args:
        recipe: The recipe class name, or None for an unconfigured machine.
        clock: The overclock, or None for an unread one.

    Returns:
        The state. Producing is True throughout: the flow is NOMINAL and must
        not depend on it, which ``test_the_producing_flag_does_not_move_the_flow``
        grades separately.
    """
    return MachineState(
        class_name=_SMELTER, producing=True, recipe_class_name=recipe, overclock=clock
    )


def _world(states: list[MachineState]) -> WorldMachines:
    """Wrap states in a machines model, the shape ``machines_of`` publishes.

    Args:
        states: The machines.

    Returns:
        The model.
    """
    return WorldMachines(
        machines=tuple(states),
        producing_available=True,
        recipe_available=True,
        overclock_available=True,
        records_considered=len(states),
        unread_payload_count=0,
        refused_overclock_count=0,
        refused_recipe_count=0,
        warnings=(),
    )


def _codes(result: flow.WorldFlow) -> dict[str, int]:
    """Map each raised warning code to its count.

    Args:
        result: The flow.

    Returns:
        Code to count.
    """
    return {warning.code: warning.count for warning in result.warnings}


# ---------------------------------------------------------------------------
# The arithmetic
# ---------------------------------------------------------------------------


def test_one_machine_at_clock_one_moves_its_recipe_rate(recipes: dict[str, Recipe]) -> None:
    result = flow.flow_of([_machine(synthetic.PLATE_RECIPE)], recipes)
    plate = result.items[_PLATE]
    ore = result.items[_ORE]
    assert (plate.produced, plate.consumed, plate.net) == (_PLATE_RATE, _ZERO, _PLATE_RATE)
    assert (ore.produced, ore.consumed, ore.net) == (_ZERO, _PLATE_RATE, -_PLATE_RATE)


def test_the_rate_is_linear_in_the_clock_and_exact(recipes: dict[str, Recipe]) -> None:
    # 5/6 is a clock no float holds; 25 per minute is the exact answer.
    clock = Fraction(5, 6)
    result = flow.flow_of([_machine(synthetic.PLATE_RECIPE, clock)], recipes)
    assert result.items[_PLATE].net == _PLATE_RATE * clock
    assert type(result.items[_PLATE].net) is Fraction


def test_machines_on_one_recipe_sum_into_one_group(recipes: dict[str, Recipe]) -> None:
    states = [_machine(synthetic.ROD_RECIPE, Fraction(5, 6)) for _ in range(_FOUR)]
    result = flow.flow_of(states, recipes)
    assert len(result.groups) == 1
    group = result.groups[0]
    assert group.recipe_class_name == synthetic.ROD_RECIPE
    assert group.machine_count == _FOUR
    assert group.machine_equivalents == Fraction(10, 3)
    assert result.items[_ROD].net == _ROD_RATE * Fraction(10, 3)


def test_a_world_machines_model_and_its_sequence_agree(recipes: dict[str, Recipe]) -> None:
    states = [_machine(synthetic.PLATE_RECIPE), _machine(synthetic.ROD_RECIPE)]
    assert flow.flow_of(states, recipes) == flow.flow_of(_world(states), recipes)


def test_the_producing_flag_does_not_move_the_flow(recipes: dict[str, Recipe]) -> None:
    running = _machine(synthetic.PLATE_RECIPE)
    idle = MachineState(
        class_name=_SMELTER,
        producing=False,
        recipe_class_name=synthetic.PLATE_RECIPE,
        overclock=Fraction(1),
    )
    assert flow.flow_of([running], recipes).items == flow.flow_of([idle], recipes).items


# ---------------------------------------------------------------------------
# Deficit, surplus, raw and demand
# ---------------------------------------------------------------------------


def test_an_unmet_intermediate_is_a_deficit_naming_both_sides(
    recipes: dict[str, Recipe],
) -> None:
    # One plate machine makes 30; three rod machines eat 45. Plate is short 15.
    states = [_machine(synthetic.PLATE_RECIPE)] + [_machine(synthetic.ROD_RECIPE) for _ in range(3)]
    result = flow.flow_of(states, recipes, raw_items=synthetic.SOLVE_RAW_ITEMS)
    assert [item.item_key for item in result.deficits] == [_PLATE]
    deficit = result.deficits[0]
    assert deficit.net == _PLATE_RATE - 3 * _ROD_RATE
    assert deficit.shortfall == 3 * _ROD_RATE - _PLATE_RATE
    assert deficit.producers == (synthetic.PLATE_RECIPE,)
    assert deficit.consumers == (synthetic.ROD_RECIPE,)


def test_raw_consumption_is_never_a_deficit(recipes: dict[str, Recipe]) -> None:
    result = flow.flow_of(
        [_machine(synthetic.PLATE_RECIPE)], recipes, raw_items=synthetic.SOLVE_RAW_ITEMS
    )
    assert result.items[_ORE].raw is True
    assert result.items[_ORE].net == -_PLATE_RATE
    assert _ORE not in [item.item_key for item in result.deficits]


def test_the_same_consumption_undeclared_raw_is_a_deficit(recipes: dict[str, Recipe]) -> None:
    # The control for the arm above: without the raw declaration the ore IS short.
    result = flow.flow_of([_machine(synthetic.PLATE_RECIPE)], recipes)
    assert [item.item_key for item in result.deficits] == [_ORE]
    assert result.deficits[0].producers == ()


def test_a_demand_above_the_net_is_a_deficit_and_below_it_a_surplus(
    recipes: dict[str, Recipe],
) -> None:
    states = [_machine(synthetic.PLATE_RECIPE)]
    short = flow.flow_of(
        states, recipes, raw_items=synthetic.SOLVE_RAW_ITEMS, demands={_PLATE: _PLATE_RATE + 1}
    )
    assert [item.item_key for item in short.deficits] == [_PLATE]
    assert short.deficits[0].shortfall == 1
    assert short.surpluses == ()

    over = flow.flow_of(
        states, recipes, raw_items=synthetic.SOLVE_RAW_ITEMS, demands={_PLATE: _PLATE_RATE - 1}
    )
    assert over.deficits == ()
    assert [item.item_key for item in over.surpluses] == [_PLATE]

    met = flow.flow_of(
        states, recipes, raw_items=synthetic.SOLVE_RAW_ITEMS, demands={_PLATE: _PLATE_RATE}
    )
    assert (met.deficits, met.surpluses) == ((), ())


def test_a_demanded_item_nothing_touches_is_a_deficit(recipes: dict[str, Recipe]) -> None:
    result = flow.flow_of(
        [_machine(synthetic.PLATE_RECIPE)], recipes, demands={_ROD: Fraction(7, 3)}
    )
    rod = result.items[_ROD]
    assert (rod.produced, rod.consumed, rod.net, rod.demand) == (
        _ZERO,
        _ZERO,
        _ZERO,
        Fraction(7, 3),
    )
    assert _ROD in [item.item_key for item in result.deficits]


# ---------------------------------------------------------------------------
# Flag and skip, never a confident zero (non-negotiable 7)
# ---------------------------------------------------------------------------


def test_an_unknown_recipe_is_flagged_and_skipped_with_a_count(
    recipes: dict[str, Recipe],
) -> None:
    states = [_machine(_UNKNOWN_RECIPE), _machine(_UNKNOWN_RECIPE)]
    result = flow.flow_of(states, recipes)
    assert result.items == {}
    assert result.groups == ()
    assert [(g.kind, g.recipe_class_name, g.machine_count) for g in result.gaps] == [
        (flow.GAP_FLOW_RECIPE_UNKNOWN, _UNKNOWN_RECIPE, _TWO)
    ]
    assert _codes(result)[flow.WARN_FLOW_RECIPE_UNKNOWN] == _TWO
    assert result.complete is False


def test_an_absent_clock_is_skipped_rather_than_read_as_one(
    recipes: dict[str, Recipe],
) -> None:
    result = flow.flow_of(
        [_machine(synthetic.PLATE_RECIPE, None), _machine(synthetic.PLATE_RECIPE)], recipes
    )
    # One machine at clock one, not two: the unread clock contributed nothing.
    assert result.items[_PLATE].net == _PLATE_RATE
    assert [(g.kind, g.recipe_class_name, g.machine_count) for g in result.gaps] == [
        (flow.GAP_FLOW_CLOCK_UNREAD, synthetic.PLATE_RECIPE, 1)
    ]
    assert _codes(result)[flow.WARN_FLOW_CLOCK_UNREAD] == 1
    assert result.complete is False


@pytest.mark.parametrize(
    "clock",
    [cast("Fraction", 0.5), cast("Fraction", 1), Fraction(-1, 2)],
    ids=["float", "int", "negative"],
)
def test_a_clock_that_is_not_an_exact_non_negative_fraction_is_refused(
    recipes: dict[str, Recipe], clock: Fraction
) -> None:
    result = flow.flow_of([_machine(synthetic.PLATE_RECIPE, clock)], recipes)
    assert result.items == {}
    assert [g.kind for g in result.gaps] == [flow.GAP_FLOW_CLOCK_REFUSED]
    assert _codes(result)[flow.WARN_FLOW_CLOCK_REFUSED] == 1


def test_a_machine_with_no_recipe_is_counted_as_a_gap(recipes: dict[str, Recipe]) -> None:
    result = flow.flow_of([_machine(None)], recipes)
    assert [(g.kind, g.recipe_class_name, g.machine_count) for g in result.gaps] == [
        (flow.GAP_FLOW_NO_RECIPE, None, 1)
    ]
    assert _codes(result)[flow.WARN_FLOW_NO_RECIPE] == 1


def test_a_zero_duration_recipe_has_no_rate_and_is_flagged(
    recipes: dict[str, Recipe],
) -> None:
    # C6: the measured zero duration. A rate per cycle of no duration is undefined.
    assert recipes[synthetic.ZERO_DURATION_RECIPE].duration == 0
    result = flow.flow_of([_machine(synthetic.ZERO_DURATION_RECIPE)], recipes)
    assert result.items == {}
    assert [(g.kind, g.recipe_class_name) for g in result.gaps] == [
        (flow.GAP_FLOW_RATE_UNDEFINED, synthetic.ZERO_DURATION_RECIPE)
    ]
    assert _codes(result)[flow.WARN_FLOW_RATE_UNDEFINED] == 1


def test_the_buckets_partition_the_population_with_conservation(
    recipes: dict[str, Recipe],
) -> None:
    states = [
        _machine(synthetic.PLATE_RECIPE),
        _machine(synthetic.PLATE_RECIPE, Fraction(1, 3)),
        _machine(synthetic.ROD_RECIPE),
        _machine(_UNKNOWN_RECIPE),
        _machine(synthetic.ROD_RECIPE, None),
        _machine(synthetic.ROD_RECIPE, cast("Fraction", 0.25)),
        _machine(None),
        _machine(synthetic.ZERO_DURATION_RECIPE),
    ]
    result = flow.flow_of(states, recipes)
    flowing = sum(group.machine_count for group in result.groups)
    skipped = sum(gap.machine_count for gap in result.gaps)
    assert result.machines_considered == len(states)
    assert (flowing, skipped) == (3, 5)
    assert flowing + skipped == result.machines_considered
    assert result.skipped_count == skipped
    assert {gap.kind for gap in result.gaps} == set(flow.GAP_FLOW_KINDS)


def test_an_empty_population_says_nothing_flowed(recipes: dict[str, Recipe]) -> None:
    result = flow.flow_of([], recipes)
    assert result.items == {}
    assert flow.WARN_FLOW_NOTHING_FLOWING in _codes(result)
    assert result.complete is False


def test_an_all_skipped_population_says_nothing_flowed(recipes: dict[str, Recipe]) -> None:
    result = flow.flow_of([_machine(_UNKNOWN_RECIPE)], recipes)
    assert flow.WARN_FLOW_NOTHING_FLOWING in _codes(result)


def test_a_clean_population_raises_no_warning(recipes: dict[str, Recipe]) -> None:
    result = flow.flow_of([_machine(synthetic.PLATE_RECIPE)], recipes)
    assert result.warnings == ()
    assert result.complete is True


# ---------------------------------------------------------------------------
# Exactness and rendering
# ---------------------------------------------------------------------------


def test_every_numeric_leaf_is_exact(recipes: dict[str, Recipe]) -> None:
    states = [
        _machine(synthetic.PLATE_RECIPE, Fraction(1, 3)),
        _machine(synthetic.ROD_RECIPE, Fraction(2, 7)),
    ]
    result = flow.flow_of(states, recipes, demands={_ROD: Fraction(1, 9)})
    exact.audit_exact(result, path="flow")
    for item in result.items.values():
        for value in (item.produced, item.consumed, item.net, item.demand, item.shortfall):
            assert type(value) is Fraction


def test_a_float_demand_is_refused_outright(recipes: dict[str, Recipe]) -> None:
    with pytest.raises(exact.InexactValueError):
        flow.flow_of(
            [_machine(synthetic.PLATE_RECIPE)], recipes, demands={_PLATE: cast("Fraction", 1.5)}
        )


def test_the_repr_renders_counts_and_no_recipe_or_item_name(
    recipes: dict[str, Recipe],
) -> None:
    states = [_machine(synthetic.PLATE_RECIPE), _machine(_UNKNOWN_RECIPE)]
    result = flow.flow_of(states, recipes)
    rendered = [repr(result), *map(repr, result.groups), *map(repr, result.gaps)]
    rendered += [repr(item) for item in result.items.values()]
    for text in rendered:
        for name in (synthetic.PLATE_RECIPE, _UNKNOWN_RECIPE, _PLATE, _ORE):
            assert name not in text
