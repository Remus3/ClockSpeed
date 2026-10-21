"""The milestone model - what a selected schematic costs, and the rate that pays it.

CS-1043 S2, pillar 4. This module names one milestone, its tier, its cost and
the rate of each cost item that would complete it inside the completion
budget, for ANY schematic the caller selects - the target is a free selector
and never a fixed pointer at the next milestone (CLAUDE.md section 7).

WHAT IT CONSUMES, BY MODEL (docs/ARCHITECTURE.md section 3). The schematic
catalog that :func:`clockspeed.data.schematics.normalize_schematics` builds,
the normalized :class:`clockspeed.data.registry.Registry` its cost items are
joined against, and the :class:`clockspeed.save.world.UnlockState` a load
publishes. It never opens the raw docs file and never opens a save.

THE BUDGET IS A NAMED CONSTANT, AND THAT IS THE ACCEPTANCE. Each required rate
is exactly ``cost / COMPLETION_BUDGET_MINUTES``, read at the division site from
:data:`COMPLETION_BUDGET_MINUTES`. A literal there would make the arm that
reddens when the budget moves unreddenable, which is the CS-1039 vacuity shape
by name (docs/item_notes/phase5.md, CS-1043).

FLAG, NEVER FABRICATE (non-negotiable 7).

- **A flagged cost publishes None with a named reason, never zero.** The
  catalog publishes None for a cost it could not read - an amount-less blob
  among them - and a defaulted zero would be a free milestone reported with
  confidence. :data:`REASON_COST_UNREADABLE` names it.
- **A zero or negative cost amount publishes None, never a zero or negative
  rate**, under :data:`REASON_NONPOSITIVE_COST` - the same answer a phase
  gives. The catalog already flags such an amount and publishes the cost as
  None; this guard holds for a catalog built without that flag.
- **An empty cost is the empty mapping, and it is not None.** The catalog
  distinguishes a schematic that costs nothing from one whose cost is unknown,
  and so does this model.
- **An unknown target publishes None under** :data:`REASON_UNKNOWN_SCHEMATIC`
  rather than raising, because a target the pinned build does not know is
  unknown content, not a caller fault.
- **A cost item the registry does not resolve is FLAGGED, never dropped and
  never counted as zero.** The S1 adversary measured cost items on the shipped
  document that name no registry item at all, and the catalog does not flag
  them, so the flag lands here: each such item is one
  :data:`WARN_UNRESOLVED_COST_ITEM` warning carrying its line count, the
  model states how many lines went unresolved, and the milestone's rates
  publish None under :data:`REASON_UNRESOLVED_COST_ITEM` - a rate list short
  of an item would read as the whole requirement. The cost itself is still
  published as written, because the document does state it.
- **The HUB tier is UNAVAILABLE, never zero.** Tier zero is a real onboarding
  tier, so publishing it for an unread level is a confident wrong answer. The
  save model's ``trading_post_level`` is None on every load today, because no
  carrier is measured for it, and this model publishes that as None under
  :data:`REASON_HUB_TIER_UNREAD`.

UNITS ARE NOT CONVERTED. A cost amount is the blob's integer exactly as
written, which is what :data:`AMOUNT_BASIS_AS_WRITTEN` names on the model, so a
rate is in the same unit per minute.

NO FLOAT, ANYWHERE (non-negotiable 6). An amount and the budget are each
checked to be exactly a Fraction at the division, and every published model is
passed through :func:`clockspeed.solve.exact.audit_exact` before it is returned.

DETERMINISM. Rates are keyed by item ClassName in sorted order, a repeated item
is summed exactly, and a set of requirements is published in tier order then
ClassName order, so the same inputs publish the same output in the same order
whatever order the document or the caller listed them in.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from fractions import Fraction
from types import MappingProxyType
from typing import Final

from clockspeed.data.registry import Registry
from clockspeed.data.schematics import CostLine, SchematicCatalog
from clockspeed.save.world import UnlockState
from clockspeed.solve.exact import InexactValueError, audit_exact

__all__ = [
    "AMOUNT_BASIS_AS_WRITTEN",
    "COMPLETION_BUDGET_MINUTES",
    "REASON_COST_UNREADABLE",
    "REASON_HUB_TIER_UNREAD",
    "REASON_NONPOSITIVE_COST",
    "REASON_UNKNOWN_SCHEMATIC",
    "REASON_UNRESOLVED_COST_ITEM",
    "WARN_UNRESOLVED_COST_ITEM",
    "HubTier",
    "MilestoneRequirement",
    "MilestoneWarning",
    "completion_budget",
    "cost_totals",
    "hub_tier",
    "milestone_requirement",
    "milestone_requirements",
    "required_rates",
    "unresolved_cost_items",
]

#: The completion budget, in minutes: two hours. Every required rate is a cost
#: amount over this value, read at the division site and never restated there.
COMPLETION_BUDGET_MINUTES: Final = Fraction(120)

#: The unit basis of every cost amount and rate: the document's integer as
#: written, never unit-converted.
AMOUNT_BASIS_AS_WRITTEN: Final = "as-written"

#: The target names no schematic in the catalog.
REASON_UNKNOWN_SCHEMATIC: Final = "unknown-schematic"
#: The catalog flagged this schematic's cost and published it as None.
REASON_COST_UNREADABLE: Final = "cost-unreadable"
#: The save model read no HUB tier; no carrier is measured for it.
REASON_HUB_TIER_UNREAD: Final = "hub-tier-unread"
#: A cost item totals zero or less, which no rate can honestly deliver.
REASON_NONPOSITIVE_COST: Final = "nonpositive-cost"
#: A cost item names nothing in the registry, so the rates are not derived.
REASON_UNRESOLVED_COST_ITEM: Final = "unresolved-cost-item"

#: The warning code for one cost item the registry does not resolve.
WARN_UNRESOLVED_COST_ITEM: Final = "unresolved-cost-item"


@dataclass(frozen=True)
class HubTier:
    """The HUB tier the world has reached, or why it is unavailable.

    Attributes:
        tier: The tier as read, or None when the save model read none. Zero is
            a real tier and is published as zero; None is never defaulted.
        reason: None when ``tier`` was read, otherwise a REASON_* constant.
    """

    tier: int | None
    reason: str | None


@dataclass(frozen=True)
class MilestoneWarning:
    """One cost item this model flagged, and why.

    Attributes:
        code: A WARN_* constant.
        subject: The item ClassName.
        detail: One line naming the consequence, never echoing a value.
        count: How many cost lines this row aggregates.
    """

    code: str
    subject: str
    detail: str
    count: int


@dataclass(frozen=True)
class MilestoneRequirement:
    """One selected schematic's cost and the rates that complete it in budget.

    Attributes:
        target: The ClassName the caller selected.
        tech_tier: The schematic's tier, or None when the catalog could not
            read one or the target is unknown.
        type_token: The schematic's ``mType`` token verbatim, or None.
        cost: Item ClassName to the total amount, sorted by ClassName, or None
            with ``reason`` set. The empty mapping is a schematic that costs
            nothing.
        rates: Item ClassName to the exact rate per minute that delivers
            ``cost`` inside ``budget_minutes``, or None with ``reason`` set -
            whenever ``cost`` is None, and whenever a cost item does not
            resolve in the registry.
        reason: None when ``rates`` was derived, otherwise a REASON_*
            constant.
        hub_tier: The world's HUB tier, or why it is unavailable.
        budget_minutes: The completion budget these rates were computed over.
        amount_basis: The unit basis of ``cost`` and ``rates``.
        warnings: Every cost item flagged, sorted by item ClassName.
        unresolved_lines: How many cost lines name an item the registry does
            not resolve, or None when the cost is not published.
    """

    target: str
    tech_tier: int | None
    type_token: str | None
    cost: Mapping[str, Fraction] | None
    rates: Mapping[str, Fraction] | None
    reason: str | None
    hub_tier: HubTier
    budget_minutes: Fraction
    amount_basis: str
    warnings: tuple[MilestoneWarning, ...]
    unresolved_lines: int | None


def _require_fraction(value: object, name: str) -> Fraction:
    """Refuse anything that is not exactly a Fraction.

    Args:
        value: The operand.
        name: How to name it in the message.

    Returns:
        The value, narrowed.

    Raises:
        InexactValueError: The value is not exactly a Fraction. Identity, not
            ``isinstance``, for the reason ``clockspeed/solve/exact.py`` gives.
    """
    if type(value) is not Fraction:
        raise InexactValueError(
            f"{name} is {type(value).__name__}, not a Fraction; a required rate is exact "
            "rational arithmetic and mixed arithmetic silently returns a float"
        )
    return value


def completion_budget() -> Fraction:
    """Read the completion budget, checked exact.

    Returns:
        :data:`COMPLETION_BUDGET_MINUTES`.

    Raises:
        InexactValueError: The budget is not exactly a Fraction.
    """
    return _require_fraction(COMPLETION_BUDGET_MINUTES, "the completion budget")


def cost_totals(lines: Iterable[CostLine]) -> Mapping[str, Fraction]:
    """Total a cost by item, exactly, in sorted ClassName order.

    Args:
        lines: The cost lines, in any order. A repeated item is summed.

    Returns:
        Item ClassName to total amount, read-only.

    Raises:
        InexactValueError: An amount is not exactly a Fraction.
    """
    totals: dict[str, Fraction] = {}
    for line in lines:
        amount = _require_fraction(line.amount, "a cost amount")
        totals[line.item_class] = totals.get(line.item_class, Fraction(0)) + amount
    return MappingProxyType({item: totals[item] for item in sorted(totals)})


def required_rates(lines: Iterable[CostLine]) -> Mapping[str, Fraction]:
    """Each cost item's required rate: its total amount over the completion budget.

    Args:
        lines: The cost lines, in any order.

    Returns:
        Item ClassName to the exact rate per minute, in sorted ClassName order.

    Raises:
        InexactValueError: An amount or the budget is not exactly a Fraction.
    """
    budget = completion_budget()
    totals = cost_totals(lines)
    return MappingProxyType({item: amount / budget for item, amount in totals.items()})


def unresolved_cost_items(lines: Iterable[CostLine], registry: Registry) -> Mapping[str, int]:
    """Count the cost lines whose item the registry does not resolve.

    Args:
        lines: The cost lines.
        registry: The normalized registry; ``items`` is the join.

    Returns:
        Unresolved item ClassName to its line count, in sorted order.
    """
    counts: dict[str, int] = {}
    for line in lines:
        if line.item_class not in registry.items:
            counts[line.item_class] = counts.get(line.item_class, 0) + 1
    return MappingProxyType({item: counts[item] for item in sorted(counts)})


def hub_tier(unlocks: UnlockState) -> HubTier:
    """Publish the HUB tier the save model read, or name why it is unavailable.

    Args:
        unlocks: The world's unlock state.

    Returns:
        The tier as read, zero included, or None under
        :data:`REASON_HUB_TIER_UNREAD` - never a defaulted zero.
    """
    level = unlocks.trading_post_level
    if level is None:
        return HubTier(tier=None, reason=REASON_HUB_TIER_UNREAD)
    return HubTier(tier=level, reason=None)


def milestone_requirement(
    catalog: SchematicCatalog, registry: Registry, unlocks: UnlockState, target: str
) -> MilestoneRequirement:
    """Build the requirement for ANY selected schematic, not only the next one.

    Args:
        catalog: The normalized schematic catalog.
        registry: The normalized registry the cost items are joined against.
        unlocks: The world's unlock state.
        target: The selected schematic's ClassName.

    Returns:
        The requirement, audited exact. An unknown target, a flagged cost, a
        non-positive amount or an unresolved cost item is published as None
        with its named reason, never as zero.

    Raises:
        InexactValueError: A cost amount or the budget is not exactly a
            Fraction.
    """
    budget = completion_budget()
    hub = hub_tier(unlocks)
    schematic = catalog.schematics.get(target)
    if schematic is None:
        requirement = MilestoneRequirement(
            target=target,
            tech_tier=None,
            type_token=None,
            cost=None,
            rates=None,
            reason=REASON_UNKNOWN_SCHEMATIC,
            hub_tier=hub,
            budget_minutes=budget,
            amount_basis=AMOUNT_BASIS_AS_WRITTEN,
            warnings=(),
            unresolved_lines=None,
        )
    elif schematic.cost is None:
        requirement = MilestoneRequirement(
            target=target,
            tech_tier=schematic.tech_tier,
            type_token=schematic.type_token,
            cost=None,
            rates=None,
            reason=REASON_COST_UNREADABLE,
            hub_tier=hub,
            budget_minutes=budget,
            amount_basis=AMOUNT_BASIS_AS_WRITTEN,
            warnings=(),
            unresolved_lines=None,
        )
    elif any(amount <= 0 for amount in cost_totals(schematic.cost).values()):
        requirement = MilestoneRequirement(
            target=target,
            tech_tier=schematic.tech_tier,
            type_token=schematic.type_token,
            cost=None,
            rates=None,
            reason=REASON_NONPOSITIVE_COST,
            hub_tier=hub,
            budget_minutes=budget,
            amount_basis=AMOUNT_BASIS_AS_WRITTEN,
            warnings=(),
            unresolved_lines=None,
        )
    else:
        unresolved = unresolved_cost_items(schematic.cost, registry)
        warnings = tuple(
            MilestoneWarning(
                code=WARN_UNRESOLVED_COST_ITEM,
                subject=item,
                detail="cost item names no registry item; the rates are not derived",
                count=count,
            )
            for item, count in unresolved.items()
        )
        requirement = MilestoneRequirement(
            target=target,
            tech_tier=schematic.tech_tier,
            type_token=schematic.type_token,
            cost=cost_totals(schematic.cost),
            rates=None if unresolved else required_rates(schematic.cost),
            reason=REASON_UNRESOLVED_COST_ITEM if unresolved else None,
            hub_tier=hub,
            budget_minutes=budget,
            amount_basis=AMOUNT_BASIS_AS_WRITTEN,
            warnings=warnings,
            unresolved_lines=sum(unresolved.values()),
        )
    audit_exact(requirement, path="requirement")
    return requirement


def _order_key(requirement: MilestoneRequirement) -> tuple[bool, int, str]:
    """Sort by tier, an unknown tier last, then by ClassName.

    Args:
        requirement: One requirement.

    Returns:
        The sort key.
    """
    tier = requirement.tech_tier
    return (tier is None, 0 if tier is None else tier, requirement.target)


def milestone_requirements(
    catalog: SchematicCatalog, registry: Registry, unlocks: UnlockState, targets: Sequence[str]
) -> tuple[MilestoneRequirement, ...]:
    """Build the requirement for every selected schematic, in a deterministic order.

    Args:
        catalog: The normalized schematic catalog.
        registry: The normalized registry the cost items are joined against.
        unlocks: The world's unlock state.
        targets: The selected ClassNames, in any order. A repeat is read once.

    Returns:
        One requirement per distinct target, in tier order with an unknown
        tier last, then ClassName order - never in the caller's order.
        Repeats are dropped in the caller's order rather than through a
        set, so nothing here depends on the hash seed even before the sort.
    """
    built = (
        milestone_requirement(catalog, registry, unlocks, target)
        for target in dict.fromkeys(targets)
    )
    return tuple(sorted(built, key=_order_key))
