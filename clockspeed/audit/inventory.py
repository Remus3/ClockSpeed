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

**AN EMPTY TOTAL IS THE EXPECTED RESULT TODAY, AND IT IS FLAGGED.** Three
measurements bound what this can recover, and every one of them is recorded
outside this file:

- ``docs/LEDGER.md`` and ``docs/GATED.md``: **no building record carries an
  ``InventoryStack``.** A building holds an ``ObjectProperty`` REFERENCE to a
  separate record, so reaching a building's contents needs a reference-resolution
  pass this layer does not have.
- ``clockspeed/save/objects.py`` ``ContainerElement.value``: a
  ``StructProperty`` element inside a container is bounded, typed and
  deliberately NOT decoded. Its interior is a separate item's work.
- The serialized grammar of an inventory stack has never been measured in this
  project at all.

So :data:`WARN_INVENTORY_TOTAL_EMPTY` accompanies every empty total. An empty
``items`` tuple with no warning is indistinguishable from a world in which the
player owns nothing, and the difference between those two is the difference
between honest silence and confident wrong advice - the position
``clockspeed.save.world.UnlockState`` already takes for the same reason.

THE RECOGNITION VOCABULARY IS CLOSED, AND ITS PROVENANCE IS NAMED
-------------------------------------------------------------------
:data:`ITEM_KEY_PROPERTY_NAMES` and :data:`ITEM_COUNT_PROPERTY_NAMES` are the
property names that, appearing together inside one struct interior, mean "this
much of this item". The two seeded below are the ONLY pair this tree has
measured. ``clockspeed/data/blobs.py`` owns that grammar -
``entry := "(ItemClass=" qpath ",Amount=" integer ")"`` - and owns the match
counts behind it; the spike report it was built from measured that only those two
inner key tokens exist in the population at all. No count is restated here: the
parser is the owner.

**THAT MEASUREMENT IS OF THE SHIPPED DOCS BLOB, NOT OF THE SAVE.** It is stated
that way on purpose. The names are seeded from the one grammar this project has
actually measured rather than invented from memory, and whether a save's own
inventory struct spells them the same way is UNMEASURED - which is exactly why
the empty total is flagged rather than treated as an anomaly. Extending either
set is how this module learns a save-side spelling, and an entry added without a
measurement behind it turns a flagged gap into a silent wrong answer.

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
in the world under one blank row that looks like a real item.

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
# publishes them: `RecordProperties.values` carries an `objects.StructValue` and
# an `objects.ObjectReference` verbatim (see `world._published_value`), so
# reading the model means naming them. `load_world` is not imported: this layer
# never opens a save. `clockspeed.data.registry` is not imported either: the
# display-name join is not this module's work.

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING, Final

from clockspeed.audit.placement import class_name_of_path
from clockspeed.save.objects import ObjectReference, StructValue
from clockspeed.save.world import ContainerContents, WorldWarning

if TYPE_CHECKING:
    from collections.abc import Mapping

    from clockspeed.save.world import WorldModel

__all__ = [
    "ITEM_COUNT_PROPERTY_NAMES",
    "ITEM_KEY_PROPERTY_NAMES",
    "SOURCE_INVENTORY",
    "WARN_INVENTORY_ENTRY_UNDECODED",
    "WARN_INVENTORY_PAYLOAD_UNREAD",
    "WARN_INVENTORY_TOTAL_EMPTY",
    "ItemTotal",
    "WorldInventory",
    "inventory_of",
]

#: Which layer noticed a warning raised here.
SOURCE_INVENTORY: Final = "inventory"

WARN_INVENTORY_TOTAL_EMPTY: Final = "inventory-total-empty"
WARN_INVENTORY_PAYLOAD_UNREAD: Final = "inventory-payload-unread"
WARN_INVENTORY_ENTRY_UNDECODED: Final = "inventory-entry-undecoded"

#: The property names that name WHICH item. See the module docstring for where
#: this spelling was measured, for why the measurement is of the shipped docs
#: blob rather than of a save, and for what adding an entry here commits to.
ITEM_KEY_PROPERTY_NAMES: Final = frozenset({"ItemClass"})

#: The property names that name HOW MANY, on the same terms.
ITEM_COUNT_PROPERTY_NAMES: Final = frozenset({"Amount"})

#: One fixed line per warning code raised here. Keyed rather than formatted, on
#: the idiom ``clockspeed/save/world.py`` established.
_WARNING_DETAIL: Final[Mapping[str, str]] = MappingProxyType(
    {
        WARN_INVENTORY_TOTAL_EMPTY: (
            "no item total was recovered, which is not the same fact as an empty world;"
            " a building names its inventory by reference rather than carrying the"
            " stacks, and the stacks sit in struct interiors the reader does not decode"
            " under the tag grammar CS-980 measured, so the join has no terms yet"
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


@dataclass(frozen=True, repr=False)
class WorldInventory:
    """The per-item total, and the three numbers that say how complete it is.

    ``repr`` renders counts only. The item keys are publisher content and safe,
    but a test runner reprs a value before a human chooses what to print, and the
    habit that survives a later field being added is the quiet one.

    Attributes:
        items: One total per item key, sorted by item key. Sorted rather than
            insertion ordered so two runs over one model produce tuples that are
            equal AND iterate identically - no set iteration reaches this field.
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
    """

    items: tuple[ItemTotal, ...]
    containers_read: int
    undecoded_entry_count: int
    records_considered: int
    unread_payload_count: int
    warnings: tuple[WorldWarning, ...]

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
        The class name, or None when the value is not a path this layer can
        reduce or when the reduction is empty. An empty key is refused because
        ADR 0009 measured that an unresolved reference carries an EMPTY object
        path, and pooling every unresolved reference under one blank row would
        publish a total that looks like a real item.
    """
    if isinstance(value, ObjectReference):
        reduced = class_name_of_path(value.object_path)
    elif type(value) is str:
        reduced = class_name_of_path(value)
    else:
        return None
    return reduced or None


def _contribution_of(struct: StructValue) -> tuple[str, int] | None:
    """Read one item key and one count out of a struct interior, or refuse it.

    BOTH HALVES OR NEITHER. A struct carrying only a key says nothing about how
    much, and one carrying only a count says nothing about what - so a partial
    match contributes nothing rather than a total under a guessed other half.

    Args:
        struct: One published struct interior.

    Returns:
        The item key and its count, or None.
    """
    key: str | None = None
    count: int | None = None
    for name, value in struct.properties.items():
        if name in ITEM_KEY_PROPERTY_NAMES and key is None:
            key = _item_key_of(value)
        elif name in ITEM_COUNT_PROPERTY_NAMES and count is None and type(value) is int:
            # `type(...) is int` and not `isinstance`: isinstance(True, int) is
            # True, so a boolean flag would publish a count of 1.
            count = value
    if key is None or count is None:
        return None
    return key, count


def _aggregate(model: WorldModel) -> tuple[dict[str, int], int, int]:
    """Walk every published value and aggregate what it can recognise.

    ITERATIVE RATHER THAN RECURSIVE. A container can hold a struct, a struct
    interior can hold a container, and the nesting depth is a property of a file
    this layer did not write - so the walk uses an explicit work list rather than
    the interpreter's stack.

    THE RECORD ORDER IS SORTED BY INDEX. Nothing in the aggregate depends on the
    order, but a walk whose order comes from a mapping's iteration is a walk
    whose behaviour changes when the mapping's construction does, and the totals
    would then be equal while the undecoded tally moved.

    Args:
        model: The world to read.

    Returns:
        The per-item totals, how many containers were walked, and how many
        container elements were undecoded.
    """
    totals: dict[str, int] = {}
    containers_read = 0
    undecoded = 0
    work: list[object] = []

    for index in sorted(model.properties.by_record_index):
        entry = model.properties.by_record_index[index]
        work.extend(entry.values.values())

    while work:
        value = work.pop()
        if isinstance(value, ContainerContents):
            containers_read += 1
            for element in value.entries:
                if element.value is None:
                    undecoded += 1
                    continue
                work.append(element.value)
            continue
        if isinstance(value, StructValue):
            contribution = _contribution_of(value)
            if contribution is not None:
                key, count = contribution
                totals[key] = totals.get(key, 0) + count
            work.extend(value.properties.values())

    return totals, containers_read, undecoded


def inventory_of(model: WorldModel) -> WorldInventory:
    """Aggregate one world's recovered container contents into per-item totals.

    PURE, AND TOTAL. Every input produces a model; nothing here raises. A world
    with no properties at all, a world whose every payload went unread and a
    world whose containers held nothing this module recognises all return a valid
    :class:`WorldInventory` carrying the flags that say which of those happened.

    Args:
        model: The world to read. Read only; nothing here mutates it and nothing
            here opens a save.

    Returns:
        The inventory model.
    """
    totals, containers_read, undecoded = _aggregate(model)
    items = tuple(ItemTotal(item_key=key, count=count) for key, count in sorted(totals.items()))
    unread = model.properties.unread_payload_count

    warnings: list[WorldWarning] = []
    if not items:
        warnings.append(_warning(WARN_INVENTORY_TOTAL_EMPTY))
    if unread:
        warnings.append(_warning(WARN_INVENTORY_PAYLOAD_UNREAD, unread))
    if undecoded:
        warnings.append(_warning(WARN_INVENTORY_ENTRY_UNDECODED, undecoded))

    return WorldInventory(
        items=items,
        containers_read=containers_read,
        undecoded_entry_count=undecoded,
        records_considered=model.properties.total,
        unread_payload_count=unread,
        warnings=tuple(warnings),
    )
