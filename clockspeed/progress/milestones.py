"""Milestone requirements: what a schematic costs, stated as an exact rate.

Owns the milestone requirement model for pillar 4 - one modelled milestone per
``EST_Milestone`` schematic entry, its tier, whether the player has bought it,
and each item it costs expressed as an exact per-minute rate.

WHY THE SOURCE IS A PROTOCOL AND NOT THE DATA LAYER'S DOCUMENT TYPE. Naming
that type here would make this module import three layers down for an
annotation, which is the argument ``clockspeed/surface/api/contract.py`` makes
for ``WorldProvider`` and the reason that one is generic too. So
:class:`SchematicSource` is declared here, parameterised over the ENTRY type,
and the site that owns a document writes the parameter. It also keeps
``clockspeed/data/registry.py`` untouched: that module already ruled that
``FGSchematic`` belongs to this layer, and this module follows the ruling rather
than reopening it.

AN ENTRY VALUE IS ``object`` AND NOT ``str``. The shipped document carries
non-string values in ``FGSchematic`` list fields - ``clockspeed/data/registry.py``
reads entries as ``Mapping[str, object]`` on its own side for exactly that
reason - so every value read below is type-checked before use, and a present
value of the wrong type is FLAGGED AND SKIPPED rather than coerced. An absent
field is silent, because absence is a meaningful reading of an optional field
while a present surprise is content this build does not understand. Collapsing
those two would hide new game content behind "not present, therefore not
applicable".

THE COMPLETION BUDGET IS A NAMED CONSTANT, :data:`MILESTONE_BUDGET_MINUTES`,
AND IT IS READ INSIDE THE FUNCTION BODY. A literal at the division site, or a
default argument value bound at def time, both make the budget impossible to
perturb from outside - and a rate nobody can move is a rate no test can grade.
That is the vacuity shape CS-1039 records by name.

THE JOIN IS THE RESOLVED CONTENT ASSET PATH. ``UnlockState.purchased_schematics``
holds whole ``/Game/...`` asset paths and an entry's ``FullName`` carries the
same path after its type token, so membership is a whole-path test. The two
shipped path reducers - ``clockspeed/save/objects.py`` ``class_name_of`` and
``clockspeed/audit/placement.py`` ``class_name_of_path`` - both reduce to a BARE
NAME and are therefore not this join; two schematics in different packages can
share a trailing token, and a bare-name match would call both of them bought.

NO ASSET PATH REACHES A REPR. Paths cross this seam and may not reach a repr, a
log line or an exception (non-negotiable 12), so
:class:`MilestoneRequirements` hand-writes a ``__repr__`` that renders counts
only, the two path-bearing fields elsewhere are declared ``repr=False``, and no
warning carries a subject.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from fractions import Fraction
from types import MappingProxyType
from typing import Final, Protocol, runtime_checkable

from clockspeed.data.blobs import BlobParseError, parse_item_amounts
from clockspeed.save.world import UnlockState, WorldWarning
from clockspeed.solve.exact import audit_exact

__all__ = [
    "ASSET_PATH_CLASS_SEPARATOR",
    "FULL_NAME_FIELD_COUNT",
    "FULL_NAME_SEPARATOR",
    "KEY_COST",
    "KEY_FULL_NAME",
    "KEY_TECH_TIER",
    "KEY_TYPE",
    "MILESTONE_BUDGET_MINUTES",
    "RATE_BASIS_FULL_CLOCK",
    "SCHEMATIC_GROUP",
    "SOURCE_MILESTONES",
    "TYPE_MILESTONE",
    "WARN_MILESTONE_ASSET_PATH_UNREADABLE",
    "WARN_MILESTONE_COST_UNREADABLE",
    "WARN_MILESTONE_HUB_TIER_UNREAD",
    "WARN_MILESTONE_SCHEMATICS_UNAVAILABLE",
    "WARN_MILESTONE_TIER_UNREADABLE",
    "WARN_MILESTONE_TYPE_UNREADABLE",
    "Milestone",
    "MilestoneCost",
    "MilestoneRequirements",
    "SchematicSource",
    "requirements_of",
]

# ---------------------------------------------------------------------------
# What this module reads, and what it deliberately does not
# ---------------------------------------------------------------------------

#: Which layer noticed a warning raised here, for ``WorldWarning.source``.
SOURCE_MILESTONES: Final = "milestones"

#: The docs group short name whose entries this module models. Named here and
#: not imported from the data layer, which excludes this group from its own
#: modelled set on the grounds that it belongs to this one.
SCHEMATIC_GROUP: Final = "FGSchematic"

#: The cost blob field. Its grammar is ``clockspeed/data/blobs.py``'s, and
#: :func:`clockspeed.data.blobs.parse_item_amounts` is the only reader of it
#: here - a second implementation of that grammar is the one way to be wrong in
#: a way the shipped marker cross-check cannot see.
KEY_COST: Final = "mCost"

#: The technology tier field.
KEY_TECH_TIER: Final = "mTechTier"

#: The schematic kind field, which decides whether an entry is a milestone.
KEY_TYPE: Final = "mType"

#: The field carrying a type token and an asset path, in that order.
KEY_FULL_NAME: Final = "FullName"

# ``mTimeToComplete`` IS DELIBERATELY NOT READ. It is a float-shaped string, and
# converting one into a rate is the single place a float would enter this layer.
# The budget below is this module's own constant precisely so that no shipped
# duration has to be parsed to produce a rate.

#: The ``mType`` value that marks a milestone, as against the other schematic
#: kinds the same group carries.
TYPE_MILESTONE: Final = "EST_Milestone"

#: The single space between a FullName's type token and its asset path.
FULL_NAME_SEPARATOR: Final = " "

#: How many fields one split on :data:`FULL_NAME_SEPARATOR` must yield. Checked
#: rather than assumed: a FullName with no space at all would otherwise raise
#: IndexError where a flag-and-skip belongs.
FULL_NAME_FIELD_COUNT: Final = 2

#: The separator between an Unreal package path and the class inside it, used
#: ONLY to derive a human label. It is never the join - see the module
#: docstring.
ASSET_PATH_CLASS_SEPARATOR: Final = "."

# ---------------------------------------------------------------------------
# The budget, and the assumption every rate holds under
# ---------------------------------------------------------------------------

#: The completion budget every required rate is taken over - two hours. A NAMED
#: CONSTANT AND NOT A LITERAL AT THE DIVISION SITE, and the reason is the whole
#: of the acceptance clause rather than style: a budget written at the site
#: cannot be moved, so no test can show that a rate follows it. It is read
#: inside :func:`requirements_of`'s body and is NEVER a default argument value,
#: which would bind at def time and be just as immovable. Graded by
#: tests/progress/test_milestones.py::test_the_required_rate_reddens_when_the_named_budget_moves
MILESTONE_BUDGET_MINUTES: Final = Fraction(120)

#: The assumption every rate here is computed under, named ON THE MODEL rather
#: than in a comment, so a consumer rendering a rate can state the terms it is
#: true on instead of implying a measurement.
RATE_BASIS_FULL_CLOCK: Final = "every-machine-at-full-clock"

# ---------------------------------------------------------------------------
# The warning vocabulary. An empty answer with nothing said about it is
# indistinguishable from a target that genuinely requires nothing.
# ---------------------------------------------------------------------------

#: No schematic document was available at all - the source said so with a
#: value, which is a true answer about a working machine and not an error.
WARN_MILESTONE_SCHEMATICS_UNAVAILABLE: Final = "milestone-schematics-unavailable"

#: A cost field that is present and cannot be read - not a string, or a blob
#: the measured grammar does not explain end to end. The milestone is still
#: modelled and publishes NO cost, because a short cost list is a wrong number
#: nothing downstream could tell from a right one.
WARN_MILESTONE_COST_UNREADABLE: Final = "milestone-cost-unreadable"

#: A tier field that is present and is not an integer. The milestone is still
#: modelled, with a null tier.
WARN_MILESTONE_TIER_UNREADABLE: Final = "milestone-tier-unreadable"

#: A kind field that is present and is not a string, so the entry could not be
#: classified either way and is not modelled.
WARN_MILESTONE_TYPE_UNREADABLE: Final = "milestone-type-unreadable"

#: A FullName that yields no asset path, so the entry has no join key and
#: nothing true can be said about whether it was bought.
WARN_MILESTONE_ASSET_PATH_UNREADABLE: Final = "milestone-asset-path-unreadable"

#: The HUB tier this reader never read. ALWAYS RAISED WHILE THE TIER IS NULL:
#: ``UnlockState.trading_post_level`` is null on every path today because no
#: carrier for it has been measured, and a null tier with nothing said about it
#: reads exactly like a HUB that is genuinely at no tier.
WARN_MILESTONE_HUB_TIER_UNREAD: Final = "milestone-hub-tier-unread"

#: Fixed detail text, one entry per code. A table rather than per-site prose so
#: the same fault reads the same way wherever it is noticed, and so no detail
#: string can be built from a value that came out of a save.
_WARNING_DETAIL: Final[Mapping[str, str]] = MappingProxyType(
    {
        WARN_MILESTONE_SCHEMATICS_UNAVAILABLE: (
            "no schematic document was available on this machine, so the milestone"
            " list is empty because there was nothing to read and never because"
            " nothing is required"
        ),
        WARN_MILESTONE_COST_UNREADABLE: (
            "this many milestones carried a cost field this build could not read,"
            " and contributed no cost at all rather than a short one; their"
            " requirement is unknown and is never zero"
        ),
        WARN_MILESTONE_TIER_UNREADABLE: (
            "this many milestones carried a tier that is not an integer, so their"
            " tier is null and no tier ordering can place them"
        ),
        WARN_MILESTONE_TYPE_UNREADABLE: (
            "this many entries carried a kind that is not a string, so they were"
            " classified as neither milestone nor anything else and are absent from"
            " the model entirely"
        ),
        WARN_MILESTONE_ASSET_PATH_UNREADABLE: (
            "this many entries yielded no asset path, so there was no key to join"
            " them to the unlock state on and they are absent from the model"
        ),
        WARN_MILESTONE_HUB_TIER_UNREAD: (
            "the HUB tier was not read, so a null tier here is this reader saying"
            " nothing and never a HUB measured to be at no tier"
        ),
    }
)


@runtime_checkable
class SchematicSource[EntryT](Protocol):
    """Whatever hands this layer the schematic entries, or says there are none.

    GENERIC OVER THE ENTRY TYPE RATHER THAN OVER A DOCUMENT, and the module
    docstring records why: naming the data layer's document type here would make
    this module import three layers down for an annotation. The site that holds
    a document writes ``SchematicSource[Mapping[str, object]]`` itself.

    ``None`` IS "NO DOCUMENT ON THIS MACHINE" AND IS NOT AN ERROR. That is a
    true answer about a working system, so it is spelled as a value, and
    :func:`requirements_of` turns it into an empty model plus a warning rather
    than a refusal.
    """

    def schematics(self) -> tuple[EntryT, ...] | None:
        """The schematic entries, or None when this machine has no document.

        Returns:
            The entries in document order, or None.
        """
        ...


@dataclass(frozen=True)
class MilestoneCost:
    """One item a milestone costs, and the rate that pays for it in the budget.

    Frozen because it is a reading of shipped data joined to a constant, not a
    working value.

    Attributes:
        item_key: The descriptor class token the blob parser derived, for
            example ``Desc_OreIron_C``.
        raw_path: The whole path exactly as the blob carried it, kept as the
            only evidence available if ``item_key`` ever fails to resolve, and
            WITHHELD FROM THE REPR because it is a content asset path.
        amount: The amount exactly as the document wrote it. NOT unit
            converted - ``clockspeed/data/blobs.py`` records why units are not
            knowable from a blob.
        required_per_minute: ``amount`` over :data:`MILESTONE_BUDGET_MINUTES`,
            as an exact Fraction. True on :data:`RATE_BASIS_FULL_CLOCK`'s terms
            and on no others.
    """

    item_key: str
    raw_path: str = field(repr=False)
    amount: int
    required_per_minute: Fraction


@dataclass(frozen=True)
class Milestone:
    """One milestone, what it costs, and whether it has already been bought.

    Attributes:
        class_name: A HUMAN LABEL derived from the trailing token of the asset
            path. NOTHING COMPARES IT - it is not the join, and two milestones
            in different packages can legitimately share one.
        asset_path: The whole resolved content asset path, which IS the join
            key, and WITHHELD FROM THE REPR for it.
        tech_tier: The declared tier, or None when none was readable. Null and
            zero are different answers and this never reports the second for
            the first.
        schematic_type: The kind token, always :data:`TYPE_MILESTONE` here,
            carried so a consumer never has to assume it.
        purchased: Whether ``asset_path`` is in the unlock state's purchased
            set. False means "not in that set", and the set carries its own
            warning about what the save layer could not read.
        costs: The readable costs, WITHHELD FROM THE REPR because each carries
            a path. Empty for a milestone whose cost could not be read, which
            is why the unreadable-cost warning exists.
    """

    class_name: str
    asset_path: str = field(repr=False)
    tech_tier: int | None
    schematic_type: str
    purchased: bool
    costs: tuple[MilestoneCost, ...] = field(repr=False)


@dataclass(frozen=True, repr=False)
class MilestoneRequirements:
    """Every milestone this reader could model, and the budget it priced them at.

    ``repr`` IS HAND WRITTEN AND RENDERS COUNTS ONLY. The milestones below hold
    content asset paths, and a test runner reprs a value before a human chooses
    what to print (non-negotiable 12). The budget and the basis ARE rendered:
    both are this module's own constants and neither can carry anything read out
    of a file.

    Attributes:
        milestones: The modelled milestones, in document order.
        budget_minutes: The completion budget every rate here is taken over,
            carried on the model so a consumer never restates it.
        rate_basis: The assumption the rates hold under.
        hub_tier: The HUB tier, or None. Null today on every path, with
            :data:`WARN_MILESTONE_HUB_TIER_UNREAD` beside it.
        warnings: Everything flagged, in the ``WorldWarning`` idiom, aggregated
            one entry per code with a count. No warning carries a subject,
            because the only subject available here would be an asset path.
    """

    milestones: tuple[Milestone, ...]
    budget_minutes: Fraction
    rate_basis: str
    hub_tier: int | None
    warnings: tuple[WorldWarning, ...]

    def __repr__(self) -> str:
        """Render counts and this module's own constants, and withhold every path.

        Returns:
            The safe rendering.
        """
        return (
            f"{type(self).__name__}("
            f"milestones={len(self.milestones)}, "
            f"budget_minutes={self.budget_minutes!r}, "
            f"rate_basis={self.rate_basis!r}, "
            f"hub_tier={self.hub_tier}, "
            f"warnings={len(self.warnings)})"
        )


def _flag(log: dict[str, int], code: str) -> None:
    """Count one occurrence of a warning code.

    Args:
        log: The running tally, keyed by code.
        code: One of this module's ``WARN_*`` constants.
    """
    log[code] = log.get(code, 0) + 1


def _warnings_of(log: dict[str, int]) -> tuple[WorldWarning, ...]:
    """Build one warning per flagged code from this module's fixed detail table.

    Sorted by code so two runs over one input return equal models.

    Args:
        log: The tally.

    Returns:
        One warning per code, with its count.
    """
    return tuple(
        WorldWarning(
            source=SOURCE_MILESTONES,
            code=code,
            detail=_WARNING_DETAIL[code],
            count=count,
        )
        for code, count in sorted(log.items())
    )


def _is_milestone(entry: Mapping[str, object], log: dict[str, int]) -> bool:
    """Whether one entry declares itself a milestone.

    An absent kind is silent - the group carries several kinds and absence is a
    reading, not a surprise. A PRESENT non-string is content this build does not
    understand, and is flagged.

    Args:
        entry: The entry mapping.
        log: The warning tally.

    Returns:
        True only for an entry whose kind is exactly :data:`TYPE_MILESTONE`.
    """
    value = entry.get(KEY_TYPE)
    if value is None:
        return False
    if isinstance(value, str):
        return value == TYPE_MILESTONE
    _flag(log, WARN_MILESTONE_TYPE_UNREADABLE)
    return False


def _asset_path_of(entry: Mapping[str, object], log: dict[str, int]) -> str | None:
    """Read the resolved content asset path out of one entry's FullName.

    The FullName is a type token and an asset path separated by one space, so
    the path is everything after the first space. THE WHOLE PATH IS KEPT: it is
    the join key, and reducing it to a trailing class token would make two
    schematics in different packages compare equal.

    Args:
        entry: The entry mapping.
        log: The warning tally.

    Returns:
        The asset path, or None when there is none to read.
    """
    value = entry.get(KEY_FULL_NAME)
    if not isinstance(value, str):
        _flag(log, WARN_MILESTONE_ASSET_PATH_UNREADABLE)
        return None
    parts = value.split(FULL_NAME_SEPARATOR, 1)
    if len(parts) != FULL_NAME_FIELD_COUNT or not parts[1]:
        _flag(log, WARN_MILESTONE_ASSET_PATH_UNREADABLE)
        return None
    return parts[1]


def _tier_of(entry: Mapping[str, object], log: dict[str, int]) -> int | None:
    """Read one entry's declared tier as an integer, or say it could not be read.

    A docs scalar arrives as a string, so the string branch is the normal one. A
    bool is rejected ahead of the int branch on purpose: ``True`` is ``1`` to
    ``isinstance``, and reporting a flag as tier one would be a confident wrong
    answer rather than a refusal.

    Args:
        entry: The entry mapping.
        log: The warning tally.

    Returns:
        The tier, or None - which means "not read" and never zero.
    """
    value = entry.get(KEY_TECH_TIER)
    if value is None:
        return None
    if isinstance(value, bool):
        _flag(log, WARN_MILESTONE_TIER_UNREADABLE)
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            _flag(log, WARN_MILESTONE_TIER_UNREADABLE)
            return None
    _flag(log, WARN_MILESTONE_TIER_UNREADABLE)
    return None


def _costs_of(
    entry: Mapping[str, object], budget: Fraction, log: dict[str, int]
) -> tuple[MilestoneCost, ...]:
    """Read one entry's costs and price each one against the budget.

    ALL OR NOTHING, AND THE BUDGET ARRIVES AS AN ARGUMENT. The blob parser
    refuses a blob it cannot account for end to end rather than returning the
    entries it recognised, so a flagged cost publishes an EMPTY tuple and never
    a partial sum. The budget is passed in rather than read here so there is
    exactly one place that reads the module constant.

    Args:
        entry: The entry mapping.
        budget: The completion budget in minutes, exactly.
        log: The warning tally.

    Returns:
        One cost per blob entry, or empty when the cost was absent or
        unreadable.
    """
    value = entry.get(KEY_COST)
    if value is None:
        return ()
    if not isinstance(value, str):
        _flag(log, WARN_MILESTONE_COST_UNREADABLE)
        return ()
    try:
        amounts = parse_item_amounts(value)
    except BlobParseError:
        _flag(log, WARN_MILESTONE_COST_UNREADABLE)
        return ()
    return tuple(
        MilestoneCost(
            item_key=amount.item_key,
            raw_path=amount.raw_path,
            amount=amount.amount,
            required_per_minute=Fraction(amount.amount) / budget,
        )
        for amount in amounts
    )


def requirements_of(
    source: SchematicSource[Mapping[str, object]], unlocks: UnlockState
) -> MilestoneRequirements:
    """Model every milestone the source carries, against one unlock state.

    Nothing here opens a save or the raw docs file: the entries arrive through
    :class:`SchematicSource` and the unlock state arrives already read.

    Args:
        source: Whatever supplies the schematic entries. ``None`` from it is a
            machine with no document and yields an empty model plus a warning.
        unlocks: The unlock state the purchased join is taken against.

    Returns:
        The requirements model, with every rate an exact Fraction.

    Raises:
        InexactValueError: If anything inexact is reachable from the model, via
            :func:`clockspeed.solve.exact.audit_exact`. That is a defect in this
            module and not a fact about the input, which is why it is the one
            thing here that refuses rather than flags.
    """
    # THE MODULE CONSTANT IS READ HERE, IN THE BODY, ON EVERY CALL. Not a
    # default argument value, which would bind at def time and freeze the
    # budget against any attempt to move it. See MILESTONE_BUDGET_MINUTES.
    budget = MILESTONE_BUDGET_MINUTES

    log: dict[str, int] = {}
    entries = source.schematics()
    if entries is None:
        _flag(log, WARN_MILESTONE_SCHEMATICS_UNAVAILABLE)
        entries = ()
    if unlocks.trading_post_level is None:
        _flag(log, WARN_MILESTONE_HUB_TIER_UNREAD)

    modelled: list[Milestone] = []
    for entry in entries:
        if not _is_milestone(entry, log):
            continue
        asset_path = _asset_path_of(entry, log)
        if asset_path is None:
            continue
        modelled.append(
            Milestone(
                class_name=asset_path.rsplit(ASSET_PATH_CLASS_SEPARATOR, 1)[-1],
                asset_path=asset_path,
                tech_tier=_tier_of(entry, log),
                schematic_type=TYPE_MILESTONE,
                purchased=asset_path in unlocks.purchased_schematics,
                costs=_costs_of(entry, budget, log),
            )
        )

    result = MilestoneRequirements(
        milestones=tuple(modelled),
        budget_minutes=budget,
        rate_basis=RATE_BASIS_FULL_CLOCK,
        hub_tier=unlocks.trading_post_level,
        warnings=_warnings_of(log),
    )
    audit_exact(result, path="requirements")
    return result
