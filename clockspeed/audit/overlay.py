"""CS-1236: the what-if overlay - virtual edits over the measured world, recomputed.

WHAT THIS MODULE OWNS
-----------------------
An immutable :class:`Overlay` - a tuple of edits - and two pure functions over
it. :func:`apply_overlay` takes the MEASURED models and returns NEW models with
every edit applied in order, plus one :class:`EditRecord` per edit naming what
it changed. :func:`evaluate_overlay` recomputes ``flow.flow_of`` (and
``balance.draw_of`` where a placement and the buildings are supplied) on the
world before and after, and returns both side by side with per-item deltas.

THE OVERLAY IS NEVER WRITTEN BACK, AND THIS MODULE OPENS NOTHING. Its inputs
are models a lower layer already published and its outputs are new models; it
imports no reader, names no path and calls no opener. The measured models are
never mutated either: every edit produces a fresh tuple, and the caller's
demand mapping is copied before an edit touches it. Non-negotiable 1 is the
reason and ``tests/audit/test_overlay.py`` proves both halves - every opener
patched to raise during an evaluation, and every file in a stand-in save and
install tree unchanged in bytes and mtime afterwards.

FOUR EDIT KINDS
-----------------
- :class:`AddMachines` - N machines of a recipe at an exact clock. The building
  is the one the caller names, else the recipe's single ``produced_in`` entry.
- :class:`RemoveMachines` - N machines of a recipe, the LAST N in population
  order, so the result is deterministic and the survivors keep their indices.
- :class:`SwapRecipe` - machines on recipe A move to recipe B, the FIRST N in
  population order or all of them. Building and clock are kept, so the draw -
  which prices built counts - does not move.
- :class:`SetDemand` - the net output asked of an item, which is how a target
  is raised.

THREE OUTCOMES, AND NO CLAMP
------------------------------
An edit is APPLIED, REFUSED or SKIPPED, and its record says which and why.

REFUSED is an edit that cannot apply to THIS world: removing more machines
than run the recipe, a remove the placement's built count cannot cover, an add
whose building cannot be resolved, an add or a swap that would run a recipe in a
building its ``produced_in`` does not name, an add into a building the supplied
buildings do not model, a swap onto itself. A refused edit changes
NOTHING - removing five of three machines does not remove three. A clamp would
be the overlay quietly answering a different question than the one asked,
which is the silently-wrong shape non-negotiable 7 forbids.

SKIPPED is an edit naming a recipe the supplied mapping does not carry - an
add of it, or a swap onto it. Its rate is unknown, so flowing it would publish
a number nothing measured; it is flagged under :data:`WARN_OVERLAY_RECIPE_UNKNOWN`
and skipped. A REMOVE or a swap AWAY from an unknown recipe is not skipped:
those machines exist in the world whatever the mapping knows of them.

A MALFORMED edit - a count that is not a positive int, a clock or rate that is
not exactly a non-negative ``Fraction`` - is refused at CONSTRUCTION, because it
is a fault in the caller's statement rather than a fact about the world. An
inexact number raises ``InexactValueError`` from ``clockspeed/solve/exact.py``;
anything else raises :class:`OverlayEditError`.

THE CLOCK IS CHECKED AGAINST WHAT IS KNOWN, AND FLAGGED WHERE IT CANNOT BE.
A clock of zero is refused at construction - a machine that never cycles is a
remove, not an add. ``clockspeed/solve/power.py`` ``clock_ceiling`` publishes NO
ceiling number (ADR 0005: the shard slot count is unmeasured), so an add above
the building's un-sharded base is APPLIED and flagged
:data:`WARN_OVERLAY_CLOCK_ABOVE_BASE` - it may or may not be reachable with
shards - and an add whose clock nothing could be checked against (no buildings
supplied, or no base declared) is flagged :data:`WARN_OVERLAY_CLOCK_UNCHECKED`.
Neither is silently accepted, and neither is refused on a ceiling nobody knows.

A VIRTUAL MACHINE WAS NEVER MEASURED. An added machine, and a swapped one,
carries ``producing=None``: the producing flag is a reading, and nothing read it.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from fractions import Fraction
from types import MappingProxyType
from typing import TYPE_CHECKING, ClassVar, Final

from clockspeed.audit.balance import WorldDraw, draw_of
from clockspeed.audit.flow import WorldFlow, flow_of
from clockspeed.audit.machines import MachineState, WorldMachines
from clockspeed.save.world import WorldWarning
from clockspeed.solve.exact import InexactValueError, audit_exact
from clockspeed.solve.power import clock_ceiling

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping

    from clockspeed.audit.placement import WorldPlacement
    from clockspeed.data.registry import Building, Recipe

__all__ = [
    "KIND_ADD",
    "KIND_DEMAND",
    "KIND_REMOVE",
    "KIND_SWAP",
    "OUTCOME_APPLIED",
    "OUTCOME_REFUSED",
    "OUTCOME_SKIPPED",
    "REFUSED_BUILDING_MISMATCH",
    "REFUSED_BUILDING_UNKNOWN",
    "REFUSED_BUILDING_UNRESOLVED",
    "REFUSED_PLACEMENT_SHORT",
    "REFUSED_SWAP_TO_SELF",
    "REFUSED_TOO_FEW_MACHINES",
    "SKIPPED_RECIPE_UNKNOWN",
    "SOURCE_OVERLAY",
    "WARN_OVERLAY_CLOCK_ABOVE_BASE",
    "WARN_OVERLAY_CLOCK_UNCHECKED",
    "WARN_OVERLAY_DRAW_UNAVAILABLE",
    "WARN_OVERLAY_EDIT_REFUSED",
    "WARN_OVERLAY_RECIPE_UNKNOWN",
    "AddMachines",
    "EditRecord",
    "ItemDelta",
    "Overlay",
    "OverlayApplication",
    "OverlayEdit",
    "OverlayEditError",
    "OverlayEvaluation",
    "RemoveMachines",
    "SetDemand",
    "SwapRecipe",
    "apply_overlay",
    "evaluate_overlay",
]

#: Which layer noticed a warning raised here, for ``WorldWarning.source``.
SOURCE_OVERLAY: Final = "overlay"

#: The edit kinds, one per edit type.
KIND_ADD: Final = "add-machines"
KIND_REMOVE: Final = "remove-machines"
KIND_SWAP: Final = "swap-recipe"
KIND_DEMAND: Final = "set-demand"

#: The three outcomes an edit can have.
OUTCOME_APPLIED: Final = "applied"
OUTCOME_REFUSED: Final = "refused"
OUTCOME_SKIPPED: Final = "skipped"

#: Fewer machines run the recipe than the edit names. Never clamped.
REFUSED_TOO_FEW_MACHINES: Final = "too-few-machines"

#: The placement's built count for a removed machine's class is lower than the
#: number removed, so decrementing it would go below zero.
REFUSED_PLACEMENT_SHORT: Final = "placement-short"

#: An add named no building and its recipe names not exactly one producer.
REFUSED_BUILDING_UNRESOLVED: Final = "building-unresolved"

#: An add or a swap would run a recipe in a building its ``produced_in`` does
#: not name.
REFUSED_BUILDING_MISMATCH: Final = "building-mismatch"

#: An add names a building the supplied buildings do not model.
REFUSED_BUILDING_UNKNOWN: Final = "building-unknown"

#: A swap whose source and target are the same recipe.
REFUSED_SWAP_TO_SELF: Final = "swap-to-self"

#: An add, or a swap target, names a recipe the supplied mapping does not carry.
SKIPPED_RECIPE_UNKNOWN: Final = "recipe-unknown"

#: This many edits were refused and changed nothing.
WARN_OVERLAY_EDIT_REFUSED: Final = "overlay-edit-refused"

#: This many edits named a recipe the mapping does not carry and were skipped.
WARN_OVERLAY_RECIPE_UNKNOWN: Final = "overlay-recipe-unknown"

#: This many adds run above the building's un-sharded base clock. Applied:
#: the shard ceiling is unmeasured, so whether the clock is reachable is unknown.
WARN_OVERLAY_CLOCK_ABOVE_BASE: Final = "overlay-clock-above-base"

#: This many adds carry a clock nothing could be checked against - no buildings
#: supplied, or the building declares no un-sharded base.
WARN_OVERLAY_CLOCK_UNCHECKED: Final = "overlay-clock-unchecked"

#: No placement or no buildings were supplied, so no draw was recomputed.
WARN_OVERLAY_DRAW_UNAVAILABLE: Final = "overlay-draw-unavailable"

#: One fixed line per warning code. Keyed rather than formatted, so a detail
#: can never be built from a recipe or item name.
_WARNING_DETAIL: Final[Mapping[str, str]] = MappingProxyType(
    {
        WARN_OVERLAY_EDIT_REFUSED: (
            "this many overlay edits could not apply to this world and changed nothing;"
            " a refused edit is never clamped to what the world holds"
        ),
        WARN_OVERLAY_RECIPE_UNKNOWN: (
            "this many overlay edits named a recipe the supplied mapping does not carry"
            " and were skipped, because its rate is unknown"
        ),
        WARN_OVERLAY_CLOCK_ABOVE_BASE: (
            "this many overlay adds run above the building's un-sharded base clock;"
            " the shard ceiling is unmeasured, so whether that clock is reachable is"
            " unknown rather than accepted"
        ),
        WARN_OVERLAY_CLOCK_UNCHECKED: (
            "this many overlay adds carry a clock that could not be checked - no"
            " buildings were supplied or the building declares no un-sharded base"
        ),
        WARN_OVERLAY_DRAW_UNAVAILABLE: (
            "no placement or no buildings were supplied, so the power draw was not"
            " recomputed before or after the overlay"
        ),
    }
)


class OverlayEditError(ValueError):
    """An overlay edit is malformed as a statement, before any world is consulted.

    Carries a fixed line naming the field, never the value - a value here is
    caller input and may be a recipe or item name.
    """


def _require_name(value: object, field: str) -> None:
    if type(value) is not str or not value:
        raise OverlayEditError(f"{field} must be a non-empty string")


def _require_count(value: object, field: str) -> None:
    if type(value) is not int or value < 1:
        raise OverlayEditError(f"{field} must be a positive int")


def _require_non_negative(value: object, field: str) -> None:
    if type(value) is not Fraction:
        raise InexactValueError(f"{field} must be exactly a Fraction")
    if value < 0:
        raise OverlayEditError(f"{field} must not be negative")


@dataclass(frozen=True, repr=False)
class AddMachines:
    """Add ``count`` machines running a recipe at an exact clock.

    Attributes:
        recipe_class_name: The recipe the new machines run.
        count: How many, a positive int.
        clock: Their clock, exactly a Fraction above zero.
        building_class_name: Their building class, or None to take the
            recipe's single ``produced_in`` entry.
    """

    KIND: ClassVar[str] = KIND_ADD

    recipe_class_name: str
    count: int
    clock: Fraction
    building_class_name: str | None = None

    def __post_init__(self) -> None:
        """Refuse a malformed statement."""
        _require_name(self.recipe_class_name, "recipe_class_name")
        _require_count(self.count, "count")
        _require_non_negative(self.clock, "clock")
        if self.clock == 0:
            raise OverlayEditError("clock must be above zero; remove the machines instead")
        if self.building_class_name is not None:
            _require_name(self.building_class_name, "building_class_name")

    def __repr__(self) -> str:
        """Render the kind and numbers, and no name.

        Returns:
            The safe rendering.
        """
        return f"{type(self).__name__}(count={self.count}, clock={self.clock})"


@dataclass(frozen=True, repr=False)
class RemoveMachines:
    """Remove the last ``count`` machines running a recipe.

    Attributes:
        recipe_class_name: The recipe.
        count: How many, a positive int.
    """

    KIND: ClassVar[str] = KIND_REMOVE

    recipe_class_name: str
    count: int

    def __post_init__(self) -> None:
        """Refuse a malformed statement."""
        _require_name(self.recipe_class_name, "recipe_class_name")
        _require_count(self.count, "count")

    def __repr__(self) -> str:
        """Render the kind and count, and no name.

        Returns:
            The safe rendering.
        """
        return f"{type(self).__name__}(count={self.count})"


@dataclass(frozen=True, repr=False)
class SwapRecipe:
    """Move machines from one recipe to another, keeping building and clock.

    Attributes:
        from_recipe: The recipe the machines run now.
        to_recipe: The recipe they run after.
        count: How many, the FIRST in population order; None for all of them.
    """

    KIND: ClassVar[str] = KIND_SWAP

    from_recipe: str
    to_recipe: str
    count: int | None = None

    def __post_init__(self) -> None:
        """Refuse a malformed statement."""
        _require_name(self.from_recipe, "from_recipe")
        _require_name(self.to_recipe, "to_recipe")
        if self.count is not None:
            _require_count(self.count, "count")

    def __repr__(self) -> str:
        """Render the kind and count, and no name.

        Returns:
            The safe rendering.
        """
        return f"{type(self).__name__}(count={self.count})"


@dataclass(frozen=True, repr=False)
class SetDemand:
    """Set the net output asked of an item, per minute.

    Attributes:
        item_key: The item.
        rate: The net rate asked, exactly a non-negative Fraction.
    """

    KIND: ClassVar[str] = KIND_DEMAND

    item_key: str
    rate: Fraction

    def __post_init__(self) -> None:
        """Refuse a malformed statement."""
        _require_name(self.item_key, "item_key")
        _require_non_negative(self.rate, "rate")

    def __repr__(self) -> str:
        """Render the kind and rate, and no name.

        Returns:
            The safe rendering.
        """
        return f"{type(self).__name__}(rate={self.rate})"


type OverlayEdit = AddMachines | RemoveMachines | SwapRecipe | SetDemand

_EDIT_TYPES: Final = (AddMachines, RemoveMachines, SwapRecipe, SetDemand)


@dataclass(frozen=True, repr=False)
class Overlay:
    """An ordered, immutable tuple of edits over one world.

    Attributes:
        edits: The edits, applied in this order, each over the previous result.
    """

    edits: tuple[OverlayEdit, ...]

    def __post_init__(self) -> None:
        """Refuse anything but a tuple of edits."""
        if type(self.edits) is not tuple:
            raise OverlayEditError("edits must be a tuple")
        for edit in self.edits:
            if not isinstance(edit, _EDIT_TYPES):
                raise OverlayEditError("every member of edits must be an overlay edit")

    def __repr__(self) -> str:
        """Render the count of edits only.

        Returns:
            The safe rendering.
        """
        return f"{type(self).__name__}(edits={len(self.edits)})"


@dataclass(frozen=True, repr=False)
class EditRecord:
    """What one edit did, in exact counts - the unit a future trace step projects.

    Attributes:
        index: The edit's position in :attr:`Overlay.edits`.
        edit: The edit itself.
        kind: The edit's kind, one of the ``KIND_*`` constants.
        outcome: One of the ``OUTCOME_*`` constants.
        reason: The ``REFUSED_*`` or ``SKIPPED_*`` code, or None when applied.
        machines_changed: How many machines were added, removed or swapped;
            zero unless applied.
        count_before: Machines on the subject recipe (the source, for a swap)
            before this edit; None for a demand edit.
        count_after: The same, after this edit.
        target_count_before: Machines on a swap's target recipe before this
            edit; None for every other kind.
        target_count_after: The same, after this edit.
        demand_before: The item's demand before a demand edit; None otherwise.
        demand_after: The same, after.
        flag: A ``WARN_*`` code the edit applied under, or None - set when an
            add's clock is above the un-sharded base or could not be checked.
    """

    index: int
    edit: OverlayEdit
    kind: str
    outcome: str
    reason: str | None
    machines_changed: int
    count_before: int | None = None
    count_after: int | None = None
    target_count_before: int | None = None
    target_count_after: int | None = None
    demand_before: Fraction | None = None
    demand_after: Fraction | None = None
    flag: str | None = None

    def __repr__(self) -> str:
        """Render the index, kind, outcome and counts, and no name.

        Returns:
            The safe rendering.
        """
        return (
            f"{type(self).__name__}(index={self.index}, kind={self.kind!r}, "
            f"outcome={self.outcome!r}, reason={self.reason!r}, "
            f"machines_changed={self.machines_changed})"
        )


@dataclass(frozen=True, repr=False)
class OverlayApplication:
    """The world with the overlay applied, as new models, and what each edit did.

    Attributes:
        machines: The machines after every edit.
        placement: The placement after every edit, or None when none was given.
        demands: Item to demand after every demand edit, sorted by key.
        records: One per edit, in edit order.
        warnings: What was refused or skipped, in the ``WorldWarning`` idiom.
    """

    machines: WorldMachines
    placement: WorldPlacement | None
    demands: Mapping[str, Fraction]
    records: tuple[EditRecord, ...]
    warnings: tuple[WorldWarning, ...]

    def __repr__(self) -> str:
        """Render counts only.

        Returns:
            The safe rendering.
        """
        return (
            f"{type(self).__name__}(machines={len(self.machines.machines)}, "
            f"records={len(self.records)}, warnings={len(self.warnings)})"
        )


@dataclass(frozen=True, repr=False)
class ItemDelta:
    """One item's net rate before and after the overlay.

    Attributes:
        item_key: The item.
        net_before: Its net per minute on the measured world, zero if absent.
        net_after: Its net per minute with the overlay, zero if absent.
        delta: ``net_after - net_before``.
    """

    item_key: str
    net_before: Fraction
    net_after: Fraction
    delta: Fraction

    def __repr__(self) -> str:
        """Render the numbers and no name.

        Returns:
            The safe rendering.
        """
        return (
            f"{type(self).__name__}(net_before={self.net_before}, "
            f"net_after={self.net_after}, delta={self.delta})"
        )


@dataclass(frozen=True, repr=False)
class OverlayEvaluation:
    """The measured world and the overlaid world, recomputed side by side.

    Attributes:
        before_flow: ``flow_of`` on the measured machines.
        after_flow: ``flow_of`` on the overlaid machines.
        before_draw: ``draw_of`` on the measured placement, or None when no
            placement or no buildings were supplied.
        after_draw: The same on the overlaid placement.
        items: One per item in either flow, sorted by key.
        application: The overlaid models and the per-edit records.
        warnings: The application's warnings, plus whether draw was withheld.
    """

    before_flow: WorldFlow
    after_flow: WorldFlow
    before_draw: WorldDraw | None
    after_draw: WorldDraw | None
    items: tuple[ItemDelta, ...]
    application: OverlayApplication
    warnings: tuple[WorldWarning, ...]

    def __repr__(self) -> str:
        """Render counts only.

        Returns:
            The safe rendering.
        """
        return (
            f"{type(self).__name__}(items={len(self.items)}, "
            f"records={len(self.application.records)}, "
            f"draw={self.before_draw is not None}, warnings={len(self.warnings)})"
        )


def _warning(code: str, count: int = 1) -> WorldWarning:
    return WorldWarning(source=SOURCE_OVERLAY, code=code, detail=_WARNING_DETAIL[code], count=count)


def _count(states: tuple[MachineState, ...], recipe: str) -> int:
    return sum(1 for state in states if state.recipe_class_name == recipe)


def _with_states(machines: WorldMachines, states: tuple[MachineState, ...]) -> WorldMachines:
    """A new machines model over ``states``, availability re-derived.

    The denominators and warnings are the MEASURED reading's and are kept: they
    describe what was read, which an overlay does not change.
    """
    return dataclasses.replace(
        machines,
        machines=states,
        producing_available=any(state.producing is not None for state in states),
        recipe_available=any(state.recipe_class_name is not None for state in states),
        overclock_available=any(state.overclock is not None for state in states),
    )


def _with_counts(placement: WorldPlacement, counts: Mapping[str, int]) -> WorldPlacement:
    kept = {key: counts[key] for key in sorted(counts) if counts[key]}
    return dataclasses.replace(placement, built_counts=MappingProxyType(kept))


class _World:
    """The mutable working copy one application threads through its edits.

    Private and never returned: every field is frozen into a new model at the
    end, and none aliases a caller's object.
    """

    def __init__(
        self,
        states: tuple[MachineState, ...],
        counts: dict[str, int] | None,
        demands: dict[str, Fraction],
    ) -> None:
        self.states = states
        self.counts = counts
        self.demands = demands


def _refused(index: int, edit: OverlayEdit, reason: str, **counts: int | None) -> EditRecord:
    return EditRecord(
        index=index,
        edit=edit,
        kind=edit.KIND,
        outcome=OUTCOME_REFUSED,
        reason=reason,
        machines_changed=0,
        **counts,  # type: ignore[arg-type]
    )


def _skipped(index: int, edit: OverlayEdit, **counts: int | None) -> EditRecord:
    return EditRecord(
        index=index,
        edit=edit,
        kind=edit.KIND,
        outcome=OUTCOME_SKIPPED,
        reason=SKIPPED_RECIPE_UNKNOWN,
        machines_changed=0,
        **counts,  # type: ignore[arg-type]
    )


def _clock_flag(clock: Fraction, entry: Building | None) -> str | None:
    """Which flag, if any, an added clock carries against its building.

    Args:
        clock: The added machines' clock.
        entry: The building, or None when no buildings were supplied.

    Returns:
        None when the clock is at or below the un-sharded base; a ``WARN_*``
        code otherwise. See the module docstring.
    """
    if entry is None:
        return WARN_OVERLAY_CLOCK_UNCHECKED
    ceiling = clock_ceiling(entry)
    if ceiling.base is None:
        return WARN_OVERLAY_CLOCK_UNCHECKED
    if clock > ceiling.base:
        return WARN_OVERLAY_CLOCK_ABOVE_BASE
    return None


def _apply_add(
    index: int,
    edit: AddMachines,
    world: _World,
    recipes: Mapping[str, Recipe],
    buildings: Mapping[str, Building] | None,
) -> EditRecord:
    before = _count(world.states, edit.recipe_class_name)
    counts = {"count_before": before, "count_after": before}
    recipe = recipes.get(edit.recipe_class_name)
    if recipe is None:
        return _skipped(index, edit, **counts)
    building = edit.building_class_name
    if building is None:
        if len(recipe.produced_in) != 1:
            return _refused(index, edit, REFUSED_BUILDING_UNRESOLVED, **counts)
        building = recipe.produced_in[0]
    if building not in recipe.produced_in:
        return _refused(index, edit, REFUSED_BUILDING_MISMATCH, **counts)
    if buildings is not None and building not in buildings:
        return _refused(index, edit, REFUSED_BUILDING_UNKNOWN, **counts)
    flag = _clock_flag(edit.clock, None if buildings is None else buildings[building])
    added = tuple(
        MachineState(
            class_name=building,
            producing=None,
            recipe_class_name=edit.recipe_class_name,
            overclock=edit.clock,
        )
        for _ in range(edit.count)
    )
    world.states = world.states + added
    if world.counts is not None:
        world.counts[building] = world.counts.get(building, 0) + edit.count
    return EditRecord(
        index=index,
        edit=edit,
        kind=edit.KIND,
        outcome=OUTCOME_APPLIED,
        reason=None,
        machines_changed=edit.count,
        count_before=before,
        count_after=before + edit.count,
        flag=flag,
    )


def _apply_remove(index: int, edit: RemoveMachines, world: _World) -> EditRecord:
    before = _count(world.states, edit.recipe_class_name)
    counts = {"count_before": before, "count_after": before}
    if before < edit.count:
        return _refused(index, edit, REFUSED_TOO_FEW_MACHINES, **counts)
    positions = [
        position
        for position, state in enumerate(world.states)
        if state.recipe_class_name == edit.recipe_class_name
    ][-edit.count :]
    removed_classes: dict[str, int] = {}
    for position in positions:
        name = world.states[position].class_name
        removed_classes[name] = removed_classes.get(name, 0) + 1
    if world.counts is not None:
        for name, removed in removed_classes.items():
            if world.counts.get(name, 0) < removed:
                return _refused(index, edit, REFUSED_PLACEMENT_SHORT, **counts)
        for name, removed in removed_classes.items():
            world.counts[name] -= removed
    dropped = frozenset(positions)
    world.states = tuple(
        state for position, state in enumerate(world.states) if position not in dropped
    )
    return EditRecord(
        index=index,
        edit=edit,
        kind=edit.KIND,
        outcome=OUTCOME_APPLIED,
        reason=None,
        machines_changed=edit.count,
        count_before=before,
        count_after=before - edit.count,
    )


def _apply_swap(
    index: int, edit: SwapRecipe, world: _World, recipes: Mapping[str, Recipe]
) -> EditRecord:
    before = _count(world.states, edit.from_recipe)
    target_before = _count(world.states, edit.to_recipe)
    counts = {
        "count_before": before,
        "count_after": before,
        "target_count_before": target_before,
        "target_count_after": target_before,
    }
    if edit.from_recipe == edit.to_recipe:
        return _refused(index, edit, REFUSED_SWAP_TO_SELF, **counts)
    if edit.to_recipe not in recipes:
        return _skipped(index, edit, **counts)
    moved = before if edit.count is None else edit.count
    if moved < 1 or before < moved:
        return _refused(index, edit, REFUSED_TOO_FEW_MACHINES, **counts)
    producers = recipes[edit.to_recipe].produced_in
    chosen = [state for state in world.states if state.recipe_class_name == edit.from_recipe][
        :moved
    ]
    if any(state.class_name not in producers for state in chosen):
        return _refused(index, edit, REFUSED_BUILDING_MISMATCH, **counts)
    remaining = moved
    states: list[MachineState] = []
    for state in world.states:
        if remaining and state.recipe_class_name == edit.from_recipe:
            states.append(
                dataclasses.replace(state, recipe_class_name=edit.to_recipe, producing=None)
            )
            remaining -= 1
        else:
            states.append(state)
    world.states = tuple(states)
    return EditRecord(
        index=index,
        edit=edit,
        kind=edit.KIND,
        outcome=OUTCOME_APPLIED,
        reason=None,
        machines_changed=moved,
        count_before=before,
        count_after=before - moved,
        target_count_before=target_before,
        target_count_after=target_before + moved,
    )


def _apply_demand(index: int, edit: SetDemand, world: _World) -> EditRecord:
    before = world.demands.get(edit.item_key, Fraction(0))
    world.demands[edit.item_key] = edit.rate
    return EditRecord(
        index=index,
        edit=edit,
        kind=edit.KIND,
        outcome=OUTCOME_APPLIED,
        reason=None,
        machines_changed=0,
        demand_before=before,
        demand_after=edit.rate,
    )


def apply_overlay(
    machines: WorldMachines,
    overlay: Overlay,
    recipes: Mapping[str, Recipe],
    *,
    placement: WorldPlacement | None = None,
    buildings: Mapping[str, Building] | None = None,
    demands: Mapping[str, Fraction] | None = None,
) -> OverlayApplication:
    """Apply every edit in order and return new models plus one record per edit.

    PURE. Nothing passed in is mutated and nothing is opened.

    Args:
        machines: The measured machines.
        overlay: The edits.
        recipes: The recipes, keyed by class name. Supplied by the caller.
        placement: The measured placement, when the draw is to be recomputed.
        buildings: The buildings, keyed by class name, which an add's building
            must be one of and its clock is checked against. None leaves every
            added clock flagged unchecked.
        demands: The caller's base demands, item to net rate per minute.

    Returns:
        The overlaid models, the records and the warnings.

    Raises:
        InexactValueError: A base demand is not exactly a Fraction.
    """
    base_demands = dict(demands or {})
    audit_exact(base_demands, path="demands")
    world = _World(
        states=machines.machines,
        counts=None if placement is None else dict(placement.built_counts),
        demands=base_demands,
    )

    records: list[EditRecord] = []
    for index, edit in enumerate(overlay.edits):
        if isinstance(edit, AddMachines):
            records.append(_apply_add(index, edit, world, recipes, buildings))
        elif isinstance(edit, RemoveMachines):
            records.append(_apply_remove(index, edit, world))
        elif isinstance(edit, SwapRecipe):
            records.append(_apply_swap(index, edit, world, recipes))
        else:
            records.append(_apply_demand(index, edit, world))

    refused = sum(1 for record in records if record.outcome == OUTCOME_REFUSED)
    skipped = sum(1 for record in records if record.outcome == OUTCOME_SKIPPED)
    warnings: list[WorldWarning] = []
    if refused:
        warnings.append(_warning(WARN_OVERLAY_EDIT_REFUSED, refused))
    if skipped:
        warnings.append(_warning(WARN_OVERLAY_RECIPE_UNKNOWN, skipped))
    for code in (WARN_OVERLAY_CLOCK_ABOVE_BASE, WARN_OVERLAY_CLOCK_UNCHECKED):
        flagged = sum(1 for record in records if record.flag == code)
        if flagged:
            warnings.append(_warning(code, flagged))

    result = OverlayApplication(
        machines=_with_states(machines, world.states),
        placement=(
            None
            if placement is None or world.counts is None
            else _with_counts(placement, world.counts)
        ),
        demands=MappingProxyType({key: world.demands[key] for key in sorted(world.demands)}),
        records=tuple(records),
        warnings=tuple(warnings),
    )
    audit_exact(result.demands, path="overlay.demands")
    return result


def evaluate_overlay(
    machines: WorldMachines,
    overlay: Overlay,
    recipes: Mapping[str, Recipe],
    *,
    placement: WorldPlacement | None = None,
    buildings: Mapping[str, Building] | None = None,
    raw_items: Iterable[str] = (),
    demands: Mapping[str, Fraction] | None = None,
) -> OverlayEvaluation:
    """Recompute the world before and after an overlay, side by side.

    PURE. The draw is recomputed only when BOTH a placement and the buildings
    are supplied, and :data:`WARN_OVERLAY_DRAW_UNAVAILABLE` says so otherwise -
    a draw of None is withheld, never zero.

    Args:
        machines: The measured machines.
        overlay: The edits.
        recipes: The recipes, keyed by class name.
        placement: The measured placement, for the draw.
        buildings: The buildings, keyed by class name, for the draw.
        raw_items: Items supplied from outside the built machines.
        demands: The caller's base demands.

    Returns:
        The evaluation, audited exact on the way out.

    Raises:
        InexactValueError: A base demand is not exactly a Fraction.
    """
    raw = tuple(sorted(set(raw_items)))
    application = apply_overlay(
        machines, overlay, recipes, placement=placement, buildings=buildings, demands=demands
    )
    before_flow = flow_of(machines, recipes, raw_items=raw, demands=dict(demands or {}))
    after_flow = flow_of(application.machines, recipes, raw_items=raw, demands=application.demands)

    before_draw: WorldDraw | None = None
    after_draw: WorldDraw | None = None
    warnings = list(application.warnings)
    if placement is not None and buildings is not None and application.placement is not None:
        before_draw = draw_of(placement, buildings)
        after_draw = draw_of(application.placement, buildings)
    else:
        warnings.append(_warning(WARN_OVERLAY_DRAW_UNAVAILABLE))

    zero = Fraction(0)
    items: list[ItemDelta] = []
    for key in sorted(set(before_flow.items) | set(after_flow.items)):
        was = before_flow.items[key].net if key in before_flow.items else zero
        now = after_flow.items[key].net if key in after_flow.items else zero
        items.append(ItemDelta(item_key=key, net_before=was, net_after=now, delta=now - was))

    result = OverlayEvaluation(
        before_flow=before_flow,
        after_flow=after_flow,
        before_draw=before_draw,
        after_draw=after_draw,
        items=tuple(items),
        application=application,
        warnings=tuple(warnings),
    )
    audit_exact(result, path="overlay")
    return result
