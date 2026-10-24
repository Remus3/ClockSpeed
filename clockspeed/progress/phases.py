"""The phase model - what a space-elevator phase costs in machines, miners and resources.

CS-1043 S2, pillar 4. A phase cost renders EXACTLY three keys, and each is an
exact Fraction mapping or None with a named reason - never ``{}`` and never 0:

- ``machine``: building ClassName to the machine count at full clock, solved by
  :func:`clockspeed.solve.ratio.solve_for_targets` over a caller-supplied
  recipe selection. Pillar 4 does not CHOOSE recipes.
- ``miner``: extractor ClassName to the count at full clock on the BASE rate,
  which :data:`MINER_BASIS_BASE_RATE` names on the model. Purity scales a node's
  rate in the game, and purity is not saved (CS-1040), so no multiplier is
  applied and the basis says so rather than a comment.
- ``resource``: raw item ClassName to the exact rate per minute the chain eats.

Each figure is driven by the phase's required rates: every cost amount over the
completion budget, computed by :func:`clockspeed.progress.milestones.required_rates`
so the budget has one owner, :data:`clockspeed.progress.milestones.COMPLETION_BUDGET_MINUTES`.

WHERE PHASE COSTS COME FROM - THE SAVE, UNDER THE MEASURED MEANING (CS-1340).
A phase cost is a fact the save carries: ``mGamePhaseCosts``, which the save
layer publishes as ``clockspeed.save.world.WorldModel.phase_costs``. The costs
arrive through :class:`PhaseCostSource`, parameterised at the wiring site, and
the shipped source is :class:`SavePhaseCosts`, built from a world model.
``docs/adr/0016-unlock-arrays-carriers-and-serialized-grammar.md`` measured
what an amount MEANS: what the world STILL OWES on that phase - a phase the
save's own phase token says was reached reads zero on every line. So the
source publishes each phase's OWED lines, drops a paid line (zero owed is
nothing to build), and a phase paid in full publishes an EMPTY entry, null
under :data:`REASON_EMPTY_COST_ENTRY`. A world that writes no array - every
1.0-native save ADR 0016 measured - publishes no table, under
:data:`REASON_NO_PHASE_COST_TABLE`, and every phase cost is null.
``phase_costs_available`` is DERIVED from the table the source returned -
never hardcoded - so it reads True on exactly the worlds that carry the array.

UNREAD AND UNMAPPED CONTENT IS FLAGGED, NEVER A TABLE (CS-1340 repair,
non-negotiable 7). A table the save layer flagged unread, or whose every
element was skipped, publishes no table under :data:`REASON_PHASE_COSTS_UNREAD`;
the skip count rides on :class:`PhaseCostTable`, and a phase missing beside a
skip is :data:`REASON_COST_ENTRY_UNREAD`, never "no entry". A phase the
installed registry does not name (:func:`installed_phases`) is withheld under
:data:`REASON_UNMAPPED_PHASE` and named on the table - ADR 0016 records that
the only table measured names pre-1.0 phases the pinned build's docs do not -
and no phase is ever mapped onto another here.

A PHASE WITH NO COST ENTRY IS NULL, NEVER ZERO (non-negotiable 7). A measured
table that holds no entry for the selected phase publishes every figure as None
under :data:`REASON_NO_COST_ENTRY`. An empty entry, a non-positive amount and a
cost item the registry does not resolve are each null under their own reason.

WHAT IS PAID OFF AND WHAT IS HELD, NEVER SUMMED (CS-1348 amended). The save
layer publishes two readings and this model keeps them apart:
``paid_off`` - what ``mTargetGamePhasePaidOffCosts`` says is paid off on the
phase ``mTargetGamePhase`` names, keyed by that phase - and ``held`` - what the
elevator's input inventory holds. A phase cost's ``paid_off_available`` and
``held_available`` are True exactly when the matching reading is present, even
when it counts nothing. Neither is ever added to the other: whether an item
sitting in the input is already counted as paid is unmeasured, because every
measured input was empty. A paid-off phase the installed vocabulary lacks is
withheld in ``unmapped`` under :data:`REASON_UNMAPPED_PHASE`, never netted
against another phase. No reading is None, never zero: no library save writes
the paid-off array (ADR 0016), so its absence is no reading, and an empty input
publishes an empty ``held`` - never an exact zero for a part already paid.
This model subtracts neither reading: every figure is driven by the amounts the
source published, which for the save source are already what the world still
owes.

NO FLOAT, ANYWHERE (non-negotiable 6). The solve is exact; an extractor's base
rate goes through :func:`clockspeed.solve.exact.per_minute`, a fluid's litres
are scaled by :data:`clockspeed.data.registry.LITRES_PER_CUBIC_METRE` as a
Fraction denominator, and every published model passes
:func:`clockspeed.solve.exact.audit_exact`.

DETERMINISM. Every published mapping is keyed in sorted order and a set of
phase costs is published in phase order, so the same inputs publish the same
output in the same order.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from fractions import Fraction
from types import MappingProxyType
from typing import Final, Protocol

from clockspeed.data.registry import LITRES_PER_CUBIC_METRE, Registry
from clockspeed.data.schematics import CostLine, SchematicCatalog
from clockspeed.progress import milestones
from clockspeed.save.world import WARN_PHASE_COSTS_UNREAD, WorldModel
from clockspeed.solve.exact import audit_exact, per_minute
from clockspeed.solve.ratio import ProductionPlan, RatioError, RatioRequest, solve_for_targets

__all__ = [
    "CLOCK_BASIS_FULL",
    "MINER_BASIS_BASE_RATE",
    "REASON_COST_ENTRY_UNREAD",
    "REASON_EMPTY_COST_ENTRY",
    "REASON_EXTRACTOR_CANNOT_YIELD",
    "REASON_EXTRACTOR_RATE_UNAVAILABLE",
    "REASON_NONPOSITIVE_COST",
    "REASON_NO_COST_ENTRY",
    "REASON_NO_EXTRACTOR_SELECTED",
    "REASON_NO_PHASE_COST_TABLE",
    "REASON_NO_RAW_INPUT",
    "REASON_NO_RECIPE_SELECTION",
    "REASON_NO_SINGLE_BUILDING",
    "REASON_PHASE_COSTS_UNREAD",
    "REASON_RATIO_REFUSED",
    "REASON_UNKNOWN_EXTRACTOR",
    "REASON_UNKNOWN_RESOURCE",
    "REASON_UNMAPPED_PHASE",
    "REASON_UNRESOLVED_COST_ITEM",
    "Figure",
    "PhaseCost",
    "PhaseCostSource",
    "PhaseCostTable",
    "PhaseIntegrityError",
    "RecipeSelection",
    "SavePhaseCosts",
    "installed_phases",
    "phase_cost",
    "phase_costs",
    "phase_costs_available",
]

#: Every machine and miner count assumes every building runs at full clock.
CLOCK_BASIS_FULL: Final = "full-clock"
#: A miner count is over the extractor's unscaled document rate: no purity
#: multiplier is applied, because purity is not saved (CS-1040).
MINER_BASIS_BASE_RATE: Final = "base-rate"

#: The world published no phase-cost table: its save writes no single readable
#: ``mGamePhaseCosts`` array - every 1.0-native save ADR 0016 measured.
REASON_NO_PHASE_COST_TABLE: Final = "no-phase-cost-table"
#: The measured table holds no entry for the selected phase.
REASON_NO_COST_ENTRY: Final = "no-cost-entry"
#: The phase's entry lists no cost line at all.
REASON_EMPTY_COST_ENTRY: Final = "empty-cost-entry"
#: A cost item totals zero or less, which is no requirement anyone can build to.
REASON_NONPOSITIVE_COST: Final = "nonpositive-cost"
#: A cost item names nothing in the registry, so no recipe can be solved for it.
REASON_UNRESOLVED_COST_ITEM: Final = "unresolved-cost-item"
#: The caller supplied no recipe selection, and this layer does not choose one.
REASON_NO_RECIPE_SELECTION: Final = "no-recipe-selection"
#: The ratio solve refused the selection; the figure's detail names the refusal.
REASON_RATIO_REFUSED: Final = "ratio-refused"
#: A recipe the plan runs is producible in no single modelled building.
REASON_NO_SINGLE_BUILDING: Final = "no-single-building"
#: The plan eats no raw input, so there is nothing to mine.
REASON_NO_RAW_INPUT: Final = "no-raw-input"
#: A raw input has no extractor in the caller's selection.
REASON_NO_EXTRACTOR_SELECTED: Final = "no-extractor-selected"
#: A selected extractor names nothing in the registry.
REASON_UNKNOWN_EXTRACTOR: Final = "unknown-extractor"
#: A raw input names no item in the registry, so its unit is unknown.
REASON_UNKNOWN_RESOURCE: Final = "unknown-resource"
#: A selected extractor's documents do not admit the raw input it was given.
REASON_EXTRACTOR_CANNOT_YIELD: Final = "extractor-cannot-yield"
#: A selected extractor's rate is absent or zero in the document.
REASON_EXTRACTOR_RATE_UNAVAILABLE: Final = "extractor-rate-unavailable"
#: CS-1340 repair. The world may hold a phase-cost table and none was READ: the
#: save layer raised ``WARN_PHASE_COSTS_UNREAD``, or every element of the array
#: was skipped. Unread content - never "no table was written".
REASON_PHASE_COSTS_UNREAD: Final = "phase-costs-unread"
#: CS-1340 repair. The table holds no entry for the selected phase AND skipped
#: elements it could not read, so the phase's entry may be one of those - its
#: absence is not evidence that nothing is owed.
REASON_COST_ENTRY_UNREAD: Final = "cost-entry-unread"
#: CS-1340 repair. The phase is not one the installed registry names, so the
#: save's entry for it is withheld rather than presented as a current phase's
#: cost. A table naming no installed phase at all is published as no table.
REASON_UNMAPPED_PHASE: Final = "unmapped-phase"


class PhaseIntegrityError(Exception):
    """A figure or a table was built in a shape this model forbids.

    A defect in the code that built it, never a property of the data: the data
    cases are published as None with a named reason. Deliberately NOT a
    :class:`ValueError`, so no input handler can swallow it.
    """


@dataclass(frozen=True)
class Figure:
    """One rendered figure: an exact mapping, or None with a named reason.

    Attributes:
        values: Key to an exact, positive Fraction, sorted by key, or None.
            Never empty: an empty answer is published as None with a reason.
        reason: None exactly when ``values`` is set, otherwise a REASON_*
            constant.
        detail: One line naming which refusal or which key, or the empty
            string. Never a value read out of a save.
    """

    values: Mapping[str, Fraction] | None
    reason: str | None
    detail: str = ""

    def __post_init__(self) -> None:
        """Refuse a figure that is both, neither, empty or not positive.

        Raises:
            PhaseIntegrityError: The figure breaks the A3 shape.
        """
        if (self.values is None) == (self.reason is None):
            raise PhaseIntegrityError("a figure carries exactly one of a mapping or a reason")
        if self.values is not None:
            if not self.values:
                raise PhaseIntegrityError("a figure never renders an empty mapping")
            for value in self.values.values():
                if type(value) is not Fraction or value <= 0:
                    raise PhaseIntegrityError(
                        "a figure renders exact positive Fractions only, never 0 or a float"
                    )


def _figure(values: Mapping[str, Fraction]) -> Figure:
    """Publish a computed mapping, sorted by key.

    Args:
        values: The computed mapping.

    Returns:
        The figure.
    """
    return Figure(
        values=MappingProxyType({key: values[key] for key in sorted(values)}), reason=None
    )


def _null(reason: str, detail: str = "") -> Figure:
    """Publish a figure that is unavailable.

    Args:
        reason: A REASON_* constant.
        detail: Which refusal or key, or the empty string.

    Returns:
        The figure.
    """
    return Figure(values=None, reason=reason, detail=detail)


@dataclass(frozen=True)
class PhaseCostTable:
    """What a phase-cost source publishes: every phase's cost, or why there is none.

    Attributes:
        entries: Phase token to its cost lines, in the registry's units - a
            count for a solid, cubic metres for a fluid - or None when the
            source has no measured table.
        reason: None exactly when ``entries`` is set, otherwise a REASON_*
            constant.
        paid_off: Phase to item ClassName to the exact count paid off on
            that phase - CS-1348 amended - or None when the source has no
            paid-off reading for any phase it may present. Independent of
            ``entries``: a reading of zero, or of no items, is still a reading.
        held: Item ClassName to the exact count the elevator's input holds,
            or None when there is no reading. NEVER summed with ``paid_off``.
        skipped_count: How many elements of the source's table did not read
            and were skipped - CS-1340 repair. Carried, never dropped: a phase
            missing while this is above zero is null under
            :data:`REASON_COST_ENTRY_UNREAD`, not :data:`REASON_NO_COST_ENTRY`.
        unmapped: The phases the source read and WITHHELD because the installed
            registry does not name them - CS-1340 repair. Each is null under
            :data:`REASON_UNMAPPED_PHASE`; none is in ``entries``.
    """

    entries: Mapping[str, tuple[CostLine, ...]] | None
    reason: str | None
    paid_off: Mapping[str, Mapping[str, Fraction]] | None = None
    held: Mapping[str, Fraction] | None = None
    skipped_count: int = 0
    unmapped: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        """Refuse a table that is both or neither, or a count that is not exact.

        Raises:
            PhaseIntegrityError: Both or neither of ``entries`` and ``reason``
                is set, a paid-off or held count is not an exact Fraction at
                zero or above, or a withheld phase is also presented.
        """
        if (self.entries is None) == (self.reason is None):
            raise PhaseIntegrityError("a phase-cost table carries exactly one of entries or reason")
        if type(self.skipped_count) is not int or self.skipped_count < 0:
            raise PhaseIntegrityError("a skipped count is an int at zero or above")
        if self.entries is not None and self.unmapped & set(self.entries):
            raise PhaseIntegrityError("a withheld phase is never also a published entry")
        if self.paid_off is not None and self.unmapped & set(self.paid_off):
            raise PhaseIntegrityError("a withheld phase is never also presented as paid off")
        readings = [] if self.held is None else [self.held]
        readings.extend(() if self.paid_off is None else self.paid_off.values())
        for reading in readings:
            for count in reading.values():
                if type(count) is not Fraction or count < 0:
                    raise PhaseIntegrityError(
                        "a paid-off or held count is an exact Fraction at zero or above,"
                        " never a float"
                    )


class PhaseCostSource(Protocol):
    """Where phase costs come from, parameterised at the wiring site."""

    def phase_costs(self) -> PhaseCostTable:
        """Publish the phase-cost table.

        Returns:
            The table, or a table carrying only the reason there is none.
        """
        ...


def installed_phases(catalog: SchematicCatalog) -> frozenset[str]:
    """The phase vocabulary the installed registry names - CS-1340 repair.

    Every phase token a schematic's game-phase dependency names in the
    installed docs, and nothing else: a token invented here would let a save's
    table pass as current. ADR 0016 records what the pinned build's docs name.

    Args:
        catalog: The installed schematic catalog.

    Returns:
        The tokens, possibly empty.
    """
    return frozenset(
        token
        for schematic in catalog.schematics.values()
        if (token := schematic.game_phase) is not None
    )


class SavePhaseCosts:
    """The shipped source: a world's own ``mGamePhaseCosts``, under the measured meaning.

    CS-1340. It consumes the save layer through its stated model only -
    ``WorldModel.phase_costs`` and the warnings on the same model - and reads
    no bytes and no record.

    NOTHING UNREAD OR UNMAPPED IS PRESENTED AS A TABLE (CS-1340 repair,
    non-negotiable 7). An array the save layer flagged unread, or one whose
    every element was skipped, publishes no table under
    :data:`REASON_PHASE_COSTS_UNREAD`, and the skip count is carried on the
    table either way. A phase the installed registry does not name is withheld
    and named in ``unmapped`` - never mapped onto a current phase - and a table
    naming no installed phase at all publishes no table under
    :data:`REASON_UNMAPPED_PHASE`.
    """

    def __init__(self, world: WorldModel, installed: frozenset[str]) -> None:
        """Hold the world, and the phase vocabulary its table is checked against.

        Args:
            world: The loaded world model.
            installed: The phases the installed registry names -
                :func:`installed_phases` at the shipped wiring site. Required:
                a table checked against nothing would pass as current.
        """
        self._world = world
        self._installed = installed

    def phase_costs(self) -> PhaseCostTable:
        """Publish each phase's OWED lines, or no table when the world wrote none.

        A line the save says is paid - zero owed - is dropped, because it is
        nothing to build; a phase paid in full is therefore an EMPTY entry.
        Kept, a paid line would null its whole phase as a non-positive cost
        and hide what the phase still owes on its other lines.

        Returns:
            The table, or one carrying only its reason - no table written,
            unread, or naming no installed phase - with the skip count, the
            withheld phases and the paid-off and held readings in every case.
        """
        paid_off, withheld = self._paid_off()
        held = None if self._world.elevator_input is None else self._world.elevator_input.items
        reading = self._world.phase_costs
        if reading is None:
            unread = any(
                warning.code == WARN_PHASE_COSTS_UNREAD for warning in self._world.warnings
            )
            reason = REASON_PHASE_COSTS_UNREAD if unread else REASON_NO_PHASE_COST_TABLE
            return PhaseCostTable(
                entries=None, reason=reason, paid_off=paid_off, held=held, unmapped=withheld
            )
        skipped = reading.skipped_count
        if skipped and not reading.by_phase:
            return PhaseCostTable(
                entries=None,
                reason=REASON_PHASE_COSTS_UNREAD,
                paid_off=paid_off,
                held=held,
                skipped_count=skipped,
                unmapped=withheld,
            )
        unmapped = frozenset(phase for phase in reading.by_phase if phase not in self._installed)
        entries = {
            phase: tuple(
                CostLine(line.item_class, line.amount) for line in lines if line.amount > 0
            )
            for phase, lines in reading.by_phase.items()
            if phase not in unmapped
        }
        if unmapped and not entries:
            return PhaseCostTable(
                entries=None,
                reason=REASON_UNMAPPED_PHASE,
                paid_off=paid_off,
                held=held,
                skipped_count=skipped,
                unmapped=unmapped | withheld,
            )
        return PhaseCostTable(
            entries=MappingProxyType({phase: entries[phase] for phase in sorted(entries)}),
            reason=None,
            paid_off=paid_off,
            held=held,
            skipped_count=skipped,
            unmapped=unmapped | withheld,
        )

    def _paid_off(self) -> tuple[Mapping[str, Mapping[str, Fraction]] | None, frozenset[str]]:
        """What is paid off on the target phase, or why it is withheld - CS-1348 amended.

        Returns:
            The phase to its exact counts, or None for no reading, and the
            phase withheld because the installed vocabulary lacks it - never
            netted against another phase, never mapped onto one.
        """
        reading = self._world.paid_off
        if reading is None:
            return None, frozenset()
        if reading.phase not in self._installed:
            return None, frozenset({reading.phase})
        return MappingProxyType({reading.phase: reading.items}), frozenset()


@dataclass(frozen=True)
class RecipeSelection:
    """The caller's choice of recipes and extractors; this layer chooses neither.

    Attributes:
        recipes: The selected recipe keys, as
            :class:`clockspeed.solve.ratio.RatioRequest` takes them.
        raw_items: Items available without bound.
        byproduct_policy: One of :data:`clockspeed.solve.ratio.BYPRODUCT_POLICIES`,
            required, with no default.
        extractors: Raw item ClassName to the extractor ClassName that mines it.
    """

    recipes: tuple[str, ...]
    raw_items: tuple[str, ...]
    byproduct_policy: str
    extractors: Mapping[str, str]


@dataclass(frozen=True)
class PhaseCost:
    """One selected phase's cost, as required rates and the three A3 figures.

    Attributes:
        phase: The phase token the caller selected.
        required: Cost item to the exact rate per minute that delivers it
            inside ``budget_minutes``. Not rendered; it drives the other three.
        machine: Building ClassName to the machine count at full clock.
        miner: Extractor ClassName to the count at full clock, base rate.
        resource: Raw item ClassName to the rate per minute the chain eats.
        budget_minutes: The completion budget the rates were computed over.
        clock_basis: :data:`CLOCK_BASIS_FULL`, named on the model.
        miner_basis: :data:`MINER_BASIS_BASE_RATE`, named on the model.
        phase_costs_available: Whether the source returned a measured table,
            derived from that table and never hardcoded.
        paid_off_available: Whether the table carries a paid-off reading for
            THIS phase, derived from its ``paid_off`` mapping and never
            hardcoded - CS-1348 amended.
        held_available: Whether the table carries the elevator's input
            reading, derived from its ``held`` mapping and never hardcoded.
            Neither changes a figure.
    """

    phase: str
    required: Figure
    machine: Figure
    miner: Figure
    resource: Figure
    budget_minutes: Fraction
    clock_basis: str
    miner_basis: str
    phase_costs_available: bool
    paid_off_available: bool
    held_available: bool

    def render(self) -> Mapping[str, Mapping[str, Fraction] | None]:
        """Render exactly the three A3 keys.

        Returns:
            ``machine``, ``miner`` and ``resource``, each an exact mapping or
            None. The reason for a None is on the matching figure.
        """
        return MappingProxyType(
            {
                "machine": self.machine.values,
                "miner": self.miner.values,
                "resource": self.resource.values,
            }
        )


@dataclass(frozen=True)
class _Readings:
    """The two derived reading flags, threaded to every site that builds a phase cost.

    Attributes:
        paid_off: The derived ``paid_off_available``.
        held: The derived ``held_available``.
    """

    paid_off: bool
    held: bool


def _missing_reason(table: PhaseCostTable, phase: str) -> str:
    """Why a measured table holds no entry for ``phase`` - CS-1340 repair.

    Args:
        table: The table, known to carry entries.
        phase: The selected phase.

    Returns:
        :data:`REASON_UNMAPPED_PHASE` for a phase the source withheld,
        :data:`REASON_COST_ENTRY_UNREAD` when the source skipped an element the
        phase's entry may be, and :data:`REASON_NO_COST_ENTRY` otherwise.
    """
    if phase in table.unmapped:
        return REASON_UNMAPPED_PHASE
    if table.skipped_count:
        return REASON_COST_ENTRY_UNREAD
    return REASON_NO_COST_ENTRY


def phase_costs_available(source: PhaseCostSource) -> bool:
    """Whether a source has a measured table, read off the table itself.

    Args:
        source: The phase-cost source.

    Returns:
        True when the source returned entries, False when it returned only a
        reason.
    """
    return source.phase_costs().entries is not None


def _machines(registry: Registry, plan: ProductionPlan) -> Figure:
    """Sum the plan's machine counts by the building each recipe runs in.

    Args:
        registry: The registry the plan was solved over.
        plan: The solved plan.

    Returns:
        Building ClassName to the full-clock machine count, or None under
        :data:`REASON_NO_SINGLE_BUILDING` when a running recipe has no single
        building - a partial count would read as the whole.
    """
    totals: dict[str, Fraction] = {}
    for step in plan.steps:
        if step.machines == 0:
            continue
        produced_in = registry.recipes[step.recipe_key].produced_in
        if len(produced_in) != 1:
            return _null(REASON_NO_SINGLE_BUILDING, step.recipe_key)
        building = produced_in[0]
        totals[building] = totals.get(building, Fraction(0)) + step.machines
    if not totals:
        return _null(REASON_NO_SINGLE_BUILDING)
    return _figure(totals)


def _base_rate(registry: Registry, item_key: str, extractor_key: str) -> Fraction | Figure:
    """One extractor's base rate per minute in the item's registry unit.

    Args:
        registry: The registry.
        item_key: The raw item.
        extractor_key: The extractor the caller selected for it.

    Returns:
        The exact positive rate, or the null figure naming why there is none.
    """
    extractor = registry.extractors.get(extractor_key)
    if extractor is None:
        return _null(REASON_UNKNOWN_EXTRACTOR, extractor_key)
    item = registry.items.get(item_key)
    if item is None:
        return _null(REASON_UNKNOWN_RESOURCE, item_key)
    if extractor.allowed_resources is not None:
        admitted = item_key in extractor.allowed_resources
    else:
        admitted = item.form in extractor.allowed_forms
    if not admitted:
        return _null(REASON_EXTRACTOR_CANNOT_YIELD, extractor_key)
    per_cycle, cycle = extractor.items_per_cycle, extractor.extract_cycle_time
    if per_cycle is None or cycle is None or per_cycle <= 0 or cycle <= 0:
        return _null(REASON_EXTRACTOR_RATE_UNAVAILABLE, extractor_key)
    rate = per_minute(per_cycle, cycle)
    if item.is_fluid:
        # mItemsPerCycle is LITRES on a fluid extractor; the solve is in cubic metres.
        rate = rate / Fraction(LITRES_PER_CUBIC_METRE)
    return rate


def _miners(
    registry: Registry, resource: Mapping[str, Fraction], chosen: RecipeSelection
) -> Figure:
    """Count the extractors the raw demand needs, at full clock and base rate.

    Args:
        registry: The registry.
        resource: Raw item to the positive rate the chain eats.
        chosen: The caller's selection, whose extractors are read.

    Returns:
        Extractor ClassName to the exact count, or the null figure naming the
        first raw item, in sorted order, that cannot be mined.
    """
    totals: dict[str, Fraction] = {}
    for item_key, demand in resource.items():
        extractor_key = chosen.extractors.get(item_key)
        if extractor_key is None:
            return _null(REASON_NO_EXTRACTOR_SELECTED, item_key)
        rate = _base_rate(registry, item_key, extractor_key)
        if isinstance(rate, Figure):
            return rate
        totals[extractor_key] = totals.get(extractor_key, Fraction(0)) + demand / rate
    return _figure(totals)


def _all_null(
    phase: str,
    required: Figure,
    reason: str,
    available: bool,
    detail: str = "",
    *,
    readings: _Readings,
) -> PhaseCost:
    """Publish a phase whose three figures share one named reason.

    Args:
        phase: The selected phase.
        required: The required-rate figure, itself possibly null.
        reason: A REASON_* constant.
        available: The derived ``phase_costs_available``.
        detail: Which refusal or key, or the empty string.
        readings: The derived ``paid_off_available`` and ``held_available``.

    Returns:
        The phase cost.
    """
    return PhaseCost(
        phase=phase,
        required=required,
        machine=_null(reason, detail),
        miner=_null(reason, detail),
        resource=_null(reason, detail),
        budget_minutes=milestones.completion_budget(),
        clock_basis=CLOCK_BASIS_FULL,
        miner_basis=MINER_BASIS_BASE_RATE,
        phase_costs_available=available,
        paid_off_available=readings.paid_off,
        held_available=readings.held,
    )


def _solved(
    phase: str,
    required: Figure,
    registry: Registry,
    chosen: RecipeSelection,
    readings: _Readings,
) -> PhaseCost:
    """Solve the required rates over the selection and publish the three figures.

    Args:
        phase: The selected phase.
        required: The required-rate figure, known to carry values.
        registry: The registry.
        chosen: The caller's selection.
        readings: The derived ``paid_off_available`` and ``held_available``.

    Returns:
        The phase cost, every figure computed or null under a named reason.
    """
    targets = required.values
    if targets is None:
        raise PhaseIntegrityError("a phase is solved only over required rates that exist")
    request = RatioRequest(
        targets=targets,
        recipes=chosen.recipes,
        raw_items=chosen.raw_items,
        byproduct_policy=chosen.byproduct_policy,
    )
    try:
        plan = solve_for_targets(registry, request)
    except RatioError as refusal:
        return _all_null(
            phase,
            required,
            REASON_RATIO_REFUSED,
            True,
            type(refusal).__name__,
            readings=readings,
        )
    eaten = {item: rate for item, rate in plan.raw_inputs.items() if rate > 0}
    resource = _figure(eaten) if eaten else _null(REASON_NO_RAW_INPUT)
    miner = _miners(registry, eaten, chosen) if eaten else _null(REASON_NO_RAW_INPUT)
    return PhaseCost(
        phase=phase,
        required=required,
        machine=_machines(registry, plan),
        miner=miner,
        resource=resource,
        budget_minutes=milestones.completion_budget(),
        clock_basis=CLOCK_BASIS_FULL,
        miner_basis=MINER_BASIS_BASE_RATE,
        phase_costs_available=True,
        paid_off_available=readings.paid_off,
        held_available=readings.held,
    )


def phase_cost(
    source: PhaseCostSource,
    registry: Registry,
    phase: str,
    chosen: RecipeSelection | None,
) -> PhaseCost:
    """Build the cost of ANY selected phase, not only the current one.

    Args:
        source: Where phase costs come from; :class:`SavePhaseCosts` over the
            loaded world at the shipped wiring site.
        registry: The registry the selection names recipes and extractors in.
        phase: The selected phase token.
        chosen: The caller's recipe and extractor selection, or None.

    Returns:
        The phase cost, audited exact. Every figure that cannot be derived is
        None with a named reason, never zero and never an empty mapping.

    Raises:
        ValueError: The selection names a recipe this registry does not hold,
            or declares an item both raw and a cost item - a caller shape bug
            the ratio solve refuses as one.
    """
    table = source.phase_costs()
    # Present is True whatever it counts: a zero-count or empty reading is one.
    readings = _Readings(
        paid_off=table.paid_off is not None and phase in table.paid_off,
        held=table.held is not None,
    )
    if table.entries is None:
        if phase in table.unmapped:
            reason = REASON_UNMAPPED_PHASE
        else:
            reason = table.reason or REASON_NO_PHASE_COST_TABLE
        cost = _all_null(phase, _null(reason), reason, False, readings=readings)
    else:
        lines = table.entries.get(phase)
        if lines is None:
            reason = _missing_reason(table, phase)
            cost = _all_null(phase, _null(reason), reason, True, readings=readings)
        elif not lines:
            reason = REASON_EMPTY_COST_ENTRY
            cost = _all_null(phase, _null(reason), reason, True, readings=readings)
        else:
            cost = _costed(phase, lines, registry, chosen, readings)
    audit_exact(cost, path="phase_cost")
    return cost


def _costed(
    phase: str,
    lines: tuple[CostLine, ...],
    registry: Registry,
    chosen: RecipeSelection | None,
    readings: _Readings,
) -> PhaseCost:
    """Publish a phase that has cost lines.

    Args:
        phase: The selected phase.
        lines: Its cost lines, at least one.
        registry: The registry.
        chosen: The caller's selection, or None.
        readings: The derived ``paid_off_available`` and ``held_available``.

    Returns:
        The phase cost.
    """
    totals = milestones.cost_totals(lines)
    nonpositive = [item for item, amount in totals.items() if amount <= 0]
    if nonpositive:
        reason = REASON_NONPOSITIVE_COST
        return _all_null(
            phase,
            _null(reason, nonpositive[0]),
            reason,
            True,
            nonpositive[0],
            readings=readings,
        )
    required = _figure(milestones.required_rates(lines))
    unresolved = [item for item in totals if item not in registry.items]
    if unresolved:
        return _all_null(
            phase,
            required,
            REASON_UNRESOLVED_COST_ITEM,
            True,
            unresolved[0],
            readings=readings,
        )
    if chosen is None:
        return _all_null(
            phase,
            required,
            REASON_NO_RECIPE_SELECTION,
            True,
            readings=readings,
        )
    return _solved(phase, required, registry, chosen, readings)


def phase_costs(
    source: PhaseCostSource,
    registry: Registry,
    phases: Sequence[str],
    chosen: RecipeSelection | None,
) -> tuple[PhaseCost, ...]:
    """Build the cost of every selected phase, in a deterministic order.

    Args:
        source: Where phase costs come from.
        registry: The registry.
        phases: The selected phase tokens, in any order. A repeat is read once.
        chosen: The caller's selection, or None.

    Returns:
        One phase cost per distinct phase, in sorted phase order - never in
        the caller's order. Repeats are dropped in the caller's order rather
        than through a set, so nothing depends on the hash seed.
    """
    return tuple(
        phase_cost(source, registry, phase, chosen) for phase in sorted(dict.fromkeys(phases))
    )
