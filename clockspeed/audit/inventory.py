"""What resources the world actually holds - and how complete that answer is.

WHAT THIS MODULE OWNS
-----------------------
One pure function over one ``clockspeed.save.world.WorldModel``, returning a
frozen :class:`WorldInventory`: a per-item total aggregated across every
published container in every walked record's properties. It is the COMPUTATION
half of "what resources do I have", and it lives here because
``clockspeed/surface/`` never computes and ``audit/`` is the layer that consumes
a whole world model.

It reads no save, no docs file and no install. Its only input is the model.

THE DENOMINATOR IS PART OF THE ANSWER, NOT A DIAGNOSTIC
---------------------------------------------------------
``WorldProperties.unread_payload_count``'s own docstring calls itself "the
honest denominator for anything computed off these values" and states the
consequence: "a consumer that treats an empty mapping as 'this record has no
properties' is wrong by exactly this many records." A total published without it
is a partial sum presented as a fact, so this model carries three numbers beside
the items - how many records were considered, how many of their payloads never
read, and how many container elements the save layer did not decode. A consumer
can then say how complete the total is instead of implying it is complete.

A BUILDING'S INVENTORY IS REACHED THROUGH THE PUBLISHED JOIN - CS-400
------------------------------------------------------------------------
A building record carries no ``InventoryStack`` of its own. It holds an
``ObjectProperty`` REFERENCE to a separate component record, and that record
carries ``mInventoryStacks``. The save layer publishes where every reference
landed as ``RecordProperties.reference_targets`` (``clockspeed.save.world``
``ReferenceTarget``), so this module follows a building to its inventory by
reading that join and never by resolving a path itself - resolution is the save
layer's, and running it here would reach past the neighbour.

"BUILDING" IS NOT CLASSIFIED, AND A CARRIER HAS AT MOST ONE OWNER. A CARRIER is
any walked record whose own published values hold at least one stack. It is
ATTRIBUTED to the ACTOR records (``ObjectRecord.kind``, published on the model)
whose resolved references name it, and to nothing else:

- exactly one claiming actor - the carrier is that building's;
- none - the carrier is UNATTRIBUTED, counted on the world model;
- more than one - the carrier is a CONFLICT, counted on the world model and
  left out of every per-building total rather than handed to one claimant.

WHY ACTORS ONLY, MEASURED RATHER THAN LISTED. A component record references
inventories too - a factory connection names the inventory it feeds - and
following those made 372 carriers in one library save reachable from several
records, so the per-building sum overran the world total. Over four library
saves across both version pairs (CS-400 S3 re-measure, counts only) every
actor reference into a carrier came from that carrier's own parent actor, and
every non-parent reference came from a component. The rule is therefore read
off the record kind the model already publishes, and no inventory property
name is hand-listed. The conflict count is what reports the day that stops
holding.

So the partition is exact by construction, and graded as an invariant: the
per-building sums plus the unattributed and conflict sums equal the world
total, for stacks and for items alike.

An UNRESOLVED or AMBIGUOUS reference is never followed: ambiguity hands over
several candidates, and taking one would be the confident wrong answer
non-negotiable 7 forbids. Both are COUNTED on the world model, as is a resolved
reference whose target has no published properties entry.

THE WORLD TOTAL DOES NOT GO THROUGH THE JOIN. :attr:`WorldInventory.items` sums
every stack in every walked record exactly once, whoever references it.

THE THREE STATES OF AN ``Item`` TAG, NEVER COLLAPSED
------------------------------------------------------
Inside one stack interior ``Item`` is either:

- a decoded ``clockspeed.save.objects.InventoryItem`` - a row when its class is
  non-empty and ``NumItems`` is positive, an EMPTY SLOT when its class is empty
  and ``NumItems`` is zero, and refused as :data:`EXCLUDED_COUNT_DISAGREES` for
  either other pairing;
- an ``InventoryItemRefusal`` - the save layer could not read the native
  interior, so the stack is excluded under the save layer's own reason word;
- ABSENT, the key missing altogether - excluded as :data:`EXCLUDED_ITEM_ABSENT`.
  ADJ-G Q4 measured it only on top-level pickup structs, outside every
  inventory carrier, and binds it as a THIRD state: an absent item is neither
  an empty slot nor an unknown item. The walk reads every struct the model
  publishes in a record's values, so one reached anywhere is counted here.

Every exclusion is COUNTED by reason on :attr:`WorldInventory.excluded` and
raised as :data:`WARN_INVENTORY_STACK_EXCLUDED`; none is guessed and none
raises. A row or an empty slot whose item state was present and left undecoded
keeps its reading and is counted on ``state_undecoded_count``; an excluded stack
is counted only under its exclusion reason.

An empty ``items`` tuple is still accompanied by :data:`WARN_INVENTORY_TOTAL_EMPTY`:
a world whose stacks were all refused, absent or unreachable is not the same
fact as a world in which the player owns nothing.

THE RECOGNITION VOCABULARY IS THE SAVE'S OWN SPELLING, AND ITS PROVENANCE IS NAMED
------------------------------------------------------------------------------------
:data:`ITEM_KEY_PROPERTY_NAMES` and :data:`ITEM_COUNT_PROPERTY_NAMES` are the
property names that, appearing inside one struct interior, mean "this much of
this item". They are ``Item`` and ``NumItems``: the spelling CS-400 S0 measured
on every ``mInventoryStacks`` element in the local save library. They REPLACE
the earlier seed, ``ItemClass`` / ``Amount``, which was the SHIPPED DOCS BLOB's
grammar (``clockspeed/data/blobs.py``) and was never measured against a save.
An entry added without a measurement behind it turns a flagged gap into a
silent wrong answer.

A plain path string or an ``ObjectReference`` under ``Item`` is still reduced
the way it always was. The save writes neither there; the branch is kept
because a published path value reduces the same way wherever it sits. Any
other value type under ``Item`` is excluded as :data:`EXCLUDED_ITEM_UNRECOGNISED`.

A COUNT IS AN ``int`` AND A BOOLEAN IS NOT
--------------------------------------------
``isinstance(True, int)`` is True in Python, so an ``isinstance`` test accepts a
flag and publishes a total of 1 for something that means nothing of the kind.
The check here is ``type(value) is int``, the same positive type audit
``tests/solve`` requires of a Fraction and for the same reason: a check that
cannot fail on the confusable input is not a check.

AN EMPTY ITEM KEY IS REFUSED
------------------------------
``docs/adr/0009-inventory-potential-top-level-carries-no-slot-count.md``
measured that an UNRESOLVED object reference carries an EMPTY object path. A
total keyed by the empty string would therefore pool every unresolved reference
in the world under one blank row that looks like a real item. An empty key
beside a ZERO count is the empty slot above; beside a positive count it is
excluded as :data:`EXCLUDED_COUNT_DISAGREES`.

WHAT NEVER LEAVES THIS MODULE
-------------------------------
A record index, a byte offset, a filesystem path, an instance name, and a
DISPLAY NAME. The first four are the refusals ``clockspeed/save/world.py``
already makes and this layer must not undo. The fifth is different: an item's
display name is a join against ``clockspeed/data/registry.py`` and belongs to
whoever performs that join. :class:`ItemTotal` carries the item KEY, and a
display-name field here would be filled in by inference the first time somebody
wanted one.
"""

# SEAM DISCIPLINE (BOOTSTRAP.md section 6).
# Each layer consumes only the layer below it through a stated model.
# solve/ never reads a save. advisor/ never reads the raw docs file.
# surface/ never computes. A layer that reaches past its neighbor is a
# design bug.
#
# THE ONE MODEL BELOW THIS ONE IS `clockspeed.save.world.WorldModel`. The types
# named from `clockspeed.save.objects` are there because the world model itself
# publishes them: `RecordProperties.values` carries an `objects.StructValue`, an
# `objects.ObjectReference`, an `objects.InventoryItem` and an
# `objects.InventoryItemRefusal` verbatim (see `world._published_value`), so
# reading the model means naming them. The join is read off
# `RecordProperties.reference_targets` and never computed here. `load_world` is
# not imported: this layer never opens a save. `clockspeed.data.registry` is not
# imported either: the display-name join is not this module's work.

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import TYPE_CHECKING, Final

from clockspeed.audit.placement import class_name_of_path
from clockspeed.save.objects import (
    ITEM_REFUSAL_REASONS,
    KIND_ACTOR,
    InventoryItem,
    InventoryItemRefusal,
    ObjectReference,
    StructValue,
)
from clockspeed.save.world import (
    TARGET_AMBIGUOUS,
    TARGET_RESOLVED,
    TARGET_UNRESOLVED,
    ContainerContents,
    WorldWarning,
)

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping

    from clockspeed.save.world import RecordProperties, WorldModel

__all__ = [
    "EXCLUDED_COUNT_DISAGREES",
    "EXCLUDED_COUNT_UNREAD",
    "EXCLUDED_ITEM_ABSENT",
    "EXCLUDED_ITEM_UNRECOGNISED",
    "ITEM_COUNT_PROPERTY_NAMES",
    "ITEM_KEY_PROPERTY_NAMES",
    "SOURCE_INVENTORY",
    "STACK_EXCLUSION_REASONS",
    "WARN_INVENTORY_ENTRY_UNDECODED",
    "WARN_INVENTORY_PAYLOAD_UNREAD",
    "WARN_INVENTORY_STACK_EXCLUDED",
    "WARN_INVENTORY_TOTAL_EMPTY",
    "BuildingInventory",
    "ItemTotal",
    "WorldInventory",
    "inventory_of",
]

#: Which layer noticed a warning raised here.
SOURCE_INVENTORY: Final = "inventory"

WARN_INVENTORY_TOTAL_EMPTY: Final = "inventory-total-empty"
WARN_INVENTORY_PAYLOAD_UNREAD: Final = "inventory-payload-unread"
WARN_INVENTORY_ENTRY_UNDECODED: Final = "inventory-entry-undecoded"
WARN_INVENTORY_STACK_EXCLUDED: Final = "inventory-stack-excluded"

#: The property names that name WHICH item - the save's own spelling. See the
#: module docstring for where it was measured and for what adding an entry here
#: commits to.
ITEM_KEY_PROPERTY_NAMES: Final = frozenset({"Item"})

#: The property names that name HOW MANY, on the same terms.
ITEM_COUNT_PROPERTY_NAMES: Final = frozenset({"NumItems"})

#: Why a stack was excluded from every total - a CLOSED vocabulary. The save
#: layer's own refusal words (``objects.ITEM_REFUSAL_REASONS``) are carried
#: verbatim beside these four, so a refusal is counted under the reason the
#: layer that refused it gave.
#:
#: - :data:`EXCLUDED_ITEM_ABSENT`: a count with no ``Item`` tag at all - the
#:   ADJ-G Q4 third state, never an empty slot.
#: - :data:`EXCLUDED_COUNT_UNREAD`: an ``Item`` with no ``NumItems``, or one that
#:   is not exactly an ``int``.
#: - :data:`EXCLUDED_ITEM_UNRECOGNISED`: an ``Item`` value of a type this module
#:   does not read.
#: - :data:`EXCLUDED_COUNT_DISAGREES`: a class and a count that contradict each
#:   other - a class with a count that is not positive, or no class with a
#:   count that is not zero.
EXCLUDED_ITEM_ABSENT: Final = "item_absent"
EXCLUDED_COUNT_UNREAD: Final = "count_unread"
EXCLUDED_ITEM_UNRECOGNISED: Final = "item_unrecognised"
EXCLUDED_COUNT_DISAGREES: Final = "item_count_disagrees"
STACK_EXCLUSION_REASONS: Final = frozenset(
    {
        EXCLUDED_ITEM_ABSENT,
        EXCLUDED_COUNT_UNREAD,
        EXCLUDED_ITEM_UNRECOGNISED,
        EXCLUDED_COUNT_DISAGREES,
        *ITEM_REFUSAL_REASONS,
    }
)

#: The two join tallies beside the three target states: references never
#: followed because their targets do not align, and resolved references whose
#: target has no properties entry to walk.
_JOIN_UNJOINED: Final = "unjoined"
_JOIN_UNWALKED: Final = "unwalked"

#: The two non-excluded outcomes of reading one stack.
_OUTCOME_ROW: Final = "row"
_OUTCOME_EMPTY: Final = "empty"

#: One fixed line per warning code raised here. Keyed rather than formatted, on
#: the idiom ``clockspeed/save/world.py`` established.
_WARNING_DETAIL: Final[Mapping[str, str]] = MappingProxyType(
    {
        WARN_INVENTORY_TOTAL_EMPTY: (
            "no item total was recovered, which is not the same fact as an empty world;"
            " every stack the walk reached was empty, excluded or absent, or no record"
            " carried a stack at all"
        ),
        WARN_INVENTORY_PAYLOAD_UNREAD: (
            "this many walked records had a property payload that never read, so the"
            " total below is a sum over the records that did and is short by whatever"
            " these hold"
        ),
        WARN_INVENTORY_ENTRY_UNDECODED: (
            "this many container elements were bounded and typed but not decoded by the"
            " save layer, so they were counted rather than dropped; an element that was"
            " not decoded is not an element that was empty"
        ),
        WARN_INVENTORY_STACK_EXCLUDED: (
            "this many inventory stacks could not be read as an item and a count, so"
            " they were counted by reason and left out of every total; an excluded"
            " stack is not an empty one"
        ),
    }
)


@dataclass(frozen=True)
class ItemTotal:
    """How much of one item the recovered containers hold, all told.

    NO DISPLAY NAME. That is a registry join and belongs to whoever performs it -
    see the module docstring.

    Attributes:
        item_key: The item's class name, reduced from whatever path or reference
            the container carried by
            ``clockspeed.audit.placement.class_name_of_path``. Publisher content,
            never an instance name.
        count: The sum over every recognised contribution. An exact integer; an
            integer count needs no rendering because it loses nothing.
    """

    item_key: str
    count: int


@dataclass(frozen=True)
class BuildingInventory:
    """What one actor holds through the inventory carriers it alone owns - CS-400.

    ONE PER ACTOR, NEVER PER REFERENCE. An actor naming one carrier under two
    tags owns it once; an actor owning two carriers sums both. A carrier another
    actor also claims is a CONFLICT and is in neither actor's view - see the
    module docstring.

    NO RECORD INDEX. The world model keys by one and this layer never hands it
    on (module docstring). The rows sit in record-table order on
    :attr:`WorldInventory.buildings`, which is a position a consumer can line up
    against nothing it was not already given.

    THE GENERATED ``repr`` RENDERS COUNTS ONLY. Every text-bearing field is
    ``field(repr=False)``: an item key is reduced from a class path read out of
    the save, and a test runner reprs a value before a human chooses what to
    print.

    Attributes:
        class_name: The actor's class name, reduced by
            ``clockspeed.audit.placement.class_name_of_path``.
        items: One total per item key over every stack owned, sorted by key.
        carriers_reached: How many carriers this actor alone owns.
        stack_count: Every stack owned, whatever its outcome.
        empty_slot_count: Stacks read as an empty slot - no class, a zero count.
        state_undecoded_count: Rows and empty slots whose item state was present
            and left undecoded; their reading still stands. An excluded stack is
            counted under its reason only.
        excluded: ``(reason, count)`` per member of
            :data:`STACK_EXCLUSION_REASONS` that occurred, sorted by reason.
        containers_read: Containers walked inside the owned carriers.
        undecoded_entry_count: Container elements inside the owned carriers the
            save layer did not decode - counted, never read as empty.
    """

    class_name: str = field(repr=False)
    items: tuple[ItemTotal, ...] = field(repr=False)
    carriers_reached: int
    stack_count: int
    empty_slot_count: int
    state_undecoded_count: int
    excluded: tuple[tuple[str, int], ...] = field(repr=False)
    containers_read: int = 0
    undecoded_entry_count: int = 0

    @property
    def excluded_count(self) -> int:
        """How many stacks were excluded, all reasons together.

        Returns:
            The count.
        """
        return sum(count for _, count in self.excluded)


@dataclass(frozen=True, repr=False)
class WorldInventory:
    """The per-item total, the per-building view, and the numbers that say how complete each is.

    ``repr`` renders counts only. The item keys are publisher content, but a
    test runner reprs a value before a human chooses what to print, and the
    habit that survives a later field being added is the quiet one.

    Attributes:
        items: One total per item key, sorted by item key. Sorted rather than
            insertion ordered so two runs over one model produce tuples that are
            equal AND iterate identically - no set iteration reaches this field.
            Summed over every walked record once, NOT through the join.
        containers_read: How many published containers were walked. The positive
            half of the denominator: zero here means the total is empty because
            there was nothing to read, which is a different fact from a total
            that is empty because nothing read was recognised.
        undecoded_entry_count: How many container elements the save layer
            bounded and typed but did not decode. Counted rather than dropped:
            None on a ``ContainerEntry`` means "not decoded", never "empty".
        records_considered: How many walked records had an entry in
            ``WorldModel.properties``. Total over the record table by
            construction.
        unread_payload_count: How many of those records' payloads never read,
            carried verbatim from ``WorldProperties.unread_payload_count`` - the
            honest denominator its own docstring names.
        warnings: Everything flagged, in the ``WorldWarning`` idiom.
        buildings: One :class:`BuildingInventory` per actor owning at least one
            carrier alone, in record-table order.
        stack_count: Every stack the world walk reached, whatever its outcome.
        empty_slot_count: Stacks read as an empty slot.
        state_undecoded_count: Rows and empty slots whose state was left undecoded.
        excluded: ``(reason, count)`` per exclusion reason that occurred over the
            world walk, sorted by reason. Never part of :attr:`items`.
        references_resolved: Published references resolved to exactly one record.
        references_unresolved: Published references borne by no record - never
            followed, so whatever they name is absent from :attr:`buildings`.
        references_ambiguous: Published references borne by several records -
            never followed, on the same terms.
        references_unjoined: References on an entry whose published targets do
            not align with them one for one, or whose target carries a state
            outside ``clockspeed.save.world.TARGET_STATES`` - never followed.
        references_to_unwalked: Resolved references whose target record has no
            entry in ``WorldModel.properties`` - nothing there to walk, counted.
        carrier_count: Records whose own values hold at least one stack.
        unattributed_carrier_count: Carriers no actor claims.
        unattributed_stack_count: Stacks in those carriers, whatever the outcome.
        unattributed_item_count: Item count summed over those carriers' rows.
        conflict_carrier_count: Carriers claimed by more than one actor - left
            out of every per-building view.
        conflict_stack_count: Stacks in those carriers.
        conflict_item_count: Item count summed over those carriers' rows.
    """

    items: tuple[ItemTotal, ...]
    containers_read: int
    undecoded_entry_count: int
    records_considered: int
    unread_payload_count: int
    warnings: tuple[WorldWarning, ...]
    buildings: tuple[BuildingInventory, ...] = ()
    stack_count: int = 0
    empty_slot_count: int = 0
    state_undecoded_count: int = 0
    excluded: tuple[tuple[str, int], ...] = ()
    references_resolved: int = 0
    references_unresolved: int = 0
    references_ambiguous: int = 0
    references_unjoined: int = 0
    references_to_unwalked: int = 0
    carrier_count: int = 0
    unattributed_carrier_count: int = 0
    unattributed_stack_count: int = 0
    unattributed_item_count: int = 0
    conflict_carrier_count: int = 0
    conflict_stack_count: int = 0
    conflict_item_count: int = 0

    @property
    def total_count(self) -> int:
        """The sum over every item total.

        Returns:
            The count.
        """
        return sum(item.count for item in self.items)

    def __repr__(self) -> str:
        """Render counts only, and none that a member could make raise.

        ``total_count`` IS DELIBERATELY ABSENT. It is a property summing a field
        off every member, so a repr that rendered it would raise on a model
        holding a planted value - which is exactly the state a forced test arm
        puts this class in, and a repr that raises there defeats the assertion
        rendering it was reached through.
        ``tests/test_assertion_rendering.py::test_the_shipped_repr_is_what_gets_bypassed_in_every_forced_arm``
        measured it raising. Every figure below is a length or a plain field.

        Returns:
            The safe rendering.
        """
        return (
            f"{type(self).__name__}(items={len(self.items)}, "
            f"containers_read={self.containers_read}, "
            f"undecoded_entry_count={self.undecoded_entry_count}, "
            f"records_considered={self.records_considered}, "
            f"unread_payload_count={self.unread_payload_count}, "
            f"warnings={len(self.warnings)}, "
            f"buildings={len(self.buildings)}, "
            f"stack_count={self.stack_count}, "
            f"empty_slot_count={self.empty_slot_count}, "
            f"state_undecoded_count={self.state_undecoded_count}, "
            f"excluded={len(self.excluded)}, "
            f"references_resolved={self.references_resolved}, "
            f"references_unresolved={self.references_unresolved}, "
            f"references_ambiguous={self.references_ambiguous}, "
            f"references_unjoined={self.references_unjoined}, "
            f"references_to_unwalked={self.references_to_unwalked}, "
            f"carrier_count={self.carrier_count}, "
            f"unattributed_carrier_count={self.unattributed_carrier_count}, "
            f"unattributed_stack_count={self.unattributed_stack_count}, "
            f"unattributed_item_count={self.unattributed_item_count}, "
            f"conflict_carrier_count={self.conflict_carrier_count}, "
            f"conflict_stack_count={self.conflict_stack_count}, "
            f"conflict_item_count={self.conflict_item_count})"
        )


@dataclass
class _Tally:
    """The mutable accumulator one walk fills. Private; never published.

    The two text-keyed mappings are ``field(repr=False)``: their keys are item
    keys read out of the save, and a generated repr would render them.

    Attributes:
        totals: Item key to its summed count.
        excluded: Exclusion reason to how many stacks it excluded.
        containers_read: Containers walked.
        undecoded_entries: Container elements the save layer did not decode.
        stacks: Stacks reached, whatever their outcome.
        empty_slots: Stacks read as an empty slot.
        state_undecoded: Item-bearing stacks whose state was left undecoded.
    """

    totals: dict[str, int] = field(default_factory=dict, repr=False)
    excluded: dict[str, int] = field(default_factory=dict, repr=False)
    containers_read: int = 0
    undecoded_entries: int = 0
    stacks: int = 0
    empty_slots: int = 0
    state_undecoded: int = 0

    def items(self) -> tuple[ItemTotal, ...]:
        """The totals, sorted by item key.

        Returns:
            One total per key.
        """
        return tuple(
            ItemTotal(item_key=key, count=count) for key, count in sorted(self.totals.items())
        )

    def exclusions(self) -> tuple[tuple[str, int], ...]:
        """The exclusion counts, sorted by reason.

        Returns:
            One pair per reason that occurred.
        """
        return tuple(sorted(self.excluded.items()))


def _warning(code: str, count: int = 1) -> WorldWarning:
    """Build one warning from this module's own fixed detail table.

    Args:
        code: One of this module's ``WARN_*`` constants.
        count: How many occurrences it aggregates.

    Returns:
        The warning.
    """
    return WorldWarning(
        source=SOURCE_INVENTORY,
        code=code,
        detail=_WARNING_DETAIL[code],
        count=count,
    )


def _item_key_of(value: object) -> str | None:
    """Reduce one decoded value to an item class name, or refuse it.

    Args:
        value: The value found under an item-key property name.

    Returns:
        The class name, the EMPTY STRING when the value names no class at all
        (an empty slot's item), or None when the value is not a type this layer
        reads. An empty name is never totalled: ADR 0009 measured that an
        unresolved reference carries an EMPTY object path, and pooling every
        unresolved reference under one blank row would publish a total that
        looks like a real item. :func:`_read_stack` decides what an empty name
        means from the count beside it.
    """
    if isinstance(value, InventoryItem):
        path = value.class_path
    elif isinstance(value, ObjectReference):
        path = value.object_path
    elif type(value) is str:
        path = value
    else:
        return None
    return class_name_of_path(path)


def _exclusion_of(value: object, count: object) -> str | None:
    """Why one stack's item and count cannot be read, or None when they can.

    Checked in a FIXED ORDER so one stack is excluded under exactly one reason:
    a refused item, then an unread count, then an item of a type not read here.

    Args:
        value: The value under the item-key name.
        count: The value under the count name, or None when the tag is missing.

    Returns:
        A member of :data:`STACK_EXCLUSION_REASONS`, or None.
    """
    if isinstance(value, InventoryItemRefusal):
        return value.reason if value.reason in ITEM_REFUSAL_REASONS else EXCLUDED_ITEM_UNRECOGNISED
    if type(count) is not int:
        # `type(...) is int` and not `isinstance`: isinstance(True, int) is
        # True, so a boolean flag would publish a count of 1.
        return EXCLUDED_COUNT_UNREAD
    if _item_key_of(value) is None:
        return EXCLUDED_ITEM_UNRECOGNISED
    return None


def _read_stack(struct: StructValue) -> tuple[str, str, int, bool] | None:
    """Read one struct interior as a stack, or say it is not one.

    A struct is a stack when it carries an item-key or an item-count property
    name. ``struct_word`` is not consulted: a stack is recognised by what it
    holds, so no struct vocabulary is hand-written here.

    Args:
        struct: One published struct interior.

    Returns:
        None when the struct carries neither name. Otherwise the outcome - a
        row, an empty slot, or a member of :data:`STACK_EXCLUSION_REASONS` -
        with the item key and count for a row, and whether the item's state was
        left undecoded.
    """
    present = [name for name in struct.properties if name in ITEM_KEY_PROPERTY_NAMES]
    counted = [name for name in struct.properties if name in ITEM_COUNT_PROPERTY_NAMES]
    if not present and not counted:
        return None
    value = struct.properties[present[0]] if present else None
    count = struct.properties[counted[0]] if counted else None
    reason = EXCLUDED_ITEM_ABSENT if not present else _exclusion_of(value, count)
    key = _item_key_of(value)
    # The last two tests are implied by `reason is None`; they are restated so
    # the type checker narrows `key` and `count` below without a cast.
    if reason is not None or key is None or type(count) is not int:
        return reason or EXCLUDED_ITEM_UNRECOGNISED, "", 0, False
    undecoded = isinstance(value, InventoryItem) and value.state_undecoded
    if key == "" and count == 0:
        return _OUTCOME_EMPTY, "", 0, undecoded
    if key == "" or count <= 0:
        return EXCLUDED_COUNT_DISAGREES, "", 0, False
    return _OUTCOME_ROW, key, count, undecoded


def _walk(values: Iterable[object], tally: _Tally) -> None:
    """Walk published values and fold every stack they hold into one tally.

    ITERATIVE RATHER THAN RECURSIVE. A container can hold a struct, a struct
    interior can hold a container, and the nesting depth is a property of a file
    this layer did not write - so the walk uses an explicit work list rather than
    the interpreter's stack.

    Args:
        values: The values to walk.
        tally: Filled in place.
    """
    work: list[object] = list(values)
    while work:
        value = work.pop()
        if isinstance(value, ContainerContents):
            tally.containers_read += 1
            for element in value.entries:
                if element.value is None:
                    tally.undecoded_entries += 1
                    continue
                work.append(element.value)
            continue
        if not isinstance(value, StructValue):
            continue
        reading = _read_stack(value)
        if reading is not None:
            outcome, key, count, undecoded = reading
            tally.stacks += 1
            tally.state_undecoded += int(undecoded)
            if outcome == _OUTCOME_ROW:
                tally.totals[key] = tally.totals.get(key, 0) + count
            elif outcome == _OUTCOME_EMPTY:
                tally.empty_slots += 1
            else:
                tally.excluded[outcome] = tally.excluded.get(outcome, 0) + 1
        work.extend(value.properties.values())


def _merge(into: _Tally, part: _Tally) -> None:
    """Add one tally into another.

    Args:
        into: Filled in place.
        part: Read only.
    """
    for key, count in part.totals.items():
        into.totals[key] = into.totals.get(key, 0) + count
    for reason, count in part.excluded.items():
        into.excluded[reason] = into.excluded.get(reason, 0) + count
    into.containers_read += part.containers_read
    into.undecoded_entries += part.undecoded_entries
    into.stacks += part.stacks
    into.empty_slots += part.empty_slots
    into.state_undecoded += part.state_undecoded


def _followed(entry: RecordProperties, joins: dict[str, int]) -> list[int]:
    """The distinct record indices one entry's references resolve to.

    A REFERENCE IS FOLLOWED ONLY WHEN RESOLVED. Unresolved and ambiguous ones
    are counted into ``joins`` and never followed; so is every reference on an
    entry whose targets do not align with its references one for one, because
    a misaligned target cannot be trusted to belong to the reference beside it.

    Args:
        entry: One record's published properties.
        joins: Filled in place, keyed by join state.

    Returns:
        The resolved target indices, first occurrence first, each once.
    """
    if len(entry.reference_targets) != len(entry.references):
        joins[_JOIN_UNJOINED] += len(entry.references)
        return []
    found: list[int] = []
    for target in entry.reference_targets:
        index = target.record_index
        if target.state == TARGET_RESOLVED and index is not None:
            joins[TARGET_RESOLVED] += 1
            if index not in found:
                found.append(index)
        elif target.state in (TARGET_UNRESOLVED, TARGET_AMBIGUOUS):
            joins[target.state] += 1
        else:
            joins[_JOIN_UNJOINED] += 1
    return found


def _is_actor(model: WorldModel, index: int) -> bool:
    """Whether the record table holds an ACTOR at this index.

    Args:
        model: The world.
        index: A record index.

    Returns:
        False for a component and for an index the table does not hold.
    """
    records = model.objects.records
    return 0 <= index < len(records) and records[index].kind == KIND_ACTOR


def _claims(
    model: WorldModel, carriers: Mapping[int, _Tally], joins: dict[str, int]
) -> dict[int, list[int]]:
    """Which actors claim each carrier, through their own resolved references.

    EVERY record's references are counted into ``joins``; only an ACTOR's
    resolved references stake a claim - see the module docstring for the
    measurement behind that.

    Args:
        model: The world.
        carriers: Carrier index to its own tally.
        joins: Filled in place.

    Returns:
        Carrier index to its claimants in record-table order, for every carrier.
    """
    by_index = model.properties.by_record_index
    claimants: dict[int, list[int]] = {index: [] for index in carriers}
    for index in sorted(by_index):
        actor = _is_actor(model, index)
        for target in _followed(by_index[index], joins):
            if target not in by_index:
                joins[_JOIN_UNWALKED] += 1
            elif actor and target in carriers:
                claimants[target].append(index)
    return claimants


def _item_count(tally: _Tally) -> int:
    """The item count a tally's rows sum to.

    Args:
        tally: Read only.

    Returns:
        The count.
    """
    return sum(tally.totals.values())


def inventory_of(model: WorldModel) -> WorldInventory:
    """Aggregate one world's recovered container contents into totals and per-building views.

    PURE, AND TOTAL. Every input produces a model; nothing here raises. A world
    with no properties at all, a world whose every payload went unread and a
    world whose containers held nothing this module recognises all return a valid
    :class:`WorldInventory` carrying the flags that say which of those happened.

    THE RECORD ORDER IS SORTED BY INDEX, so two runs over one model iterate
    identically, and the per-building view is in record-table order.

    Args:
        model: The world to read. Read only; nothing here mutates it and nothing
            here opens a save.

    Returns:
        The inventory model.
    """
    by_index = model.properties.by_record_index
    world = _Tally()
    carriers: dict[int, _Tally] = {}
    for index in sorted(by_index):
        own = _Tally()
        _walk(by_index[index].values.values(), own)
        _merge(world, own)
        if own.stacks:
            carriers[index] = own

    joins = {
        TARGET_RESOLVED: 0,
        TARGET_UNRESOLVED: 0,
        TARGET_AMBIGUOUS: 0,
        _JOIN_UNJOINED: 0,
        _JOIN_UNWALKED: 0,
    }
    claimants = _claims(model, carriers, joins)
    owned: dict[int, list[int]] = {}
    unattributed = _Tally()
    conflict = _Tally()
    unattributed_carriers = 0
    conflict_carriers = 0
    for carrier in sorted(carriers):
        claimed_by = claimants[carrier]
        if not claimed_by:
            unattributed_carriers += 1
            _merge(unattributed, carriers[carrier])
        elif len(claimed_by) > 1:
            conflict_carriers += 1
            _merge(conflict, carriers[carrier])
        else:
            owned.setdefault(claimed_by[0], []).append(carrier)

    records = model.objects.records
    buildings: list[BuildingInventory] = []
    for actor in sorted(owned):
        held = _Tally()
        for carrier in owned[actor]:
            _merge(held, carriers[carrier])
        buildings.append(
            BuildingInventory(
                class_name=class_name_of_path(records[actor].type_path),
                items=held.items(),
                carriers_reached=len(owned[actor]),
                stack_count=held.stacks,
                empty_slot_count=held.empty_slots,
                state_undecoded_count=held.state_undecoded,
                excluded=held.exclusions(),
                containers_read=held.containers_read,
                undecoded_entry_count=held.undecoded_entries,
            )
        )

    items = world.items()
    excluded = world.exclusions()
    unread = model.properties.unread_payload_count

    warnings: list[WorldWarning] = []
    if not items:
        warnings.append(_warning(WARN_INVENTORY_TOTAL_EMPTY))
    if unread:
        warnings.append(_warning(WARN_INVENTORY_PAYLOAD_UNREAD, unread))
    if world.undecoded_entries:
        warnings.append(_warning(WARN_INVENTORY_ENTRY_UNDECODED, world.undecoded_entries))
    excluded_total = sum(count for _, count in excluded)
    if excluded_total:
        warnings.append(_warning(WARN_INVENTORY_STACK_EXCLUDED, excluded_total))

    return WorldInventory(
        items=items,
        containers_read=world.containers_read,
        undecoded_entry_count=world.undecoded_entries,
        records_considered=model.properties.total,
        unread_payload_count=unread,
        warnings=tuple(warnings),
        buildings=tuple(buildings),
        stack_count=world.stacks,
        empty_slot_count=world.empty_slots,
        state_undecoded_count=world.state_undecoded,
        excluded=excluded,
        references_resolved=joins[TARGET_RESOLVED],
        references_unresolved=joins[TARGET_UNRESOLVED],
        references_ambiguous=joins[TARGET_AMBIGUOUS],
        references_unjoined=joins[_JOIN_UNJOINED],
        references_to_unwalked=joins[_JOIN_UNWALKED],
        carrier_count=len(carriers),
        unattributed_carrier_count=unattributed_carriers,
        unattributed_stack_count=unattributed.stacks,
        unattributed_item_count=_item_count(unattributed),
        conflict_carrier_count=conflict_carriers,
        conflict_stack_count=conflict.stacks,
        conflict_item_count=_item_count(conflict),
    )
