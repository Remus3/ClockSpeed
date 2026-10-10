"""What each built machine is doing - its recipe, its producing flag, its clock.

WHAT THIS MODULE OWNS
-----------------------
One pure function over one ``clockspeed.save.world.WorldModel``, returning a
frozen :class:`WorldMachines`: one entry per walked record that carries any
measured machine property. It is the COMPUTATION half of "is this machine
running and on what", and it lives here because ``clockspeed/surface/`` never
computes and ``audit/`` is the layer that consumes a whole world model.

It reads no save, no docs file and no install. Its only input is the model.

AN ABSENT VALUE IS NULL AND IS NEVER THE GAME'S DEFAULT
---------------------------------------------------------
This is the whole of CS-1041's second acceptance clause and it is not a style
choice. The game's default clock IS 1, so a reader that substitutes 1 for an
absent ``mCurrentPotential`` produces an answer indistinguishable from the right
one on every machine nobody has overclocked, and wrong on exactly the machines
where the number matters. Non-negotiable 7 names that shape: unknown content is
flagged and skipped, never silently wrong.

The same collapse wears a bool. ``mIsProducing`` absent is NOT ``False``: false
means "measured, and it is not producing" and absent means "this reader saw no
such tag", which is the difference between an idle machine and an unread one.
Every field on :class:`MachineState` is therefore three-state, and the model
carries a per-field availability flag so a consumer can ask which case a whole
world is in without walking the population.

WHAT THE PREMISE ACTUALLY WAS, AND WHAT IT ACTUALLY IS
--------------------------------------------------------
CS-1041's item line says ``mCurrentRecipe`` is "decoded and then dropped". That
is overstated: the per-name value has reached ``RecordProperties.values`` for as
long as that mapping has existed. What was genuinely missing is the TYPED,
tag-ordered reference population, which CS-1039 landed as
``RecordProperties.references``.

This module reads the recipe from THAT population and not from ``values``, and
the difference is a measured defect rather than a preference.
``clockspeed/save/objects.py`` ``ObjectReference`` records it: a
``SoftObjectProperty`` decodes to a ``tuple[str, str]`` indistinguishable from an
``ObjectProperty``'s, so a consumer recovering references from the value map by
SHAPE silently takes both type words. The typed population is the one that knows
which word it came from.

THE RECIPE REFERENCE IS CLASSIFIED BEFORE IT IS PUBLISHED
------------------------------------------------------------
ADR 0016 measured that one reference population is entirely ASSET paths joining
the registry, and CS-1041's own join in ``clockspeed/audit/network.py`` is
entirely RECORD instance paths. Which population ``mCurrentRecipe`` is in is
UNMEASURED in this project, and the two carry different obligations: an asset
path is shipped content, byte-identical on every install, while a record
instance path is a census of the operator's own factory and is world content
under non-negotiable 12.

So the value is admitted only when it is structurally a shipped asset path -
carrying no instance separator, under a root on :data:`RECIPE_ASSET_ROOTS` - and
is REFUSED AND COUNTED otherwise. The guard fails CLOSED, which is the shape
``clockspeed/save/world.py`` ``_permitted_asset_path`` already established after
this repository measured a denylist leaking four times across four green commits.
A refusal is never silent: :data:`WARN_MACHINES_RECIPE_REFUSED` carries the count.

THE FLOAT-TO-FRACTION BRIDGE, NAMED EXPLICITLY
------------------------------------------------
``mCurrentPotential`` is a ``FloatProperty``: ``clockspeed/save/objects.py``
decodes it as four bytes under ``"<f"``, so what reaches this layer is a float32
value widened to a Python float. Non-negotiable 6 forbids a float in the solve
path, and CS-1041's filed acceptance requires no bridge at all - which is the gap
this module closes rather than inherits.

:func:`exact_from_float32` is that bridge, and the obvious conversion is the
wrong one. ``Fraction(1.2999999523162842)`` is an EXACT reading of a binary
approximation and a WRONG reading of the decimal the game wrote; being exact, it
passes every downstream exactness check unchanged. That is precisely the trap
``clockspeed/solve/exact.py`` ``to_exact`` refuses a float outright to avoid, and
refusing here instead of converting would leave the field unpublishable.

The bridge recovers the SHORTEST DECIMAL THAT ROUND-TRIPS THROUGH FLOAT32 and
hands that STRING to ``Fraction``, so 1.3 comes back as 13/10. A value no float32
holds is REFUSED rather than approximated: it did not come from a
``FloatProperty``, so guessing which decimal it meant would be an invention.
``DoubleProperty`` is a different width and would need its own bridge; this one
claims nothing about it.

WHAT IS NOT ADMITTED IS COUNTED, PER CLASS (CS-1266)
------------------------------------------------------
Membership is property-driven, so a built record carrying no machine tag - or
one whose payload never read, and so carries nothing at all - is not a machine
here. That is the right answer for a foundation and the wrong SILENCE for a
power consumer: the clocked draw in ``clockspeed/audit/balance.py`` priced the
population it was handed and could not see what was left out of it. So every
walked record that is not admitted is COUNTED by class, split by whether its
payload read: :attr:`WorldMachines.unadmitted_read_counts` and
:attr:`WorldMachines.unadmitted_unread_counts`. With the population they
partition the record table. This module never reads the registry, so it never
decides which of those classes draw power; the balance does, one layer up.

"READ" NEEDS A PAYLOAD THAT WAS READ, NOT AN ENTRY THAT SAYS SO. The property
reader hands back an entry marked read with nothing in it for a record the
object walk attributed NO payload extent to - every record of the flat walk,
and every record of a level whose record and payload counts disagree, where the
pairing is undefined and ``objects.WARN_PAYLOAD_COUNT_DISAGREEMENT`` is raised.
Nothing in ``payload_read`` or ``values`` tells it from a payload that was
read and held nothing, so the save layer publishes the FACT:
``RecordProperties.payload_present`` is False for such a record, and the tally
routes it to UNREAD. This module never reads a record's extent - an offset or a
length is a position the save layer publishes to nobody, and
``tests/audit/test_extent_seam.py::test_no_audit_module_reads_a_record_extent``
pins that over the whole package.

WHICH OF THEM READ CLEAN (CS-1280)
------------------------------------
The CS-1280 ruling prices a tagless power consumer at its class default ONLY
when its payload read clean, and this module is the one that holds the
payload. So it publishes, per class, how many READ and unadmitted records also
read CLEAN - :attr:`WorldMachines.unadmitted_clean_counts`: a payload paired
and read, no value that disagreed with its declared size, and no tag on
:data:`CLEAN_PAYLOAD_REFUSING_NAMES` among the decoded values or the dropped-tag
names. That is the clean-payload test the elided clock uses
(:attr:`MachineState.overclock_elided`), plus the pending clock tag and the
boost tags the ruling's carve-out adds. A SUBSET of
:attr:`WorldMachines.unadmitted_read_counts`, never a third bucket, so the
partition above is untouched; which of those classes draw power is still the
balance's question, one layer up.
"""

from __future__ import annotations

import math
import struct
from dataclasses import dataclass
from fractions import Fraction
from types import MappingProxyType
from typing import TYPE_CHECKING, Final

from clockspeed.audit.network import names_a_record_instance
from clockspeed.audit.placement import class_name_of_path
from clockspeed.save.world import WorldWarning

if TYPE_CHECKING:  # pragma: no cover - import-time typing only
    from collections.abc import Mapping

    from clockspeed.save.objects import ObjectReference
    from clockspeed.save.world import RecordProperties, WorldModel

__all__ = [
    "CLEAN_PAYLOAD_REFUSING_NAMES",
    "MACHINE_PROPERTY_NAMES",
    "PRODUCTION_BOOST_PROPERTY_NAMES",
    "PROPERTY_OVERCLOCK",
    "PROPERTY_PENDING_OVERCLOCK",
    "PROPERTY_PRODUCING",
    "PROPERTY_RECIPE",
    "RECIPE_ASSET_ROOTS",
    "SOURCE_MACHINES",
    "WARN_MACHINES_NONE_READ",
    "WARN_MACHINES_OVERCLOCK_REFUSED",
    "WARN_MACHINES_PAYLOAD_UNREAD",
    "WARN_MACHINES_RECIPE_REFUSED",
    "MachineState",
    "WorldMachines",
    "exact_from_float32",
    "machines_of",
]

#: Which layer noticed a warning raised here, for ``WorldWarning.source``.
SOURCE_MACHINES: Final = "machines"

#: The producing flag's tag name. A ``BoolProperty``.
PROPERTY_PRODUCING: Final = "mIsProducing"

#: The current recipe's tag name. An ``ObjectProperty``, read from the TYPED
#: reference population and never from the value map - see the module docstring.
PROPERTY_RECIPE: Final = "mCurrentRecipe"

#: The live overclock's tag name. A ``FloatProperty``.
#: ``docs/adr/0005-overclock-ceiling-source.md`` measured it at five records
#: across three worlds, and records that ``mPendingPotential`` is its sibling.
#: THE SIBLING'S VALUE IS NOT READ HERE: no acceptance clause grades it, and a
#: field nothing grades is a field nothing measures. Its PRESENCE is read, for
#: CS-1280 alone - see :data:`PROPERTY_PENDING_OVERCLOCK`.
PROPERTY_OVERCLOCK: Final = "mCurrentPotential"

#: CS-1280. The pending overclock's tag name, the sibling ADR 0005 records.
#: ONLY ITS PRESENCE IS READ, decoded or not, and only to decide whether a
#: record carrying no machine tag read clean: the session 133 CS-1280
#: measurement found tagless miner and water-pump records carrying it, and the
#: ruling keeps such a record unpriced. NOT a machine-membership tag - a record
#: admitted on it alone would be an elided clock, priced at the default by
#: CS-1263, which is the price the carve-out refuses it.
PROPERTY_PENDING_OVERCLOCK: Final = "mPendingPotential"

#: CS-1264. The production-boost tag names: the live boost and its pending
#: sibling, mirroring the clock's own pair above. THE SPELLING IS MEASURED, THE
#: WRITING IS NOT. Measured for CS-1264: both names sit on ``FGBuildableFactory``
#: in the shipped property mapping, exactly as spelled, with the same type id as
#: ``mCurrentPotential``. Whether the game ever WRITES either to a save is
#: unmeasured - no save in the library carries the string ``ProductionBoost``.
#: Only PRESENCE is read, never the value - and presence counts the dropped-tag
#: names beside the decoded values, so a boost whose value did not decode is
#: still a boost. The value's saved encoding is unmeasured, so a reading of it
#: would be invented, and a consumer told only that a boost exists can refuse to
#: price the machine, which is the one thing it may safely do. Both names are
#: read because a presence read only ever refuses, so a wider net costs
#: completeness and never correctness. NOT a machine-membership tag:
#: :data:`MACHINE_PROPERTY_NAMES` is unchanged.
PRODUCTION_BOOST_PROPERTY_NAMES: Final = frozenset(
    {"mCurrentProductionBoost", "mPendingProductionBoost"}
)

#: The closed vocabulary that decides whether a record is a MACHINE at all.
#:
#: THE POPULATION IS PROPERTY-DRIVEN AND NOT CLASS-DRIVEN, ON PURPOSE. A class
#: allowlist is a second list to keep current, and a machine of a class nobody
#: listed would be dropped in silence - which is the filter
#: ``clockspeed/audit/placement.py`` publishes a count for precisely because it
#: could not avoid one. Here it can be avoided: a record carrying a measured
#: machine tag IS a machine, whatever its class, and a modded or unmodelled
#: building is admitted on the same terms as a shipped one.
MACHINE_PROPERTY_NAMES: Final = frozenset({PROPERTY_PRODUCING, PROPERTY_RECIPE, PROPERTY_OVERCLOCK})

#: CS-1280. The tag names whose PRESENCE, decoded or not, keeps a record from
#: reading clean: both clock tags and both production-boost tags. The current
#: clock is here although it already admits a record, so the clean test states
#: the ruling whole rather than leaning on the admission rule above it.
CLEAN_PAYLOAD_REFUSING_NAMES: Final = (
    frozenset({PROPERTY_OVERCLOCK, PROPERTY_PENDING_OVERCLOCK}) | PRODUCTION_BOOST_PROPERTY_NAMES
)

#: Which asset roots a recipe reference MAY be published from. An ALLOWLIST and
#: never a denylist, on the terms ``clockspeed/save/world.py``
#: ``UNLOCK_ASSET_ROOTS`` states: this repository has measured a denylist leaking
#: four times, and only an allowlist of good values held. A ``/Game/...`` path is
#: shipped content carrying no account id, no world name and no home path.
RECIPE_ASSET_ROOTS: Final = ("/Game/",)

#: No walked record carried any measured machine property, so the population
#: below is empty. Flagged rather than reported as a measured zero: the tag names
#: are seeded from the item filing and ADR 0005 rather than from an occurrence
#: count this project has taken over a real save for all three, so an empty
#: result may mean the tags are spelled some way this reader has never seen.
WARN_MACHINES_NONE_READ: Final = "machines-none-read"

#: This many walked records had a property payload that never read, so whatever
#: machine state they hold was never available.
WARN_MACHINES_PAYLOAD_UNREAD: Final = "machines-payload-unread"

#: This many overclock values did not round-trip through float32 and were
#: refused rather than approximated.
WARN_MACHINES_OVERCLOCK_REFUSED: Final = "machines-overclock-refused"

#: This many recipe references were not structurally shipped asset paths and
#: were refused rather than published.
WARN_MACHINES_RECIPE_REFUSED: Final = "machines-recipe-refused"

#: How many significant decimal digits are ever needed to round-trip a float32.
#: IEEE 754 binary32 needs at most 9, and the search below stops at the first
#: precision that round-trips, so the shortest decimal is what gets read.
_FLOAT32_ROUND_TRIP_DIGITS: Final = 9

#: One fixed line per warning code raised here. Keyed rather than formatted, so
#: a detail can never be built from something read out of a save - the idiom
#: ``clockspeed/save/world.py`` established for the same reason.
_WARNING_DETAIL: Final[Mapping[str, str]] = MappingProxyType(
    {
        WARN_MACHINES_NONE_READ: (
            "no walked record carried any measured machine property, which is not the same"
            " fact as a world with no machines in it; the three tag names this reader knows"
            " are seeded from the item filing and from ADR 0005 rather than from an"
            " occurrence count taken over a real save for all three"
        ),
        WARN_MACHINES_PAYLOAD_UNREAD: (
            "this many walked records had a property payload that never read, so whatever"
            " machine state they hold was never available; the population below is short by"
            " whatever those records carry"
        ),
        WARN_MACHINES_OVERCLOCK_REFUSED: (
            "this many overclock values did not round-trip through float32 and were refused"
            " rather than approximated; a value that did not come from a FloatProperty has"
            " no authored decimal to recover, and inventing one would be exact and wrong"
        ),
        WARN_MACHINES_RECIPE_REFUSED: (
            "this many recipe references were not structurally shipped asset paths and were"
            " refused rather than published; a reference naming a record instance is a"
            " census of the operator's own factory and never crosses this seam"
        ),
    }
)


def exact_from_float32(value: object) -> Fraction | None:
    """One stored float32 as the exact decimal it was authored from, or None.

    NEVER ``Fraction(value)``. That reads the binary approximation exactly and
    the decimal wrongly, and being exact it is invisible to every downstream
    exactness check - see the module docstring for why that is the trap rather
    than the shortcut.

    FOUR REFUSALS, EACH INDEPENDENT. A non-``float`` is refused by TYPE IDENTITY,
    so a ``bool`` is refused rather than admitted by way of ``int``. A non-finite
    value is refused, because no decimal names it. A value too large to pack as
    float32 is refused. And a value that no float32 holds is refused rather than
    rounded to the nearest one that does: it did not come from a
    ``FloatProperty``, and choosing a decimal for it would be an invention.

    Args:
        value: The decoded property value, of any shape.

    Returns:
        The exact value, or None when this reader will not claim one.
    """
    if type(value) is not float:
        return None
    if not math.isfinite(value):
        return None
    for digits in range(1, _FLOAT32_ROUND_TRIP_DIGITS + 1):
        text = f"{value:.{digits}g}"
        try:
            narrowed = struct.unpack("<f", struct.pack("<f", float(text)))[0]
        except (OverflowError, ValueError):
            return None
        if narrowed == value:
            return Fraction(text)
    return None


def _permitted_recipe_path(path: str) -> str | None:
    """One recipe reference value, admitted only if it is a shipped asset path.

    TWO REFUSALS, AND THE ORDER DOES NOT MATTER BECAUSE EACH IS INDEPENDENT. A
    path naming a record instance is refused, because that is world content. A
    path under no permitted root is refused, because the list is of what MAY
    cross rather than of what may not.

    Args:
        path: The object path half of the decoded reference.

    Returns:
        The path when it may be published, and None otherwise.
    """
    if names_a_record_instance(path):
        return None
    if not any(path.startswith(root) for root in RECIPE_ASSET_ROOTS):
        return None
    return path


@dataclass(frozen=True)
class MachineState:
    """One machine's state: what it is, what it makes, whether it is running.

    NO INSTANCE NAME, NO INDEX, NO OFFSET, NO PATH - the position of this entry
    in :attr:`WorldMachines.machines` is its key, on the terms
    ``clockspeed/audit/placement.py`` ``Placement`` states.

    EVERY FIELD IS THREE-STATE AND NONE COLLAPSES TO A DEFAULT. None means this
    reader saw no such tag; it never means the game's default, and it never
    means zero, false or one.

    Attributes:
        class_name: The record's actor class, reduced from its type path by
            ``clockspeed.audit.placement.class_name_of_path``. Publisher content.
        producing: The decoded ``mIsProducing``, or None when the tag was absent
            or decoded as something other than a ``bool``. FALSE IS NOT ABSENT -
            see the module docstring. Admitted by TYPE IDENTITY, so an int 1 is
            refused rather than coerced.
        recipe_class_name: The bare class name of the recipe the record names,
            or None when the tag was absent OR when its value was refused by
            :func:`_permitted_recipe_path`. Those two are counted apart on the
            model, because a refusal is a fact and an absence is not.
        overclock: The decoded ``mCurrentPotential`` as an exact ``Fraction``, or
            None when the tag was absent OR when :func:`exact_from_float32`
            refused its value. NEVER 1 FOR AN ABSENT TAG, which is the whole of
            CS-1041's second acceptance clause -
            ``tests/audit/test_machines.py::test_an_absent_overclock_is_null_rather_than_one``.
        overclock_elided: CS-1263. True ONLY when the payload read under the
            measured grammar, no measured-type tag disagreed with its declared
            size, and no ``mCurrentPotential`` tag was present at all -
            neither decoded nor among the dropped-tag names (CS-1264: a tag
            of an unmeasured type was WRITTEN, so it was not elided) - the
            shape the save serializer writes for a value equal to the class
            default, which it elides. MEASURED, not assumed: over the save
            library for CS-1263, no present tag carried exactly one while most
            machines carried no tag at all.
            False for a refused value, an unread payload, a disagreeing tag, a
            present tag, and by default for a hand-built state, so a consumer
            that has not been told the tag was elided never assumes it. The
            :attr:`overclock` field stays None either way - this flag says WHY.
        production_boost_tagged: CS-1264. True when the payload carried any
            tag on :data:`PRODUCTION_BOOST_PROPERTY_NAMES`, WHATEVER ITS VALUE
            and whether that value decoded: the name is looked for in
            ``RecordProperties.values`` AND ``RecordProperties.undecoded_names``,
            so a torn or unmeasured boost tag counts, and so does one beside a
            disagreeing neighbour. The value is not published - see that
            constant for why. False when no such tag was seen, and by default
            for a hand-built state. Independent of :attr:`overclock_elided`: a
            boosted machine's clock may well be at the class default, and the
            boost is what makes that default the wrong price.
    """

    class_name: str
    producing: bool | None
    recipe_class_name: str | None
    overclock: Fraction | None
    overclock_elided: bool = False
    production_boost_tagged: bool = False


@dataclass(frozen=True, repr=False)
class WorldMachines:
    """Every machine's state, the per-field availability, and the denominators.

    ``repr`` renders counts and flags only, for the reason
    ``clockspeed/audit/inventory.py`` ``WorldInventory`` gives.

    Attributes:
        machines: One entry per walked record carrying any measured machine
            property, in RECORD INDEX order.
        producing_available: Whether at least one entry carries a producing
            flag. A FIELD rather than a derivation a consumer must do by walking
            the population - the idiom
            ``clockspeed/audit/placement.py`` ``WorldPlacement.node_semantics_available``
            established. False over a non-empty population means the tag was
            never seen, which is a fact about this reader.
        recipe_available: The same question for the recipe.
        overclock_available: The same question for the overclock.
        records_considered: How many walked records had an entry in
            ``WorldModel.properties``. The denominator the machine count is a
            fraction of.
        unread_payload_count: How many of those records' payloads never read,
            carried verbatim from ``WorldProperties.unread_payload_count`` - the
            honest denominator its own docstring names.
        refused_overclock_count: How many overclock values were refused by
            :func:`exact_from_float32`. Counted rather than dropped: a refusal is
            not an absence.
        refused_recipe_count: How many recipe references were refused by
            :func:`_permitted_recipe_path`, on identical terms.
        warnings: Everything flagged, in the ``WorldWarning`` idiom.
        unadmitted_read_counts: CS-1266. Per class, how many records READ
            cleanly enough to be walked and carried no machine tag, so were not
            admitted - ``(class name, count)`` pairs in class order, the class
            reduced exactly as :attr:`MachineState.class_name` is. PAIRS AND NOT
            A MAPPING PROXY, because a proxy cannot be deep-copied and a caller
            that snapshots this model to prove nothing mutated it must be able
            to. Empty by default, for a hand-built model with no record table
            behind it.
        unadmitted_unread_counts: CS-1266. Per class, how many records were
            not admitted because no payload of theirs was read - the walk
            aborted on it, the object walk paired it with no payload
            (``RecordProperties.payload_present`` False), or no property pass
            reached the record at all. Nothing was read to
            admit such a record on, so this is a fact about this reader and
            never about the record. With :attr:`machines` and the field above
            it partitions the record table.
        unadmitted_clean_counts: CS-1280. Per class, how many of the records
            counted in :attr:`unadmitted_read_counts` also read CLEAN - see
            :func:`_reads_clean` - in the same pair shape and class order. A
            SUBSET of that census and never a third bucket: no class carries
            more here than there. Empty by default, so a hand-built model
            claims no clean record and a consumer prices none.
    """

    machines: tuple[MachineState, ...]
    producing_available: bool
    recipe_available: bool
    overclock_available: bool
    records_considered: int
    unread_payload_count: int
    refused_overclock_count: int
    refused_recipe_count: int
    warnings: tuple[WorldWarning, ...]
    # Appended with defaults, so every existing construction stays valid.
    unadmitted_read_counts: tuple[tuple[str, int], ...] = ()
    unadmitted_unread_counts: tuple[tuple[str, int], ...] = ()
    unadmitted_clean_counts: tuple[tuple[str, int], ...] = ()

    def __repr__(self) -> str:
        """Render counts and flags, and none that a member could make raise.

        Returns:
            The safe rendering.
        """
        return (
            f"{type(self).__name__}(machines={len(self.machines)}, "
            f"producing_available={self.producing_available}, "
            f"recipe_available={self.recipe_available}, "
            f"overclock_available={self.overclock_available}, "
            f"records_considered={self.records_considered}, "
            f"unread_payload_count={self.unread_payload_count}, "
            f"refused_overclock_count={self.refused_overclock_count}, "
            f"refused_recipe_count={self.refused_recipe_count}, "
            f"unadmitted_read={sum(count for _, count in self.unadmitted_read_counts)}, "
            f"unadmitted_unread={sum(count for _, count in self.unadmitted_unread_counts)}, "
            f"unadmitted_clean={sum(count for _, count in self.unadmitted_clean_counts)}, "
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
        source=SOURCE_MACHINES,
        code=code,
        detail=_WARNING_DETAIL[code],
        count=count,
    )


def _recipe_tag(references: tuple[ObjectReference, ...]) -> ObjectReference | None:
    """The FIRST reference tag named for the current recipe, or None.

    FIRST rather than only, and the population is a tuple rather than a mapping
    precisely because two tags may share a name -
    ``clockspeed/save/world.py`` ``RecordProperties.references`` says so. A
    record carrying two recipe tags is not a shape this project has measured, so
    this takes the one the payload wrote first rather than inventing a rule for
    resolving them.

    Args:
        references: The record's typed, tag-ordered references.

    Returns:
        The tag, or None when the record carries none by that name.
    """
    for reference in references:
        if reference.property_name == PROPERTY_RECIPE:
            return reference
    return None


def _is_machine(entry: RecordProperties) -> bool:
    """Whether one record carries any measured machine property.

    A TAG IS PRESENT WHETHER OR NOT ITS VALUE DECODED - CS-1264. The
    dropped-tag names are read beside the values: a record whose every machine
    tag was torn or of an unmeasured type is still a machine, and dropping it
    here would take it out of every count below without a trace - the draw
    would price its neighbours and call itself complete.

    Args:
        entry: The record's published properties.

    Returns:
        True when a measured tag appears in any of the three populations.
    """
    if not MACHINE_PROPERTY_NAMES.isdisjoint(entry.values):
        return True
    if not MACHINE_PROPERTY_NAMES.isdisjoint(entry.undecoded_names):
        return True
    return _recipe_tag(entry.references) is not None


def _counted(tally: dict[str, int]) -> tuple[tuple[str, int], ...]:
    """Freeze one per-class tally in class order, so two runs agree.

    Args:
        tally: Class name to count.

    Returns:
        ``(class name, count)`` pairs.
    """
    return tuple(sorted(tally.items()))


def _payload_was_read(entry: RecordProperties) -> bool:
    """Whether a payload of this record was actually read, as opposed to reported read.

    CS-1266. ``RecordProperties.payload_read`` is True for a record the object
    walk paired with NO payload - the reader returns an empty, read entry
    without reading a byte - so it cannot by itself support the claim "read and
    carried no machine tag". ``RecordProperties.payload_present`` can: the save
    layer publishes it from the extent it alone reads.

    Args:
        entry: The record's published properties.

    Returns:
        True only when a payload was paired with the record AND it read.
    """
    return entry.payload_present and entry.payload_read


def _reads_clean(entry: RecordProperties) -> bool:
    """Whether a read payload is clean enough to price its record at the default (CS-1280).

    THE CLEAN-PAYLOAD TEST THE ELIDED CLOCK USES, PLUS THE CARVE-OUT. A payload
    paired and read (:func:`_payload_was_read`), no value that disagreed with
    its declared size - such a tag may have been the clock itself - and no tag
    on :data:`CLEAN_PAYLOAD_REFUSING_NAMES` among the values or the dropped-tag
    names, because a tag whose value never decoded was still written.

    Args:
        entry: The record's published properties.

    Returns:
        True only when every clause holds.
    """
    return (
        _payload_was_read(entry)
        and not entry.disagreeing_value_count
        and CLEAN_PAYLOAD_REFUSING_NAMES.isdisjoint(entry.values)
        and CLEAN_PAYLOAD_REFUSING_NAMES.isdisjoint(entry.undecoded_names)
    )


def _count_never_walked(model: WorldModel, tally: dict[str, int]) -> None:
    """Count, as unread, every record no property pass reached (CS-1266).

    The property mapping is total over the table whenever a pass ran; a model
    built without one carries an empty mapping, and its records are UNREAD
    rather than absent - nothing was read to admit them on.

    Args:
        model: The world model.
        tally: The per-class unread tally, added to in place.
    """
    walked = model.properties.by_record_index
    for index, record in enumerate(model.objects.records):
        if index not in walked:
            class_name = class_name_of_path(record.type_path)
            tally[class_name] = tally.get(class_name, 0) + 1


def machines_of(model: WorldModel) -> WorldMachines:
    """Read every walked record's machine state out of the world model.

    Args:
        model: The world model.

    Returns:
        One :class:`MachineState` per record carrying a measured machine
        property, with the per-field availability flags, the denominators, the
        counts of what was refused, and - per class - every record that was not
        admitted (CS-1266).
    """
    records = model.objects.records
    walked = model.properties.by_record_index
    states: list[MachineState] = []
    refused_overclock = 0
    refused_recipe = 0
    unadmitted_read: dict[str, int] = {}
    unadmitted_unread: dict[str, int] = {}
    unadmitted_clean: dict[str, int] = {}

    for index in sorted(walked):
        entry = walked[index]
        if not _is_machine(entry):
            # COUNTED, NEVER DROPPED - CS-1266. One bucket per record: one of
            # these two tallies here, or a machine further down.
            class_name = (
                class_name_of_path(records[index].type_path) if index < len(records) else ""
            )
            tally = unadmitted_read if _payload_was_read(entry) else unadmitted_unread
            tally[class_name] = tally.get(class_name, 0) + 1
            # CS-1280. A MARK on a read record, never a third bucket.
            if _reads_clean(entry):
                unadmitted_clean[class_name] = unadmitted_clean.get(class_name, 0) + 1
            continue

        raw_producing = entry.values.get(PROPERTY_PRODUCING)
        producing = raw_producing if type(raw_producing) is bool else None

        recipe_class_name = None
        tag = _recipe_tag(entry.references)
        if tag is not None:
            permitted = _permitted_recipe_path(tag.object_path)
            if permitted is None:
                refused_recipe += 1
            else:
                recipe_class_name = class_name_of_path(permitted)

        overclock = None
        if PROPERTY_OVERCLOCK in entry.values:
            overclock = exact_from_float32(entry.values[PROPERTY_OVERCLOCK])
            if overclock is None:
                refused_overclock += 1

        states.append(
            MachineState(
                class_name=(
                    class_name_of_path(records[index].type_path) if index < len(records) else ""
                ),
                producing=producing,
                recipe_class_name=recipe_class_name,
                overclock=overclock,
                # A TAG IS PRESENT WHETHER OR NOT ITS VALUE DECODED - CS-1264.
                # Both flags read the dropped-tag names beside the values: a
                # clock tag that was written is not elided, and a boost tag is
                # a boost whatever became of its value.
                overclock_elided=(
                    PROPERTY_OVERCLOCK not in entry.values
                    and PROPERTY_OVERCLOCK not in entry.undecoded_names
                    and entry.payload_read
                    and not entry.disagreeing_value_count
                ),
                production_boost_tagged=not (
                    PRODUCTION_BOOST_PROPERTY_NAMES.isdisjoint(entry.values)
                    and PRODUCTION_BOOST_PROPERTY_NAMES.isdisjoint(entry.undecoded_names)
                ),
            )
        )

    _count_never_walked(model, unadmitted_unread)

    machines = tuple(states)
    unread = model.properties.unread_payload_count

    warnings: list[WorldWarning] = []
    if not machines:
        warnings.append(_warning(WARN_MACHINES_NONE_READ))
    if unread:
        warnings.append(_warning(WARN_MACHINES_PAYLOAD_UNREAD, unread))
    if refused_overclock:
        warnings.append(_warning(WARN_MACHINES_OVERCLOCK_REFUSED, refused_overclock))
    if refused_recipe:
        warnings.append(_warning(WARN_MACHINES_RECIPE_REFUSED, refused_recipe))

    return WorldMachines(
        machines=machines,
        producing_available=any(state.producing is not None for state in machines),
        recipe_available=any(state.recipe_class_name is not None for state in machines),
        overclock_available=any(state.overclock is not None for state in machines),
        records_considered=model.properties.total,
        unread_payload_count=unread,
        refused_overclock_count=refused_overclock,
        refused_recipe_count=refused_recipe,
        warnings=tuple(warnings),
        unadmitted_read_counts=_counted(unadmitted_read),
        unadmitted_unread_counts=_counted(unadmitted_unread),
        unadmitted_clean_counts=_counted(unadmitted_clean),
    )
