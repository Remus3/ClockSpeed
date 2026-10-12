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

CS-1278: A PRODUCTION BOOST IS A NAMED FLOW GAP. A boost multiplies output on
top of the clock, its saved value is unmeasured, and CS-1264 already names a
boosted machine a gap in the balance - so the flow names it a gap too, by the
tag's PRESENCE, whatever its clock reads and whether or not its value decoded.
The agreement world carries boosted rows, so the both-audits arm reddens the
moment the flow prices a machine the balance refuses.

CS-1298: A CLASS THAT CANNOT BE CLOCKED HAS NO CLOCK TO ELIDE. Since CS-1281 the
balance prices an untagged machine of a class the registry declares cannot be
clocked at the reference clock, outside its elided count. The flow asks the
balance's own predicate, ``balance.clock_is_elidable``, with the buildings its
caller hands it, so the agreement world carries such a class and the both-audits
arm reddens when the flow counts it elided - or when either of the flow's
callers, the overlay and the fuel audit, drops the buildings and so counts it.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace
from fractions import Fraction
from types import MappingProxyType
from typing import Any, Final, cast

import pytest

from clockspeed.audit import balance, flow, fuel, machines, overlay
from clockspeed.audit.machines import MachineState, WorldMachines
from clockspeed.data.registry import Building, Recipe, Registry
from clockspeed.save.world import RecordProperties, WorldModel, WorldProperties
from clockspeed.solve import exact, power
from tests.audit import test_balance as balance_fx
from tests.audit import test_machines as machines_fx
from tests.save import synthetic as save_synthetic
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


def _boosted(state: MachineState) -> MachineState:
    """Mark one synthetic machine as carrying a production-boost tag.

    Args:
        state: The machine.

    Returns:
        The same machine with ``production_boost_tagged`` set, the shape
        ``machines_of`` publishes for a payload carrying a boost tag.
    """
    return replace(state, production_boost_tagged=True)


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


# ---------------------------------------------------------------------------
# CS-1298: a class that cannot be clocked has no clock to elide
# ---------------------------------------------------------------------------
#
# The flow asks ``balance.clock_is_elidable`` - the balance's own predicate, not
# a copy of it - whether an untagged machine's clock was elided. Only a class
# the buildings DECLARE cannot be clocked answers no: such a machine flows at
# the reference clock and is never counted elided. The registry's None, a class
# it does not carry and no buildings at all are one unknown and stay elided.
# The elided default IS the reference clock, so no rate moves here: these arms
# grade counts.

#: An invented built class whose registry entry declares it cannot be clocked.
_FIXED_CLASS: Final = "Build_SyntheticFixedClockQx98_C"


def _capability(declared: Mapping[str, bool | None]) -> Mapping[str, Building]:
    """Build a buildings mapping declaring each class's clock capability.

    Args:
        declared: Class name to its ``Building.clockable``.

    Returns:
        The mapping, every entry at an exact draw so only the capability differs.
    """
    return balance_fx.registry(
        *(
            replace(
                balance_fx.building(name, consumption=balance_fx.THIRD_MEGAWATTS), clockable=flag
            )
            for name, flag in declared.items()
        )
    )


def _fixed(state: MachineState) -> MachineState:
    """Move one synthetic machine onto :data:`_FIXED_CLASS`.

    Args:
        state: The machine.

    Returns:
        The same machine, of the class that cannot be clocked.
    """
    return replace(state, class_name=_FIXED_CLASS)


def test_a_class_that_cannot_be_clocked_flows_at_the_reference_clock_outside_the_elided_count(
    recipes: dict[str, Recipe],
) -> None:
    """Alike in every machine field but the class, so only the declaration decides.

    Two untagged machines of the fixed class - one per recipe - and one untagged
    smelter, a class declared clockable, beside the fixed plate machine. All
    three flow at the same rate, but only the smelter is an elided clock. A flow
    that ignores the declaration counts the fixed two elided as well: one per
    group becomes two and one, and the world's one becomes three.
    """
    states = [
        _fixed(_elided(synthetic.PLATE_RECIPE)),
        _elided(synthetic.PLATE_RECIPE),
        _fixed(_elided(synthetic.ROD_RECIPE)),
    ]
    result = flow.flow_of(
        states, recipes, buildings=_capability({_FIXED_CLASS: False, _SMELTER: True})
    )

    assert power.REFERENCE_CLOCK == balance.ELIDED_CLOCK_DEFAULT
    assert sorted(
        (group.machine_count, group.elided_machine_count, group.machine_equivalents)
        for group in result.groups
    ) == [
        (1, 0, power.REFERENCE_CLOCK),
        (_TWO, 1, power.REFERENCE_CLOCK + balance.ELIDED_CLOCK_DEFAULT),
    ]
    assert result.elided_clock_count == 1
    assert result.items[_PLATE].produced == _PLATE_RATE * _TWO
    assert result.gaps == ()
    assert result.complete is True
    assert _codes(result) == {}


@pytest.mark.parametrize(
    "declared",
    [
        pytest.param({_FIXED_CLASS: False, _SMELTER: None}, id="clockable-none"),
        pytest.param({_FIXED_CLASS: False}, id="no-entry"),
        pytest.param(None, id="no-buildings"),
    ],
)
def test_a_class_whose_clock_capability_is_unknown_stays_an_elided_flow_clock(
    recipes: dict[str, Recipe], declared: Mapping[str, bool | None] | None
) -> None:
    """The registry's None is a named unknown, never read as False.

    The mapping carries a declared-False entry beside the asked class, so a
    flow that reads ANY False in it, a missing entry as False, or the
    registry's None as False counts this smelter fixed and its elided count 0.
    """
    buildings = None if declared is None else _capability(declared)
    result = flow.flow_of([_elided(synthetic.PLATE_RECIPE)], recipes, buildings=buildings)

    assert [(group.machine_count, group.elided_machine_count) for group in result.groups] == [
        (1, 1)
    ]
    assert result.elided_clock_count == 1


def test_a_read_or_unread_clock_of_a_non_clockable_class_is_not_rescued(
    recipes: dict[str, Recipe],
) -> None:
    """Only the elision mark is re-read, exactly as ``balance.clocked_draw_of`` does.

    A read clock is a measurement and stays one, even beside a stale mark no
    reader writes; an unread or refused clock is a fact about this reader, and a
    class with no clock does not make it go away. A flow that fixed every clock
    of the class would flow the two read machines at one and the unread one too.
    """
    stale = replace(_machine(synthetic.ROD_RECIPE, Fraction(1, 2)), overclock_elided=True)
    states = [
        _fixed(_machine(synthetic.PLATE_RECIPE, Fraction(1, 2))),
        _fixed(stale),
        _fixed(_machine(synthetic.PLATE_RECIPE, None)),
        _fixed(_machine(synthetic.ROD_RECIPE, cast("Fraction", 0.5))),
    ]
    result = flow.flow_of(states, recipes, buildings=_capability({_FIXED_CLASS: False}))

    assert [
        (group.machine_count, group.elided_machine_count, group.machine_equivalents)
        for group in result.groups
    ] == [(1, 0, Fraction(1, 2)), (1, 0, Fraction(1, 2))]
    assert sorted((gap.kind, gap.machine_count) for gap in result.gaps) == [
        (flow.GAP_FLOW_CLOCK_REFUSED, 1),
        (flow.GAP_FLOW_CLOCK_UNREAD, 1),
    ]
    assert result.elided_clock_count == 0


def test_the_flow_reads_the_balances_own_clock_predicate(
    recipes: dict[str, Recipe], monkeypatch: pytest.MonkeyPatch
) -> None:
    """One owner: the flow's binding IS the balance's, and the flow decides through it.

    The identity alone passes a flow that imports the predicate and never asks
    it; the inverted stub alone passes a flow asking a private copy bound under
    the same name. A stub answering the opposite of the declarations must flip
    both classes, asked only for the two untagged machines - as the balance
    asks - in record order, with the very mapping the flow was handed.
    """
    assert getattr(flow, "clock_is_elidable", None) is balance.clock_is_elidable

    table = _capability({_FIXED_CLASS: False, _SMELTER: True})
    asked: list[tuple[str, Mapping[str, Building] | None]] = []

    def inverted(class_name: str, buildings: Mapping[str, Building] | None) -> bool:
        asked.append((class_name, buildings))
        return class_name == _FIXED_CLASS

    monkeypatch.setattr(flow, "clock_is_elidable", inverted)
    states = [
        _elided(synthetic.PLATE_RECIPE),
        _machine(synthetic.PLATE_RECIPE),
        _fixed(_elided(synthetic.ROD_RECIPE)),
    ]
    result = flow.flow_of(states, recipes, buildings=table)

    assert sorted((group.machine_count, group.elided_machine_count) for group in result.groups) == [
        (1, 1),
        (_TWO, 0),
    ]
    assert result.elided_clock_count == 1
    assert [name for name, _held in asked] == [_SMELTER, _FIXED_CLASS]
    assert all(held is table for _name, held in asked)


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
        _boosted(_machine(synthetic.PLATE_RECIPE)),
    ]
    result = flow.flow_of(states, recipes)
    flowing = sum(group.machine_count for group in result.groups)
    skipped = sum(gap.machine_count for gap in result.gaps)
    assert result.machines_considered == len(states)
    assert (flowing, skipped) == (_FOUR, 6)
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
# CS-1278: a production-boost tag is a named flow gap, never flowed at its clock
# ---------------------------------------------------------------------------
#
# No save in the library carries a boost tag, so every arm here is synthetic.
# THE TEST OWNS THE SPELLING of the one tag name it plants, and checks it
# against the reader's vocabulary rather than reading it off the module.

#: The live production boost, as the game spells it.
_BOOST_TAG: Final = "mCurrentProductionBoost"


@pytest.mark.parametrize(
    "boosted",
    [
        _boosted(_machine(synthetic.PLATE_RECIPE)),
        _boosted(_machine(synthetic.PLATE_RECIPE, Fraction(1, 2))),
        _boosted(_elided(synthetic.PLATE_RECIPE)),
        _boosted(_machine(synthetic.PLATE_RECIPE, None)),
        _boosted(_machine(synthetic.PLATE_RECIPE, Fraction(-1, 2))),
        _boosted(_machine(synthetic.PLATE_RECIPE, cast("Fraction", 0.5))),
        _boosted(_machine(synthetic.PLATE_RECIPE, Fraction(5, 2))),
        _boosted(_machine(synthetic.PLATE_RECIPE, Fraction(0))),
        replace(_boosted(_machine(synthetic.PLATE_RECIPE)), producing=False),
    ],
    ids=[
        "read-one",
        "read-half",
        "elided",
        "unread",
        "negative",
        "float",
        "overclocked",
        "zero",
        "stalled",
    ],
)
def test_a_boosted_machine_is_a_named_gap_whatever_its_clock(
    recipes: dict[str, Recipe], boosted: MachineState
) -> None:
    """The boost is decided BEFORE the clock, so no clock reading moves the gap kind.

    An unboosted machine at clock one sits beside it on the same recipe, so the
    plate net is exactly one machine's rate: flowing the boosted machine at its
    clock or at the elided default moves the net, and a clock gap in its place
    names the wrong fault. A boosted machine at clock zero would move no net
    if flowed, so the gap and the group's machine count are what grade it.

    The flow is NOMINAL and never reads the producing flag, so a STALLED
    boosted machine is a boost gap too: a check that skipped the boost on a
    stalled machine would flow it at its clock.
    """
    result = flow.flow_of([boosted, _machine(synthetic.PLATE_RECIPE)], recipes)

    assert result.items[_PLATE].net == _PLATE_RATE
    assert [(g.kind, g.recipe_class_name, g.machine_count) for g in result.gaps] == [
        (flow.GAP_FLOW_BOOST_UNMODELED, synthetic.PLATE_RECIPE, 1)
    ]
    assert _codes(result) == {flow.WARN_FLOW_BOOST_UNMODELED: 1}
    assert [(group.machine_count, group.elided_machine_count) for group in result.groups] == [
        (1, 0)
    ]
    assert result.elided_clock_count == 0
    assert result.complete is False


def test_a_boosted_elided_machine_is_not_counted_beside_an_unboosted_one(
    recipes: dict[str, Recipe],
) -> None:
    """Both carry the elision mark on one recipe; only the unboosted one flows and counts.

    A count that reads the mark before the boost - or that counts every
    marked machine on a flowing recipe - reports two here, and one is right.
    """
    result = flow.flow_of(
        [_boosted(_elided(synthetic.PLATE_RECIPE)), _elided(synthetic.PLATE_RECIPE)], recipes
    )

    assert [
        (group.machine_count, group.elided_machine_count, group.machine_equivalents)
        for group in result.groups
    ] == [(1, 1, balance.ELIDED_CLOCK_DEFAULT)]
    assert result.elided_clock_count == 1
    assert [(g.kind, g.machine_count) for g in result.gaps] == [(flow.GAP_FLOW_BOOST_UNMODELED, 1)]


def test_a_recipe_side_gap_outranks_the_boost(recipes: dict[str, Recipe]) -> None:
    """The recipe side runs first, as the balance's registry side does.

    A machine with no recipe, or one the mapping cannot rate, moves nothing in
    this flow whether or not it is boosted, and that is the fault named.
    """
    result = flow.flow_of(
        [
            _boosted(_machine(None)),
            _boosted(_machine(_UNKNOWN_RECIPE)),
            _boosted(_elided(synthetic.ZERO_DURATION_RECIPE)),
        ],
        recipes,
    )

    assert [gap.kind for gap in result.gaps] == [
        flow.GAP_FLOW_NO_RECIPE,
        flow.GAP_FLOW_RECIPE_UNKNOWN,
        flow.GAP_FLOW_RATE_UNDEFINED,
    ]
    assert flow.WARN_FLOW_BOOST_UNMODELED not in _codes(result)
    assert result.elided_clock_count == 0


def test_the_boost_gap_ranks_after_the_recipe_side_and_before_the_clock(
    recipes: dict[str, Recipe],
) -> None:
    """Gaps publish in kind order, and the boost sits where the balance decides it."""
    result = flow.flow_of(
        [
            _machine(synthetic.PLATE_RECIPE, None),
            _boosted(_machine(synthetic.PLATE_RECIPE)),
            _machine(synthetic.ZERO_DURATION_RECIPE),
        ],
        recipes,
    )

    assert [gap.kind for gap in result.gaps] == [
        flow.GAP_FLOW_RATE_UNDEFINED,
        flow.GAP_FLOW_BOOST_UNMODELED,
        flow.GAP_FLOW_CLOCK_UNREAD,
    ]
    assert [warning.code for warning in result.warnings] == [
        flow.WARN_FLOW_RATE_UNDEFINED,
        flow.WARN_FLOW_BOOST_UNMODELED,
        flow.WARN_FLOW_CLOCK_UNREAD,
        flow.WARN_FLOW_NOTHING_FLOWING,
    ]


@pytest.mark.parametrize(
    ("state", "flow_kind", "balance_kind"),
    [
        (
            _boosted(_machine(_UNKNOWN_RECIPE)),
            flow.GAP_FLOW_RECIPE_UNKNOWN,
            balance.GAP_BOOST_UNMODELED,
        ),
        (_boosted(_machine(None)), flow.GAP_FLOW_NO_RECIPE, balance.GAP_BOOST_UNMODELED),
        (
            _boosted(_elided(synthetic.ZERO_DURATION_RECIPE)),
            flow.GAP_FLOW_RATE_UNDEFINED,
            balance.GAP_BOOST_UNMODELED,
        ),
        (
            replace(_boosted(_machine(synthetic.PLATE_RECIPE)), class_name=_UNMODELED_CLASS),
            flow.GAP_FLOW_BOOST_UNMODELED,
            balance.GAP_NO_REGISTRY_ENTRY,
        ),
    ],
    ids=["recipe-unknown", "no-recipe", "rate-undefined", "class-unmodeled"],
)
def test_both_audits_name_a_boosted_machine_a_gap_when_an_earlier_fault_wins(
    recipes: dict[str, Recipe], state: MachineState, flow_kind: str, balance_kind: str
) -> None:
    """Some gap in both audits, never a number - but not always the same NAME.

    Each audit decides the boost after its own earlier checks: the flow after
    the recipe side, which the balance never reads, and the balance after its
    registry side, which the flow never reads. So where an earlier fault wins
    in either audit the two name different gaps for one boosted machine, and
    the claim that holds - the one ``clockspeed/audit/flow.py`` states - is that
    neither audit prices or flows it.
    """
    flowed = flow.flow_of([state], recipes)
    drawn = balance.clocked_draw_of(
        _world([state]),
        balance_fx.registry(balance_fx.building(_SMELTER, consumption=balance_fx.THIRD_MEGAWATTS)),
    )

    assert flowed.groups == ()
    assert flowed.items == {}
    assert drawn.contributions == ()
    assert [(gap.kind, gap.machine_count) for gap in flowed.gaps] == [(flow_kind, 1)]
    assert [(gap.kind, gap.machine_count) for gap in drawn.gaps] == [(balance_kind, 1)]
    assert (flowed.complete, drawn.complete) == (False, False)
    assert flowed.elided_clock_count == drawn.elided_clock_count == 0


#: The recipe class the decoder arms' recipe reference reduces to.
_DECODED_RECIPE: Final = balance_fx.RECIPE_ASSET.rpartition(".")[2]


def _decoded_recipe_tag() -> bytes:
    """A current-recipe reference whose two strings fill its declared size.

    Returns:
        The encoded tag, the untorn sibling of ``balance_fx.torn_recipe_tag``.
    """
    pair = save_synthetic.fstring(save_synthetic.MAP_NAME) + save_synthetic.fstring(
        balance_fx.RECIPE_ASSET
    )
    return save_synthetic.property_tag(machines.PROPERTY_RECIPE, "ObjectProperty", pair)


def _decoded_population(*extra: bytes) -> WorldMachines:
    """One actor at a read clock of one on a decoded recipe, through the REAL loader.

    Args:
        extra: Further encoded tags, appended after the machine's own.

    Returns:
        The machines model ``machines_of`` publishes.
    """
    return machines.machines_of(
        balance_fx.decoded_world(
            balance_fx.float_tag(machines.PROPERTY_OVERCLOCK, 1.0),
            balance_fx.producing_tag(),
            _decoded_recipe_tag(),
            *extra,
        )
    )


@pytest.mark.parametrize(
    "boost_tag",
    [
        balance_fx.torn_float_tag(_BOOST_TAG),
        save_synthetic.legacy_struct_tag(_BOOST_TAG, balance_fx.BOOST_STRUCT_WORD, bytes(8)),
    ],
    ids=["torn-float", "struct-typed"],
)
def test_a_boost_tag_whose_value_never_decoded_is_still_a_flow_gap(
    recipes: dict[str, Recipe], boost_tag: bytes
) -> None:
    """Presence is the fact read, never the value - a boost the decoder dropped is a boost.

    THE PREMISE IS ASSERTED FIRST: the reader's vocabulary carries the planted
    name, and the real decoder dropped its value, so no boost name reaches the
    values. A read clock of one sits beside it, so ignoring the boost flows the
    machine at one and reports the flow complete.
    """
    assert _BOOST_TAG in machines.PRODUCTION_BOOST_PROPERTY_NAMES
    population = _decoded_population(boost_tag)
    assert [
        (state.recipe_class_name, state.overclock, state.production_boost_tagged)
        for state in population.machines
    ] == [(_DECODED_RECIPE, Fraction(1), True)]

    result = flow.flow_of(population, {_DECODED_RECIPE: recipes[synthetic.PLATE_RECIPE]})

    assert result.items == {}
    assert [(g.kind, g.recipe_class_name, g.machine_count) for g in result.gaps] == [
        (flow.GAP_FLOW_BOOST_UNMODELED, _DECODED_RECIPE, 1)
    ]
    assert result.complete is False


def test_a_decoded_payload_with_no_boost_tag_flows(recipes: dict[str, Recipe]) -> None:
    """The control for the arm above: the same loader, no boost tag, a flow at one."""
    population = _decoded_population()
    assert [state.production_boost_tagged for state in population.machines] == [False]

    result = flow.flow_of(population, {_DECODED_RECIPE: recipes[synthetic.PLATE_RECIPE]})

    assert result.items[_PLATE].net == _PLATE_RATE
    assert result.gaps == ()
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
# Every class is modeled and every recipe has a rate, so the clock - and, for
# the CS-1278 rows, the production boost, and for the CS-1298 rows, the class's
# declared clock capability - is the only thing either audit is asked about.

#: One row per way a clock reaches both audits, in record order. The
#: ``Boosted`` rows carry a production-boost tag beside a clock each audit
#: would otherwise price - read at one, elided, overclocked above one, at zero,
#: or read at one on a STALLED machine - or refuse (``BoostedNegative``,
#: ``BoostedUndecoded``), so a boost decided after the clock, not at all, or
#: only on some clocks or some producing states, disagrees with the balance on
#: at least one of them. CS-1298: the :data:`_FIXED_ROWS` are of classes the
#: buildings declare cannot be clocked - untagged, read, unread and boosted - so
#: a flow that counts the untagged one elided, or fixes a clock the balance
#: reads or names unread, disagrees with the balance.
_AGREEMENT_ROWS: Final = (
    "Read",
    "ReadOne",
    "Zero",
    "Elided",
    "Refused",
    "Negative",
    "Unread",
    "Disagreeing",
    "BoostedRead",
    "BoostedElided",
    "BoostedNegative",
    "BoostedUndecoded",
    "BoostedOverclocked",
    "BoostedZero",
    "BoostedStalled",
    "Fixed",
    "FixedRead",
    "FixedUnread",
    "BoostedFixed",
)

#: The rows whose payload carries a production-boost tag.
_BOOSTED_ROWS: Final = frozenset(label for label in _AGREEMENT_ROWS if label.startswith("Boosted"))

#: The rows whose clock tag the serializer elided.
_ELIDED_ROWS: Final = frozenset({"Elided", "BoostedElided", "Fixed", "BoostedFixed"})

#: CS-1298. The rows whose class the buildings declare cannot be clocked.
_FIXED_ROWS: Final = frozenset({"Fixed", "FixedRead", "FixedUnread", "BoostedFixed"})

#: The rows whose payload never read.
_UNREAD_PAYLOAD_ROWS: Final = frozenset({"Unread", "FixedUnread"})

#: A decoded boost value. Never read by either audit; any float32 serves.
_BOOST_VALUE: Final = machines_fx.as_float32("2")

#: Each row's decoded values. A cleanly read payload with no clock tag is the
#: elided shape; ``Unread``, ``Disagreeing`` and ``BoostedUndecoded`` reuse it
#: and are spoiled below.
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
        "BoostedRead": {machines.PROPERTY_OVERCLOCK: 1.0, _BOOST_TAG: _BOOST_VALUE},
        "BoostedElided": {machines.PROPERTY_PRODUCING: True, _BOOST_TAG: _BOOST_VALUE},
        "BoostedNegative": {machines.PROPERTY_OVERCLOCK: -0.5, _BOOST_TAG: _BOOST_VALUE},
        "BoostedUndecoded": {machines.PROPERTY_PRODUCING: True},
        "BoostedOverclocked": {
            machines.PROPERTY_OVERCLOCK: 2.5,
            machines.PROPERTY_PRODUCING: True,
            _BOOST_TAG: _BOOST_VALUE,
        },
        "BoostedZero": {machines.PROPERTY_OVERCLOCK: 0.0, _BOOST_TAG: _BOOST_VALUE},
        "BoostedStalled": {
            machines.PROPERTY_OVERCLOCK: 1.0,
            machines.PROPERTY_PRODUCING: False,
            _BOOST_TAG: _BOOST_VALUE,
        },
        "Fixed": {machines.PROPERTY_PRODUCING: True},
        "FixedRead": {
            machines.PROPERTY_OVERCLOCK: machines_fx.as_float32(machines_fx.AUTHORED_OVERCLOCK)
        },
        "FixedUnread": {machines.PROPERTY_PRODUCING: True},
        "BoostedFixed": {machines.PROPERTY_PRODUCING: True, _BOOST_TAG: _BOOST_VALUE},
    }
)

#: The shared vocabulary both audits' answers are read into.
_PRICED: Final = "priced"
_UNREAD: Final = "unread"
_REFUSED: Final = "refused"
_BOOSTED: Final = "boosted"

#: The flow's clock and boost gap kinds, in the shared vocabulary.
_FLOW_CLOCK_GAP: Final[Mapping[str, str]] = MappingProxyType(
    {
        flow.GAP_FLOW_CLOCK_UNREAD: _UNREAD,
        flow.GAP_FLOW_CLOCK_REFUSED: _REFUSED,
        flow.GAP_FLOW_BOOST_UNMODELED: _BOOSTED,
    }
)

#: The balance's clock and boost gap kinds, in the shared vocabulary. A negative
#: clock has no real draw there and no flow here: a named gap in both, priced in
#: neither.
_BALANCE_CLOCK_GAP: Final[Mapping[str, str]] = MappingProxyType(
    {
        balance.GAP_CLOCK_UNREAD: _UNREAD,
        balance.GAP_LAW_INEXACT: _REFUSED,
        power.OUTCOME_UNDEFINED: _REFUSED,
        balance.GAP_BOOST_UNMODELED: _BOOSTED,
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
    built = machines_fx.entry(
        _AGREEMENT_VALUES[label], reference, payload_read=label not in _UNREAD_PAYLOAD_ROWS
    )
    if label == "BoostedUndecoded":
        # A torn boost tag, as the real decoder publishes one: its value dropped,
        # a disagreement counted, and its NAME carried so presence still reads.
        return replace(built, disagreeing_value_count=1, undecoded_names=frozenset({_BOOST_TAG}))
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

    CS-1298: a :data:`_FIXED_ROWS` class declares it cannot be clocked; every
    other class leaves its capability None, the registry's named unknown.

    Returns:
        Class name to registry entry.
    """
    return balance_fx.registry(
        *(
            replace(
                balance_fx.building(
                    _agreement_class(label), consumption=balance_fx.THIRD_MEGAWATTS
                ),
                clockable=False if label in _FIXED_ROWS else None,
            )
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
        "BoostedRead": (_BOOSTED, None),
        "BoostedElided": (_BOOSTED, None),
        "BoostedNegative": (_BOOSTED, None),
        "BoostedUndecoded": (_BOOSTED, None),
        "BoostedOverclocked": (_BOOSTED, None),
        "BoostedZero": (_BOOSTED, None),
        "BoostedStalled": (_BOOSTED, None),
        "Fixed": (_PRICED, power.REFERENCE_CLOCK),
        "FixedRead": (_PRICED, Fraction(machines_fx.AUTHORED_OVERCLOCK)),
        "FixedUnread": (_UNREAD, None),
        "BoostedFixed": (_BOOSTED, None),
    }


def test_the_agreement_world_carries_the_mark_only_where_the_payload_earns_it() -> None:
    """The precondition: without it the arm below would be about nothing.

    CS-1278: every boosted row reaches the model boosted, including the one
    whose boost value never decoded, and the boosted rows still carry the
    clock and producing flag each would be priced at without the boost - one
    elided, the rest read at one, above one and at zero, one of them stalled.

    CS-1298: the fixed rows reach the model as their clockable twins do - one
    elided, one read, one unread - and only the buildings declare them fixed.
    """
    model = machines.machines_of(_agreement_world())

    assert [state.overclock_elided for state in model.machines] == [
        label in _ELIDED_ROWS for label in _AGREEMENT_ROWS
    ]
    assert [state.production_boost_tagged for state in model.machines] == [
        label in _BOOSTED_ROWS for label in _AGREEMENT_ROWS
    ]
    by_label = dict(zip(_AGREEMENT_ROWS, model.machines, strict=True))
    assert [
        (by_label[label].overclock, by_label[label].producing)
        for label in ("BoostedRead", "BoostedOverclocked", "BoostedZero", "BoostedStalled")
    ] == [(Fraction(1), None), (Fraction(5, 2), True), (Fraction(0), None), (Fraction(1), False)]
    assert [by_label[label].overclock for label in ("Fixed", "FixedRead", "FixedUnread")] == [
        None,
        Fraction(machines_fx.AUTHORED_OVERCLOCK),
        None,
    ]
    assert {
        label
        for label in _AGREEMENT_ROWS
        if _agreement_buildings()[_agreement_class(label)].clockable is False
    } == _FIXED_ROWS
    assert _BOOST_TAG in machines.PRODUCTION_BOOST_PROPERTY_NAMES
    assert sum(state.recipe_class_name is not None for state in model.machines) == len(
        _AGREEMENT_ROWS
    )


def test_the_flow_and_the_balance_classify_every_clock_alike(
    recipes: dict[str, Recipe], monkeypatch: pytest.MonkeyPatch
) -> None:
    """CS-1265's acceptance arm: one world, both audits, every machine's clock.

    A row the flow reads as unread while the balance prices it at the default
    is the disagreement; a row either audit prices that the other names a gap
    is the same fault the other way round.

    CS-1278 extends it to the boost: a boosted row the flow flows, or names
    by its clock, while the balance names it boost-unmodeled is the same
    two-audits-one-machine disagreement, and the boosted elided row stays out
    of both elided counts.

    CS-1298 extends it to the clock capability: the balance prices the untagged
    ``Fixed`` row at the reference clock outside its elided count, so a flow
    that counts it elided disagrees - on the row and on the world. The rate is
    the same either way, so the elided counts are where it shows. The flow's
    two callers are held to the same world: the overlay's before and after
    flows, and the flow the fuel audit builds, must each EQUAL the flow built
    here, so a caller that drops ``buildings`` counts ``Fixed`` elided and
    reddens this arm.
    """
    model = machines.machines_of(_agreement_world())
    rows = _agreement_recipes(recipes)
    buildings = _agreement_buildings()
    flowed = flow.flow_of(model, rows, buildings=buildings)
    drawn = balance.clocked_draw_of(model, buildings)

    assert _flow_clocks(flowed) == _balance_clocks(drawn) == _agreement_expected()
    assert (
        _flow_elided(flowed)
        == _balance_elided(drawn)
        == {
            "Read": 0,
            "ReadOne": 0,
            "Zero": 0,
            "Elided": 1,
            "Fixed": 0,
            "FixedRead": 0,
        }
    )
    assert flowed.elided_clock_count == drawn.elided_clock_count == 1
    assert flowed.machines_considered == drawn.machines_considered == len(_AGREEMENT_ROWS)

    built: list[flow.WorldFlow] = []

    def recording(*args: Any, **kwargs: Any) -> flow.WorldFlow:
        result = flow.flow_of(*args, **kwargs)
        built.append(result)
        return result

    monkeypatch.setattr(fuel, "flow_of", recording)
    fuel.fuel_supply_of(
        model,
        Registry(
            items=MappingProxyType({}),
            recipes=MappingProxyType(rows),
            buildings=buildings,
            warnings=(),
            unknown_groups=(),
        ),
    )
    evaluated = overlay.evaluate_overlay(
        model, overlay.Overlay(edits=()), rows, buildings=buildings
    )

    assert built == [flowed]
    assert evaluated.before_flow == flowed
    assert evaluated.after_flow == flowed


# ---------------------------------------------------------------------------
# CS-1314: a census record of a recipe class keeps the flow incomplete
# ---------------------------------------------------------------------------
#
# ``WorldMachines`` counts every built record it did not admit, per class and
# split the CS-1280 way: never read, read but not clean, read clean. A record
# of a class the recipes name among their producers may be running one of
# them, so a flow that judges only the admitted machines is short by whatever
# it moves. Every world here is built through the real ``machines_of`` seam,
# so the census is the one a save yields, never a hand-set count.

#: The recipe class the census record is of: the corpus assembler, which the
#: corpus recipes name as a producer and which no admitted machine here is.
_CENSUS_CLASS: Final = synthetic.SOLVE_ASSEMBLER_BUILDING

#: A class no corpus recipe names among its producers.
_NON_RECIPE_CLASS: Final = balance_fx.FIXED_WHOLE

#: The plate recipe's asset path, under a permitted root, so the one admitted
#: machine reduces it to the corpus recipe name.
_PLATE_ASSET: Final = (
    f"/Game/FactoryGame/Synthetic/{synthetic.PLATE_RECIPE}.{synthetic.PLATE_RECIPE}"
)

#: Each census kind under the id the parametrised arms read it by.
_CENSUS_KIND_IDS: Final = {
    "clean": balance.CENSUS_TAGLESS_CLEAN,
    "unclean": balance.GAP_NO_MACHINE_STATE,
    "unread": balance.GAP_PAYLOAD_UNREAD,
}


def _census_flow_world(census_class: str, kind: str) -> WorldModel:
    """One plate smelter that flows, then one census record of one class and kind.

    Args:
        census_class: The class of the record ``machines_of`` will not admit.
        kind: Its census kind: read clean with no tag at all, read with only a
            pending clock tag, or never read.

    Returns:
        The model.
    """
    rows: list[tuple[str, Mapping[str, object]]] = [(_SMELTER, balance_fx.TAGGED)]
    unread: tuple[str, ...] = ()
    if kind == balance.CENSUS_TAGLESS_CLEAN:
        rows.append((census_class, {}))
    elif kind == balance.GAP_NO_MACHINE_STATE:
        rows.append((census_class, balance_fx.PENDING))
    else:
        unread = (census_class,)
    base = balance_fx.census_world(*rows, unread=unread)
    entries = dict(base.properties.by_record_index)
    entries[0] = replace(entries[0], references=(machines_fx.recipe_reference(_PLATE_ASSET),))
    return replace(base, properties=WorldProperties(by_record_index=MappingProxyType(entries)))


def _census_rows(result: flow.WorldFlow) -> list[tuple[str, str, int]]:
    """Each unadmitted entry as ``(class, kind, records)``, in published order.

    Args:
        result: The flow.

    Returns:
        The rows.
    """
    return list(result.unadmitted)


@pytest.mark.parametrize("kind", list(_CENSUS_KIND_IDS.values()), ids=list(_CENSUS_KIND_IDS))
def test_an_unadmitted_record_of_a_recipe_class_keeps_the_flow_incomplete(
    recipes: dict[str, Recipe], kind: str
) -> None:
    """CS-1314's flow arm: every census kind of a recipe class reads incomplete.

    THE ONE ADMITTED MACHINE FLOWS AND NOTHING IS SKIPPED, so without the
    census the flow reads complete; the record left out of the population is
    the only thing that can make it not. A clean tagless record is no
    exception (ruling Q3 b): its class runs recipes, and nothing here says it
    is not running one.
    """
    model = machines.machines_of(_census_flow_world(_CENSUS_CLASS, kind))
    result = flow.flow_of(model, recipes)

    assert [group.recipe_class_name for group in result.groups] == [synthetic.PLATE_RECIPE]
    assert result.skipped_count == 0
    assert result.complete is False
    assert _census_rows(result) == [(_CENSUS_CLASS, kind, 1)]
    assert _codes(result).get(flow.WARN_FLOW_RECIPE_CLASS_UNADMITTED) == 1
    # Conservation is untouched: the census sits beside the population.
    assert result.machines_considered == 1


@pytest.mark.parametrize("kind", list(_CENSUS_KIND_IDS.values()), ids=list(_CENSUS_KIND_IDS))
def test_an_unadmitted_record_of_no_recipe_class_leaves_the_flow_complete(
    recipes: dict[str, Recipe], kind: str
) -> None:
    """The guard: a class no recipe names moves no recipe item, so it is not named."""
    model = machines.machines_of(_census_flow_world(_NON_RECIPE_CLASS, kind))
    held = sum(
        count
        for pairs in (model.unadmitted_read_counts, model.unadmitted_unread_counts)
        for _class, count in pairs
    )
    result = flow.flow_of(model, recipes)

    assert held == 1
    assert result.complete is True
    assert result.unadmitted == ()
    assert flow.WARN_FLOW_RECIPE_CLASS_UNADMITTED not in _codes(result)


#: CS-1314 fix 1. Records of the census class per kind in the counting arm:
#: several of each, and a different number of each, so a count of records, a
#: count of (class, kind) rows and a count of classes all differ.
_CLEAN_RECORDS: Final = 3
_PENDING_RECORDS: Final = 2
_UNREAD_RECORDS: Final = 4


def test_the_flow_counts_unadmitted_records_and_never_class_rows(
    recipes: dict[str, Recipe],
) -> None:
    """CS-1314 fix 1: the census is counted in RECORDS, per class and kind.

    One class carries several records of each of the three kinds. Counting the
    (class, kind) rows would publish three where nine records sit outside the
    flow - on the library, one row per save where the constructor census holds
    many records.
    """
    rows: list[tuple[str, Mapping[str, object]]] = [(_SMELTER, balance_fx.TAGGED)]
    rows += [(_CENSUS_CLASS, {})] * _CLEAN_RECORDS
    rows += [(_CENSUS_CLASS, balance_fx.PENDING)] * _PENDING_RECORDS
    base = balance_fx.census_world(*rows, unread=(_CENSUS_CLASS,) * _UNREAD_RECORDS)
    entries = dict(base.properties.by_record_index)
    entries[0] = replace(entries[0], references=(machines_fx.recipe_reference(_PLATE_ASSET),))
    model = machines.machines_of(
        replace(base, properties=WorldProperties(by_record_index=MappingProxyType(entries)))
    )
    result = flow.flow_of(model, recipes)

    assert _census_rows(result) == [
        (_CENSUS_CLASS, balance.GAP_PAYLOAD_UNREAD, _UNREAD_RECORDS),
        (_CENSUS_CLASS, balance.GAP_NO_MACHINE_STATE, _PENDING_RECORDS),
        (_CENSUS_CLASS, balance.CENSUS_TAGLESS_CLEAN, _CLEAN_RECORDS),
    ]
    assert _codes(result).get(flow.WARN_FLOW_RECIPE_CLASS_UNADMITTED) == (
        _CLEAN_RECORDS + _PENDING_RECORDS + _UNREAD_RECORDS
    )
    assert result.complete is False


def test_a_bare_sequence_carries_no_census(recipes: dict[str, Recipe]) -> None:
    """Ruling Q3 c: the census is read only from a ``WorldMachines``.

    The same machines as a bare sequence carry nothing to read it from, so the
    flow over them reads only them - while the model of the same world, which
    does carry it, does not read complete.
    """
    model = machines.machines_of(_census_flow_world(_CENSUS_CLASS, balance.CENSUS_TAGLESS_CLEAN))
    bare = flow.flow_of(model.machines, recipes)
    modelled = flow.flow_of(model, recipes)

    assert bare.complete is True
    assert bare.unadmitted == ()
    assert flow.WARN_FLOW_RECIPE_CLASS_UNADMITTED not in _codes(bare)
    assert modelled.complete is False


def test_a_producer_named_only_by_an_unresolved_token_is_a_recipe_class(
    recipes: dict[str, Recipe],
) -> None:
    """Ruling Q3 a: an unresolved producer token names a recipe class too."""
    stranger = "Build_SyntheticUnresolvedProducerQx14_C"
    rows = {
        **recipes,
        "R_SyntheticUnresolvedQx14": replace(
            recipes[synthetic.PLATE_RECIPE],
            key="R_SyntheticUnresolvedQx14",
            produced_in=(),
            unresolved_produced_in=(stranger,),
        ),
    }
    model = machines.machines_of(_census_flow_world(stranger, balance.GAP_PAYLOAD_UNREAD))

    assert flow.flow_of(model, recipes).complete is True
    result = flow.flow_of(model, rows)
    assert result.complete is False
    assert _census_rows(result) == [(stranger, balance.GAP_PAYLOAD_UNREAD, 1)]


def test_residual_a_recipe_the_registry_dropped_hides_its_producer_class_from_the_flow(
    recipes: dict[str, Recipe],
) -> None:
    """A NAMED RESIDUAL, NOT A FIX - the session 138 CS-1314 ruling's common mode.

    A recipe class is known only from the recipes the caller hands in. When
    the registry dropped every recipe a class produces - one it could not read
    - the class is no recipe class here, so its census record is not named and
    the flow reads complete. This arm pins today's behaviour so the blind spot
    stays visible; it reddens the day a fix lands, which is when it is
    rewritten.
    """
    survivors = {
        key: recipe
        for key, recipe in recipes.items()
        if _CENSUS_CLASS not in (*recipe.produced_in, *recipe.unresolved_produced_in)
    }
    model = machines.machines_of(_census_flow_world(_CENSUS_CLASS, balance.GAP_PAYLOAD_UNREAD))

    assert len(survivors) < len(recipes)
    assert flow.flow_of(model, recipes).complete is False
    blind = flow.flow_of(model, survivors)
    assert blind.complete is True
    assert blind.unadmitted == ()
