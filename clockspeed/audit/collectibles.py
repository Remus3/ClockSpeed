"""What is still out there to collect - the uncollected model over one world.

WHAT THIS MODULE OWNS
-----------------------
One pure function over one ``clockspeed.save.world.WorldModel``, returning a
frozen :class:`WorldCollectibles`. It lives here for the reason
``clockspeed/audit/placement.py`` and ``clockspeed/audit/footprint.py`` do:
``clockspeed/surface/`` never computes (CLAUDE.md section 2.1) and ``audit/`` is
the layer that consumes a whole world model.

It reads no save, no docs file and no install. Its only input is the model.

THE POLARITY IS COLLECTED, AND IT IS THE ONE THING A CONSUMER GETS BACKWARDS
------------------------------------------------------------------------------
The save's collectable section records what has ALREADY BEEN COLLECTED, as
(level name, actor instance name) pairs. ``objects.Collectable`` states it: an
entry names an actor that is no longer in the world, and a field named for the
complement would invert every consumer downstream of it.

So UNCOLLECTED IS A SUBTRACTION AND NOT A LOOKUP. It is the live records of an
allowlisted class, carrying a transform, MINUS the actors those pairs name. A
reader that plots every collectible it finds answers a different question and
looks identical on a world where nothing has been picked up yet.

THE JOIN HAS A HOLE IN IT, AND A COUNT WOULD NOT COVER THE HOLE
------------------------------------------------------------------
Some pairs carry an EMPTY instance half. ``objects.Collectable`` publishes both
halves as ``str`` - no Optional, no flag, no count - so a consumer joining on
``instance_name`` sees ``""``, finds no live record of that name, and treats the
row as an ordinary NON-MATCH. The row is gone and nothing in the output says so.

AN OPTIONAL, A FLAG AND A COUNT ARE EACH INDIVIDUALLY INSUFFICIENT, because each
is ignorable: a consumer that does not read the flag is exactly the consumer the
flag was for. What this module publishes instead is a PARTITION WITH
CONSERVATION. Every collectable row lands in exactly one bucket of
:class:`CollectedPartition` - joinable or unjoinable - and the type REFUSES TO
EXIST unless the two buckets account for every declared row. A dropped row is
not merely detectable here; it is not a value this layer can construct. The same
shape covers the records, in :class:`RecordCensus`.

tests/audit/test_collectibles.py::test_a_partition_that_drops_a_row_cannot_be_constructed
is where that refusal is measured, and
tests/audit/test_collectibles.py::test_every_collectable_row_lands_in_exactly_one_bucket
is where the conservation is asserted over a real result.

AND AN EMPTY HALF SUBTRACTS NOTHING. A live record may itself carry an empty
instance name. If the key set were built from every pair's second string, ``""``
would be in it, and that record would be joined and deleted from the world by a
pair that names nothing. An unjoinable pair therefore contributes NO KEY at all -
tests/audit/test_collectibles.py::test_an_empty_instance_half_subtracts_no_record
is the arm whose fixture nothing else in the module refuses.

EMPTY MEANS "SAW NONE", NEVER "HAS NONE"
------------------------------------------
``objects.parse_object_headers`` reads the FLAT single-table shape and walks no
collectable block at all, so it returns an empty collectable list on a world
whose every collectible has been picked up. Reporting that as a measured zero is
the silently-wrong half of non-negotiable 7 wearing an empty tuple.

:attr:`WorldCollectibles.collected_state_available` is therefore driven by
READER PROVENANCE and not by the length of the list.
``ObjectTable.level_count`` is the discriminator: ``parse_body`` returns one per
level plus the persistent one, so it is always at least one there, and the flat
reader leaves the field at its zero DEFAULT. The default is what makes the safe
direction the automatic one - a table built without saying how it was read reads
as unavailable rather than as measured.

THE CLASS FILTER IS AN ALLOWLIST AND NEVER A DENYLIST
-------------------------------------------------------
:data:`COLLECTIBLE_CLASS_ALLOWLIST` is a closed frozenset of class names that MAY
be served. A denylist over class names is a claim about every name that does not
exist yet, and this project has measured one defect wearing four different
spellings across four green commits before an allowlist of good values held it.

NO SPELLING HERE WAS INVENTED FROM MEMORY. Every name below was read out of a
read-only census of the pinned development world's own actor classes, reported as
class names and counts - the same measurement path that grew ``placement.py``'s
list and ``footprint.py``'s. A class name is publisher content
(``clockspeed/save/usmap.py``: a class path comes from the asset registry and is
not personal data). NO COUNT FROM THAT CENSUS IS WRITTEN HERE: the operator plays
this world and a figure transcribed into a tracked file is a lie with a timestamp
on it (CLAUDE.md section 4).

THE RESOURCE NODE CLASSES ARE DELIBERATELY ABSENT, and that is not an oversight.
``clockspeed/save/world.py`` ``NODE_CLASS_NAMES`` already serves them as NODES,
through ``WorldModel.nodes`` and the placement view. Serving them here as well
would publish one actor twice under two meanings, and a reader counting "things
left to collect" would find the world's every deposit in the total. The two sets
are asserted disjoint by
tests/audit/test_collectibles.py::test_the_allowlist_shares_no_class_with_the_resource_node_population,
so the day somebody adds a name to either list the overlap is caught rather than
shipped.

WHAT IS SKIPPED IS COUNTED PER CLASS, NOT POOLED
---------------------------------------------------
:attr:`WorldCollectibles.skipped_counts` names every class this view did not
serve and how many records carried it. A single pooled total is met by its
strongest member while the weakest goes unmeasured, so the per-class mapping is
the published form and the total is derived from it.

WHAT NEVER LEAVES THIS MODULE
-------------------------------
An instance name, a level name, a record index, a byte offset, a filesystem path,
a world token and a float. The class name, the coordinates and the orientation
are the whole output, on the terms ``placement.py`` states at length: an instance
name is a census of the operator's own factory and is withheld, and a coordinate
leaves as an exact decimal string because the wire forbids a JSON float and a
rounding done here cannot be undone by a consumer.

THE JOIN KEYS ARE INSTANCE NAMES AND THEY STAY IN THIS FRAME. They are read off
the model, used to decide a membership, and never placed on the returned value -
which is why the partition publishes counts while the subtraction itself is
exact.
"""

# SEAM DISCIPLINE (BOOTSTRAP.md section 6).
# This module consumes ONE `clockspeed.save.world.WorldModel` and computes. It
# never opens a save and never reads the raw docs file. `model.objects` is the
# stated model `clockspeed/save/world.py` publishes, and reading its
# `collectables` attribute is the same idiom `placement.py` and `footprint.py`
# already use for `records` - not a reach past a neighbour.
#
# The four helpers it takes from `clockspeed.audit.placement` are SIBLINGS IN
# THIS LAYER: `Placement`, `class_name_of_path`, `decimal_string` and
# `COORDINATE_UNITS` are this layer's own stated renderings, and importing them
# is what keeps this view and the placement view from matching classes by two
# different rules or rendering one coordinate two ways.

from __future__ import annotations

import math
from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING, Final

from clockspeed.audit.placement import (
    COORDINATE_UNITS,
    Placement,
    class_name_of_path,
    decimal_string,
)
from clockspeed.save.world import WorldWarning

if TYPE_CHECKING:
    from collections.abc import Mapping

    from clockspeed.save.objects import Collectable, Transform
    from clockspeed.save.world import WorldModel

__all__ = [
    "COLLECTIBLE_CLASS_ALLOWLIST",
    "COORDINATE_UNITS",
    "SOURCE_COLLECTIBLES",
    "WARN_COLLECTED_ENTRY_UNJOINABLE",
    "WARN_COLLECTED_STATE_UNAVAILABLE",
    "WARN_COLLECTIBLE_CLASS_NOT_SERVED",
    "WARN_COLLECTIBLE_COORDINATE_NON_FINITE",
    "WARN_COLLECTIBLE_NONE_SERVED",
    "WARN_COLLECTIBLE_TRANSFORM_ABSENT",
    "CollectedPartition",
    "ConservationError",
    "RecordCensus",
    "WorldCollectibles",
    "collectibles_of",
]

#: Which layer noticed a warning raised here.
SOURCE_COLLECTIBLES: Final = "collectibles"

#: The collectable list was empty because the READER never looked, not because
#: the world holds nothing collected. See the module docstring.
WARN_COLLECTED_STATE_UNAVAILABLE: Final = "collected-state-unavailable"

#: How many collected pairs carried an empty instance half and so could join
#: nothing. Published beside the partition rather than instead of it.
WARN_COLLECTED_ENTRY_UNJOINABLE: Final = "collected-entry-unjoinable"

#: How many records this view did not serve because their class is off the
#: allowlist. The per-class breakdown is on the model.
WARN_COLLECTIBLE_CLASS_NOT_SERVED: Final = "collectible-class-not-served"

#: An allowlisted record carried no transform, so it was counted rather than
#: placed at invented coordinates.
WARN_COLLECTIBLE_TRANSFORM_ABSENT: Final = "collectible-transform-absent"

#: An allowlisted record carried a non-finite coordinate. Refused on exactly the
#: terms ``placement.py`` refuses one - a position no consumer can parse.
WARN_COLLECTIBLE_COORDINATE_NON_FINITE: Final = "collectible-coordinate-non-finite"

#: Nothing was served. Raised so an empty list is never mistaken for a world
#: that genuinely holds no uncollected item (non-negotiable 7).
WARN_COLLECTIBLE_NONE_SERVED: Final = "collectible-none-served"

#: The classes this view MAY serve. See the module docstring for why this is an
#: allowlist, where the spellings were measured, and why the resource-node
#: classes are deliberately not among them.
COLLECTIBLE_CLASS_ALLOWLIST: Final = frozenset(
    {
        # The crystals - the power slug line, all three marks.
        "BP_Crystal_C",
        "BP_Crystal_mk2_C",
        "BP_Crystal_mk3_C",
        # The alien artifacts and the shrine that holds one.
        "BP_MercerShrine_C",
        "BP_WAT1_C",
        "BP_WAT2_C",
        # Drop pods and crash-site debris - one-shot pickups with a cost.
        "BP_DropPod_C",
        "BP_CrashSiteDebris_C",
        # Flora, which is what the early collectable stems are.
        "BP_BerryBush_C",
        "BP_NutBush_C",
        "BP_Shroom_01_C",
        # The spawnable pickups, under both spellings the census carried.
        "BP_ItemPickup_Spawnable_C",
        "FGItemPickup_Spawnable",
    }
)

#: One fixed line per warning code raised here. Keyed rather than formatted, so
#: a detail can never be built from something read out of a save - the idiom
#: ``clockspeed/save/world.py`` established for the same reason.
_WARNING_DETAIL: Final[Mapping[str, str]] = MappingProxyType(
    {
        WARN_COLLECTED_STATE_UNAVAILABLE: (
            "this world was read by the flat object-header walk, which reads no collectable"
            " block at all, so nothing is known about what has been collected; every row"
            " served here is 'not known to be collected' rather than 'known uncollected'"
        ),
        WARN_COLLECTED_ENTRY_UNJOINABLE: (
            "a collected entry carried an empty instance half, so it names no actor and"
            " joins nothing; it is counted here rather than allowed to look like an"
            " ordinary non-match, and it contributes no key to the subtraction"
        ),
        WARN_COLLECTIBLE_CLASS_NOT_SERVED: (
            "records were skipped because their class is not one this view models as a"
            " collectible; the per-class breakdown says which, so a class that should be"
            " served is visible rather than silently absent"
        ),
        WARN_COLLECTIBLE_TRANSFORM_ABSENT: (
            "a record of an allowlisted class carried no transform, so it was counted"
            " rather than placed at invented coordinates; the uncollected list is short"
            " by this many"
        ),
        WARN_COLLECTIBLE_COORDINATE_NON_FINITE: (
            "a record carried a non-finite coordinate, so it was refused rather than"
            " published as a position no consumer can parse"
        ),
        WARN_COLLECTIBLE_NONE_SERVED: (
            "no uncollected item was served, which is indistinguishable from a world that"
            " holds none unless this says which; read the census and the partition beside"
            " it to tell an empty world from an unread one"
        ),
    }
)


class ConservationError(Exception):
    """A partition was asked to exist without accounting for every row.

    NOT A DATA CONDITION AND NOT A SAVE FORMAT COMPLAINT. Every value this
    module classifies reaches exactly one bucket by construction, so this can
    only be raised by a caller that built a partition by hand out of numbers
    that do not add up. It exists so that a DROPPED ROW IS INEXPRESSIBLE rather
    than merely detectable: an Optional, a flag and a count are each ignorable,
    and a type that refuses to hold the wrong answer is not.

    It carries no value read out of a save - only the counts a caller supplied -
    so it is safe on every echo path under non-negotiable 12.
    """


@dataclass(frozen=True)
class CollectedPartition:
    """Every collected pair, in exactly one bucket.

    THE TWO BUCKETS ARE EXHAUSTIVE AND DISJOINT OVER THE DECLARED ROWS, and
    ``__post_init__`` is what makes that a property of the TYPE rather than a
    promise in a docstring.

    Attributes:
        joinable: Pairs whose instance half is a usable join key. These are the
            keys the subtraction ran against.
        unjoinable: Pairs whose instance half is the empty string. They name no
            actor, they contribute NO KEY, and they are the rows a consumer
            joining on ``instance_name`` would have dropped in silence.
        declared: How many pairs the reader declared - ``len(collectables)``.

    Raises:
        ConservationError: The buckets do not account for every declared row.
    """

    joinable: int
    unjoinable: int
    declared: int

    def __post_init__(self) -> None:
        """Refuse a partition that loses a row.

        Raises:
            ConservationError: The two buckets do not sum to ``declared``.
        """
        if self.joinable + self.unjoinable != self.declared:
            raise ConservationError(SOURCE_COLLECTIBLES)

    @property
    def total(self) -> int:
        """The two buckets summed.

        Returns:
            The count, which conservation makes equal to ``declared``.
        """
        return self.joinable + self.unjoinable


@dataclass(frozen=True)
class RecordCensus:
    """Every record the walk carried, in exactly one bucket.

    THE SAME CONSERVATION THE COLLECTED PARTITION KEEPS, one layer over. A view
    that published only its served rows could lose a record to any of the four
    other outcomes and look exactly like a world that never had it.

    Attributes:
        served: Records published as uncollected.
        collected: Records the subtraction removed - an allowlisted record whose
            instance name a joinable pair named.
        skipped: Records whose class is off :data:`COLLECTIBLE_CLASS_ALLOWLIST`.
            Every component and every subsystem lands here too, which is why the
            number is large in a real world and why the per-class breakdown on
            the model is the readable form.
        transform_absent: Allowlisted records carrying no transform.
        coordinate_non_finite: Allowlisted records whose transform carried a
            coordinate that is not finite.
        declared: How many records the walk returned.

    Raises:
        ConservationError: The buckets do not account for every declared record.
    """

    served: int
    collected: int
    skipped: int
    transform_absent: int
    coordinate_non_finite: int
    declared: int

    def __post_init__(self) -> None:
        """Refuse a census that loses a record.

        Raises:
            ConservationError: The five buckets do not sum to ``declared``.
        """
        if self.total != self.declared:
            raise ConservationError(SOURCE_COLLECTIBLES)

    @property
    def total(self) -> int:
        """The five buckets summed.

        Returns:
            The count, which conservation makes equal to ``declared``.
        """
        return (
            self.served
            + self.collected
            + self.skipped
            + self.transform_absent
            + self.coordinate_non_finite
        )


@dataclass(frozen=True, repr=False)
class WorldCollectibles:
    """What is still out there to collect in one world, and what was accounted for.

    ``repr`` renders counts and flags only, on the terms every published type in
    ``clockspeed/save/world.py`` and ``clockspeed/audit/placement.py`` states.

    Attributes:
        uncollected: One row per live, allowlisted, finitely placed record the
            subtraction did NOT remove, in record order. NAMED FOR WHAT IT
            HOLDS: a field named for the complement would invert every consumer.
        uncollected_counts: How many uncollected rows of each class, keyed by
            class name and iterating in sorted order so two runs agree.
        skipped_counts: How many records of each NON-served class, on the same
            terms. Per class rather than pooled - see the module docstring.
        collected_partition: Every collected pair, bucketed and conserved.
        records: Every record, bucketed and conserved.
        collected_state_available: Whether the reader that produced this world
            looked at the collectable blocks at all. FALSE means nothing is
            known about what has been collected, NOT that nothing has been.
        coordinate_units: :data:`COORDINATE_UNITS`, carried on the model so a
            consumer never has to import a constant to read a number.
        warnings: Everything flagged, in the ``WorldWarning`` idiom.
    """

    uncollected: tuple[Placement, ...]
    uncollected_counts: Mapping[str, int]
    skipped_counts: Mapping[str, int]
    collected_partition: CollectedPartition
    records: RecordCensus
    collected_state_available: bool
    coordinate_units: str
    warnings: tuple[WorldWarning, ...]

    @property
    def skipped_total(self) -> int:
        """How many records were skipped across every non-served class.

        Derived from the per-class mapping rather than carried beside it, so the
        total and the breakdown cannot disagree.

        Returns:
            The count.
        """
        return sum(self.skipped_counts.values())

    def __repr__(self) -> str:
        """Render counts and flags, and nothing about any member.

        A NESTED FIELD IS DELEGATED, NEVER REACHED INTO. Rendering
        ``self.collected_partition.declared`` would make this repr raise on any
        instance whose partition is not the declared type - and an instance in
        that state is exactly what a test runner reprs while it explains why a
        construction went wrong. ``tests/test_assertion_rendering.py`` builds
        every redacting class in this tree with stand-ins in the fields its arm
        is not about, and measured this repr raising on one. Both sub-models
        carry integers only, so delegating to their own reprs is safe as well as
        total.

        Returns:
            The safe rendering.
        """
        return (
            f"{type(self).__name__}(uncollected={len(self.uncollected)}, "
            f"uncollected_classes={len(self.uncollected_counts)}, "
            f"skipped={self.skipped_total}, "
            f"skipped_classes={len(self.skipped_counts)}, "
            f"collected={self.collected_partition!r}, "
            f"records={self.records!r}, "
            f"collected_state_available={self.collected_state_available}, "
            f"warnings={len(self.warnings)})"
        )


def _warning(code: str, count: int = 1) -> WorldWarning:
    """Build one warning from this module's own fixed detail table.

    Args:
        code: One of this module's ``WARN_*`` constants.
        count: How many occurrences it aggregates.

    Returns:
        The warning.
    """
    return WorldWarning(
        source=SOURCE_COLLECTIBLES,
        code=code,
        detail=_WARNING_DETAIL[code],
        count=count,
    )


def _sorted_counts(tally: Mapping[str, int]) -> Mapping[str, int]:
    """Freeze a tally into a deterministic read-only mapping.

    Sorted rather than insertion ordered, so two runs over one model produce
    mappings that iterate identically as well as compare equal.

    Args:
        tally: The raw counts.

    Returns:
        A read-only mapping from class name to count.
    """
    return MappingProxyType(dict(sorted(tally.items())))


def _partition_collected(pairs: tuple[Collectable, ...]) -> tuple[CollectedPartition, set[str]]:
    """Bucket every collected pair and return the keys the subtraction may use.

    AN UNJOINABLE PAIR CONTRIBUTES NO KEY. Its instance half is the empty
    string, and a live record may carry an empty instance name of its own - so a
    key set built from every second string would join those two and delete a row
    the body declares. See the module docstring.

    Args:
        pairs: Every collectable entry the reader carried, in file order.

    Returns:
        The conserved partition, and the join keys.
    """
    keys = {pair.instance_name for pair in pairs if pair.instance_name}
    unjoinable = sum(1 for pair in pairs if not pair.instance_name)
    return (
        CollectedPartition(
            joinable=len(pairs) - unjoinable,
            unjoinable=unjoinable,
            declared=len(pairs),
        ),
        keys,
    )


def _placement_or_none(class_name: str, transform: Transform) -> Placement | None:
    """Render one allowlisted record's transform, or refuse a non-finite coordinate.

    THE ORIENTATION RULE IS ``placement.py``'S AND IS NOT RE-ARGUED HERE. A
    non-finite COORDINATE refuses the row, because a position no consumer can
    parse is not a row; a non-finite ROTATION or SCALE withholds that block WHOLE
    and keeps the row, because a partial quaternion normalises into garbage while
    the coordinates beside it are still exactly what the save stored.

    Args:
        class_name: The already-reduced class name.
        transform: The record's transform. The caller's branch has already
            established that it is not None.

    Returns:
        The placement, or None when any coordinate is not finite.
    """
    x, y, z = (float(axis) for axis in transform.translation)
    if not (math.isfinite(x) and math.isfinite(y) and math.isfinite(z)):
        return None
    qa, qb, qc, qd = (float(part) for part in transform.rotation)
    sa, sb, sc = (float(part) for part in transform.scale)
    rotation = (
        (decimal_string(qa), decimal_string(qb), decimal_string(qc), decimal_string(qd))
        if all(math.isfinite(part) for part in (qa, qb, qc, qd))
        else None
    )
    scale = (
        (decimal_string(sa), decimal_string(sb), decimal_string(sc))
        if all(math.isfinite(part) for part in (sa, sb, sc))
        else None
    )
    return Placement(
        class_name=class_name,
        x=decimal_string(x),
        y=decimal_string(y),
        z=decimal_string(z),
        rotation=rotation,
        scale=scale,
    )


def _warnings_for(counted: tuple[tuple[str, int], ...]) -> list[WorldWarning]:
    """Raise one warning per code that actually has occurrences behind it.

    ORDER IS THE CALLER'S AND ZERO IS A SILENCE, on the terms
    ``clockspeed/audit/placement.py`` states: a warning saying "this happened
    zero times" is noise a consumer has to filter and is indistinguishable, at a
    glance, from one that happened.

    Args:
        counted: One ``(code, count)`` pair per advisory driven by a tally, in
            publication order.

    Returns:
        The warnings, in that order, for the codes with a non-zero count.
    """
    return [_warning(code, count) for code, count in counted if count]


def collectibles_of(model: WorldModel) -> WorldCollectibles:
    """Compute what is still out there to collect in one world.

    PURE, AND TOTAL over every world model. An empty world, a world read by the
    flat walk and a world whose every collectible was refused all return a valid
    :class:`WorldCollectibles` carrying the flags that say so. The only exception
    this path can raise is :class:`ConservationError`, which is a statement about
    this module's own arithmetic and never about the save.

    Args:
        model: The world to describe. Read only; nothing here mutates it and
            nothing here reads a save.

    Returns:
        The uncollected model.
    """
    table = model.objects
    partition, keys = _partition_collected(table.collectables)
    # READER PROVENANCE, NOT LIST LENGTH. `parse_body` returns one level per
    # level plus the persistent one; the flat walk leaves the DEFAULT zero.
    available = table.level_count > 0
    if not available:
        keys = set()

    uncollected: list[Placement] = []
    skipped: dict[str, int] = {}
    subtracted = 0
    transform_absent = 0
    non_finite = 0

    for record in table.records:
        class_name = class_name_of_path(record.type_path)
        if class_name not in COLLECTIBLE_CLASS_ALLOWLIST:
            skipped[class_name] = skipped.get(class_name, 0) + 1
            continue
        transform = record.transform
        if transform is None:
            transform_absent += 1
            continue
        placed = _placement_or_none(class_name, transform)
        if placed is None:
            non_finite += 1
            continue
        if record.instance_name in keys:
            subtracted += 1
            continue
        uncollected.append(placed)

    census = RecordCensus(
        served=len(uncollected),
        collected=subtracted,
        skipped=sum(skipped.values()),
        transform_absent=transform_absent,
        coordinate_non_finite=non_finite,
        declared=len(table.records),
    )

    warnings = _warnings_for(
        (
            (WARN_COLLECTED_ENTRY_UNJOINABLE, partition.unjoinable),
            (WARN_COLLECTIBLE_CLASS_NOT_SERVED, census.skipped),
            (WARN_COLLECTIBLE_TRANSFORM_ABSENT, transform_absent),
            (WARN_COLLECTIBLE_COORDINATE_NON_FINITE, non_finite),
        )
    )
    # NEITHER OF THESE IS DRIVEN BY A TALLY. Each fires on a STATE - one on how
    # the world was read, one on the absence of any served row - and folding
    # them into the list above would mean inventing a count that means nothing.
    if not available:
        warnings.insert(0, _warning(WARN_COLLECTED_STATE_UNAVAILABLE))
    if not uncollected:
        warnings.append(_warning(WARN_COLLECTIBLE_NONE_SERVED))

    tally: dict[str, int] = {}
    for placement in uncollected:
        tally[placement.class_name] = tally.get(placement.class_name, 0) + 1

    return WorldCollectibles(
        uncollected=tuple(uncollected),
        uncollected_counts=_sorted_counts(tally),
        skipped_counts=_sorted_counts(skipped),
        collected_partition=partition,
        records=census,
        collected_state_available=available,
        coordinate_units=COORDINATE_UNITS,
        warnings=tuple(warnings),
    )
