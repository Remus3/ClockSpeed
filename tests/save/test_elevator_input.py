"""CS-1348 - the save layer publishes the space elevator's input inventory.

WHAT WAS MISSING. CS-1343 closed with the phase model publishing
``delivered_available`` False on every world, because no layer below
``clockspeed/progress/`` published a delivered reading: the inventory model
lives in ``clockspeed/audit/``, which is not below it. The carrier is now
measured (``docs/adr/0016-unlock-arrays-carriers-and-serialized-grammar.md``,
names and counts only) and the save layer publishes it as
``WorldModel.elevator_input``, which the phase model reads.

THE CARRIER, AS MEASURED. The elevator actor's top-level ``mInputInventory``
reference lands on one inventory component whose ``mInventoryStacks`` holds
the input slots. Every measured elevator held six slots, every one empty, so
the EMPTY reading is the common case: it is a reading of nothing delivered and
is published as an empty mapping, never as None. None is reserved for "no
reading": no elevator, two elevators, an input reference that does not land on
exactly one record, or a carrier whose stacks do not read.

ONE UNREADABLE STACK WITHHOLDS THE WHOLE READING. A count published short of
one stack would understate what was delivered, and nothing downstream could
tell (non-negotiable 7), so the reader publishes no reading rather than a
partial one.

SYNTHETIC ONLY - every fixture comes from ``tests/save/elevator_synthetic.py``.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Final

import pytest

from clockspeed.save import objects, world
from tests.save import elevator_synthetic as es
from tests.save import test_world

#: An item outside the shipped ``/Game/`` root - unknown content, the shape a
#: mod's item takes. Invented: no such mod exists.
_MOD_PATH: Final = "/SynthMod/Items/Desc_SynthModPart.Desc_SynthModPart_C"


def _flag_counts(model: world.WorldModel, code: str) -> list[int]:
    """The count of every world warning carrying ``code``, in stream order.

    Args:
        model: The loaded world.
        code: The warning code.

    Returns:
        One count per warning with that code; empty when none was raised.
    """
    return [warning.count for warning in model.warnings if warning.code == code]


#: Units held in each of two stacks of the same item, and one of another.
_FIRST_STACK: Final = 3
_SECOND_STACK: Final = 4
_OTHER_STACK: Final = 5


def _elevator_input(blob: bytes) -> world.ElevatorInput | None:
    """Load a synthetic save and return its published elevator reading.

    Args:
        blob: The save bytes.

    Returns:
        The reading, or None when the world published none.
    """
    return world.load_world_from_bytes(blob).elevator_input


def test_an_elevator_of_empty_slots_publishes_an_empty_reading_and_not_none() -> None:
    """The measured shape: six empty slots read as nothing delivered, a reading."""
    reading = _elevator_input(es.save_blob(slots=es.EMPTY_SLOTS))

    assert reading is not None, "an elevator whose slots are all empty published no reading"
    assert dict(reading.items) == {}
    assert reading.slot_count == len(es.EMPTY_SLOTS)


def test_an_elevator_holding_items_publishes_exact_counts_by_item() -> None:
    """Every stack of one item sums into one exact count; an empty slot adds nothing."""
    slots = (
        (es.PART_A_PATH, _FIRST_STACK),
        ("", 0),
        (es.PART_B_PATH, _OTHER_STACK),
        (es.PART_A_PATH, _SECOND_STACK),
    )
    reading = _elevator_input(es.save_blob(slots=slots))

    assert reading is not None
    assert dict(reading.items) == {
        es.PART_A: Fraction(_FIRST_STACK + _SECOND_STACK),
        es.PART_B: Fraction(_OTHER_STACK),
    }
    kinds = sorted({type(count).__name__ for count in reading.items.values()})
    assert kinds == ["Fraction"]
    assert list(reading.items) == sorted(reading.items)
    assert reading.slot_count == len(slots)


def test_a_world_without_an_elevator_publishes_no_reading() -> None:
    """No elevator is no reading - None, never an empty mapping and never zero.

    AND NO FLAG: this is the control every unread case below is told apart
    from. A world with no elevator raises neither elevator flag.
    """
    model = world.load_world_from_bytes(es.save_blob(manager_tags=()))

    assert model.elevator_input is None
    assert _flag_counts(model, world.WARN_ELEVATOR_INPUT_UNREAD) == []
    assert _flag_counts(model, world.WARN_ELEVATOR_INPUT_STACK_SKIPPED) == []


def test_two_elevators_publish_no_reading_and_claim_neither() -> None:
    """Two elevators are ambiguous; picking one would publish a reading no save made.

    UNAVAILABLE WITH A FLAG (round 3): never silently "no elevator".
    """
    model = world.load_world_from_bytes(es.save_blob(slots=es.EMPTY_SLOTS, elevators=2))

    assert model.elevator_input is None
    assert _flag_counts(model, world.WARN_ELEVATOR_INPUT_UNREAD) == [1]


def test_an_input_reference_that_lands_on_no_record_publishes_no_reading() -> None:
    """An unresolved input reference is never followed, and never read as empty.

    UNAVAILABLE WITH A FLAG (round 3): the elevator is there and its input is
    unread, which is not a world with no elevator.
    """
    blob = es.save_blob(
        slots=es.EMPTY_SLOTS, input_target="Persistent_Level:PersistentLevel.SyntheticNobody_0"
    )
    model = world.load_world_from_bytes(blob)

    assert model.elevator_input is None
    assert _flag_counts(model, world.WARN_ELEVATOR_INPUT_UNREAD) == [1]


@pytest.mark.parametrize(
    "bad_slot",
    [
        (es.PART_A_PATH, 0),
        ("", 3),
        ("Persistent_Level:PersistentLevel.Thing_0", 2),
        (es.PART_A_PATH, -1),
        ("/Game/Synthetic:PersistentLevel.Desc_SynthPartA_C", 2),
        (_MOD_PATH, -1),
    ],
    ids=[
        "class-at-zero",
        "count-without-class",
        "instance-path-item",
        "negative-count",
        "game-rooted-instance-path-item",
        "negative-count-on-an-unknown-item",
    ],
)
def test_one_malformed_stack_withholds_the_whole_reading(bad_slot: tuple[str, int]) -> None:
    """Non-negotiable 7: never a partial count published as the whole one.

    A MALFORMED stack - a count that contradicts its class, or a "class" that
    is a record path - says the carrier is not in the measured shape, so the
    reading is UNAVAILABLE WITH A FLAG rather than partial (round 3): any
    count beside it could be the misread one. The readable stack beside the
    bad one is the control: the same fixture without the bad slot publishes a
    reading and raises no flag, so the None below is the bad slot's doing.
    """
    good = ((es.PART_B_PATH, _OTHER_STACK),)
    control = world.load_world_from_bytes(es.save_blob(slots=good))
    assert control.elevator_input is not None
    assert _flag_counts(control, world.WARN_ELEVATOR_INPUT_UNREAD) == []

    model = world.load_world_from_bytes(es.save_blob(slots=(*good, bad_slot)))

    assert model.elevator_input is None
    assert _flag_counts(model, world.WARN_ELEVATOR_INPUT_UNREAD) == [1]


def test_a_well_formed_stack_of_an_unknown_item_is_skipped_and_flagged() -> None:
    """Unknown content - an item outside the shipped asset root - is flagged and skipped.

    PARTIAL WITH A FLAG (round 3): the stack is well formed, so the counts of
    every shipped item beside it are exact; only the unknown item is left out,
    and the reading says how many stacks it skipped while the world flag
    carries the same count. Never fatal, never silently "no elevator".
    """
    slots = ((es.PART_A_PATH, _FIRST_STACK), (_MOD_PATH, _OTHER_STACK), ("", 0))
    model = world.load_world_from_bytes(es.save_blob(slots=slots))
    reading = model.elevator_input

    assert reading is not None
    assert dict(reading.items) == {es.PART_A: Fraction(_FIRST_STACK)}
    assert reading.skipped_count == 1
    assert reading.slot_count == len(slots)
    assert _flag_counts(model, world.WARN_ELEVATOR_INPUT_STACK_SKIPPED) == [1]
    assert _flag_counts(model, world.WARN_ELEVATOR_INPUT_UNREAD) == []


@pytest.mark.parametrize(
    "inventory_tags",
    [
        (),
        (es.int_array_tag(es.STACKS_PROPERTY, (1, 2)),),
        (es.struct_array_tag(es.STACKS_PROPERTY, "InventoryStack", ()), es.int_tag("x", 1)[:-2]),
    ],
    ids=["no-stack-array", "stacks-not-structs", "carrier-payload-unread"],
)
def test_an_elevator_whose_input_carrier_does_not_read_is_flagged(
    inventory_tags: tuple[bytes, ...],
) -> None:
    """The elevator and its carrier are there and no stack array reads: unread, flagged.

    The carrier writes no stack array, writes one whose elements are not
    stacks, or has a payload that does not read at all. Each is UNAVAILABLE
    WITH A FLAG, never the empty reading of an elevator holding nothing.
    """
    model = world.load_world_from_bytes(
        es.save_blob(slots=es.EMPTY_SLOTS, inventory_tags=inventory_tags)
    )

    assert model.elevator_input is None
    assert _flag_counts(model, world.WARN_ELEVATOR_INPUT_UNREAD) == [1]


def test_the_elevator_carrier_is_reachable_from_the_adr_carrier_table() -> None:
    """The carrier key is the class a SAVE writes, bound to ADR 0016's measured table."""
    measured = test_world._adr_carrier_paths()  # noqa: SLF001
    carrier, name = world.ELEVATOR_INPUT_CARRIER

    assert name in measured, f"ADR 0016's carrier table records no {name}"
    assert objects.class_name_of(measured[name]) == carrier
    assert objects.class_name_of(es.ELEVATOR_CLASS) == carrier


def test_the_elevator_reading_renders_counts_only() -> None:
    """Non-negotiable 12: the reading renders counts, never an item."""
    reading = _elevator_input(es.save_blob(slots=((es.PART_A_PATH, _FIRST_STACK),)))
    assert reading is not None
    rendered = repr(reading)

    assert es.PART_A not in rendered
    assert rendered == "ElevatorInput(items=1, slot_count=1, skipped_count=0)"
