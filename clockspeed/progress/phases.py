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

A PHASE WITH NO COST ENTRY IS NULL, NEVER ZERO (non-negotiable 7). A measured
table that holds no entry for the selected phase publishes every figure as None
under :data:`REASON_NO_COST_ENTRY`. An empty entry, a non-positive amount and a
cost item the registry does not resolve are each null under their own reason.

STILL TO BUILD, AND ``delivered_available`` IS DERIVED (CS-1343). Items already
delivered into the elevator sit in its input inventory. A source publishes that
reading as the ``delivered`` mapping on :class:`PhaseCostTable`, and a phase
cost's ``delivered_available`` is True exactly when the mapping is present -
even when every count in it is zero, because a zero-count reading is still a
reading. :class:`SavePhaseCosts` publishes no delivered reading yet, so the
flag reads False on it. Either way this model does not subtract a delivered
reading: every figure is driven by the amounts the source published, which
for the save source are already what the world still owes.

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
from clockspeed.data.schematics import CostLine
from clockspeed.progress import milestones
from clockspeed.save.world import WorldModel
from clockspeed.solve.exact import audit_exact, per_minute
from clockspeed.solve.ratio import ProductionPlan, RatioError, RatioRequest, solve_for_targets

__all__ = [
    "CLOCK_BASIS_FULL",
    "MINER_BASIS_BASE_RATE",
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
    "REASON_RATIO_REFUSED",
    "REASON_UNKNOWN_EXTRACTOR",
    "REASON_UNKNOWN_RESOURCE",
    "REASON_UNRESOLVED_COST_ITEM",
    "Figure",
    "PhaseCost",
    "PhaseCostSource",
    "PhaseCostTable",
    "PhaseIntegrityError",
    "RecipeSelection",
    "SavePhaseCosts",
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
        delivered: Item ClassName to the exact count already delivered into
            the elevator, in the registry's units, or None when the source has
            no delivered reading. Independent of ``entries``: a reading of
            zero counts, or of no items at all, is still a reading.
    """

    entries: Mapping[str, tuple[CostLine, ...]] | None
    reason: str | None
    delivered: Mapping[str, Fraction] | None = None

    def __post_init__(self) -> None:
        """Refuse a table that is both or neither, or a delivered count that is not exact.

        Raises:
            PhaseIntegrityError: Both or neither of ``entries`` and ``reason``
                is set, or a delivered count is not an exact Fraction at zero
                or above.
        """
        if (self.entries is None) == (self.reason is None):
            raise PhaseIntegrityError("a phase-cost table carries exactly one of entries or reason")
        if self.delivered is not None:
            for count in self.delivered.values():
                if type(count) is not Fraction or count < 0:
                    raise PhaseIntegrityError(
                        "a delivered count is an exact Fraction at zero or above, never a float"
                    )


class PhaseCostSource(Protocol):
    """Where phase costs come from, parameterised at the wiring site."""

    def phase_costs(self) -> PhaseCostTable:
        """Publish the phase-cost table.

        Returns:
            The table, or a table carrying only the reason there is none.
        """
        ...


class SavePhaseCosts:
    """The shipped source: a world's own ``mGamePhaseCosts``, under the measured meaning.

    CS-1340. It consumes the save layer through its stated model only -
    ``WorldModel.phase_costs`` - and reads no bytes and no record.
    """

    def __init__(self, world: WorldModel) -> None:
        """Hold the world whose phase costs this source publishes.

        Args:
            world: The loaded world model.
        """
        self._world = world

    def phase_costs(self) -> PhaseCostTable:
        """Publish each phase's OWED lines, or no table when the world wrote none.

        A line the save says is paid - zero owed - is dropped, because it is
        nothing to build; a phase paid in full is therefore an EMPTY entry.
        Kept, a paid line would null its whole phase as a non-positive cost
        and hide what the phase still owes on its other lines.

        Returns:
            The table, or one carrying only :data:`REASON_NO_PHASE_COST_TABLE`.
            No delivered reading: :class:`SavePhaseCosts` publishes none yet.
        """
        reading = self._world.phase_costs
        if reading is None:
            return PhaseCostTable(entries=None, reason=REASON_NO_PHASE_COST_TABLE, delivered=None)
        entries = {
            phase: tuple(
                CostLine(line.item_class, line.amount) for line in lines if line.amount > 0
            )
            for phase, lines in reading.by_phase.items()
        }
        return PhaseCostTable(
            entries=MappingProxyType({phase: entries[phase] for phase in sorted(entries)}),
            reason=None,
            delivered=None,
        )


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
        delivered_available: Whether the source returned a delivered
            reading, derived from the table's ``delivered`` mapping and never
            hardcoded. Every figure stays the REQUIRED quantity either way.
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
    delivered_available: bool

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
    delivered_available: bool,
) -> PhaseCost:
    """Publish a phase whose three figures share one named reason.

    Args:
        phase: The selected phase.
        required: The required-rate figure, itself possibly null.
        reason: A REASON_* constant.
        available: The derived ``phase_costs_available``.
        detail: Which refusal or key, or the empty string.
        delivered_available: The derived ``delivered_available``.

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
        delivered_available=delivered_available,
    )


def _solved(
    phase: str,
    required: Figure,
    registry: Registry,
    chosen: RecipeSelection,
    delivered_available: bool,
) -> PhaseCost:
    """Solve the required rates over the selection and publish the three figures.

    Args:
        phase: The selected phase.
        required: The required-rate figure, known to carry values.
        registry: The registry.
        chosen: The caller's selection.
        delivered_available: The derived ``delivered_available``.

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
            delivered_available=delivered_available,
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
        delivered_available=delivered_available,
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
    delivered = table.delivered is not None
    if table.entries is None:
        reason = table.reason or REASON_NO_PHASE_COST_TABLE
        cost = _all_null(phase, _null(reason), reason, False, delivered_available=delivered)
    else:
        lines = table.entries.get(phase)
        if lines is None:
            reason = REASON_NO_COST_ENTRY
            cost = _all_null(phase, _null(reason), reason, True, delivered_available=delivered)
        elif not lines:
            reason = REASON_EMPTY_COST_ENTRY
            cost = _all_null(phase, _null(reason), reason, True, delivered_available=delivered)
        else:
            cost = _costed(phase, lines, registry, chosen, delivered)
    audit_exact(cost, path="phase_cost")
    return cost


def _costed(
    phase: str,
    lines: tuple[CostLine, ...],
    registry: Registry,
    chosen: RecipeSelection | None,
    delivered_available: bool,
) -> PhaseCost:
    """Publish a phase that has cost lines.

    Args:
        phase: The selected phase.
        lines: Its cost lines, at least one.
        registry: The registry.
        chosen: The caller's selection, or None.
        delivered_available: The derived ``delivered_available``.

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
            delivered_available=delivered_available,
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
            delivered_available=delivered_available,
        )
    if chosen is None:
        return _all_null(
            phase,
            required,
            REASON_NO_RECIPE_SELECTION,
            True,
            delivered_available=delivered_available,
        )
    return _solved(phase, required, registry, chosen, delivered_available)


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
