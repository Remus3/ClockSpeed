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

CS-1265: AN ELIDED CLOCK IS NOT AN UNREAD ONE. A clock tag absent from a cleanly
read payload is how the save writes a machine at the class default, and
``clockspeed/audit/balance.py`` prices it there under CS-1263. The flow reads the
same ``MachineState.overclock_elided`` mark and flows such a machine at the same
default, counted. :func:`test_the_flow_and_the_balance_classify_every_clock_alike`
drives both audits over one synthetic world built through the real
``machines_of`` seam, so the mark is derived the way a save derives it.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace
from fractions import Fraction
from types import MappingProxyType
from typing import Final, cast

import pytest

from clockspeed.audit import balance, flow, machines
from clockspeed.audit.machines import MachineState, WorldMachines
from clockspeed.data.registry import Building, Recipe
from clockspeed.save.world import RecordProperties, WorldModel
from clockspeed.solve import exact, power
from tests.audit import test_balance as balance_fx
from tests.audit import test_machines as machines_fx
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
_THREE = 3
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


def _elided(recipe: str | None) -> MachineState:
    """Build one synthetic machine whose clock tag the serializer elided.

    Args:
        recipe: The recipe class name, or None for an unconfigured machine.

    Returns:
        The state: overclock None with the CS-1263 elision mark set, the shape
        ``machines_of`` publishes for a cleanly read payload with no clock tag.
    """
    return MachineState(
        class_name=_SMELTER,
        producing=True,
        recipe_class_name=recipe,
        overclock=None,
        overclock_elided=True,
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


# ---------------------------------------------------------------------------
# CS-1265: an ELIDED clock flows at the class default, counted
# ---------------------------------------------------------------------------


def test_an_elided_clock_flows_at_the_class_default_and_is_counted(
    recipes: dict[str, Recipe],
) -> None:
    """Alike in every field but the clock, so only the elision mark decides.

    The balance prices this machine at ``ELIDED_CLOCK_DEFAULT``; reading it as
    unread here is the two-audits-one-fact disagreement CS-1265 names.
    """
    result = flow.flow_of(
        [_elided(synthetic.PLATE_RECIPE), _machine(synthetic.PLATE_RECIPE)], recipes
    )

    assert result.gaps == ()
    assert result.items[_PLATE].net == _PLATE_RATE * (balance.ELIDED_CLOCK_DEFAULT + 1)
    assert [
        (group.machine_count, group.elided_machine_count, group.machine_equivalents)
        for group in result.groups
    ] == [(_TWO, 1, balance.ELIDED_CLOCK_DEFAULT + 1)]
    assert type(result.groups[0].machine_equivalents) is Fraction
    assert result.elided_clock_count == 1
    assert flow.WARN_FLOW_CLOCK_UNREAD not in _codes(result)
    assert result.complete is True


def test_a_read_clock_outranks_an_elided_mark(recipes: dict[str, Recipe]) -> None:
    """A present clock is a measurement; the mark only says why a None is None.

    ``balance.clocked_draw_of`` admits the default only when the clock is None
    AND the mark is set, so the flow must not price this machine at one.
    """
    stale = replace(_machine(synthetic.PLATE_RECIPE, Fraction(1, 2)), overclock_elided=True)
    result = flow.flow_of([stale], recipes)

    assert result.items[_PLATE].net == _PLATE_RATE / _TWO
    assert result.elided_clock_count == 0
    assert [group.elided_machine_count for group in result.groups] == [0]


def test_an_elided_clock_never_rescues_a_recipe_side_gap(recipes: dict[str, Recipe]) -> None:
    """The recipe-side checks still run first, so the mark moves no gap kind."""
    result = flow.flow_of(
        [_elided(None), _elided(_UNKNOWN_RECIPE), _elided(synthetic.ZERO_DURATION_RECIPE)],
        recipes,
    )

    assert [gap.kind for gap in result.gaps] == [
        flow.GAP_FLOW_NO_RECIPE,
        flow.GAP_FLOW_RECIPE_UNKNOWN,
        flow.GAP_FLOW_RATE_UNDEFINED,
    ]
    assert result.groups == ()
    assert result.elided_clock_count == 0


def test_the_elided_counts_sum_within_a_recipe_and_across_recipes(
    recipes: dict[str, Recipe],
) -> None:
    """Two elided on one recipe, one on another: the counts are SUMS, not flags.

    Every other arm holds at most one elided machine per recipe and one elided
    recipe per world, so a per-group flag or a world maximum passes all of them.
    Here the per-group counts are two and one and the world count is three, and
    each group's machine count is distinct, so no assertion leans on group order.
    """
    states = [
        _elided(synthetic.PLATE_RECIPE),
        _elided(synthetic.PLATE_RECIPE),
        _machine(synthetic.PLATE_RECIPE),
        _elided(synthetic.ROD_RECIPE),
        _machine(synthetic.ROD_RECIPE, Fraction(1, 2)),
    ]
    result = flow.flow_of(states, recipes)

    assert sorted(
        (group.machine_count, group.elided_machine_count, group.machine_equivalents)
        for group in result.groups
    ) == [(_TWO, 1, Fraction(3, 2)), (_THREE, _TWO, Fraction(_THREE))]
    assert result.elided_clock_count == _THREE
    assert result.gaps == ()


def test_the_elided_count_survives_an_interleaved_recipe_order(
    recipes: dict[str, Recipe],
) -> None:
    """Two elided machines on one recipe, another recipe between them.

    A save walks machines in record order, not recipe order, so a count that
    restarts whenever the recipe changes - the unsorted ``groupby`` shape - is
    right on every arm that places a recipe's machines together and wrong here:
    it would report one elided plate machine where there are two.
    """
    states = [
        _elided(synthetic.PLATE_RECIPE),
        _machine(synthetic.ROD_RECIPE),
        _elided(synthetic.PLATE_RECIPE),
        _machine(synthetic.PLATE_RECIPE),
    ]
    result = flow.flow_of(states, recipes)

    assert sorted(
        (group.machine_count, group.elided_machine_count, group.machine_equivalents)
        for group in result.groups
    ) == [(1, 0, Fraction(1)), (_THREE, _TWO, Fraction(_THREE))]
    assert result.elided_clock_count == _TWO
    assert result.gaps == ()


#: A built class the balance registry below does not model.
_UNMODELED_CLASS: Final = "Build_SyntheticUnmodeledQx65_C"


def test_the_elided_counts_are_scoped_to_each_audits_own_population(
    recipes: dict[str, Recipe],
) -> None:
    """Pins the scope ``WorldFlow.elided_clock_count`` documents, both ways round.

    Two elided machines carry no recipe: a recipe-side gap in the flow, never
    counted there, yet priced and counted by the balance, which reads no recipe.
    One elided machine flows on a known recipe but is of a class the balance does
    not model: counted by the flow, a registry gap in the balance. So the flow
    counts one and the balance two - the counts are each audit's own, and a doc
    that called them the same figure would be refuted by this world.
    """
    states = [
        _elided(None),
        _elided(None),
        replace(_elided(synthetic.PLATE_RECIPE), class_name=_UNMODELED_CLASS),
    ]
    flowed = flow.flow_of(states, recipes)
    drawn = balance.clocked_draw_of(
        _world(states),
        balance_fx.registry(balance_fx.building(_SMELTER, consumption=balance_fx.THIRD_MEGAWATTS)),
    )

    assert [(gap.kind, gap.machine_count) for gap in flowed.gaps] == [
        (flow.GAP_FLOW_NO_RECIPE, _TWO)
    ]
    assert flowed.elided_clock_count == 1
    assert [(gap.kind, gap.machine_count) for gap in drawn.gaps] == [
        (balance.GAP_NO_REGISTRY_ENTRY, 1)
    ]
    assert drawn.elided_clock_count == _TWO


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
        _elided(synthetic.ROD_RECIPE),
    ]
    result = flow.flow_of(states, recipes)
    flowing = sum(group.machine_count for group in result.groups)
    skipped = sum(gap.machine_count for gap in result.gaps)
    assert result.machines_considered == len(states)
    assert (flowing, skipped) == (_FOUR, 5)
    assert flowing + skipped == result.machines_considered
    assert result.skipped_count == skipped
    assert {gap.kind for gap in result.gaps} == set(flow.GAP_FLOW_KINDS)
    # CS-1265: the elided machine flows, and the count it raises is inside the groups.
    assert sum(group.elided_machine_count for group in result.groups) == 1
    assert result.elided_clock_count == 1


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


# ---------------------------------------------------------------------------
# CS-1265: the flow and the balance classify every machine's clock alike
# ---------------------------------------------------------------------------
#
# ONE SYNTHETIC WORLD, BUILT THROUGH ``machines_of``, so the elision mark is
# derived from a payload the way a save derives it rather than set by hand. One
# machine per row, each with its OWN class and its OWN recipe, so the balance's
# per-class groups and the flow's per-recipe groups each hold exactly one machine
# and every machine's classification can be read back out of both audits.
# Every class is modeled and every recipe has a rate, so the clock is the only
# thing either audit is asked about.

#: One row per way a clock reaches both audits, in record order.
_AGREEMENT_ROWS: Final = (
    "Read",
    "ReadOne",
    "Zero",
    "Elided",
    "Refused",
    "Negative",
    "Unread",
    "Disagreeing",
)

#: Each row's decoded values. A cleanly read payload with no clock tag is the
#: elided shape; ``Unread`` and ``Disagreeing`` reuse it and are spoiled below.
_AGREEMENT_VALUES: Final[Mapping[str, Mapping[str, object]]] = MappingProxyType(
    {
        "Read": {
            machines.PROPERTY_OVERCLOCK: machines_fx.as_float32(machines_fx.AUTHORED_OVERCLOCK)
        },
        "ReadOne": {machines.PROPERTY_OVERCLOCK: 1.0},
        "Zero": {machines.PROPERTY_OVERCLOCK: 0.0},
        "Elided": {machines.PROPERTY_PRODUCING: True},
        "Refused": {machines.PROPERTY_OVERCLOCK: 0.1},
        "Negative": {machines.PROPERTY_OVERCLOCK: -0.5},
        "Unread": {machines.PROPERTY_PRODUCING: True},
        "Disagreeing": {machines.PROPERTY_PRODUCING: True},
    }
)

#: The shared vocabulary both audits' answers are read into.
_PRICED: Final = "priced"
_UNREAD: Final = "unread"
_REFUSED: Final = "refused"

#: The flow's clock-gap kinds, in the shared vocabulary.
_FLOW_CLOCK_GAP: Final[Mapping[str, str]] = MappingProxyType(
    {flow.GAP_FLOW_CLOCK_UNREAD: _UNREAD, flow.GAP_FLOW_CLOCK_REFUSED: _REFUSED}
)

#: The balance's clock-gap kinds, in the shared vocabulary. A negative clock has
#: no real draw there and no flow here: a named gap in both, priced in neither.
_BALANCE_CLOCK_GAP: Final[Mapping[str, str]] = MappingProxyType(
    {
        balance.GAP_CLOCK_UNREAD: _UNREAD,
        balance.GAP_LAW_INEXACT: _REFUSED,
        power.OUTCOME_UNDEFINED: _REFUSED,
    }
)

#: One row as an audit classified it: ``(class, clock)``.
_Classified = tuple[str, Fraction | None]


def _agreement_class(label: str) -> str:
    """The built class of one row.

    Args:
        label: The row.

    Returns:
        A synthetic class name no other module authors.
    """
    return f"Build_SyntheticClockAgree{label}Qx65_C"


def _agreement_recipe(label: str) -> str:
    """The recipe class of one row, as ``machines_of`` reduces its asset path.

    Args:
        label: The row.

    Returns:
        A synthetic recipe class name no other module authors.
    """
    return f"Recipe_ClockAgree{label}Qx65_C"


def _agreement_entry(label: str) -> RecordProperties:
    """One row's published properties, carrying a permitted recipe reference.

    Args:
        label: The row.

    Returns:
        The properties.
    """
    recipe = _agreement_recipe(label)
    reference = machines_fx.recipe_reference(
        f"/Game/FactoryGame/Synthetic/{recipe.removesuffix('_C')}.{recipe}"
    )
    built = machines_fx.entry(_AGREEMENT_VALUES[label], reference, payload_read=label != "Unread")
    return replace(built, disagreeing_value_count=1) if label == "Disagreeing" else built


def _agreement_world() -> WorldModel:
    """The one world both audits read: one record per row, each its own class.

    Returns:
        The model.
    """
    base = machines_fx.world(*(_agreement_entry(label) for label in _AGREEMENT_ROWS))
    records = tuple(
        replace(
            record,
            type_path=(
                f"/Game/FactoryGame/Buildable/{_agreement_class(label)}.{_agreement_class(label)}"
            ),
        )
        for record, label in zip(base.objects.records, _AGREEMENT_ROWS, strict=True)
    )
    return replace(base, objects=replace(base.objects, records=records))


def _agreement_recipes(recipes: Mapping[str, Recipe]) -> dict[str, Recipe]:
    """Every row's recipe, each the corpus plate recipe under the row's own name.

    Args:
        recipes: The corpus recipes.

    Returns:
        Row recipe class name to recipe.
    """
    return {_agreement_recipe(label): recipes[synthetic.PLATE_RECIPE] for label in _AGREEMENT_ROWS}


def _agreement_buildings() -> Mapping[str, Building]:
    """Every row's class, modeled at an exact draw under a whole exponent.

    Returns:
        Class name to registry entry.
    """
    return balance_fx.registry(
        *(
            balance_fx.building(_agreement_class(label), consumption=balance_fx.THIRD_MEGAWATTS)
            for label in _AGREEMENT_ROWS
        )
    )


def _flow_clocks(result: flow.WorldFlow) -> dict[str, _Classified]:
    """Each row's clock as the flow classified it.

    Args:
        result: The flow over the agreement world.

    Returns:
        Row to ``(class, clock)``: a priced row carries the clock it flowed at,
        a gap row carries None.
    """
    label_of = {_agreement_recipe(label): label for label in _AGREEMENT_ROWS}
    view: dict[str, _Classified] = {
        label_of[group.recipe_class_name]: (
            _PRICED,
            group.machine_equivalents / group.machine_count,
        )
        for group in result.groups
    }
    for gap in result.gaps:
        view[label_of.get(gap.recipe_class_name or "", "")] = (
            _FLOW_CLOCK_GAP.get(gap.kind, gap.kind),
            None,
        )
    return view


def _balance_clocks(result: balance.WorldClockedDraw) -> dict[str, _Classified]:
    """Each row's clock as the balance classified it.

    Args:
        result: The clocked draw over the agreement world.

    Returns:
        Row to ``(class, clock)``, on the terms of :func:`_flow_clocks`.
    """
    label_of = {_agreement_class(label): label for label in _AGREEMENT_ROWS}
    view: dict[str, _Classified] = {
        label_of[group.class_name]: (_PRICED, group.clock) for group in result.contributions
    }
    for gap in result.gaps:
        view[label_of.get(gap.class_name, "")] = (_BALANCE_CLOCK_GAP.get(gap.kind, gap.kind), None)
    return view


def _flow_elided(result: flow.WorldFlow) -> dict[str, int]:
    """Each priced row's elided count as the flow published it.

    Args:
        result: The flow over the agreement world.

    Returns:
        Row to how many of its machines flowed at the elided default.
    """
    label_of = {_agreement_recipe(label): label for label in _AGREEMENT_ROWS}
    return {
        label_of[group.recipe_class_name]: group.elided_machine_count for group in result.groups
    }


def _balance_elided(result: balance.WorldClockedDraw) -> dict[str, int]:
    """Each priced row's elided count as the balance published it.

    Args:
        result: The clocked draw over the agreement world.

    Returns:
        Row to how many of its machines were priced at the elided default.
    """
    label_of = {_agreement_class(label): label for label in _AGREEMENT_ROWS}
    return {
        label_of[group.class_name]: group.machine_count if group.clock_elided else 0
        for group in result.contributions
    }


def _agreement_expected() -> dict[str, _Classified]:
    """What both audits must say about each row, authored from the rows alone.

    Returns:
        Row to ``(class, clock)``.
    """
    return {
        "Read": (_PRICED, Fraction(machines_fx.AUTHORED_OVERCLOCK)),
        "ReadOne": (_PRICED, Fraction(1)),
        "Zero": (_PRICED, Fraction(0)),
        "Elided": (_PRICED, balance.ELIDED_CLOCK_DEFAULT),
        "Refused": (_UNREAD, None),
        "Negative": (_REFUSED, None),
        "Unread": (_UNREAD, None),
        "Disagreeing": (_UNREAD, None),
    }


def test_the_agreement_world_carries_the_mark_only_where_the_payload_earns_it() -> None:
    """The precondition: without it the arm below would be about nothing."""
    model = machines.machines_of(_agreement_world())

    assert [state.overclock_elided for state in model.machines] == [
        label == "Elided" for label in _AGREEMENT_ROWS
    ]
    assert sum(state.recipe_class_name is not None for state in model.machines) == len(
        _AGREEMENT_ROWS
    )


def test_the_flow_and_the_balance_classify_every_clock_alike(
    recipes: dict[str, Recipe],
) -> None:
    """CS-1265's acceptance arm: one world, both audits, every machine's clock.

    A row the flow reads as unread while the balance prices it at the default
    is the disagreement; a row either audit prices that the other names a gap
    is the same fault the other way round.
    """
    model = machines.machines_of(_agreement_world())
    flowed = flow.flow_of(model, _agreement_recipes(recipes))
    drawn = balance.clocked_draw_of(model, _agreement_buildings())

    assert _flow_clocks(flowed) == _balance_clocks(drawn) == _agreement_expected()
    assert (
        _flow_elided(flowed)
        == _balance_elided(drawn)
        == {
            "Read": 0,
            "ReadOne": 0,
            "Zero": 0,
            "Elided": 1,
        }
    )
    assert flowed.elided_clock_count == drawn.elided_clock_count == 1
    assert flowed.machines_considered == drawn.machines_considered == len(_AGREEMENT_ROWS)
