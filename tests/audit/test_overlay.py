"""CS-1236: the what-if overlay - virtual edits over a measured world, never written back.

Every recipe here comes from the hand-authored synthetic SOLVER corpus,
``tests/solve/synthetic.py``, through the real ``docs_extract`` and
``build_registry`` seam. Every machine is a synthetic ``MachineState`` literal
authored in this module. Nothing opens a save, a docs file or the install - and
one arm below proves the module under test opens nothing at all.

THE RATES ARE RE-DERIVED FROM THE CORPUS CONSTANTS, never read back out of the
module under test: R_Plate turns one ore into one plate every
``PLATE_DURATION_S`` seconds, so one machine at clock one moves
``60 / PLATE_DURATION_S`` plates per minute.

THE DEFECTS GRADED HARDEST are the three that would make an overlay lie: a
remove of more machines than exist CLAMPED to what exists instead of refused by
name; an unknown recipe ADDED as if it flowed; and a measured model MUTATED by
the evaluation, which would leak a what-if into the real world's answer.
"""

from __future__ import annotations

import builtins
import copy
import dataclasses
import io
import json
import os
import subprocess
import sys
from collections.abc import Mapping
from fractions import Fraction
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from clockspeed.audit import balance, flow, overlay
from clockspeed.audit.machines import MachineState, WorldMachines
from clockspeed.solve import exact
from tests.audit import plan_world
from tests.solve import synthetic

if TYPE_CHECKING:
    from clockspeed.audit.placement import WorldPlacement
    from clockspeed.data.registry import Building, Recipe

_SMELTER = synthetic.SOLVE_SMELTER_BUILDING
_ASSEMBLER = synthetic.SOLVE_ASSEMBLER_BUILDING
_PLATE = synthetic.SOLVE_PLATE_ITEM
_ROD = synthetic.SOLVE_ROD_ITEM
_TRINKET = synthetic.SOLVE_TRINKET_ITEM
_R_PLATE = synthetic.PLATE_RECIPE
_R_ROD = synthetic.ROD_RECIPE
_STD = synthetic.STD_GADGET_RECIPE
_ALT = synthetic.ALT_GADGET_RECIPE
_HANDCRAFT = synthetic.ZERO_DURATION_RECIPE

_MINUTE = Fraction(synthetic.SECONDS_PER_MINUTE)
#: One R_Plate machine at clock one, per minute - derived from the corpus.
_PLATE_RATE = _MINUTE / synthetic.PLATE_DURATION_S
#: One R_Rod machine at clock one, plates eaten and rods made per minute.
_ROD_RATE = _MINUTE / synthetic.ROD_DURATION_S
#: One Std_Gadget machine: one trinket per cycle.
_STD_TRINKETS = _MINUTE / synthetic.GADGET_DURATION_S
#: One Alt_Gadget machine: three trinkets per cycle, same duration.
_ALT_TRINKETS = 3 * _MINUTE / synthetic.GADGET_DURATION_S

_UNKNOWN_RECIPE = "R_SolveNeverAuthored"

_HALF = Fraction(1, 2)
_ONE = Fraction(1)
_THREE_HALVES = Fraction(3, 2)

#: A whole evaluation serialises to far more than this; less means a field went missing.
_MIN_CANONICAL_BYTES = 1000
#: How many stand-in files the never-write arm plants.
_STANDIN_FILES = 3


def _machine(building: str, recipe: str, clock: Fraction) -> MachineState:
    """One synthetic producing machine.

    Args:
        building: The building class.
        recipe: The recipe class.
        clock: The exact clock.

    Returns:
        The state.
    """
    return MachineState(
        class_name=building, producing=True, recipe_class_name=recipe, overclock=clock
    )


#: The base world: two plate smelters at one, one rod smelter at a half, two
#: standard gadget assemblers at one.
_STATES = (
    _machine(_SMELTER, _R_PLATE, _ONE),
    _machine(_SMELTER, _R_PLATE, _ONE),
    _machine(_SMELTER, _R_ROD, _HALF),
    _machine(_ASSEMBLER, _STD, _ONE),
    _machine(_ASSEMBLER, _STD, _ONE),
)


@pytest.fixture(name="recipes", scope="module")
def recipes_fixture() -> dict[str, Recipe]:
    """The corpus recipes, keyed the way a caller supplies them.

    Returns:
        A plain dict.
    """
    return dict(synthetic.solve_registry().recipes)


@pytest.fixture(name="buildings", scope="module")
def buildings_fixture() -> dict[str, Building]:
    """The corpus buildings.

    Returns:
        A plain dict.
    """
    return dict(synthetic.solve_registry().buildings)


@pytest.fixture(name="machines")
def machines_fixture() -> WorldMachines:
    """The base world's machines.

    Returns:
        The model.
    """
    return plan_world.machines_model(_STATES)


@pytest.fixture(name="placement")
def placement_fixture() -> WorldPlacement:
    """The base world's built counts.

    Returns:
        The model.
    """
    return plan_world.placement_model(_STATES)


def _count(machines: WorldMachines, recipe: str) -> int:
    return sum(1 for state in machines.machines if state.recipe_class_name == recipe)


def _codes(warnings: tuple[object, ...]) -> list[str]:
    return [warning.code for warning in warnings]  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# The four edit kinds
# ---------------------------------------------------------------------------


def test_an_empty_overlay_recomputes_the_same_flow(
    machines: WorldMachines, recipes: dict[str, Recipe]
) -> None:
    result = overlay.evaluate_overlay(machines, overlay.Overlay(edits=()), recipes)

    assert result.after_flow == result.before_flow
    assert result.before_flow == flow.flow_of(machines, recipes)
    assert result.application.records == ()
    assert all(delta.delta == 0 for delta in result.items)


def test_adding_machines_raises_the_flow_by_the_exact_clock_scaled_rate(
    machines: WorldMachines, recipes: dict[str, Recipe]
) -> None:
    edit = overlay.AddMachines(recipe_class_name=_R_PLATE, count=2, clock=_THREE_HALVES)
    result = overlay.evaluate_overlay(machines, overlay.Overlay(edits=(edit,)), recipes)

    before = result.before_flow.items[_PLATE].produced
    after = result.after_flow.items[_PLATE].produced
    assert before == 2 * _PLATE_RATE
    assert after == before + 2 * _THREE_HALVES * _PLATE_RATE
    (record,) = result.application.records
    assert record.index == 0
    assert record.edit is edit
    assert record.kind == overlay.KIND_ADD
    assert record.outcome == overlay.OUTCOME_APPLIED
    assert record.reason is None
    assert (record.count_before, record.count_after, record.machines_changed) == (2, 4, 2)
    added = result.application.machines.machines[-2:]
    assert all(state.class_name == _SMELTER for state in added)
    assert all(state.overclock == _THREE_HALVES for state in added)
    # A virtual machine was never measured, so its producing flag is unread.
    assert all(state.producing is None for state in added)


def test_adding_machines_raises_the_draw_by_the_resolved_building(
    machines: WorldMachines,
    placement: WorldPlacement,
    recipes: dict[str, Recipe],
    buildings: dict[str, Building],
) -> None:
    edit = overlay.AddMachines(recipe_class_name=_R_PLATE, count=3, clock=_ONE)
    result = overlay.evaluate_overlay(
        machines, overlay.Overlay(edits=(edit,)), recipes, placement=placement, buildings=buildings
    )

    assert result.before_draw == balance.draw_of(placement, buildings)
    assert result.after_draw is not None
    assert result.before_draw is not None
    assert (
        result.after_draw.consumption_megawatts
        == result.before_draw.consumption_megawatts + 3 * synthetic.SMELTER_POWER_MW
    )
    after_placement = result.application.placement
    assert after_placement is not None
    assert after_placement.built_counts[_SMELTER] == placement.built_counts[_SMELTER] + 3


def test_an_explicit_building_overrides_the_recipe_resolution(
    machines: WorldMachines, placement: WorldPlacement, recipes: dict[str, Recipe]
) -> None:
    edit = overlay.AddMachines(
        recipe_class_name=_R_PLATE, count=1, clock=_ONE, building_class_name=_ASSEMBLER
    )
    result = overlay.apply_overlay(
        machines, overlay.Overlay(edits=(edit,)), recipes, placement=placement
    )

    assert result.machines.machines[-1].class_name == _ASSEMBLER
    assert result.placement is not None
    assert result.placement.built_counts[_ASSEMBLER] == placement.built_counts[_ASSEMBLER] + 1


def test_an_add_whose_building_cannot_be_resolved_is_a_named_refusal(
    machines: WorldMachines, recipes: dict[str, Recipe]
) -> None:
    # The build-gun recipe names no automated producer, so no machine class.
    edit = overlay.AddMachines(recipe_class_name=_HANDCRAFT, count=1, clock=_ONE)
    result = overlay.apply_overlay(machines, overlay.Overlay(edits=(edit,)), recipes)

    (record,) = result.records
    assert record.outcome == overlay.OUTCOME_REFUSED
    assert record.reason == overlay.REFUSED_BUILDING_UNRESOLVED
    assert result.machines == machines
    assert overlay.WARN_OVERLAY_EDIT_REFUSED in _codes(result.warnings)


def test_removing_machines_takes_the_last_ones_and_lowers_flow_and_count(
    machines: WorldMachines,
    placement: WorldPlacement,
    recipes: dict[str, Recipe],
    buildings: dict[str, Building],
) -> None:
    edit = overlay.RemoveMachines(recipe_class_name=_R_PLATE, count=1)
    result = overlay.evaluate_overlay(
        machines, overlay.Overlay(edits=(edit,)), recipes, placement=placement, buildings=buildings
    )

    assert result.after_flow.items[_PLATE].produced == _PLATE_RATE
    (record,) = result.application.records
    assert (record.count_before, record.count_after, record.machines_changed) == (2, 1, 1)
    after_placement = result.application.placement
    assert after_placement is not None
    assert after_placement.built_counts[_SMELTER] == placement.built_counts[_SMELTER] - 1
    assert result.after_draw is not None
    assert result.before_draw is not None
    assert (
        result.after_draw.consumption_megawatts
        == result.before_draw.consumption_megawatts - synthetic.SMELTER_POWER_MW
    )
    # The LAST plate machine went: the first survives at its own index.
    assert result.application.machines.machines[0] == _STATES[0]
    assert result.application.machines.machines[1] == _STATES[2]


def test_removing_more_machines_than_exist_is_a_named_refusal_not_a_clamp(
    machines: WorldMachines, recipes: dict[str, Recipe]
) -> None:
    edit = overlay.RemoveMachines(recipe_class_name=_R_ROD, count=3)
    result = overlay.evaluate_overlay(machines, overlay.Overlay(edits=(edit,)), recipes)

    (record,) = result.application.records
    assert record.outcome == overlay.OUTCOME_REFUSED
    assert record.reason == overlay.REFUSED_TOO_FEW_MACHINES
    # A clamp would have removed the one rod machine. A refusal removes none.
    assert record.machines_changed == 0
    assert (record.count_before, record.count_after) == (1, 1)
    assert _count(result.application.machines, _R_ROD) == 1
    assert result.after_flow == result.before_flow
    assert overlay.WARN_OVERLAY_EDIT_REFUSED in _codes(result.warnings)


def test_a_remove_the_placement_cannot_cover_is_a_named_refusal(
    machines: WorldMachines, placement: WorldPlacement, recipes: dict[str, Recipe]
) -> None:
    # The placement saw fewer smelters than the machine reader did - a
    # placement filter can drop records - so decrementing would go negative.
    short = dataclasses.replace(placement, built_counts={_SMELTER: 1, _ASSEMBLER: 2})
    edit = overlay.RemoveMachines(recipe_class_name=_R_PLATE, count=2)
    result = overlay.apply_overlay(
        machines, overlay.Overlay(edits=(edit,)), recipes, placement=short
    )

    (record,) = result.records
    assert record.outcome == overlay.OUTCOME_REFUSED
    assert record.reason == overlay.REFUSED_PLACEMENT_SHORT
    assert result.machines == machines
    assert result.placement == short


def test_swapping_a_recipe_keeps_clocks_and_buildings_and_moves_the_flow(
    machines: WorldMachines,
    placement: WorldPlacement,
    recipes: dict[str, Recipe],
    buildings: dict[str, Building],
) -> None:
    edit = overlay.SwapRecipe(from_recipe=_STD, to_recipe=_ALT)
    result = overlay.evaluate_overlay(
        machines, overlay.Overlay(edits=(edit,)), recipes, placement=placement, buildings=buildings
    )

    assert result.before_flow.items[_TRINKET].produced == 2 * _STD_TRINKETS
    assert result.after_flow.items[_TRINKET].produced == 2 * _ALT_TRINKETS
    (record,) = result.application.records
    assert record.kind == overlay.KIND_SWAP
    assert (record.count_before, record.count_after) == (2, 0)
    assert (record.target_count_before, record.target_count_after) == (0, 2)
    assert record.machines_changed == len(swapped_states := _STATES[3:])
    assert all(state.recipe_class_name == _STD for state in swapped_states)
    assert result.after_draw == result.before_draw
    swapped = result.application.machines.machines[3:]
    assert all(state.class_name == _ASSEMBLER and state.overclock == _ONE for state in swapped)


def test_a_counted_swap_moves_only_the_first_n(
    machines: WorldMachines, recipes: dict[str, Recipe]
) -> None:
    edit = overlay.SwapRecipe(from_recipe=_STD, to_recipe=_ALT, count=1)
    result = overlay.apply_overlay(machines, overlay.Overlay(edits=(edit,)), recipes)

    assert result.machines.machines[3].recipe_class_name == _ALT
    assert result.machines.machines[4].recipe_class_name == _STD


def test_a_swap_of_more_than_exist_and_a_swap_to_itself_are_named_refusals(
    machines: WorldMachines, recipes: dict[str, Recipe]
) -> None:
    edits = (
        overlay.SwapRecipe(from_recipe=_STD, to_recipe=_ALT, count=3),
        overlay.SwapRecipe(from_recipe=_ALT, to_recipe=_STD),
        overlay.SwapRecipe(from_recipe=_STD, to_recipe=_STD),
    )
    result = overlay.apply_overlay(machines, overlay.Overlay(edits=edits), recipes)

    assert [record.reason for record in result.records] == [
        overlay.REFUSED_TOO_FEW_MACHINES,
        overlay.REFUSED_TOO_FEW_MACHINES,
        overlay.REFUSED_SWAP_TO_SELF,
    ]
    assert result.machines == machines
    refused = [w for w in result.warnings if w.code == overlay.WARN_OVERLAY_EDIT_REFUSED]
    assert [w.count for w in refused] == [3]


def test_raising_a_target_names_the_new_deficit(
    machines: WorldMachines, recipes: dict[str, Recipe]
) -> None:
    asked = 5 * _PLATE_RATE
    edit = overlay.SetDemand(item_key=_PLATE, rate=asked)
    result = overlay.evaluate_overlay(machines, overlay.Overlay(edits=(edit,)), recipes)

    assert _PLATE not in [item.item_key for item in result.before_flow.deficits]
    after = result.after_flow.items[_PLATE]
    assert after.demand == asked
    assert after.is_deficit
    assert after.shortfall == asked - after.net
    (record,) = result.application.records
    assert record.kind == overlay.KIND_DEMAND
    assert (record.demand_before, record.demand_after) == (Fraction(0), asked)
    assert result.application.demands[_PLATE] == asked


def test_a_demand_edit_replaces_the_callers_demand_and_leaves_the_rest(
    machines: WorldMachines, recipes: dict[str, Recipe]
) -> None:
    base = {_ROD: _ROD_RATE, _PLATE: _ONE}
    edit = overlay.SetDemand(item_key=_PLATE, rate=Fraction(7))
    result = overlay.evaluate_overlay(
        machines, overlay.Overlay(edits=(edit,)), recipes, demands=base
    )

    assert result.before_flow.items[_PLATE].demand == _ONE
    assert result.after_flow.items[_PLATE].demand == Fraction(7)
    assert result.after_flow.items[_ROD].demand == _ROD_RATE
    assert base == {_ROD: _ROD_RATE, _PLATE: _ONE}


def test_an_unknown_recipe_is_flagged_and_skipped_never_flowed(
    machines: WorldMachines, recipes: dict[str, Recipe]
) -> None:
    edits = (
        overlay.AddMachines(
            recipe_class_name=_UNKNOWN_RECIPE, count=4, clock=_ONE, building_class_name=_SMELTER
        ),
        overlay.SwapRecipe(from_recipe=_STD, to_recipe=_UNKNOWN_RECIPE),
    )
    result = overlay.evaluate_overlay(machines, overlay.Overlay(edits=edits), recipes)

    assert [record.outcome for record in result.application.records] == [
        overlay.OUTCOME_SKIPPED,
        overlay.OUTCOME_SKIPPED,
    ]
    assert [record.reason for record in result.application.records] == [
        overlay.SKIPPED_RECIPE_UNKNOWN,
        overlay.SKIPPED_RECIPE_UNKNOWN,
    ]
    assert result.application.machines == machines
    assert result.after_flow == result.before_flow
    unknown = [w for w in result.warnings if w.code == overlay.WARN_OVERLAY_RECIPE_UNKNOWN]
    assert [w.count for w in unknown] == [2]


def test_edits_apply_in_order_each_over_the_previous_result(
    machines: WorldMachines, recipes: dict[str, Recipe]
) -> None:
    # Removing two rod machines is refused against the base world (one exists)
    # and applies once the add before it has run.
    edits = (
        overlay.AddMachines(recipe_class_name=_R_ROD, count=1, clock=_ONE),
        overlay.RemoveMachines(recipe_class_name=_R_ROD, count=2),
    )
    result = overlay.apply_overlay(machines, overlay.Overlay(edits=edits), recipes)

    assert [record.outcome for record in result.records] == [
        overlay.OUTCOME_APPLIED,
        overlay.OUTCOME_APPLIED,
    ]
    assert [record.index for record in result.records] == [0, 1]
    assert _count(result.machines, _R_ROD) == 0


# ---------------------------------------------------------------------------
# The value and its refusals
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "build",
    [
        lambda: overlay.AddMachines(recipe_class_name=_R_PLATE, count=0, clock=_ONE),
        lambda: overlay.AddMachines(recipe_class_name=_R_PLATE, count=True, clock=_ONE),
        lambda: overlay.AddMachines(recipe_class_name=_R_PLATE, count=1, clock=Fraction(-1)),
        lambda: overlay.AddMachines(recipe_class_name="", count=1, clock=_ONE),
        lambda: overlay.RemoveMachines(recipe_class_name=_R_PLATE, count=-1),
        lambda: overlay.SwapRecipe(from_recipe=_STD, to_recipe=_ALT, count=0),
        lambda: overlay.SetDemand(item_key=_PLATE, rate=Fraction(-1)),
        lambda: overlay.Overlay(
            edits=[overlay.RemoveMachines(recipe_class_name=_R_PLATE, count=1)]  # type: ignore[arg-type]
        ),
        lambda: overlay.Overlay(edits=("not an edit",)),  # type: ignore[arg-type]
    ],
    ids=[
        "zero-count",
        "bool-count",
        "negative-clock",
        "empty-recipe",
        "negative-remove",
        "zero-swap",
        "negative-demand",
        "list-not-tuple",
        "foreign-member",
    ],
)
def test_a_malformed_edit_is_refused_at_construction(build: object) -> None:
    with pytest.raises(overlay.OverlayEditError):
        build()  # type: ignore[operator]


@pytest.mark.parametrize(
    "build",
    [
        lambda: overlay.AddMachines(recipe_class_name=_R_PLATE, count=1, clock=1.5),  # type: ignore[arg-type]
        lambda: overlay.AddMachines(recipe_class_name=_R_PLATE, count=1, clock=1),  # type: ignore[arg-type]
        lambda: overlay.SetDemand(item_key=_PLATE, rate=0.5),  # type: ignore[arg-type]
    ],
    ids=["float-clock", "int-clock", "float-rate"],
)
def test_an_inexact_number_is_refused_rather_than_converted(build: object) -> None:
    with pytest.raises(exact.InexactValueError):
        build()  # type: ignore[operator]


def test_the_overlay_and_its_edits_are_immutable() -> None:
    edit = overlay.RemoveMachines(recipe_class_name=_R_PLATE, count=1)
    value = overlay.Overlay(edits=(edit,))

    with pytest.raises(dataclasses.FrozenInstanceError):
        edit.count = 2  # type: ignore[misc]
    with pytest.raises(dataclasses.FrozenInstanceError):
        value.edits = ()  # type: ignore[misc]
    assert isinstance(value.edits, tuple)
    assert hash(value) == hash(overlay.Overlay(edits=(edit,)))


def test_no_rendering_names_a_recipe_or_an_item() -> None:
    edits = (
        overlay.AddMachines(recipe_class_name=_R_PLATE, count=1, clock=_ONE),
        overlay.RemoveMachines(recipe_class_name=_R_PLATE, count=1),
        overlay.SwapRecipe(from_recipe=_STD, to_recipe=_ALT),
        overlay.SetDemand(item_key=_PLATE, rate=_ONE),
    )
    renderings = [repr(edit) for edit in edits] + [repr(overlay.Overlay(edits=edits))]

    for rendering in renderings:
        for name in (_R_PLATE, _STD, _ALT, _PLATE):
            assert name not in rendering, rendering


# ---------------------------------------------------------------------------
# Purity: exact, unmutated, deterministic, and opening nothing
# ---------------------------------------------------------------------------


def _mixed_overlay() -> overlay.Overlay:
    return overlay.Overlay(
        edits=(
            overlay.AddMachines(recipe_class_name=_R_ROD, count=2, clock=Fraction(5, 4)),
            overlay.RemoveMachines(recipe_class_name=_R_PLATE, count=1),
            overlay.SwapRecipe(from_recipe=_STD, to_recipe=_ALT, count=1),
            overlay.SetDemand(item_key=_ROD, rate=Fraction(40, 3)),
            overlay.RemoveMachines(recipe_class_name=_R_PLATE, count=9),
            overlay.AddMachines(recipe_class_name=_UNKNOWN_RECIPE, count=1, clock=_ONE),
        )
    )


def _evaluate_mixed() -> overlay.OverlayEvaluation:
    registry = synthetic.solve_registry()
    return overlay.evaluate_overlay(
        plan_world.machines_model(_STATES),
        _mixed_overlay(),
        dict(registry.recipes),
        placement=plan_world.placement_model(_STATES),
        buildings=dict(registry.buildings),
        raw_items=(synthetic.SOLVE_ORE_ITEM,),
    )


def _plain(value: object) -> object:
    """Reduce a result to JSON-ready primitives, every field and every member.

    Args:
        value: Anything the module under test returns.

    Returns:
        The plain form. A Fraction renders as ``num/den``, a mapping with its
        keys sorted, a dataclass with its type name.
    """
    if isinstance(value, Fraction):
        return f"{value.numerator}/{value.denominator}"
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return {
            "__type__": type(value).__name__,
            **{
                field.name: _plain(getattr(value, field.name))
                for field in dataclasses.fields(value)
            },
        }
    if isinstance(value, Mapping):
        return {str(key): _plain(value[key]) for key in sorted(value)}
    if isinstance(value, tuple | list):
        return [_plain(member) for member in value]
    if value is None or isinstance(value, bool | int | str):
        return value
    raise TypeError(type(value).__name__)


def canonical_mixed() -> str:
    """The canonical serialisation of the mixed evaluation.

    Returns:
        Sorted-key JSON.
    """
    return json.dumps(_plain(_evaluate_mixed()), sort_keys=True, separators=(",", ":"))


def test_the_evaluation_is_exact_all_the_way_down() -> None:
    exact.audit_exact(_evaluate_mixed(), path="evaluation")


def test_the_mixed_overlay_records_one_line_per_edit_in_order() -> None:
    result = _evaluate_mixed()

    records = result.application.records
    assert [record.index for record in records] == list(range(len(_mixed_overlay().edits)))
    assert [record.outcome for record in records] == [
        overlay.OUTCOME_APPLIED,
        overlay.OUTCOME_APPLIED,
        overlay.OUTCOME_APPLIED,
        overlay.OUTCOME_APPLIED,
        overlay.OUTCOME_REFUSED,
        overlay.OUTCOME_SKIPPED,
    ]
    keys = [delta.item_key for delta in result.items]
    assert keys == sorted(set(result.before_flow.items) | set(result.after_flow.items))
    for delta in result.items:
        assert delta.delta == delta.net_after - delta.net_before


def test_the_measured_models_are_never_mutated(
    machines: WorldMachines,
    placement: WorldPlacement,
    recipes: dict[str, Recipe],
    buildings: dict[str, Building],
) -> None:
    demands = {_PLATE: _ONE}
    kept = copy.deepcopy((machines, dict(placement.built_counts), demands))

    overlay.evaluate_overlay(
        machines,
        _mixed_overlay(),
        recipes,
        placement=placement,
        buildings=buildings,
        demands=demands,
    )

    assert (machines, dict(placement.built_counts), demands) == kept


def test_the_same_world_and_overlay_give_byte_identical_output_in_process() -> None:
    first = canonical_mixed()
    second = canonical_mixed()

    assert first == second
    assert len(first) > _MIN_CANONICAL_BYTES, (
        "the serialisation is too small to be the whole result"
    )


def test_the_same_world_and_overlay_give_byte_identical_output_across_processes() -> None:
    # Two interpreters with different string-hash seeds: any result whose order
    # leaned on set or dict iteration of strings would differ here.
    root = Path(__file__).resolve().parents[2]
    script = (
        "import sys; from tests.audit.test_overlay import canonical_mixed;"
        " sys.stdout.write(canonical_mixed())"
    )
    outputs = []
    for seed in ("1", "2"):
        env = {**os.environ, "PYTHONHASHSEED": seed}
        run = subprocess.run(
            [sys.executable, "-c", script], cwd=root, env=env, capture_output=True, check=False
        )
        assert run.returncode == 0, run.stderr.decode("ascii", "replace")[-2000:]
        outputs.append(run.stdout)

    assert outputs[0] == outputs[1]
    assert outputs[0] == canonical_mixed().encode("ascii")


def _snapshot(root: Path) -> dict[str, tuple[int, bytes]]:
    return {
        path.relative_to(root).as_posix(): (path.stat().st_mtime_ns, path.read_bytes())
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def test_the_door_patch_bites() -> None:
    # Control: without this the never-open arm below could pass vacuously.
    with pytest.MonkeyPatch.context() as patch:
        tried: list[str] = []

        def opener(*_args: object, **_kwargs: object) -> object:
            tried.append("x")
            raise AssertionError

        patch.setattr(Path, "open", opener)
        with pytest.raises(AssertionError):
            Path(__file__).read_bytes()
    assert tried == ["x"]


def test_an_overlay_evaluation_opens_no_file_and_changes_none(
    tmp_path: Path,
    machines: WorldMachines,
    placement: WorldPlacement,
    recipes: dict[str, Recipe],
    buildings: dict[str, Building],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Stand-ins for the save and install directories. Synthetic bytes only.
    save_dir = tmp_path / "save"
    install_dir = tmp_path / "install"
    (save_dir / "account").mkdir(parents=True)
    (install_dir / "docs").mkdir(parents=True)
    (save_dir / "account" / "world.sav").write_bytes(b"synthetic-save-bytes\x00\x01")
    (save_dir / "account" / "world_autosave_0.sav").write_bytes(b"synthetic-autosave")
    (install_dir / "docs" / "en-US.json").write_bytes(b'{"synthetic": true}')
    before = _snapshot(tmp_path)
    assert len(before) == _STANDIN_FILES

    tried: list[str] = []

    def opener(door: str) -> object:
        def refuse(*_args: object, **_kwargs: object) -> object:
            tried.append(door)
            raise AssertionError(f"the overlay path opened a file through {door}")

        return refuse

    with monkeypatch.context() as patch:
        patch.setattr(builtins, "open", opener("builtins.open"))
        patch.setattr(io, "open", opener("io.open"))
        patch.setattr(os, "open", opener("os.open"))
        patch.setattr(Path, "open", opener("Path.open"))
        result = overlay.evaluate_overlay(
            machines,
            _mixed_overlay(),
            recipes,
            placement=placement,
            buildings=buildings,
            raw_items=(synthetic.SOLVE_ORE_ITEM,),
        )

    assert tried == []
    assert result.application.records, "nothing was evaluated, so the arm is vacuous"
    assert _snapshot(tmp_path) == before


def test_draw_is_withheld_and_said_so_without_a_placement(
    machines: WorldMachines, recipes: dict[str, Recipe]
) -> None:
    result = overlay.evaluate_overlay(machines, _mixed_overlay(), recipes)

    assert result.before_draw is None
    assert result.after_draw is None
    assert overlay.WARN_OVERLAY_DRAW_UNAVAILABLE in _codes(result.warnings)
