"""CS-1235: plan round-trip proof - a solved plan, built, must audit clean.

THE LOOP UNDER TEST. ``clockspeed/solve/ratio.py`` answers "what should be
built"; ``clockspeed/audit/flow.py`` answers "what does the built world move".
Neither ever reads the other. This module closes the loop through the synthetic
SOLVER corpus (``tests/solve/synthetic.py``): solve a chain, materialise the
plan as a synthetic world (``tests/audit/plan_world.py``), audit that world, and
require the audit to agree with the plan EXACTLY - zero deficits, every target
at its achieved rate, raw consumption equal to the plan's raw demand, byproducts
equal to the plan's byproducts, and every other item netting to zero.

ONE PREDICATE GRADES BOTH DIRECTIONS. :func:`_disagreements` lists every way the
audit departs from the plan. The clean arms assert it is empty; the planted arms
drop one machine and assert it is NOT, and that a deficit finding NAMES the
recipe whose group was short. A predicate that could not go red would pass the
clean arms for free, so the red arms are the half that gives the green ones
meaning.

THE POWER ARM PINS A DIVERGENCE RATHER THAN HIDING ONE. The solver prices a
step at ``machines * draw`` - fractional machine EQUIVALENTS at the reference
clock. ``balance.draw_of`` prices BUILT COUNTS at the reference clock and never
reads a clock. The materialised world builds ``ceil(machines)`` machines, so
the two figures agree exactly when every step is integral and differ by
``draw * (ceil(m) - m)`` per step otherwise. Neither is the physical draw: an
underclocked machine draws ``draw * clock ** exponent``, which
``power.draw_at_clock`` defers because it has no exact rational value.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from fractions import Fraction
from typing import Final

import pytest

from clockspeed.audit import balance, flow
from clockspeed.audit.machines import MachineState
from clockspeed.data.registry import Registry
from clockspeed.solve import exact, optimize, power, ratio
from tests.audit import plan_world
from tests.solve import synthetic

_RAW: Final = tuple(sorted(synthetic.SOLVE_RAW_ITEMS))

_C3_RECIPES: Final = (
    synthetic.GADGET_RECIPE,
    synthetic.RECOVER_RECIPE,
    synthetic.FLUID_RECIPE,
    synthetic.PLATE_RECIPE,
)

#: C3 with the recovery leg removed, under the sinkable policy - the corpus's
#: one shape whose plan publishes a NON-EMPTY byproduct map (Residue), so the
#: byproduct clause is graded on a real value rather than an empty mapping.
_C3_OPEN_RECIPES: Final = (
    synthetic.GADGET_RECIPE,
    synthetic.FLUID_RECIPE,
    synthetic.PLATE_RECIPE,
)

PlanBuilder = Callable[[Registry, Fraction], ratio.ProductionPlan]


def _targets(
    item: str, recipes: tuple[str, ...], policy: str = ratio.BYPRODUCT_BALANCED
) -> PlanBuilder:
    """Build a forward solve for one target item.

    Args:
        item: The target item.
        recipes: The selected recipes.
        policy: The byproduct policy.

    Returns:
        A function from a registry and a rate to the solved plan.
    """

    def build(registry: Registry, rate: Fraction) -> ratio.ProductionPlan:
        return ratio.solve_for_targets(
            registry,
            ratio.RatioRequest(
                targets={item: rate}, recipes=recipes, raw_items=_RAW, byproduct_policy=policy
            ),
        )

    return build


def _supply(registry: Registry, cap: Fraction) -> ratio.ProductionPlan:
    """C4: the C3 loop driven backwards from an ore cap.

    Args:
        registry: The corpus registry.
        cap: The ore cap per minute.

    Returns:
        The plan.
    """
    return ratio.solve_for_supply(
        registry,
        ratio.SupplyRequest(
            supply={synthetic.SOLVE_ORE_ITEM: cap},
            target_item=synthetic.SOLVE_GADGET_ITEM,
            recipes=_C3_RECIPES,
            raw_items=_RAW,
            byproduct_policy=ratio.BYPRODUCT_BALANCED,
        ),
    )


#: Chain id to (builder, the corpus's own published rate for it).
_CHAINS: Final[dict[str, tuple[PlanBuilder, Fraction]]] = {
    "C1": (
        _targets(synthetic.SOLVE_ROD_ITEM, (synthetic.ROD_RECIPE, synthetic.PLATE_RECIPE)),
        synthetic.C1_ROD_TARGET,
    ),
    "C2": (
        _targets(synthetic.SOLVE_FLUID_ITEM, (synthetic.FLUID_RECIPE,)),
        synthetic.C2_FLUID_TARGET,
    ),
    "C3-balanced": (
        _targets(synthetic.SOLVE_GADGET_ITEM, _C3_RECIPES),
        synthetic.C3_GADGET_TARGET,
    ),
    "C3-sinkable": (
        _targets(synthetic.SOLVE_GADGET_ITEM, _C3_RECIPES, ratio.BYPRODUCT_SINKABLE),
        synthetic.C3_GADGET_TARGET,
    ),
    "C3-open": (
        _targets(synthetic.SOLVE_GADGET_ITEM, _C3_OPEN_RECIPES, ratio.BYPRODUCT_SINKABLE),
        synthetic.C3_GADGET_TARGET,
    ),
    "C4": (_supply, synthetic.C4_ORE_CAP),
    "C5": (
        _targets(synthetic.SOLVE_TRINKET_ITEM, (synthetic.STD_GADGET_RECIPE,)),
        synthetic.C5_TRINKET_TARGET,
    ),
}

#: Rates beside each chain's own: one a whole number below every published
#: rate, one no float holds, and one large enough that every step spans several
#: machines.
_EXTRA_RATES: Final = (Fraction(1), Fraction(7, 3), Fraction(100))

_CASES: Final = [
    pytest.param(chain, rate, id=f"{chain}@{rate}")
    for chain, (_builder, published) in _CHAINS.items()
    for rate in (published, *_EXTRA_RATES)
]


@pytest.fixture(name="registry", scope="module")
def registry_fixture() -> Registry:
    """The built solve corpus.

    Returns:
        The registry every phase 3 slice tests against.
    """
    return synthetic.solve_registry()


def _plan(registry: Registry, chain: str, rate: Fraction) -> ratio.ProductionPlan:
    """Solve one chain at one rate.

    Args:
        registry: The corpus registry.
        chain: A key of :data:`_CHAINS`.
        rate: The target rate, or the supply cap for C4.

    Returns:
        The plan.
    """
    builder, _published = _CHAINS[chain]
    return builder(registry, rate)


def _audit(
    registry: Registry, plan: ratio.ProductionPlan, world: plan_world.MaterialisedWorld
) -> flow.WorldFlow:
    """Audit a materialised world against the plan's own targets.

    Args:
        registry: The corpus registry, whose recipes the caller supplies.
        plan: The plan, whose achieved targets are the demands.
        world: The world to audit.

    Returns:
        The flow.
    """
    return flow.flow_of(
        world.machines, registry.recipes, raw_items=_RAW, demands=dict(plan.targets)
    )


def _disagreements(plan: ratio.ProductionPlan, result: flow.WorldFlow) -> list[str]:
    """Every way the audited flow departs from the plan. Empty means clean.

    Args:
        plan: The solved plan.
        result: The flow audited off its materialised world.

    Returns:
        One line per disagreement. A deficit line names the item, its shortfall
        and the recipes that produce it, so a finding is traceable to a group.
    """
    found: list[str] = [
        f"deficit {item.item_key} short {item.shortfall} produced by {list(item.producers)}"
        for item in result.deficits
    ]
    if not result.complete or result.warnings:
        found.append(f"incomplete flow: {[w.code for w in result.warnings]}")
    explained: set[str] = set()
    for item, rate in plan.targets.items():
        explained.add(item)
        net = result.items[item].net if item in result.items else Fraction(0)
        if net != rate:
            found.append(f"target {item} nets {net}, plan achieves {rate}")
    for item, rate in plan.raw_inputs.items():
        explained.add(item)
        net = result.items[item].net if item in result.items else Fraction(0)
        if -net != rate:
            found.append(f"raw {item} consumed {-net}, plan consumes {rate}")
    for item, rate in plan.byproducts.items():
        explained.add(item)
        net = result.items[item].net if item in result.items else Fraction(0)
        if net != rate:
            found.append(f"byproduct {item} nets {net}, plan produces {rate}")
    found.extend(
        f"intermediate {key} nets {entry.net}, plan balances it to zero"
        for key, entry in result.items.items()
        if key not in explained and entry.net != 0
    )
    return found


# ---------------------------------------------------------------------------
# The materialiser is exact
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(("chain", "rate"), _CASES)
def test_the_materialised_world_carries_every_step_exactly(
    registry: Registry, chain: str, rate: Fraction
) -> None:
    plan = _plan(registry, chain, rate)
    world = plan_world.materialise(registry, plan)
    groups = {g.recipe_class_name: g for g in _audit(registry, plan, world).groups}
    for step in plan.steps:
        if step.machines == 0:
            assert step.recipe_key not in groups
            continue
        group = groups[step.recipe_key]
        assert group.machine_count == math.ceil(step.machines)
        assert group.machine_equivalents == step.machines
    exact.audit_exact(world.machines, path="world")


# ---------------------------------------------------------------------------
# The round trip is clean
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(("chain", "rate"), _CASES)
def test_a_solved_plan_audits_clean(registry: Registry, chain: str, rate: Fraction) -> None:
    plan = _plan(registry, chain, rate)
    result = _audit(registry, plan, plan_world.materialise(registry, plan))
    assert _disagreements(plan, result) == []
    assert result.deficits == ()
    for item, achieved in plan.targets.items():
        assert result.items[item].net == achieved
    for item, consumed in plan.raw_inputs.items():
        assert -result.items[item].net == consumed
    for item, produced in plan.byproducts.items():
        assert result.items[item].net == produced
    assert {item.item_key for item in result.surpluses} == {
        item for item, produced in plan.byproducts.items() if produced > 0
    }


def test_the_byproduct_clause_is_graded_on_a_nonzero_byproduct(registry: Registry) -> None:
    # The control that the byproduct arm above is not vacuous over empty maps.
    plan = _plan(registry, "C3-open", synthetic.C3_GADGET_TARGET)
    assert plan.byproducts[synthetic.SOLVE_RESIDUE_ITEM] > 0
    result = _audit(registry, plan, plan_world.materialise(registry, plan))
    assert (
        result.items[synthetic.SOLVE_RESIDUE_ITEM].net
        == (plan.byproducts[synthetic.SOLVE_RESIDUE_ITEM])
    )


def test_the_case_population_is_not_empty() -> None:
    assert len(_CASES) == len(_CHAINS) * (1 + len(_EXTRA_RATES))


# ---------------------------------------------------------------------------
# A planted one-machine shortfall turns it red, naming the group
# ---------------------------------------------------------------------------


def _planted_cases(*, multi: bool) -> list[object]:
    """Every (chain, rate, step) whose step materialises to two-plus machines or to one.

    Args:
        multi: True for steps of two or more machines - dropping one leaves a
            group to name - and False for single-machine steps.

    Returns:
        The pytest params.
    """
    registry = synthetic.solve_registry()
    cases: list[object] = []
    for chain, (builder, published) in _CHAINS.items():
        for rate in (published, *_EXTRA_RATES):
            for step in builder(registry, rate).steps:
                built = math.ceil(step.machines)
                if built == 0 or (built >= 2) != multi:  # noqa: PLR2004
                    continue
                cases.append(
                    pytest.param(
                        chain, rate, step.recipe_key, id=f"{chain}@{rate}-{step.recipe_key}"
                    )
                )
    return cases


_PLANTED_MULTI: Final = _planted_cases(multi=True)
_PLANTED_LONE: Final = _planted_cases(multi=False)


@pytest.mark.parametrize(("chain", "rate", "recipe"), _PLANTED_MULTI)
def test_dropping_one_machine_reddens_and_names_its_recipe(
    registry: Registry, chain: str, rate: Fraction, recipe: str
) -> None:
    plan = _plan(registry, chain, rate)
    world = plan_world.without_one(plan_world.materialise(registry, plan), recipe)
    result = _audit(registry, plan, world)

    found = _disagreements(plan, result)
    assert found != [], "a world one machine short audited clean"
    # FOR THE RIGHT REASON: some item that recipe makes is short, and the
    # finding names the recipe among that item's producers.
    named = [item for item in result.deficits if recipe in item.producers]
    assert named, f"no deficit names {recipe}: {found}"
    assert any(recipe in line for line in found if line.startswith("deficit "))
    for item in named:
        assert item.shortfall > 0


@pytest.mark.parametrize(("chain", "rate", "recipe"), _PLANTED_LONE)
def test_dropping_a_lone_machine_reddens_but_leaves_no_group_to_name(
    registry: Registry, chain: str, rate: Fraction, recipe: str
) -> None:
    # PINNED LIMIT, not a pass: with its only machine gone the recipe is absent
    # from the world, so nothing built can name it. The deficit still names the
    # ITEM it made, and the audit still goes red.
    plan = _plan(registry, chain, rate)
    world = plan_world.without_one(plan_world.materialise(registry, plan), recipe)
    result = _audit(registry, plan, world)
    assert _disagreements(plan, result) != []
    assert result.deficits != ()
    assert recipe not in {g.recipe_class_name for g in result.groups}
    assert all(recipe not in item.producers for item in result.deficits)


def test_both_planted_populations_are_populated() -> None:
    assert _PLANTED_MULTI
    assert _PLANTED_LONE


# ---------------------------------------------------------------------------
# The power arm: where solver and audit agree, and where they genuinely do not
# ---------------------------------------------------------------------------

#: What the materialised C1 world draws per ``balance.draw_of``: four rod and
#: two plate smelters at the declared reference draw.
_C1_AUDIT_MW: Final = Fraction(24)
#: The same for C3: five refineries and two smelters.
_C3_AUDIT_MW: Final = Fraction(158)


def _solver_mw(registry: Registry, plan: ratio.ProductionPlan) -> Fraction:
    """The solver's power figure, through its public scoring seam.

    Args:
        registry: The corpus registry.
        plan: The plan.

    Returns:
        ``score_plan`` under a power-only objective - ``_total_power`` exactly.
    """
    return optimize.score_plan(registry, plan, optimize.weighted_objective(power=Fraction(1)))


def _audit_mw(registry: Registry, plan: ratio.ProductionPlan) -> Fraction:
    """The audit's power figure over the materialised world.

    Args:
        registry: The corpus registry.
        plan: The plan.

    Returns:
        ``balance.draw_of``'s consumption total, asserted complete.
    """
    world = plan_world.materialise(registry, plan)
    drawn = balance.draw_of(world.placement, registry.buildings)
    assert drawn.consumption_complete
    return drawn.consumption_megawatts


def _rounding_mw(registry: Registry, plan: ratio.ProductionPlan) -> Fraction:
    """The draw of the machine fractions the materialiser rounds up.

    Args:
        registry: The corpus registry.
        plan: The plan.

    Returns:
        ``sum(draw * (ceil(m) - m))`` over the steps.
    """
    total = Fraction(0)
    for step in plan.steps:
        building = registry.buildings[plan_world.building_of(registry, step.recipe_key)]
        declared = power.declared_draw(building).megawatts
        assert declared is not None
        total += declared * (math.ceil(step.machines) - step.machines)
    return total


def test_the_corpus_base_is_the_reference_clock(registry: Registry) -> None:
    # The precondition for every equality below: the solver clamps to the
    # un-sharded base and the audit prices the reference, and here they are one.
    for building in registry.buildings.values():
        assert power.clamp_to_unsharded_base(building, power.REFERENCE_CLOCK).clock == (
            power.REFERENCE_CLOCK
        )


@pytest.mark.parametrize(("chain", "rate"), _CASES)
def test_solver_and_audit_power_differ_by_exactly_the_rounded_up_fraction(
    registry: Registry, chain: str, rate: Fraction
) -> None:
    plan = _plan(registry, chain, rate)
    assert _audit_mw(registry, plan) - _solver_mw(registry, plan) == _rounding_mw(registry, plan)


@pytest.mark.parametrize(
    ("chain", "rate"),
    [("C5", synthetic.C5_TRINKET_TARGET), ("C2", Fraction(50)), ("C3-balanced", Fraction(30))],
    ids=["C5@30-three-assemblers", "C2@50-two-refineries", "C3@30-all-integral"],
)
def test_solver_and_audit_power_agree_exactly_on_integral_plans(
    registry: Registry, chain: str, rate: Fraction
) -> None:
    plan = _plan(registry, chain, rate)
    assert all(step.machines.denominator == 1 for step in plan.steps)
    assert _audit_mw(registry, plan) == _solver_mw(registry, plan)


def test_the_power_divergence_on_c1_is_pinned(registry: Registry) -> None:
    plan = _plan(registry, "C1", synthetic.C1_ROD_TARGET)
    assert _solver_mw(registry, plan) == synthetic.C1_POWER_MW
    assert _audit_mw(registry, plan) == _C1_AUDIT_MW
    assert (
        synthetic.SMELTER_POWER_MW
        * (math.ceil(synthetic.C1_ROD_MACHINES) + math.ceil(synthetic.C1_PLATE_MACHINES))
        == _C1_AUDIT_MW
    )


def test_the_power_divergence_on_c3_is_pinned(registry: Registry) -> None:
    plan = _plan(registry, "C3-balanced", synthetic.C3_GADGET_TARGET)
    assert _solver_mw(registry, plan) == synthetic.C3_POWER_MW
    assert _audit_mw(registry, plan) == _C3_AUDIT_MW
    refineries = (
        math.ceil(synthetic.C3_GADGET_MACHINES)
        + math.ceil(synthetic.C3_RECOVER_MACHINES)
        + math.ceil(synthetic.C3_FLUID_MACHINES)
    )
    smelters = math.ceil(synthetic.C3_PLATE_MACHINES)
    assert (
        synthetic.REFINERY_POWER_MW * refineries + synthetic.SMELTER_POWER_MW * smelters
    ) == _C3_AUDIT_MW


def test_the_audit_figure_is_clock_blind(registry: Registry) -> None:
    # The same built counts at clock one and at the materialised clocks price
    # identically: draw_of reads the placement and never the machines.
    plan = _plan(registry, "C1", synthetic.C1_ROD_TARGET)
    world = plan_world.materialise(registry, plan)
    assert any(state.overclock != 1 for state in world.machines.machines)
    at_reference = plan_world.placement_model(
        tuple(
            MachineState(
                class_name=state.class_name,
                producing=True,
                recipe_class_name=state.recipe_class_name,
                overclock=Fraction(1),
            )
            for state in world.machines.machines
        )
    )
    assert balance.draw_of(at_reference, registry.buildings) == balance.draw_of(
        world.placement, registry.buildings
    )


def test_neither_figure_is_the_physical_draw_of_an_underclocked_machine(
    registry: Registry,
) -> None:
    # C1's rod machines run at 5/6. The physical draw there is the power law,
    # which has no exact rational value - so there is no third exact figure for
    # either of the two above to be reconciled against.
    clock = synthetic.C1_ROD_MACHINES / math.ceil(synthetic.C1_ROD_MACHINES)
    assert clock == Fraction(5, 6)
    smelter = registry.buildings[synthetic.SOLVE_SMELTER_BUILDING]
    drawn = power.draw_at_clock(smelter, clock)
    assert drawn.outcome == power.OUTCOME_DEFERRED
    assert drawn.megawatts is None
