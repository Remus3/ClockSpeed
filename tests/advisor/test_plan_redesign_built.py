"""CS-1375: a redesign is compared with what is built, dependency-ordered.

Graded here against CS-1375's acceptance in ``docs/item_notes/phase5.md``, at the advisor: the
route a no-plan solves, read against the audit machines model that
``clockspeed.advisor.advise.inputs_of`` composes, and the ``plan.redesign.built`` input the rule
reads and tier 3 renders from the trace. ``solve/`` sees no machine.

EVERY WORLD IS THE SYNTHETIC ONE ``tests/advisor/test_plan_redesign.py`` builds, every cycle is
six seconds and every amount is one, so a stated 30 of an item a minute is three machines at
each stage it passes through, at clock 1. EVERY MACHINE IS A REAL
:class:`~clockspeed.audit.machines.MachineState` in a real
:class:`~clockspeed.audit.machines.WorldMachines`, built through the dataclasses' own fields.

THE SHAPE OF A NEGATIVE. Each arm that says a reading did not move carries a control on the
same fixture, where it does.
"""

from __future__ import annotations

import dataclasses
from fractions import Fraction
from types import MappingProxyType
from typing import Final

import pytest

from clockspeed.advisor import advise as advise_mod
from clockspeed.advisor import plans as plans_module
from clockspeed.advisor.advise import inputs_of
from clockspeed.advisor.cards import Card, card_for
from clockspeed.advisor.plans import PlanRequest, plan_offer, plan_offer_with_schematics
from clockspeed.advisor.rules.plan import (
    BUILT_ENOUGH,
    BUILT_MORE,
    BUILT_REPLACE,
    BUILT_UNMEASURED,
    IN_REDESIGN_BUILT,
    REDESIGN_RULE,
    BuiltRow,
    RedesignBuilt,
)
from clockspeed.advisor.trace import StepKind, Trace, WorldInputs, run_rule
from clockspeed.audit.machines import MachineState, WorldMachines
from clockspeed.data.registry import Registry
from clockspeed.solve.ratio import PlanStep, ProductionPlan
from tests.advisor import test_plan_redesign as worlds
from tests.advisor.build_fixtures import docs_pin, game_pin
from tests.solve.synthetic import SOLVE_ORE_ITEM, SOLVE_RELIC_ITEM

#: A machine class the audit would read, which nothing here prices.
MACHINE_CLASS: Final = "Build_SolveAssemblerMk1_C"

#: The three stages, declared consumer-first so registry order is the reverse of dependency order.
TOP: Final = "R_Top"
MID: Final = "R_Mid"
LOW: Final = "R_Low"

#: Machine counts the arms below compare with, named so no figure reads as a bare number.
TWO: Final = 2
THREE: Final = 3
FOUR: Final = 4
NINE: Final = 9

#: The one recipe off the route: pathless, so no join checks it and no route can take it.
ALT: Final = "R_Alt"


def _state(
    recipe: str | None,
    *,
    overclock: Fraction | None = Fraction(1),
    elided: bool = False,
    boost: bool = False,
) -> MachineState:
    """One machine, as the audit publishes it, naming this recipe at this clock."""
    return MachineState(
        class_name=MACHINE_CLASS,
        producing=True,
        recipe_class_name=recipe,
        overclock=overclock,
        overclock_elided=elided,
        production_boost_tagged=boost,
    )


def _machines(*states: MachineState, refused: int = 0) -> WorldMachines:
    """A real machines model over these states, every flag read off them."""
    return WorldMachines(
        machines=tuple(states),
        producing_available=any(state.producing is not None for state in states),
        recipe_available=any(state.recipe_class_name is not None for state in states),
        overclock_available=any(state.overclock is not None for state in states),
        records_considered=len(states),
        unread_payload_count=0,
        refused_overclock_count=0,
        refused_recipe_count=refused,
        warnings=(),
    )


def _chain() -> Registry:
    """Low makes S1 from Ore, Mid makes S2 from S1, Top makes Relic from S2, and Alt makes S2.

    Declared Top first. ALT is pathless, so the join never checks it and the route never takes
    it, yet it makes the item Mid makes, which is what a replace reads.
    """
    s1, s2 = worlds._item("S1"), worlds._item("S2")  # noqa: SLF001
    return worlds._registry(  # noqa: SLF001
        [
            worlds._recipe(TOP, [s2], [SOLVE_RELIC_ITEM]),  # noqa: SLF001
            worlds._recipe(MID, [s1], [s2]),  # noqa: SLF001
            worlds._recipe(LOW, [SOLVE_ORE_ITEM], [s1]),  # noqa: SLF001
            worlds._recipe(ALT, [SOLVE_ORE_ITEM], [s2], pathless=True),  # noqa: SLF001
        ],
        items=[s1, s2],
    )


def _request(registry: Registry) -> PlanRequest:
    """30 Relic a minute, which is three machines at every stage."""
    return worlds._request(registry, rate="30")  # noqa: SLF001


def _built(machines: WorldMachines | None, *, registry: Registry | None = None) -> RedesignBuilt:
    """The comparison the plan offer makes for the chain world, which must exist."""
    registry = _chain() if registry is None else registry
    offered = plan_offer_with_schematics(
        worlds._unlocks(()),  # noqa: SLF001
        registry,
        _request(registry),
        None,
        machines=machines,
    )
    value = offered[IN_REDESIGN_BUILT].value
    assert type(value) is RedesignBuilt
    return value


def _row(built: RedesignBuilt, recipe: str) -> BuiltRow:
    """One recipe's row, which must be there exactly once."""
    found = [row for row in built.rows if row.recipe == recipe]
    assert len(found) == 1
    return found[0]


def _order(built: RedesignBuilt) -> tuple[str, ...]:
    """The recipes of a comparison, in the order it lists them."""
    return tuple(row.recipe for row in built.rows)


def _three(recipe: str, **kwargs: object) -> list[MachineState]:
    """Three machines on one recipe."""
    return [_state(recipe, **kwargs) for _ in range(3)]  # type: ignore[arg-type]


def _tagged_elsewhere() -> list[MachineState]:
    """Every stage's three machines at clock 1: a measured world that closes nothing it is told."""
    return [_state(name) for name in (TOP, MID, LOW) for _ in range(3)]


# ---------------------------------------------------------------------------
# Case 1 - a shortfall at clock 1
# ---------------------------------------------------------------------------


def test_a_stage_with_fewer_machines_built_reads_more_with_the_exact_shortfall() -> None:
    built = _built(_machines(_state(TOP), _state(TOP), *_three(MID), *_three(LOW)))

    row = _row(built, TOP)
    assert row.reading == BUILT_MORE
    assert row.route_machines == Fraction(3)
    assert row.built_capacity == Fraction(2)
    assert row.shortfall == Fraction(1)
    assert type(row.shortfall) is Fraction
    # Control: the same stage with all three built reads enough, with no shortfall.
    assert _row(built, MID).reading == BUILT_ENOUGH
    assert _row(built, MID).shortfall is None


def test_a_stage_nothing_built_runs_reads_more_by_the_whole_count() -> None:
    built = _built(_machines(*_three(MID), *_three(LOW)))

    row = _row(built, TOP)
    assert (row.reading, row.shortfall, row.built_machines) == (BUILT_MORE, Fraction(3), 0)
    assert built.measured


# ---------------------------------------------------------------------------
# Case 2 - an overclocked machine closing it
# ---------------------------------------------------------------------------


def test_an_overclocked_machine_closes_the_shortfall_at_its_exact_clock() -> None:
    control = _built(_machines(_state(TOP), *_three(MID), *_three(LOW)))
    closed = _built(_machines(_state(TOP, overclock=Fraction(3)), *_three(MID), *_three(LOW)))
    short = _built(_machines(_state(TOP, overclock=Fraction(3, 2)), *_three(MID), *_three(LOW)))

    assert _row(control, TOP).reading == BUILT_MORE
    assert _row(control, TOP).shortfall == Fraction(2)
    assert _row(closed, TOP).reading == BUILT_ENOUGH
    assert _row(closed, TOP).built_capacity == Fraction(3)
    # The capacity is the exact clock, never a count of machines: one at 3/2 leaves 3/2.
    assert _row(short, TOP).reading == BUILT_MORE
    assert _row(short, TOP).shortfall == Fraction(3, 2)
    assert type(_row(short, TOP).shortfall) is Fraction


def test_capacity_adds_exactly_where_a_float_would_not() -> None:
    # Three machines at 1/10 sum to 3/10, which no binary float holds, so 3 minus it is exact only
    # in Fraction: 27/10.
    built = _built(
        _machines(*_three(TOP, overclock=Fraction(1, 10)), *_three(MID), *_three(LOW)),
    )

    row = _row(built, TOP)
    assert row.built_capacity == Fraction(3, 10)
    assert row.shortfall == Fraction(27, 10)
    assert type(row.built_capacity) is Fraction


# ---------------------------------------------------------------------------
# Case 3 - an elided overclock reads as 1
# ---------------------------------------------------------------------------


def test_an_elided_overclock_reads_as_one() -> None:
    control = _built(_machines(*_three(TOP, overclock=None), *_three(MID), *_three(LOW)))
    elided = _built(
        _machines(*_three(TOP, overclock=None, elided=True), *_three(MID), *_three(LOW))
    )

    assert _row(control, TOP).reading == BUILT_UNMEASURED
    assert _row(elided, TOP).reading == BUILT_ENOUGH
    assert _row(elided, TOP).built_capacity == Fraction(3)
    assert _row(elided, TOP).unknown_capacity == 0


# ---------------------------------------------------------------------------
# Case 4 - an unread overclock is unmeasured
# ---------------------------------------------------------------------------


def test_one_unread_overclock_makes_its_recipe_unmeasured_and_no_other() -> None:
    built = _built(
        _machines(
            _state(TOP),
            _state(TOP),
            _state(TOP, overclock=None),
            *_three(MID),
            *_three(LOW),
        )
    )

    row = _row(built, TOP)
    assert row.reading == BUILT_UNMEASURED
    assert row.unknown_capacity == 1
    assert row.built_machines == THREE
    assert row.built_capacity is None
    assert row.shortfall is None
    # Control: a recipe none of whose machines is unread still reads.
    assert _row(built, MID).reading == BUILT_ENOUGH


# ---------------------------------------------------------------------------
# Case 5 - a boosted machine is unmeasured
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "state",
    [
        _state(TOP, boost=True),
        _state(TOP, overclock=None, elided=True, boost=True),
    ],
    ids=["boost-over-a-read-clock", "boost-over-an-elided-clock"],
)
def test_a_production_boost_makes_its_machine_unknown_whatever_its_clock(
    state: MachineState,
) -> None:
    built = _built(_machines(state, _state(TOP), _state(TOP), *_three(MID), *_three(LOW)))

    row = _row(built, TOP)
    assert row.reading == BUILT_UNMEASURED
    assert row.unknown_capacity == 1
    # Control: the same machines with the boost tag off measure, and close the stage.
    plain = _built(
        _machines(_state(TOP), _state(TOP), _state(TOP), *_three(MID), *_three(LOW)),
    )
    assert _row(plain, TOP).reading == BUILT_ENOUGH


# ---------------------------------------------------------------------------
# Case 6 - an off-route producer of a stage output is a replace
# ---------------------------------------------------------------------------


def test_built_machines_on_an_off_route_producer_of_a_stage_output_read_replace_first() -> None:
    control = _built(_machines(*_three(MID), *_three(LOW)))
    built = _built(_machines(_state(ALT), _state(ALT), *_three(MID), _state(LOW)))

    assert ALT not in _order(control)
    row = _row(built, ALT)
    assert row.reading == BUILT_REPLACE
    assert row.built_machines == TWO
    assert row.route_machines is None
    assert row.shortfall is None
    # Listed before every more, which is where an expensive change belongs.
    readings = [item.reading for item in built.rows]
    assert readings[0] == BUILT_REPLACE
    assert BUILT_MORE in readings
    assert max(i for i, r in enumerate(readings) if r == BUILT_REPLACE) < min(
        i for i, r in enumerate(readings) if r == BUILT_MORE
    )


def test_an_off_route_recipe_making_no_stage_output_is_no_replace() -> None:
    other = worlds._item("Other")  # noqa: SLF001
    s1, s2 = worlds._item("S1"), worlds._item("S2")  # noqa: SLF001
    registry = worlds._registry(  # noqa: SLF001
        [
            worlds._recipe(TOP, [s2], [SOLVE_RELIC_ITEM]),  # noqa: SLF001
            worlds._recipe(MID, [s1], [s2]),  # noqa: SLF001
            worlds._recipe(LOW, [SOLVE_ORE_ITEM], [s1]),  # noqa: SLF001
            worlds._recipe(ALT, [SOLVE_ORE_ITEM], [other], pathless=True),  # noqa: SLF001
        ],
        items=[s1, s2, other],
    )

    built = _built(_machines(_state(ALT), *_three(MID)), registry=registry)

    assert ALT not in _order(built)


# ---------------------------------------------------------------------------
# Case 7 - no recipe tag reads unmeasured, whole
# ---------------------------------------------------------------------------


def test_with_no_recipe_tag_on_any_machine_the_whole_comparison_reads_unmeasured() -> None:
    untagged = _built(_machines(*[_state(None) for _ in range(9)]))
    empty = _built(_machines())
    tagged = _built(_machines(_state(TOP)))

    for built in (untagged, empty):
        assert not built.measured
        assert {row.reading for row in built.rows} == {BUILT_UNMEASURED}
        assert len(built.rows) == THREE
    # Control: one recipe tag anywhere makes the comparison measured, and the rest read more.
    assert tagged.measured
    assert _row(tagged, MID).reading == BUILT_MORE
    assert untagged.untagged_machines == NINE


# ---------------------------------------------------------------------------
# Counted, never dropped
# ---------------------------------------------------------------------------


def test_refused_recipe_tags_and_machines_naming_no_registry_recipe_are_counted() -> None:
    built = _built(
        _machines(
            _state("R_NotInTheRegistry"),
            _state("R_NotInTheRegistry"),
            _state(None),
            *_three(MID),
            refused=4,
        )
    )

    assert built.refused_recipe_tags == FOUR
    assert built.unregistered_machines == TWO
    assert built.untagged_machines == 1
    assert "R_NotInTheRegistry" not in _order(built)
    # Control: a model refusing nothing and naming only registry recipes counts none.
    clean = _built(_machines(*_three(MID)))
    assert (clean.refused_recipe_tags, clean.unregistered_machines, clean.untagged_machines) == (
        0,
        0,
        0,
    )


# ---------------------------------------------------------------------------
# Case 8 - producers first, on a three-stage chain
# ---------------------------------------------------------------------------


def test_stages_list_producers_first_though_the_registry_lists_the_target_first() -> None:
    registry = _chain()
    offered = plan_offer_with_schematics(
        worlds._unlocks(()),  # noqa: SLF001
        registry,
        _request(registry),
        None,
        machines=_machines(*_tagged_elsewhere()),
    )
    plan = offered["plan.redesign.plan"].value
    assert type(plan) is ProductionPlan
    # The control: the plan's own order is registry order, the consumer first.
    assert tuple(step.recipe_key for step in plan.steps) == (TOP, MID, LOW)

    built = offered[IN_REDESIGN_BUILT].value
    assert type(built) is RedesignBuilt
    assert _order(built) == (LOW, MID, TOP)
    assert built.cycles == ()


def _plan(*steps: tuple[str, int]) -> ProductionPlan:
    """A hand-built plan over these stages, in this registry order, one machine each unless told."""
    return ProductionPlan(
        steps=tuple(PlanStep(recipe, Fraction(count)) for recipe, count in steps),
        targets=MappingProxyType({SOLVE_RELIC_ITEM: Fraction(10)}),
        raw_inputs=MappingProxyType({}),
        byproducts=MappingProxyType({}),
        excluded=(),
        byproduct_policy="balanced",
    )


def test_independent_stages_keep_registry_order() -> None:
    a, b = worlds._item("TieA"), worlds._item("TieB")  # noqa: SLF001
    registry = worlds._registry(  # noqa: SLF001
        [
            worlds._recipe("R_Zebra", [SOLVE_ORE_ITEM], [a]),  # noqa: SLF001
            worlds._recipe("R_Apple", [SOLVE_ORE_ITEM], [b]),  # noqa: SLF001
        ],
        items=[a, b],
    )

    built = plans_module._compare_built(  # noqa: SLF001
        registry, _plan(("R_Zebra", 1), ("R_Apple", 1)), _machines(_state("R_Zebra"))
    )

    # Registry order and not the alphabet: Zebra was declared first.
    assert _order(built) == ("R_Zebra", "R_Apple")


# ---------------------------------------------------------------------------
# Case 9 - a two-stage loop is named
# ---------------------------------------------------------------------------


def _loop_registry() -> Registry:
    """A loop of two stages with a feeder before it and a consumer after it.

    Declared Two, Out, One, In. In makes X from Ore. One eats X and makes Y. Two eats Y and makes
    X, so One and Two feed each other. Out eats Y and makes Relic.
    """
    x, y = worlds._item("LoopX"), worlds._item("LoopY")  # noqa: SLF001
    return worlds._registry(  # noqa: SLF001
        [
            worlds._recipe("R_Two", [y], [x]),  # noqa: SLF001
            worlds._recipe("R_Out", [y], [SOLVE_RELIC_ITEM]),  # noqa: SLF001
            worlds._recipe("R_One", [x], [y]),  # noqa: SLF001
            worlds._recipe("R_In", [SOLVE_ORE_ITEM], [x]),  # noqa: SLF001
        ],
        items=[x, y],
    )


def test_a_loop_is_named_and_its_members_follow_every_predecessor_in_registry_order() -> None:
    registry = _loop_registry()
    plan = _plan(("R_Two", 1), ("R_Out", 1), ("R_One", 1), ("R_In", 1))

    built = plans_module._compare_built(registry, plan, _machines(_state("R_One")))  # noqa: SLF001

    assert built.cycles == (("R_Two", "R_One"),)
    # In feeds the loop, so it comes first; the loop's members follow in registry order, Two
    # before One; Out consumes the loop, so it comes last.
    assert _order(built) == ("R_In", "R_Two", "R_One", "R_Out")


def test_a_chain_names_no_cycle() -> None:
    registry = _chain()
    plan = _plan((TOP, 3), (MID, 3), (LOW, 3))

    built = plans_module._compare_built(registry, plan, _machines(_state(TOP)))  # noqa: SLF001

    assert built.cycles == ()


# ---------------------------------------------------------------------------
# The rule: tier 2 counts, tier 3 rows, from the trace
# ---------------------------------------------------------------------------


def _world(
    machines: WorldMachines, monkeypatch: pytest.MonkeyPatch, registry: Registry | None = None
) -> WorldInputs:
    """The advisor's own inputs for the chain world over these machines, no stand-in route."""
    registry = _chain() if registry is None else registry
    monkeypatch.setattr(advise_mod, "machines_of", lambda _model: machines)
    return inputs_of(
        worlds._model(()),  # noqa: SLF001
        registry,
        pinned_changelist=game_pin(),
        pinned_docs_sha256=docs_pin(),
        plan_request=_request(registry),
    )


def _trace(world: WorldInputs) -> Trace:
    """The plan.redesign trace of a world."""
    return run_rule(REDESIGN_RULE, world)


def _card(world: WorldInputs) -> Card:
    """The plan.redesign card of a world, which must fire."""
    card = card_for(_trace(world))
    assert card is not None
    return card


def _errors(trace: Trace) -> list[str]:
    """The rule-error subjects a trace recorded."""
    return [step.subject for step in trace.steps if step.kind is StepKind.RULE_ERROR]


def _reason_of(card: Card) -> str:
    """Tier 2, which a card carries as its reason."""
    return card.tier2


def test_tier_two_states_how_many_stages_read_more_and_how_many_recipes_read_replace(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    machines = _machines(_state(ALT), _state(ALT), *_three(MID), _state(LOW))
    reason = _reason_of(_card(_world(machines, monkeypatch)))

    # Top and Low read more, Mid reads enough, and Alt reads replace.
    assert "against what is built 2 stage(s) read more, 1 recipe(s) read replace" in reason
    assert "and 0 stage(s) read unmeasured" in reason
    assert "never compared with what is built" not in reason


def test_tier_two_counts_a_stage_that_reads_unmeasured_apart_from_more(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    machines = _machines(_state(TOP, overclock=None), *_three(MID), *_three(LOW), _state(ALT))
    reason = _reason_of(_card(_world(machines, monkeypatch)))

    assert "0 stage(s) read more, 1 recipe(s) read replace and 1 stage(s) read unmeasured" in reason


def test_with_nothing_measured_tier_two_still_states_the_counts_and_says_unmeasured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    reason = _reason_of(_card(_world(_machines(), monkeypatch)))

    # The comparison ran and read unmeasured, so it was compared: no never-compared sentence.
    assert "the comparison read unmeasured, as no machine names a recipe" in reason
    assert (
        "against what is built 0 stage(s) read more, 0 recipe(s) read replace"
        " and 3 stage(s) read unmeasured"
    ) in reason
    assert "never compared with what is built" not in reason


def test_with_no_machines_model_at_all_tier_two_keeps_saying_the_route_was_never_compared() -> None:
    registry = _chain()
    offered = plan_offer(worlds._unlocks(()), registry, _request(registry))  # noqa: SLF001
    world = worlds._with_value(  # noqa: SLF001
        worlds._inputs(worlds._model(()), registry, _request(registry)),  # noqa: SLF001
        IN_REDESIGN_BUILT,
        offered[IN_REDESIGN_BUILT].value,
    )

    reason = _reason_of(_card(world))

    assert "it was never compared with what is built" in reason
    assert "stage(s) read more" not in reason


def test_tier_three_carries_the_rows_read_from_the_trace(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    machines = _machines(_state(ALT), _state(TOP), _state(TOP), *_three(MID), _state(LOW))
    card = _card(_world(machines, monkeypatch))
    derivation = card.tier3

    assert "Read plan.redesign.built = RedesignBuilt(" in derivation
    assert 'BuiltRow(recipe="R_Alt", reading="replace"' in derivation
    assert 'BuiltRow(recipe="R_Top", reading="more", route_machines=3.00, built_machines=2' in (
        derivation
    )
    assert "shortfall=1.00" in derivation
    # The rows are in the order the rule read them: the replace row, then Low, Mid, Top.
    ordered = [derivation.index(f'recipe="{name}"') for name in (ALT, LOW, MID, TOP)]
    assert ordered == sorted(ordered)


def test_a_comparison_that_disagrees_with_its_plan_is_a_rule_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    machines = _machines(*_three(MID), _state(LOW))
    world = _world(machines, monkeypatch)
    built = world.values[IN_REDESIGN_BUILT].value
    assert type(built) is RedesignBuilt
    assert _errors(_trace(world)) == []

    lost = dataclasses.replace(built, rows=built.rows[1:])
    forged = dataclasses.replace(
        built.rows[0], reading=BUILT_ENOUGH, built_capacity=Fraction(0), shortfall=None
    )
    lied = dataclasses.replace(built, rows=(forged, *built.rows[1:]))
    for planted in (lost, lied):
        values = dict(world.values)
        values[IN_REDESIGN_BUILT] = dataclasses.replace(values[IN_REDESIGN_BUILT], value=planted)
        trace = _trace(WorldInputs(values=values, unlocks=world.unlocks))
        assert _errors(trace) != []


def test_a_world_with_no_machines_model_offers_no_comparison_and_says_what_it_did() -> None:
    registry = _chain()
    offered = plan_offer(worlds._unlocks(()), registry, _request(registry))  # noqa: SLF001

    assert offered[IN_REDESIGN_BUILT].value is None
