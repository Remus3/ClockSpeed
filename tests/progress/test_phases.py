"""CS-1043 S2 - the phase model: machine, miner and resource, or a named null.

Every arm hand-authors a small SYNTHETIC registry - three items, two recipes,
two buildings, two extractors - and a synthetic phase-cost source in this file,
so no game install and no save file is needed and no slice of real game data is
checked in (CLAUDE.md section 7).

THE CHAIN, AND THE ORACLE WORKED BY HAND. One phase costs 1000 plates over the
two-hour budget, so the required plate rate is 1000/120 = 25/3 a minute.

- A constructor makes 2 plates from 3 ingots and 2 cubic metres of water every
  6 seconds: 20 plates, 30 ingots and 20 cubic metres a minute per machine. So
  25/3 plates need 5/12 constructors, which eat 25/2 ingots and 25/3 cubic
  metres a minute.
- A smelter makes 1 ingot from 1 ore every 4 seconds: 15 a minute. So 25/2
  ingots need 5/6 smelters, which eat 25/2 ore a minute.
- A miner pulls 1 ore a second, 60 a minute at its base rate, so 25/2 ore need
  5/24 miners. A pump moves 2000 LITRES a second, 120 cubic metres a minute,
  so 25/3 cubic metres need 5/72 pumps. A pump count that forgot the litre
  conversion would be a thousand times smaller and would redden this arm.

The expected values are written below as those hand-worked Fractions with the
two-hour figure spelled in THIS file, never computed by the module under test.
"""

from __future__ import annotations

from collections.abc import Mapping
from fractions import Fraction
from pathlib import Path
from types import MappingProxyType
from typing import Final

import pytest

from clockspeed.data.registry import (
    FORM_LIQUID,
    FORM_SOLID,
    Building,
    Extractor,
    Item,
    Recipe,
    RecipeIO,
    Registry,
)
from clockspeed.data.schematics import CostLine
from clockspeed.progress import milestones, phases
from clockspeed.solve.exact import audit_exact
from clockspeed.solve.ratio import BYPRODUCT_BALANCED
from tests.solve.test_phase3_gate import inexact_violations

# ---------------------------------------------------------------------------
# The synthetic corpus, authored here
# ---------------------------------------------------------------------------

#: Two hours in minutes, spelled here as the oracle rather than imported.
TWO_HOURS_IN_MINUTES: Final = 120

ORE_ITEM: Final = "Desc_SynthOre_C"
WATER_ITEM: Final = "Desc_SynthWater_C"
INGOT_ITEM: Final = "Desc_SynthIngot_C"
PLATE_ITEM: Final = "Desc_SynthPlate_C"

SMELTER: Final = "Build_SynthSmelter_C"
CONSTRUCTOR: Final = "Build_SynthConstructor_C"
MINER: Final = "Build_SynthMiner_C"
PUMP: Final = "Build_SynthPump_C"

INGOT_RECIPE: Final = "Recipe_SynthIngot_C"
PLATE_RECIPE: Final = "Recipe_SynthPlate_C"

COSTED_PHASE: Final = "EGP_SynthPhaseCosted"
UNCOSTED_PHASE: Final = "EGP_SynthPhaseUncosted"
PLATE_COST: Final = 1000

KEY_MACHINE: Final = "machine"
KEY_MINER: Final = "miner"
KEY_RESOURCE: Final = "resource"


def _item(key: str, form: str) -> Item:
    """Build one synthetic item.

    Args:
        key: The ClassName.
        form: The verbatim form token.

    Returns:
        The item.
    """
    return Item(
        key=key,
        display_name=key,
        form=form,
        energy_value=None,
        sink_points=None,
        is_fluid=form == FORM_LIQUID,
    )


def _building(key: str) -> Building:
    """Build one synthetic fixed-draw building.

    Args:
        key: The ClassName.

    Returns:
        The building.
    """
    return Building(
        key=key,
        display_name=key,
        power_consumption=Fraction(4),
        power_exponent=None,
        estimated_min_power=None,
        estimated_max_power=None,
        is_variable_power=False,
    )


def synthetic_registry() -> Registry:
    """Build the four-item, two-recipe chain the module docstring works by hand.

    Returns:
        The registry.
    """
    items = {
        ORE_ITEM: _item(ORE_ITEM, FORM_SOLID),
        WATER_ITEM: _item(WATER_ITEM, FORM_LIQUID),
        INGOT_ITEM: _item(INGOT_ITEM, FORM_SOLID),
        PLATE_ITEM: _item(PLATE_ITEM, FORM_SOLID),
    }
    recipes = {
        INGOT_RECIPE: Recipe(
            key=INGOT_RECIPE,
            display_name="Synthetic Ingot",
            duration=Fraction(4),
            inputs=(RecipeIO(ORE_ITEM, Fraction(1)),),
            outputs=(RecipeIO(INGOT_ITEM, Fraction(1)),),
            produced_in=(SMELTER,),
            variable_power_constant=None,
            variable_power_factor=None,
        ),
        PLATE_RECIPE: Recipe(
            key=PLATE_RECIPE,
            display_name="Synthetic Plate",
            duration=Fraction(6),
            inputs=(RecipeIO(INGOT_ITEM, Fraction(3)), RecipeIO(WATER_ITEM, Fraction(2))),
            outputs=(RecipeIO(PLATE_ITEM, Fraction(2)),),
            produced_in=(CONSTRUCTOR,),
            variable_power_constant=None,
            variable_power_factor=None,
        ),
    }
    extractors = {
        MINER: Extractor(
            key=MINER,
            display_name="Synthetic Miner",
            items_per_cycle=Fraction(1),
            extract_cycle_time=Fraction(1),
            allowed_forms=frozenset({FORM_SOLID}),
        ),
        PUMP: Extractor(
            key=PUMP,
            display_name="Synthetic Pump",
            items_per_cycle=Fraction(2000),
            extract_cycle_time=Fraction(1),
            allowed_forms=frozenset({FORM_LIQUID}),
        ),
    }
    buildings = {key: _building(key) for key in (SMELTER, CONSTRUCTOR, MINER, PUMP)}
    return Registry(
        items=MappingProxyType(items),
        recipes=MappingProxyType(recipes),
        buildings=MappingProxyType(buildings),
        warnings=(),
        unknown_groups=(),
        extractors=MappingProxyType(extractors),
    )


def selection() -> phases.RecipeSelection:
    """Select the two recipes, the two raw items and an extractor for each.

    Returns:
        The caller-supplied selection.
    """
    return phases.RecipeSelection(
        recipes=(INGOT_RECIPE, PLATE_RECIPE),
        raw_items=(ORE_ITEM, WATER_ITEM),
        byproduct_policy=BYPRODUCT_BALANCED,
        extractors=MappingProxyType({ORE_ITEM: MINER, WATER_ITEM: PUMP}),
    )


class MeasuredSource:
    """A synthetic measured source: one costed phase and nothing else."""

    def __init__(self, entries: Mapping[str, tuple[CostLine, ...]] | None = None) -> None:
        """Hold the entries this source publishes.

        Args:
            entries: Phase to cost lines; the one costed phase when omitted.
        """
        default = {COSTED_PHASE: (CostLine(PLATE_ITEM, Fraction(PLATE_COST)),)}
        self._entries = MappingProxyType(dict(default if entries is None else entries))

    def phase_costs(self) -> phases.PhaseCostTable:
        """Publish the table.

        Returns:
            The measured table.
        """
        return phases.PhaseCostTable(entries=self._entries, reason=None)


# ---------------------------------------------------------------------------
# A3 - machine, miner and resource render as distinct keys
# ---------------------------------------------------------------------------


def test_a_phase_cost_renders_machine_miner_and_resource_as_distinct_keys() -> None:
    """A costed phase renders exactly the three keys, each its own exact mapping.

    The expected mappings are the hand-worked chain in the module docstring.
    """
    cost = phases.phase_cost(MeasuredSource(), synthetic_registry(), COSTED_PHASE, selection())
    rendered = cost.render()
    assert sorted(rendered) == [KEY_MACHINE, KEY_MINER, KEY_RESOURCE]
    machine, miner, resource = (rendered[k] for k in (KEY_MACHINE, KEY_MINER, KEY_RESOURCE))
    assert machine is not None
    assert miner is not None
    assert resource is not None
    assert dict(machine) == {CONSTRUCTOR: Fraction(5, 12), SMELTER: Fraction(5, 6)}
    assert dict(miner) == {MINER: Fraction(5, 24), PUMP: Fraction(5, 72)}
    assert dict(resource) == {ORE_ITEM: Fraction(25, 2), WATER_ITEM: Fraction(25, 3)}
    leaf_types = sorted(
        {type(value).__name__ for figure in (machine, miner, resource) for value in figure.values()}
    )
    assert leaf_types == ["Fraction"]
    assert cost.phase_costs_available is True
    assert cost.clock_basis == phases.CLOCK_BASIS_FULL
    assert cost.miner_basis == phases.MINER_BASIS_BASE_RATE


def test_a_phase_with_no_cost_entry_is_null() -> None:
    """A phase the measured source has no entry for is None with a reason, never zero."""
    cost = phases.phase_cost(MeasuredSource(), synthetic_registry(), UNCOSTED_PHASE, selection())
    rendered = cost.render()
    assert sorted(rendered) == [KEY_MACHINE, KEY_MINER, KEY_RESOURCE]
    nulls = [rendered[key] is None for key in (KEY_MACHINE, KEY_MINER, KEY_RESOURCE)]
    assert nulls == [True, True, True]
    reasons = [cost.machine.reason, cost.miner.reason, cost.resource.reason]
    assert reasons == [phases.REASON_NO_COST_ENTRY] * 3
    assert cost.required.values is None
    assert cost.required.reason == phases.REASON_NO_COST_ENTRY
    assert cost.phase_costs_available is True


MODULE_SOURCE: Final = Path(phases.__file__)
#: A moved budget, one hour in minutes, planted by the budget-moved arm.
MOVED_BUDGET_MINUTES: Final = 60
#: A cost item the synthetic registry deliberately does not declare.
GHOST_ITEM: Final = "Desc_SynthGhost_C"


def null_reasons(cost: phases.PhaseCost) -> list[str | None]:
    """Read the three rendered figures' reasons, in A3 key order.

    Args:
        cost: The phase cost.

    Returns:
        The machine, miner and resource reasons.
    """
    return [cost.machine.reason, cost.miner.reason, cost.resource.reason]


def rendered_nulls(cost: phases.PhaseCost) -> list[bool]:
    """Read whether each rendered key is None, in A3 key order.

    Args:
        cost: The phase cost.

    Returns:
        Three booleans.
    """
    rendered = cost.render()
    return [rendered[key] is None for key in (KEY_MACHINE, KEY_MINER, KEY_RESOURCE)]


# ---------------------------------------------------------------------------
# Phase costs are unmeasured today, and availability is derived
# ---------------------------------------------------------------------------


def test_the_shipped_source_publishes_every_phase_null_as_unmeasured() -> None:
    """The shipped source has no table, so every figure is None, never zero."""
    cost = phases.phase_cost(
        phases.SHIPPED_PHASE_COST_SOURCE, synthetic_registry(), COSTED_PHASE, selection()
    )
    assert rendered_nulls(cost) == [True, True, True]
    assert null_reasons(cost) == [phases.REASON_PHASE_COSTS_UNMEASURED] * 3
    assert cost.required.values is None
    assert cost.phase_costs_available is False
    assert phases.phase_costs_available(phases.SHIPPED_PHASE_COST_SOURCE) is False


def test_phase_costs_available_is_derived_from_the_table_not_hardcoded() -> None:
    """Availability follows the table a source returns, whatever the source is.

    A measured table holding NO entry at all is still a measured table, so it
    reads True; only a table with no entries mapping reads False.
    """
    empty_measured = MeasuredSource(entries={})
    assert phases.phase_costs_available(empty_measured) is True
    assert phases.phase_costs_available(MeasuredSource()) is True
    cost = phases.phase_cost(empty_measured, synthetic_registry(), COSTED_PHASE, selection())
    assert cost.phase_costs_available is True
    assert null_reasons(cost) == [phases.REASON_NO_COST_ENTRY] * 3


# ---------------------------------------------------------------------------
# Each figure that cannot be derived is null with its own reason
# ---------------------------------------------------------------------------


def test_a_phase_cost_item_the_registry_does_not_resolve_is_null() -> None:
    """A ghost cost item nulls the three figures and keeps the required rates."""
    source = MeasuredSource(
        entries={
            COSTED_PHASE: (
                CostLine(PLATE_ITEM, Fraction(PLATE_COST)),
                CostLine(GHOST_ITEM, Fraction(PLATE_COST)),
            )
        }
    )
    cost = phases.phase_cost(source, synthetic_registry(), COSTED_PHASE, selection())
    assert rendered_nulls(cost) == [True, True, True]
    assert null_reasons(cost) == [phases.REASON_UNRESOLVED_COST_ITEM] * 3
    assert cost.machine.detail == GHOST_ITEM
    assert cost.required.values is not None
    assert sorted(cost.required.values) == [GHOST_ITEM, PLATE_ITEM]


def test_a_phase_without_a_recipe_selection_is_null() -> None:
    """This layer does not choose recipes, so no selection is a named null."""
    cost = phases.phase_cost(MeasuredSource(), synthetic_registry(), COSTED_PHASE, None)
    assert rendered_nulls(cost) == [True, True, True]
    assert null_reasons(cost) == [phases.REASON_NO_RECIPE_SELECTION] * 3


def test_a_ratio_refusal_is_null_with_the_refusal_named() -> None:
    """A selection that cannot make the cost item is refused, never zeroed."""
    starved = phases.RecipeSelection(
        recipes=(PLATE_RECIPE,),
        raw_items=(ORE_ITEM, WATER_ITEM),
        byproduct_policy=BYPRODUCT_BALANCED,
        extractors=MappingProxyType({ORE_ITEM: MINER, WATER_ITEM: PUMP}),
    )
    cost = phases.phase_cost(MeasuredSource(), synthetic_registry(), COSTED_PHASE, starved)
    assert rendered_nulls(cost) == [True, True, True]
    assert null_reasons(cost) == [phases.REASON_RATIO_REFUSED] * 3
    assert cost.machine.detail == "UnsolvableChain"


def test_a_miner_figure_is_null_on_its_own_when_a_resource_cannot_be_mined() -> None:
    """A missing or mismatched extractor nulls the miner figure and nothing else."""
    unmapped = phases.RecipeSelection(
        recipes=(INGOT_RECIPE, PLATE_RECIPE),
        raw_items=(ORE_ITEM, WATER_ITEM),
        byproduct_policy=BYPRODUCT_BALANCED,
        extractors=MappingProxyType({ORE_ITEM: MINER}),
    )
    cost = phases.phase_cost(MeasuredSource(), synthetic_registry(), COSTED_PHASE, unmapped)
    assert rendered_nulls(cost) == [False, True, False]
    assert cost.miner.reason == phases.REASON_NO_EXTRACTOR_SELECTED
    assert cost.miner.detail == WATER_ITEM
    crossed = phases.RecipeSelection(
        recipes=(INGOT_RECIPE, PLATE_RECIPE),
        raw_items=(ORE_ITEM, WATER_ITEM),
        byproduct_policy=BYPRODUCT_BALANCED,
        extractors=MappingProxyType({ORE_ITEM: PUMP, WATER_ITEM: MINER}),
    )
    cost = phases.phase_cost(MeasuredSource(), synthetic_registry(), COSTED_PHASE, crossed)
    assert cost.miner.reason == phases.REASON_EXTRACTOR_CANNOT_YIELD


def test_a_figure_never_holds_an_empty_mapping_a_zero_or_both_halves() -> None:
    """The A3 shape is enforced on the model, not left to every builder."""
    with pytest.raises(phases.PhaseIntegrityError):
        phases.Figure(values=MappingProxyType({}), reason=None)
    with pytest.raises(phases.PhaseIntegrityError):
        phases.Figure(values=MappingProxyType({SMELTER: Fraction(0)}), reason=None)
    with pytest.raises(phases.PhaseIntegrityError):
        phases.Figure(values=None, reason=None)
    with pytest.raises(phases.PhaseIntegrityError):
        phases.Figure(values=MappingProxyType({SMELTER: Fraction(1)}), reason="both")


# ---------------------------------------------------------------------------
# The phase budget is the milestone budget, read by name
# ---------------------------------------------------------------------------


def test_a_phase_required_rate_follows_the_budget_when_it_moves(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Moving the one named budget moves the phase's rates and machine counts.

    Over one hour 1000 plates need 50/3 a minute, which is 5/6 constructors.

    Args:
        monkeypatch: Replaces the budget for this arm only.
    """
    monkeypatch.setattr(milestones, "COMPLETION_BUDGET_MINUTES", Fraction(MOVED_BUDGET_MINUTES))
    cost = phases.phase_cost(MeasuredSource(), synthetic_registry(), COSTED_PHASE, selection())
    assert cost.required.values is not None
    assert dict(cost.required.values) == {PLATE_ITEM: Fraction(PLATE_COST, MOVED_BUDGET_MINUTES)}
    assert cost.machine.values is not None
    assert cost.machine.values[CONSTRUCTOR] == Fraction(5, 6)
    assert cost.budget_minutes == Fraction(MOVED_BUDGET_MINUTES)
    unmoved = Fraction(PLATE_COST, TWO_HOURS_IN_MINUTES)
    assert cost.required.values[PLATE_ITEM] != unmoved


# ---------------------------------------------------------------------------
# No float anywhere, and determinism
# ---------------------------------------------------------------------------


def test_no_float_reaches_a_phase_figure_or_the_module() -> None:
    """The published model audits exact and the source scans clean.

    A planted float in a copy of the same source is the control that the
    phase 3 gate's AST scan can see one at all.
    """
    cost = phases.phase_cost(MeasuredSource(), synthetic_registry(), COSTED_PHASE, selection())
    audit_exact(cost, path="phase_cost")
    source = MODULE_SOURCE.read_text(encoding="utf-8")
    assert inexact_violations(source) == []
    planted = inexact_violations(source + "\nPLANTED_RATE = 0.5\n")
    assert len(planted) == 1


def test_the_same_inputs_publish_the_same_phase_output_in_the_same_order() -> None:
    """Permuted phases, recipes and raw items publish a byte-identical result."""
    registry = synthetic_registry()
    reordered = phases.RecipeSelection(
        recipes=(PLATE_RECIPE, INGOT_RECIPE),
        raw_items=(WATER_ITEM, ORE_ITEM),
        byproduct_policy=BYPRODUCT_BALANCED,
        extractors=MappingProxyType({WATER_ITEM: PUMP, ORE_ITEM: MINER}),
    )
    first = phases.phase_costs(
        MeasuredSource(), registry, [UNCOSTED_PHASE, COSTED_PHASE], selection()
    )
    second = phases.phase_costs(
        MeasuredSource(), registry, [COSTED_PHASE, UNCOSTED_PHASE, COSTED_PHASE], reordered
    )
    assert [cost.phase for cost in first] == [COSTED_PHASE, UNCOSTED_PHASE]
    assert repr(first) == repr(second)
    machine = first[0].machine.values
    assert machine is not None
    assert list(machine) == [CONSTRUCTOR, SMELTER]
