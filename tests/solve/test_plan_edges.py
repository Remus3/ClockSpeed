"""CS-1395: a solved plan publishes its producer-to-consumer edges, and they reconcile.

Graded here, against CS-1395's acceptance in ``docs/item_notes/phase7.md`` and the
session 158 ruling that widened it:

- ``clockspeed/solve/ratio.py`` publishes, per solved plan, an edge per
  ``(producer recipe, item, consumer recipe)`` with its exact per-minute rate;
- a two-stage synthetic chain pins its edges, and the edge rates reconcile with
  ``raw_inputs``, ``targets`` and ``byproducts`` exactly;
- BOUNDARY edges are included so the totals reconcile: a raw input has no producer
  recipe (``producer`` is None) and a target or byproduct has no consumer recipe
  (``consumer`` is None, ``sink`` names which);
- an item with several producers and several consumers splits in EXACT proportion,
  ``edge(p, c) = out_p * in_c / total``, documented as an allocation and not a route;
- every edge carries a unit (``item``, ``m3`` or ``unknown``) read from the item's
  form, so a reader never compares a fluid rate with a solid one by accident;
- ``PlanEdge`` is frozen with ``__slots__`` so the advice trace admits it, and no rate
  is a float or zero.

NO EXPECTED VALUE IS A RETYPED COPY OF THE SOLVER'S ARITHMETIC. The reconciliation arm
re-derives each recipe's per-item production and consumption from the registry with its
own few lines, as ``tests/solve/test_ratio.py`` does, and shares no code with
``ratio.py``. The chains are ``tests/solve/synthetic.py``'s invented registry; the
extra recipes are invented here and loaded through the same seam. No save, docs file
or install is read.
"""

from __future__ import annotations

import dataclasses
from collections.abc import Mapping
from fractions import Fraction
from types import MappingProxyType
from typing import Any, Final

import pytest

from clockspeed.advisor.trace import _inexact_reason
from clockspeed.data.registry import Recipe, Registry
from clockspeed.solve import ratio
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
from tests.solve import synthetic

_RAW: Final = tuple(sorted(synthetic.SOLVE_RAW_ITEMS))

#: The invented recipes the many-to-many and unknown-unit arms add. Plate has TWO
#: producers (the corpus's R_Plate and R_PlateB) and TWO consumers (R_Rod and
#: R_TrinketFromPlate), and each side is pinned by a target of its own, so the system
#: has exactly one solution.
PLATE_B_RECIPE: Final = "R_PlateB"
TRINKET_RECIPE: Final = "R_TrinketFromPlate"
SMELTER_PART_RECIPE: Final = "R_SmelterPart"


def _entry(
    key: str,
    seconds: int,
    ingredients: list[tuple[str, int]],
    products: list[tuple[str, int]],
) -> dict[str, str]:
    """Build one invented recipe entry that runs in the corpus's smelter.

    Args:
        key: The recipe ClassName.
        seconds: Whole seconds per cycle.
        ingredients: ``(item ClassName, verbatim amount)`` pairs.
        products: The product side.

    Returns:
        The entry mapping, in the document's string-valued shape.
    """
    return {
        KEY_CLASS_NAME: key,
        KEY_DISPLAY_NAME: key.removeprefix("R_"),
        KEY_DURATION: f"{seconds}.000000",
        KEY_INGREDIENTS: amount_blob(ingredients),
        KEY_PRODUCT: amount_blob(products),
        KEY_PRODUCED_IN: class_path_blob(
            [synthetic.building_path(synthetic.SOLVE_SMELTER_BUILDING)]
        ),
    }


_EXTRA_ENTRIES: Final[tuple[Mapping[str, Any], ...]] = (
    _entry(
        PLATE_B_RECIPE,
        6,
        [(synthetic.SOLVE_ORE_ITEM, 1)],
        [(synthetic.SOLVE_PLATE_ITEM, 1), (synthetic.SOLVE_TWIN_ITEM, 1)],
    ),
    _entry(
        TRINKET_RECIPE,
        6,
        [(synthetic.SOLVE_PLATE_ITEM, 1)],
        [(synthetic.SOLVE_TRINKET_ITEM, 1)],
    ),
    _entry(
        SMELTER_PART_RECIPE,
        6,
        [(synthetic.SOLVE_PLATE_ITEM, 1)],
        [(synthetic.SOLVE_SMELTER_DESCRIPTOR, 1)],
    ),
)


@pytest.fixture(name="registry", scope="module")
def registry_fixture() -> Registry:
    """The corpus plus the invented recipes above.

    Returns:
        The built variant registry.
    """
    return synthetic.registry_with(add=list(_EXTRA_ENTRIES))


def _solve(
    registry: Registry,
    targets: dict[str, Fraction],
    recipes: tuple[str, ...],
    policy: str = ratio.BYPRODUCT_BALANCED,
) -> ratio.ProductionPlan:
    """Solve a target-rate request against the corpus's raw set.

    Args:
        registry: The registry to solve against.
        targets: Item key to requested net rate per minute.
        recipes: The selected recipe keys.
        policy: The byproduct policy, stated at every call site.

    Returns:
        The plan.
    """
    return ratio.solve_for_targets(
        registry,
        ratio.RatioRequest(
            targets=targets, recipes=recipes, raw_items=_RAW, byproduct_policy=policy
        ),
    )


def _by_key(plan: ratio.ProductionPlan) -> dict[tuple[str | None, str, str | None], Fraction]:
    """Index a plan's edges by ``(producer, item, consumer)``.

    Args:
        plan: The plan under test.

    Returns:
        The key to rate map. A duplicate key fails the arm, because the published
        granularity is one edge per triple.
    """
    keyed: dict[tuple[str | None, str, str | None], Fraction] = {}
    for edge in plan.edges:
        key = (edge.producer, edge.item, edge.consumer)
        assert key not in keyed, f"two edges share {key}"
        keyed[key] = edge.rate
    return keyed


def _flows(
    registry: Registry, plan: ratio.ProductionPlan
) -> tuple[dict[str, dict[str, Fraction]], dict[str, dict[str, Fraction]]]:
    """Re-derive what each recipe produces and consumes, independent of ratio.py.

    Args:
        registry: The registry the plan was solved against.
        plan: The plan under test.

    Returns:
        ``(produced, consumed)``, each mapping item to recipe key to the per-minute
        rate that recipe contributes across its machines.
    """
    produced: dict[str, dict[str, Fraction]] = {}
    consumed: dict[str, dict[str, Fraction]] = {}
    for step in plan.steps:
        recipe: Recipe = registry.recipes[step.recipe_key]
        net: dict[str, Fraction] = {}
        for flow in recipe.inputs:
            net[flow.item_key] = net.get(flow.item_key, Fraction(0)) - flow.amount
        for flow in recipe.outputs:
            net[flow.item_key] = net.get(flow.item_key, Fraction(0)) + flow.amount
        for item, amount in net.items():
            rate = step.machines * amount * 60 / recipe.duration
            if rate > 0:
                produced.setdefault(item, {})[step.recipe_key] = rate
            elif rate < 0:
                consumed.setdefault(item, {})[step.recipe_key] = -rate
    return produced, consumed


def _assert_reconciles(registry: Registry, plan: ratio.ProductionPlan) -> None:
    """Assert every edge total equals what the plan and the registry say.

    Args:
        registry: The registry the plan was solved against.
        plan: The plan under test.
    """
    produced, consumed = _flows(registry, plan)
    for edge in plan.edges:
        assert type(edge.rate) is Fraction
        assert edge.rate > 0
    for item, makers in produced.items():
        for recipe_key, rate in makers.items():
            total = sum(
                (e.rate for e in plan.edges if e.item == item and e.producer == recipe_key),
                Fraction(0),
            )
            assert total == rate, (item, recipe_key)
    for item, users in consumed.items():
        for recipe_key, rate in users.items():
            total = sum(
                (e.rate for e in plan.edges if e.item == item and e.consumer == recipe_key),
                Fraction(0),
            )
            assert total == rate, (item, recipe_key)
    raw = {e.item: Fraction(0) for e in plan.edges if e.producer is None}
    for edge in plan.edges:
        if edge.producer is None:
            raw[edge.item] += edge.rate
    assert raw == {item: rate for item, rate in plan.raw_inputs.items() if rate > 0}
    for sink, expected in (
        (ratio.SINK_TARGET, plan.targets),
        (ratio.SINK_BYPRODUCT, plan.byproducts),
    ):
        seen: dict[str, Fraction] = {}
        for edge in plan.edges:
            if edge.consumer is None and edge.sink == sink:
                seen[edge.item] = seen.get(edge.item, Fraction(0)) + edge.rate
        assert seen == {item: rate for item, rate in expected.items() if rate > 0}, sink
    for edge in plan.edges:
        assert (edge.consumer is None) == (edge.sink is not None)


# ---------------------------------------------------------------------------
# The two-stage chain, and its reconciliation
# ---------------------------------------------------------------------------


def test_a_two_stage_chain_publishes_its_producer_to_consumer_edges(registry: Registry) -> None:
    plan = _solve(
        registry,
        {synthetic.SOLVE_ROD_ITEM: synthetic.C1_ROD_TARGET},
        (synthetic.ROD_RECIPE, synthetic.PLATE_RECIPE),
    )
    assert _by_key(plan) == {
        (None, synthetic.SOLVE_ORE_ITEM, synthetic.PLATE_RECIPE): synthetic.C1_ORE_DEMAND,
        (
            synthetic.PLATE_RECIPE,
            synthetic.SOLVE_PLATE_ITEM,
            synthetic.ROD_RECIPE,
        ): synthetic.C1_PLATE_DEMAND,
        (synthetic.ROD_RECIPE, synthetic.SOLVE_ROD_ITEM, None): synthetic.C1_ROD_TARGET,
    }
    assert [(e.producer, e.item, e.consumer) for e in plan.edges] == sorted(
        ((e.producer, e.item, e.consumer) for e in plan.edges),
        key=lambda k: (k[1], k[0] or "", k[2] or ""),
    )


def test_the_edge_rates_reconcile_with_the_boundary_totals(registry: Registry) -> None:
    plan = _solve(
        registry,
        {synthetic.SOLVE_ROD_ITEM: synthetic.C1_ROD_TARGET},
        (synthetic.ROD_RECIPE, synthetic.PLATE_RECIPE),
    )
    _assert_reconciles(registry, plan)
    raw_edge = next(e for e in plan.edges if e.producer is None)
    assert raw_edge.rate == plan.raw_inputs[synthetic.SOLVE_ORE_ITEM]
    target_edge = next(e for e in plan.edges if e.sink == ratio.SINK_TARGET)
    assert target_edge.rate == plan.targets[synthetic.SOLVE_ROD_ITEM]


def test_a_chain_with_no_edges_published_by_hand_defaults_to_none(registry: Registry) -> None:
    plan = _solve(
        registry,
        {synthetic.SOLVE_ROD_ITEM: synthetic.C1_ROD_TARGET},
        (synthetic.ROD_RECIPE, synthetic.PLATE_RECIPE),
    )
    bare = ratio.ProductionPlan(
        steps=plan.steps,
        targets=plan.targets,
        raw_inputs=plan.raw_inputs,
        byproducts=plan.byproducts,
        excluded=plan.excluded,
        byproduct_policy=plan.byproduct_policy,
    )
    assert bare.edges == ()


# ---------------------------------------------------------------------------
# Several producers and consumers of one item
# ---------------------------------------------------------------------------

_MANY_TARGETS: Final = MappingProxyType(
    {
        synthetic.SOLVE_ROD_ITEM: Fraction(30),
        synthetic.SOLVE_TRINKET_ITEM: Fraction(20),
        synthetic.SOLVE_TWIN_ITEM: Fraction(20),
    }
)
_MANY_RECIPES: Final = (
    synthetic.PLATE_RECIPE,
    PLATE_B_RECIPE,
    synthetic.ROD_RECIPE,
    TRINKET_RECIPE,
)


def test_a_shared_item_splits_in_proportion_exactly(registry: Registry) -> None:
    plan = _solve(registry, dict(_MANY_TARGETS), _MANY_RECIPES)
    plate = synthetic.SOLVE_PLATE_ITEM
    edges = _by_key(plan)
    # Plate: R_Plate makes 30 a minute, R_PlateB 20; R_Rod takes 30, the trinket recipe 20.
    assert edges[(synthetic.PLATE_RECIPE, plate, synthetic.ROD_RECIPE)] == Fraction(18)
    assert edges[(synthetic.PLATE_RECIPE, plate, TRINKET_RECIPE)] == Fraction(12)
    assert edges[(PLATE_B_RECIPE, plate, synthetic.ROD_RECIPE)] == Fraction(12)
    assert edges[(PLATE_B_RECIPE, plate, TRINKET_RECIPE)] == Fraction(8)
    _assert_reconciles(registry, plan)


def test_an_uneven_split_stays_an_exact_fraction(registry: Registry) -> None:
    plan = _solve(
        registry,
        {
            synthetic.SOLVE_ROD_ITEM: Fraction(30),
            synthetic.SOLVE_TRINKET_ITEM: Fraction(7),
            synthetic.SOLVE_TWIN_ITEM: Fraction(20),
        },
        _MANY_RECIPES,
    )
    shared = [e for e in plan.edges if e.item == synthetic.SOLVE_PLATE_ITEM and e.producer]
    assert {(e.producer, e.consumer) for e in shared} == {
        (maker, user)
        for maker in (synthetic.PLATE_RECIPE, PLATE_B_RECIPE)
        for user in (synthetic.ROD_RECIPE, TRINKET_RECIPE)
    }
    assert any(e.rate.denominator != 1 for e in shared)
    for edge in shared:
        assert type(edge.rate) is Fraction
    _assert_reconciles(registry, plan)


# ---------------------------------------------------------------------------
# Byproducts, the loop, and the unit on every edge
# ---------------------------------------------------------------------------


def test_a_byproduct_is_a_sink_edge_that_reconciles() -> None:
    reclaim = synthetic.reclaim_registry()
    plan = _solve(
        reclaim,
        {synthetic.SOLVE_ROD_ITEM: synthetic.C10_ROD_TARGET},
        (synthetic.SCRAP_ROD_RECIPE, synthetic.PLATE_RECIPE),
        ratio.BYPRODUCT_SINKABLE,
    )
    assert plan.byproducts[synthetic.SOLVE_RESIDUE_ITEM] > 0
    sink = [e for e in plan.edges if e.sink == ratio.SINK_BYPRODUCT]
    assert [(e.producer, e.item, e.consumer, e.unit) for e in sink] == [
        (synthetic.SCRAP_ROD_RECIPE, synthetic.SOLVE_RESIDUE_ITEM, None, ratio.UNIT_M3)
    ]
    assert sink[0].rate == plan.byproducts[synthetic.SOLVE_RESIDUE_ITEM]
    _assert_reconciles(reclaim, plan)


def test_a_cycle_publishes_edges_around_the_loop() -> None:
    loop_registry = synthetic.solve_registry()
    plan = _solve(
        loop_registry,
        {synthetic.SOLVE_GADGET_ITEM: synthetic.C3_GADGET_TARGET},
        (
            synthetic.GADGET_RECIPE,
            synthetic.RECOVER_RECIPE,
            synthetic.FLUID_RECIPE,
            synthetic.PLATE_RECIPE,
        ),
    )
    keyed = _by_key(plan)
    assert (
        keyed[(synthetic.GADGET_RECIPE, synthetic.SOLVE_RESIDUE_ITEM, synthetic.RECOVER_RECIPE)] > 0
    )
    assert (
        keyed[(synthetic.RECOVER_RECIPE, synthetic.SOLVE_FLUID_ITEM, synthetic.GADGET_RECIPE)] > 0
    )
    assert keyed[(synthetic.FLUID_RECIPE, synthetic.SOLVE_FLUID_ITEM, synthetic.GADGET_RECIPE)] > 0
    _assert_reconciles(loop_registry, plan)


def test_every_edge_carries_the_unit_of_its_item(registry: Registry) -> None:
    plan = _solve(
        registry,
        {synthetic.SOLVE_FLUID_ITEM: synthetic.C2_FLUID_TARGET},
        (synthetic.FLUID_RECIPE,),
    )
    assert {e.item: e.unit for e in plan.edges} == {
        synthetic.SOLVE_ORE_ITEM: ratio.UNIT_ITEM,
        synthetic.SOLVE_FLUID_ITEM: ratio.UNIT_M3,
    }


def test_an_item_with_no_known_form_carries_the_unknown_unit(registry: Registry) -> None:
    plan = _solve(
        registry,
        {synthetic.SOLVE_SMELTER_DESCRIPTOR: Fraction(10)},
        (SMELTER_PART_RECIPE, synthetic.PLATE_RECIPE),
    )
    units = {e.item: e.unit for e in plan.edges}
    assert units[synthetic.SOLVE_SMELTER_DESCRIPTOR] == ratio.UNIT_UNKNOWN
    assert units[synthetic.SOLVE_PLATE_ITEM] == ratio.UNIT_ITEM


# ---------------------------------------------------------------------------
# Shape: frozen, slotted, trace-admitted, exact
# ---------------------------------------------------------------------------


def test_a_plan_edge_is_frozen_slotted_and_admitted_by_the_trace(registry: Registry) -> None:
    plan = _solve(
        registry,
        {synthetic.SOLVE_ROD_ITEM: synthetic.C1_ROD_TARGET},
        (synthetic.ROD_RECIPE, synthetic.PLATE_RECIPE),
    )
    edge = plan.edges[0]
    assert dataclasses.is_dataclass(edge)
    assert type(edge).__dataclass_params__.frozen  # type: ignore[attr-defined]
    assert "__slots__" in vars(type(edge))
    assert not hasattr(edge, "__dict__")
    assert "PlanEdge" in ratio.__all__
    assert _inexact_reason(plan) is None


def test_no_edge_rate_is_a_float_or_zero(registry: Registry) -> None:
    plans = (
        _solve(
            registry,
            {synthetic.SOLVE_ROD_ITEM: synthetic.C1_ROD_TARGET},
            (synthetic.ROD_RECIPE, synthetic.PLATE_RECIPE),
        ),
        _solve(registry, dict(_MANY_TARGETS), _MANY_RECIPES),
    )
    for plan in plans:
        assert plan.edges
        for edge in plan.edges:
            assert type(edge.rate) is Fraction
            assert edge.rate > 0
