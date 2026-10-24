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

import dataclasses
from collections.abc import Mapping
from fractions import Fraction
from pathlib import Path
from types import MappingProxyType
from typing import Final, cast

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
from clockspeed.data.schematics import CostLine, normalize_schematics
from clockspeed.progress import milestones, phases
from clockspeed.save import world
from clockspeed.solve.exact import audit_exact
from clockspeed.solve.ratio import BYPRODUCT_BALANCED
from tests.data import synthetic
from tests.progress.test_milestones import KEY_COST, schematic_document, schematic_entry
from tests.save import elevator_synthetic
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
# A world with no phase-cost array has no table, and availability is derived
# ---------------------------------------------------------------------------


def no_table_source() -> phases.SavePhaseCosts:
    """The shipped save source over a synthetic world that writes no phase-cost array.

    The phase manager is PRESENT and the array is not - the shape ADR 0016
    measured on every 1.0-native save in the library - and there is no
    elevator, so the source publishes neither a table nor a delivered reading.

    Returns:
        The source.
    """
    blob = elevator_synthetic.save_blob(manager_tags=())
    return phases.SavePhaseCosts(world.load_world_from_bytes(blob), frozenset({COSTED_PHASE}))


def test_the_shipped_source_publishes_every_phase_null_as_unmeasured() -> None:
    """A world that writes no array has no table, so every figure is None, never zero.

    THE NAME IS KEPT, NOT THE CLAIM IN IT. ``docs/LEDGER.md`` cites this arm by
    name and is append-only, so it keeps the CS-1043 spelling; since CS-1340 the
    shipped source is :class:`~clockspeed.progress.phases.SavePhaseCosts`, and
    its null is "no table on this world", not "unmeasured".
    """
    source = no_table_source()
    cost = phases.phase_cost(source, synthetic_registry(), COSTED_PHASE, selection())
    assert rendered_nulls(cost) == [True, True, True]
    assert null_reasons(cost) == [phases.REASON_NO_PHASE_COST_TABLE] * 3
    assert cost.required.values is None
    assert cost.phase_costs_available is False
    assert phases.phase_costs_available(source) is False


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


# ---------------------------------------------------------------------------
# Repair arms - each written against a mutant that survived the first suite
# ---------------------------------------------------------------------------

ASSEMBLER: Final = "Build_SynthAssembler_C"
KILN: Final = "Build_SynthKiln_C"
TWIN_PLATE_RECIPE: Final = "Recipe_SynthTwinPlate_C"
SLAG_RECIPE: Final = "Recipe_SynthSlag_C"
SAND_ITEM: Final = "Desc_SynthSand_C"
SLAG_ITEM: Final = "Desc_SynthSlag_C"

#: The basis labels as published, spelled here so a relabel reddens.
CLOCK_BASIS_SPELLING: Final = "full-clock"
MINER_BASIS_SPELLING: Final = "base-rate"


def extended_registry() -> Registry:
    """Add a two-building plate recipe and an idle slag recipe to the base chain.

    The twin plate recipe is the plate recipe made in EITHER the constructor
    or the assembler. The slag recipe eats sand into slag; under the balanced
    policy nothing consumes slag, so the solve runs it at exactly zero
    machines and the plan eats exactly zero sand.

    Returns:
        The registry.
    """
    base = synthetic_registry()
    plate = base.recipes[PLATE_RECIPE]
    twin = dataclasses.replace(plate, key=TWIN_PLATE_RECIPE, produced_in=(CONSTRUCTOR, ASSEMBLER))
    slag = Recipe(
        key=SLAG_RECIPE,
        display_name="Synthetic Slag",
        duration=Fraction(1),
        inputs=(RecipeIO(SAND_ITEM, Fraction(1)),),
        outputs=(RecipeIO(SLAG_ITEM, Fraction(1)),),
        produced_in=(KILN,),
        variable_power_constant=None,
        variable_power_factor=None,
    )
    items = dict(base.items)
    items[SAND_ITEM] = _item(SAND_ITEM, FORM_SOLID)
    items[SLAG_ITEM] = _item(SLAG_ITEM, FORM_SOLID)
    recipes = dict(base.recipes)
    recipes[TWIN_PLATE_RECIPE] = twin
    recipes[SLAG_RECIPE] = slag
    buildings = dict(base.buildings)
    buildings[ASSEMBLER] = _building(ASSEMBLER)
    buildings[KILN] = _building(KILN)
    return dataclasses.replace(
        base,
        items=MappingProxyType(items),
        recipes=MappingProxyType(recipes),
        buildings=MappingProxyType(buildings),
    )


def test_a_recipe_made_in_two_buildings_nulls_the_machine_figure() -> None:
    """A running recipe with two producing buildings is never charged to the first.

    Which building runs it is the caller's choice, and the selection does not
    make it, so the machine figure is None under its reason while the resource
    figure, which does not depend on the building, is still published.
    """
    twin = phases.RecipeSelection(
        recipes=(INGOT_RECIPE, TWIN_PLATE_RECIPE),
        raw_items=(ORE_ITEM, WATER_ITEM),
        byproduct_policy=BYPRODUCT_BALANCED,
        extractors=MappingProxyType({ORE_ITEM: MINER, WATER_ITEM: PUMP}),
    )
    cost = phases.phase_cost(MeasuredSource(), extended_registry(), COSTED_PHASE, twin)
    assert cost.machine.values is None
    assert cost.machine.reason == phases.REASON_NO_SINGLE_BUILDING
    assert cost.machine.detail == TWIN_PLATE_RECIPE
    assert cost.resource.values is not None
    assert dict(cost.resource.values) == {ORE_ITEM: Fraction(25, 2), WATER_ITEM: Fraction(25, 3)}


@pytest.mark.parametrize("amount", [Fraction(0), Fraction(-5)])
def test_a_non_positive_phase_cost_is_null_with_a_reason_never_an_error(amount: Fraction) -> None:
    """A zero or negative cost amount publishes every figure None, by name.

    It must not reach the required-rate figure, which refuses a zero by
    raising - an error where the contract is a named None.

    Args:
        amount: The non-positive amount planted on the plate line.
    """
    source = MeasuredSource(entries={COSTED_PHASE: (CostLine(PLATE_ITEM, amount),)})
    cost = phases.phase_cost(source, synthetic_registry(), COSTED_PHASE, selection())
    assert rendered_nulls(cost) == [True, True, True]
    assert null_reasons(cost) == [phases.REASON_NONPOSITIVE_COST] * 3
    assert cost.required.values is None
    assert cost.required.reason == phases.REASON_NONPOSITIVE_COST
    assert cost.machine.detail == PLATE_ITEM


def test_a_raw_input_the_plan_eats_none_of_is_excluded_not_published_as_zero() -> None:
    """A raw item the solve assigns zero consumption is left out of every figure.

    The slag recipe runs at zero machines, so its sand is declared raw and is
    eaten at exactly zero. Publishing it would render a 0, and a miner count
    for it would demand an extractor for nothing.
    """
    idle = phases.RecipeSelection(
        recipes=(INGOT_RECIPE, PLATE_RECIPE, SLAG_RECIPE),
        raw_items=(ORE_ITEM, WATER_ITEM, SAND_ITEM),
        byproduct_policy=BYPRODUCT_BALANCED,
        extractors=MappingProxyType({ORE_ITEM: MINER, WATER_ITEM: PUMP}),
    )
    cost = phases.phase_cost(MeasuredSource(), extended_registry(), COSTED_PHASE, idle)
    assert cost.resource.values is not None
    assert dict(cost.resource.values) == {ORE_ITEM: Fraction(25, 2), WATER_ITEM: Fraction(25, 3)}
    assert cost.miner.values is not None
    assert dict(cost.miner.values) == {MINER: Fraction(5, 24), PUMP: Fraction(5, 72)}
    assert cost.machine.values is not None
    assert dict(cost.machine.values) == {CONSTRUCTOR: Fraction(5, 12), SMELTER: Fraction(5, 6)}


def test_the_basis_labels_are_pinned_by_their_exact_spelling() -> None:
    """The two bases named on the model are published under fixed spellings.

    A consumer reads the label, not the constant's name, so a relabel is a
    contract change and must redden here rather than move with the constant.
    """
    cost = phases.phase_cost(MeasuredSource(), synthetic_registry(), COSTED_PHASE, selection())
    assert (cost.clock_basis, cost.miner_basis) == (CLOCK_BASIS_SPELLING, MINER_BASIS_SPELLING)
    shipped = phases.phase_cost(no_table_source(), synthetic_registry(), COSTED_PHASE, selection())
    assert (shipped.clock_basis, shipped.miner_basis) == (
        CLOCK_BASIS_SPELLING,
        MINER_BASIS_SPELLING,
    )


def test_every_phase_reason_code_is_distinct() -> None:
    """No two REASON_* constants share a spelling, so a reason names one cause."""
    codes = [getattr(phases, name) for name in phases.__all__ if name.startswith("REASON_")]
    assert len(codes) == len(set(codes))
    assert len(codes) > 1


# ---------------------------------------------------------------------------
# CS-1339 - the cost guards read every total, not only the first
# ---------------------------------------------------------------------------

#: A positive amount, planted on the valid line beside the non-positive one.
VALID_LINE_COST: Final = 5
#: Two-line costs, ingot then plate, with the zero on the SECOND line and then
#: on the FIRST - the ingot sorts before the plate, so each holds in source AND
#: sorted order - and the item the null must name. The guard reads sorted
#: totals, so a check that read only the first total passes the first cost, and
#: one that read only the last total passes the second.
NONPOSITIVE_PHASE_COSTS: Final = (
    (
        (CostLine(INGOT_ITEM, Fraction(VALID_LINE_COST)), CostLine(PLATE_ITEM, Fraction(0))),
        PLATE_ITEM,
    ),
    (
        (CostLine(INGOT_ITEM, Fraction(0)), CostLine(PLATE_ITEM, Fraction(VALID_LINE_COST))),
        INGOT_ITEM,
    ),
)
#: A cost item the synthetic registry does not declare, spelled to sort AFTER
#: the plate. The ghost arm's ghost sorts before it, so a check that read only
#: the first sorted total still caught that one.
LATE_GHOST_ITEM: Final = "Desc_SynthZGhost_C"
#: Two-line costs, plate and late ghost, with the ghost LAST in source order and
#: then FIRST. The late ghost sorts after the plate, so it is last in sorted
#: order in both. A check that read only the first sorted total passes the
#: first cost, and one that read only the last source line passes the second.
UNRESOLVED_PHASE_COSTS: Final = (
    (CostLine(PLATE_ITEM, Fraction(PLATE_COST)), CostLine(LATE_GHOST_ITEM, Fraction(PLATE_COST))),
    (CostLine(LATE_GHOST_ITEM, Fraction(PLATE_COST)), CostLine(PLATE_ITEM, Fraction(PLATE_COST))),
)


@pytest.mark.parametrize(
    ("lines", "zero_item"), NONPOSITIVE_PHASE_COSTS, ids=["zero-second", "zero-first"]
)
def test_a_non_positive_phase_cost_on_either_line_is_null_never_an_error(
    lines: tuple[CostLine, ...], zero_item: str
) -> None:
    """A zero on either of two cost lines nulls every figure by name.

    The zero is second in both orders in one case and first in both in the
    other, so a guard that read only one end of the sorted totals would hand
    the zero to the required-rate figure, which refuses it by raising.

    Args:
        lines: The two cost lines, ingot first.
        zero_item: The item on the non-positive line, which the null names.
    """
    assert INGOT_ITEM < PLATE_ITEM
    source = MeasuredSource(entries={COSTED_PHASE: lines})
    cost = phases.phase_cost(source, synthetic_registry(), COSTED_PHASE, selection())
    machine_reason = cost.machine.reason
    assert machine_reason == phases.REASON_NONPOSITIVE_COST
    reasons_named = null_reasons(cost) == [phases.REASON_NONPOSITIVE_COST] * 3
    assert reasons_named
    all_null = rendered_nulls(cost) == [True, True, True]
    assert all_null
    detail, required_reason = cost.machine.detail, cost.required.reason
    assert detail == zero_item
    assert required_reason == phases.REASON_NONPOSITIVE_COST
    required_withheld = cost.required.values is None
    assert required_withheld


@pytest.mark.parametrize("lines", UNRESOLVED_PHASE_COSTS, ids=["ghost-last", "ghost-first"])
def test_an_unresolved_phase_cost_item_on_either_line_is_null(
    lines: tuple[CostLine, ...],
) -> None:
    """A ghost on either of two cost lines nulls the three figures.

    The ghost is last in source order in one case and first in the other, and
    last in sorted order in both. A check that read only the first sorted
    total, or only the last source line, would pass a selection that makes
    plates on to the solve, which refuses the ghost under the wrong reason.

    Args:
        lines: The two cost lines, one a plate and one the late ghost.
    """
    assert PLATE_ITEM < LATE_GHOST_ITEM
    registry = synthetic_registry()
    ghost_declared = LATE_GHOST_ITEM in registry.items
    assert not ghost_declared
    source = MeasuredSource(entries={COSTED_PHASE: lines})
    cost = phases.phase_cost(source, registry, COSTED_PHASE, selection())
    machine_reason = cost.machine.reason
    assert machine_reason == phases.REASON_UNRESOLVED_COST_ITEM
    reasons_named = null_reasons(cost) == [phases.REASON_UNRESOLVED_COST_ITEM] * 3
    assert reasons_named
    all_null = rendered_nulls(cost) == [True, True, True]
    assert all_null
    detail = cost.machine.detail
    assert detail == LATE_GHOST_ITEM
    required = cost.required.values
    assert required is not None
    required_keys_kept = sorted(required) == [PLATE_ITEM, LATE_GHOST_ITEM]
    assert required_keys_kept


# ---------------------------------------------------------------------------
# CS-1343, CS-1348 amended - paid_off and held are derived from the table
# ---------------------------------------------------------------------------
#
# THE NAMES BELOW ARE KEPT, THE CLAIM IN THEM IS NOT. `docs/LEDGER.md` cites
# four arms of this section by name, and it is append-only. CS-1348's amended
# acceptance replaced the table's one `delivered` reading with two - `paid_off`
# and `held`, never summed - so each arm keeps its cited name and grades the
# two readings that replaced the one it was written for.

#: The machine-figure reason each publishing path in ``delivered_sweep`` must
#: reach, in its order - None for the solved chain. Asserting it proves every
#: path was entered, so no flag below is read off a path that never ran.
SWEEP_REASONS: Final = [
    phases.REASON_NO_PHASE_COST_TABLE,
    phases.REASON_NO_COST_ENTRY,
    phases.REASON_EMPTY_COST_ENTRY,
    phases.REASON_NONPOSITIVE_COST,
    phases.REASON_UNRESOLVED_COST_ITEM,
    phases.REASON_NO_RECIPE_SELECTION,
    phases.REASON_RATIO_REFUSED,
    None,
]

#: A paid-off reading for every phase the sweep selects, at one item's zero.
PAID_ZERO: Final[Mapping[str, Mapping[str, Fraction]]] = MappingProxyType(
    {
        COSTED_PHASE: MappingProxyType({PLATE_ITEM: Fraction(0)}),
        UNCOSTED_PHASE: MappingProxyType({PLATE_ITEM: Fraction(0)}),
    }
)


class ReadingSource:
    """A synthetic source that carries paid-off and held readings, measured or not."""

    def __init__(
        self,
        entries: Mapping[str, tuple[CostLine, ...]] | None,
        paid_off: Mapping[str, Mapping[str, Fraction]] | None,
        held: Mapping[str, Fraction] | None,
    ) -> None:
        """Hold the table this source publishes.

        Args:
            entries: Phase to cost lines, or None for an unmeasured table.
            paid_off: The paid-off reading by phase, or None for no reading.
            held: The input reading, or None for no reading.
        """
        self._entries = None if entries is None else MappingProxyType(dict(entries))
        self._paid_off = paid_off
        self._held = held

    def phase_costs(self) -> phases.PhaseCostTable:
        """Publish the table.

        Returns:
            The table, unmeasured when no entries were given.
        """
        reason = phases.REASON_NO_PHASE_COST_TABLE if self._entries is None else None
        return phases.PhaseCostTable(
            entries=self._entries, reason=reason, paid_off=self._paid_off, held=self._held
        )


def delivered_sweep(
    paid_off: Mapping[str, Mapping[str, Fraction]] | None,
    held: Mapping[str, Fraction] | None,
) -> list[tuple[str | None, bool, bool]]:
    """Read both flags off every path in the module that builds a phase cost.

    The paths, in :data:`SWEEP_REASONS` order: an unmeasured table, a phase
    with no entry, an empty entry, a non-positive cost, an unresolved cost
    item, no recipe selection, a ratio refusal and the solved chain. Each runs
    over a source carrying the two readings, so a site that hard-coded either
    flag reddens on its own row.

    Args:
        paid_off: The paid-off reading every source carries, or None.
        held: The input reading every source carries, or None.

    Returns:
        One (machine reason, ``paid_off_available``, ``held_available``) per path.
    """
    registry = synthetic_registry()
    starved = phases.RecipeSelection(
        recipes=(PLATE_RECIPE,),
        raw_items=(ORE_ITEM, WATER_ITEM),
        byproduct_policy=BYPRODUCT_BALANCED,
        extractors=MappingProxyType({ORE_ITEM: MINER, WATER_ITEM: PUMP}),
    )
    plate = (CostLine(PLATE_ITEM, Fraction(PLATE_COST)),)
    cases: tuple[
        tuple[Mapping[str, tuple[CostLine, ...]] | None, str, phases.RecipeSelection | None], ...
    ] = (
        (None, COSTED_PHASE, selection()),
        ({COSTED_PHASE: plate}, UNCOSTED_PHASE, selection()),
        ({COSTED_PHASE: ()}, COSTED_PHASE, selection()),
        ({COSTED_PHASE: (CostLine(PLATE_ITEM, Fraction(0)),)}, COSTED_PHASE, selection()),
        ({COSTED_PHASE: (CostLine(GHOST_ITEM, Fraction(PLATE_COST)),)}, COSTED_PHASE, selection()),
        ({COSTED_PHASE: plate}, COSTED_PHASE, None),
        ({COSTED_PHASE: plate}, COSTED_PHASE, starved),
        ({COSTED_PHASE: plate}, COSTED_PHASE, selection()),
    )
    readings: list[tuple[str | None, bool, bool]] = []
    for entries, phase, chosen in cases:
        source = ReadingSource(entries, paid_off, held)
        cost = phases.phase_cost(source, registry, phase, chosen)
        readings.append((cost.machine.reason, cost.paid_off_available, cost.held_available))
    return readings


def test_the_shipped_source_publishes_delivered_available_false_required_only() -> None:
    """No paid-off and no held reading, so both flags read False on every path.

    The shipped save source over a world with neither reading publishes
    neither, and a measured table whose source carries none reads False too,
    on every path that builds a phase cost. The required figure is the whole
    cost over the budget, with nothing taken off it. The name is kept because
    ``docs/LEDGER.md`` and ``docs/history_notes.md`` cite it.
    """
    source = no_table_source()
    shipped = phases.phase_cost(source, synthetic_registry(), COSTED_PHASE, selection())
    assert (shipped.paid_off_available, shipped.held_available) == (False, False)
    table = source.phase_costs()
    assert (table.paid_off, table.held) == (None, None)
    measured = phases.phase_cost(MeasuredSource(), synthetic_registry(), COSTED_PHASE, selection())
    assert (measured.paid_off_available, measured.held_available) == (False, False)
    required = measured.required.values
    assert required is not None
    assert dict(required) == {PLATE_ITEM: Fraction(PLATE_COST, TWO_HOURS_IN_MINUTES)}
    readings = delivered_sweep(None, None)
    assert [reason for reason, _, _ in readings] == SWEEP_REASONS
    assert [(paid, held) for _, paid, held in readings] == [(False, False)] * len(SWEEP_REASONS)


def test_delivered_available_is_derived_with_a_zero_count_reading_true() -> None:
    """A present reading reads True, even when it counts nothing - each on its own.

    A zero-count reading is still a reading. A paid-off reading of one item at
    zero, and an EMPTY held reading, each turn their own flag True and leave
    the other False, on every path - so a flag derived from the counts, from
    truthiness, or from the other reading reddens. The unmeasured table on the
    first path keeps its readings, so the flags follow the readings and not the
    cost table - and ``phase_costs_available`` still reads False beside them.
    """
    paid = delivered_sweep(PAID_ZERO, None)
    assert [reason for reason, _, _ in paid] == SWEEP_REASONS
    assert [(p, h) for _, p, h in paid] == [(True, False)] * len(SWEEP_REASONS)
    empty: Mapping[str, Fraction] = MappingProxyType({})
    held = delivered_sweep(None, empty)
    assert [reason for reason, _, _ in held] == SWEEP_REASONS
    assert [(p, h) for _, p, h in held] == [(False, True)] * len(SWEEP_REASONS)
    unmeasured = ReadingSource(None, PAID_ZERO, empty)
    assert phases.phase_costs_available(unmeasured) is False


def test_a_paid_off_reading_is_per_phase_never_another_phases() -> None:
    """A paid-off reading for one phase never sets the flag on another."""
    only_costed = MappingProxyType({COSTED_PHASE: MappingProxyType({PLATE_ITEM: Fraction(0)})})
    source = ReadingSource(None, only_costed, None)
    registry = synthetic_registry()
    costed = phases.phase_cost(source, registry, COSTED_PHASE, selection())
    other = phases.phase_cost(source, registry, UNCOSTED_PHASE, selection())

    assert costed.paid_off_available is True
    assert other.paid_off_available is False


def test_a_delivered_reading_holds_exact_non_negative_counts_only() -> None:
    """Every paid-off and held count is an exact Fraction at zero or above.

    The zero-count table is the control: it constructs, so each refusal below
    is about its own value and not about a reading being present at all. The
    float has a case of its own, so a check that let a float through beside a
    Fraction reddens here and not only under the module's source scan. The
    name is kept because ``docs/LEDGER.md`` cites it.
    """
    reason = phases.REASON_NO_PHASE_COST_TABLE
    zero = MappingProxyType({PLATE_ITEM: Fraction(0)})
    table = phases.PhaseCostTable(
        entries=None, reason=reason, paid_off=MappingProxyType({COSTED_PHASE: zero}), held=zero
    )
    assert table.held is zero
    not_a_fraction = cast("Fraction", 1)
    a_float = cast("Fraction", 0.5)
    for bad in (Fraction(-1), not_a_fraction, a_float):
        counts = MappingProxyType({PLATE_ITEM: bad})
        with pytest.raises(phases.PhaseIntegrityError):
            phases.PhaseCostTable(entries=None, reason=reason, held=counts)
        with pytest.raises(phases.PhaseIntegrityError):
            phases.PhaseCostTable(
                entries=None, reason=reason, paid_off=MappingProxyType({COSTED_PHASE: counts})
            )


def test_a_table_refuses_a_phase_both_withheld_and_paid_off() -> None:
    """A phase withheld as unmapped is never also presented as paid off."""
    reason = phases.REASON_NO_PHASE_COST_TABLE
    paid = MappingProxyType({COSTED_PHASE: MappingProxyType({PLATE_ITEM: Fraction(1)})})
    beside = phases.PhaseCostTable(
        entries=None, reason=reason, paid_off=paid, unmapped=frozenset({UNCOSTED_PHASE})
    )
    assert beside.unmapped == frozenset({UNCOSTED_PHASE})
    with pytest.raises(phases.PhaseIntegrityError):
        phases.PhaseCostTable(
            entries=None, reason=reason, paid_off=paid, unmapped=frozenset({COSTED_PHASE})
        )


#: The synthetic schematic whose document cost the schematic-document arm reads.
PHASE_SCHEMATIC: Final = "Schematic_SynthElevatorPhase_C"


class TableSource:
    """A synthetic source that publishes one table exactly as it was built."""

    def __init__(self, table: phases.PhaseCostTable) -> None:
        """Hold the table this source publishes.

        Args:
            table: The table.
        """
        self._table = table

    def phase_costs(self) -> phases.PhaseCostTable:
        """Publish the table.

        Returns:
            The table as built.
        """
        return self._table


def test_delivered_available_is_graded_on_a_synthetic_schematic_document() -> None:
    """Cost lines normalized from a hand-authored schematic document carry the flags.

    One synthetic schematic costing the plates is loaded through the real
    docs_extract seam with the milestone arms' own builders, and normalized by
    :func:`clockspeed.data.schematics.normalize_schematics`. Its cost lines
    become the phase's entry in a table carrying a zero-count paid-off reading
    and an empty held reading, which read True; the same table with neither
    reads False. The required figure is the hand-worked 25/3 a minute on both,
    so the document's lines drove the required rate and nothing paid or held
    came off it. The name is kept because ``docs/LEDGER.md`` cites it.
    """
    blob = synthetic.amount_blob([(PLATE_ITEM, PLATE_COST)])
    catalog = normalize_schematics(
        schematic_document([schematic_entry(PHASE_SCHEMATIC, **{KEY_COST: blob})])
    )
    lines = catalog.schematics[PHASE_SCHEMATIC].cost
    assert lines is not None
    assert lines == (CostLine(PLATE_ITEM, Fraction(PLATE_COST)),)
    read = phases.PhaseCostTable(
        entries=MappingProxyType({COSTED_PHASE: lines}),
        reason=None,
        paid_off=PAID_ZERO,
        held=MappingProxyType({}),
    )
    unread = dataclasses.replace(read, paid_off=None, held=None)
    required_rate = {PLATE_ITEM: Fraction(PLATE_COST, TWO_HOURS_IN_MINUTES)}
    registry = synthetic_registry()
    with_reading = phases.phase_cost(TableSource(read), registry, COSTED_PHASE, selection())
    assert (with_reading.paid_off_available, with_reading.held_available) == (True, True)
    assert with_reading.required.values is not None
    assert dict(with_reading.required.values) == required_rate
    without = phases.phase_cost(TableSource(unread), registry, COSTED_PHASE, selection())
    assert (without.paid_off_available, without.held_available) == (False, False)
    assert without.required.values is not None
    assert dict(without.required.values) == required_rate


# ---------------------------------------------------------------------------
# CS-1340 round 3 - the table refuses a skip count or a withheld phase it cannot hold
# ---------------------------------------------------------------------------


def test_a_table_refuses_a_skip_count_that_is_not_an_int_at_zero_or_above() -> None:
    """A skip count is a count: an int at zero or above, and a bool is not one.

    The count of one constructs, so each refusal is about its own value.
    Kills the mutant that drops the check.
    """
    plate = MappingProxyType({COSTED_PHASE: (CostLine(PLATE_ITEM, Fraction(PLATE_COST)),)})
    table = phases.PhaseCostTable(entries=plate, reason=None, skipped_count=1)
    assert table.skipped_count == 1
    for bad in (-1, True, cast("int", Fraction(1))):
        with pytest.raises(phases.PhaseIntegrityError):
            phases.PhaseCostTable(entries=plate, reason=None, skipped_count=bad)


def test_a_table_refuses_a_phase_both_withheld_and_published() -> None:
    """A withheld phase is never also an entry: the two would contradict each other.

    A phase withheld beside a DIFFERENT published one constructs, so the
    refusal is about the overlap. Kills the mutant that drops the check.
    """
    plate = MappingProxyType({COSTED_PHASE: (CostLine(PLATE_ITEM, Fraction(PLATE_COST)),)})
    beside = phases.PhaseCostTable(entries=plate, reason=None, unmapped=frozenset({UNCOSTED_PHASE}))
    assert beside.unmapped == frozenset({UNCOSTED_PHASE})
    with pytest.raises(phases.PhaseIntegrityError):
        phases.PhaseCostTable(entries=plate, reason=None, unmapped=frozenset({COSTED_PHASE}))
