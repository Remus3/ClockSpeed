"""CS-1340 - the save layer publishes ``mGamePhaseCosts`` as an exact phase-cost table.

WHAT WAS MISSING. ADR 0016 found ``mGamePhaseCosts`` on the game phase manager
and nothing read it: ``clockspeed/save/world.py`` published no phase cost, so
``clockspeed/progress/phases.py`` shipped an unmeasured source and every phase
published null. CS-1340 measured the array on work copies of the local library
(the measurement and its limits are recorded in ADR 0016, names and counts
only) and wires it here.

WHAT AN AMOUNT MEANS IS ADR 0016's FACT, not this module's: each ``Amount`` is
the quantity the world STILL OWES on that phase - a phase the save's own phase
token says was reached reads zero on every line. These arms grade the reader,
not the meaning: every published amount is an exact ``Fraction``, zero kept,
and a world that writes no array publishes NO TABLE - None, never an empty
reading and never a zero one.

SYNTHETIC ONLY. Every fixture comes from ``tests/save/elevator_synthetic.py``,
hand-authored in the measured grammar.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Final

import pytest

from clockspeed.save import objects, world
from tests.save import elevator_synthetic as es
from tests.save import synthetic, test_world

#: A phase token in the measured shape, for the arms that need a third phase.
_THIRD_PHASE: Final = "EGP_SynthPhaseThird"

#: Both copies of a phase written twice are counted as skipped.
_BOTH_COPIES: Final = 2


def _phase_costs(blob: bytes) -> world.PhaseCostReading | None:
    """Load a synthetic save and return its published phase-cost reading.

    Args:
        blob: The save bytes.

    Returns:
        The reading, or None when the world published no table.
    """
    return world.load_world_from_bytes(blob).phase_costs


def _amounts(reading: world.PhaseCostReading, phase: str) -> list[tuple[str, Fraction]]:
    """One phase's lines as ``(item class, amount)`` pairs, in file order.

    Args:
        reading: The published reading.
        phase: The phase token.

    Returns:
        The pairs.
    """
    return [(line.item_class, line.amount) for line in reading.by_phase[phase]]


def test_a_world_carrying_the_array_publishes_every_amount_as_an_exact_fraction() -> None:
    """CS-1340 acceptance: each decoded cost amount is an exact Fraction.

    The paid phase's zero is KEPT as ``Fraction(0)`` - a reading of nothing
    owed is a reading, and dropping it would make a paid line read as absent.
    The type is asserted exactly, so an ``int`` (and a ``bool``, which is one)
    reddens here rather than passing an equality against a Fraction.
    """
    reading = _phase_costs(es.save_blob(manager_tags=(es.phase_costs_tag(),)))

    assert reading is not None, "the world carries the array and published no table"
    assert sorted(reading.by_phase) == sorted([es.PAID_PHASE, es.OWED_PHASE])
    assert _amounts(reading, es.PAID_PHASE) == [(es.PART_A, Fraction(0))]
    assert _amounts(reading, es.OWED_PHASE) == [
        (es.PART_A, Fraction(2500)),
        (es.PART_B, Fraction(100)),
    ]
    kinds = sorted(
        {type(line.amount).__name__ for lines in reading.by_phase.values() for line in lines}
    )
    assert kinds == ["Fraction"]
    assert reading.skipped_count == 0


def test_a_world_without_the_array_publishes_no_table_rather_than_an_empty_one() -> None:
    """CS-1340 acceptance: no array, no table - None, never empty and never zero.

    The control is the phase manager itself, PRESENT and carrying the phase
    reference the pinned development world carries: the record is there and
    read, only the array is absent. That is the shape every 1.0-native save in
    the library has (ADR 0016), so an empty reading here would be the
    confident wrong answer on exactly the world this project plays.
    """
    manager_only = (
        es.asset_reference_tag("mCurrentGamePhase", "/Game/Synthetic/GP_Synth.GP_Synth_C"),
    )
    model = world.load_world_from_bytes(es.save_blob(manager_tags=manager_only))

    present = [
        index
        for index, record in enumerate(model.objects.records)
        if objects.class_name_of(record.type_path) == world.PHASE_COST_CARRIER[0]
    ]
    assert len(present) == 1, "the control's phase manager record is missing"
    assert model.properties.by_record_index[present[0]].payload_read
    assert model.phase_costs is None


def test_a_world_with_no_phase_manager_publishes_no_table() -> None:
    """No carrier record at all is the same answer as a carrier without the array."""
    assert _phase_costs(es.save_blob(manager_tags=None, slots=es.EMPTY_SLOTS)) is None


def test_an_empty_array_publishes_an_empty_reading_and_not_none() -> None:
    """A PRESENT array with no element is a reading of no phase - it is not absence."""
    reading = _phase_costs(es.save_blob(manager_tags=(es.phase_costs_tag(()),)))

    assert reading is not None
    assert dict(reading.by_phase) == {}
    assert reading.skipped_count == 0


def test_the_array_on_another_owner_is_not_read() -> None:
    """THE SECOND-OWNER TRAP, carried over from the unlock carriers.

    The match is on the owning class AND the property name together, so the
    same tag on a class no save writes it on contributes nothing.
    """
    stranger = (
        es.STRANGER_CLASS,
        "Persistent_Level:PersistentLevel.Stranger_0",
        (es.phase_costs_tag(),),
    )
    blob = es.save_blob(manager_tags=(), extra_actors=(stranger,))

    assert _phase_costs(blob) is None


def test_two_carrier_arrays_publish_no_table_and_claim_neither() -> None:
    """Two phase managers each carrying the array are ambiguous, never merged or picked."""
    second = (
        es.PHASE_MANAGER_CLASS,
        "Persistent_Level:PersistentLevel.SyntheticPhaseManager_1",
        (es.phase_costs_tag(),),
    )
    blob = es.save_blob(manager_tags=(es.phase_costs_tag(),), extra_actors=(second,))

    assert _phase_costs(blob) is None


@pytest.mark.parametrize(
    "bad_entry",
    [
        # A phase token outside the measured EGP_ shape is world content, not vocabulary.
        es.tag_list(
            es.enum_byte_tag("gamePhase", "EGamePhase", "Persistent_Level:Planted"),
            es.struct_array_tag("cost", "ItemAmount", (es.item_amount(es.PART_A_PATH, 5),)),
        ),
        # No phase token at all.
        es.tag_list(
            es.struct_array_tag("cost", "ItemAmount", (es.item_amount(es.PART_A_PATH, 5),))
        ),
        # An item named by a record instance path, not a shipped asset path.
        es.tag_list(
            es.enum_byte_tag("gamePhase", "EGamePhase", _THIRD_PHASE),
            es.struct_array_tag(
                "cost",
                "ItemAmount",
                (es.item_amount("Persistent_Level:PersistentLevel.Thing_0", 5),),
            ),
        ),
        # A negative amount is no quantity anyone can owe.
        es.tag_list(
            es.enum_byte_tag("gamePhase", "EGamePhase", _THIRD_PHASE),
            es.struct_array_tag("cost", "ItemAmount", (es.item_amount(es.PART_A_PATH, -1),)),
        ),
        # An amount carried as a string is not a count.
        es.tag_list(
            es.enum_byte_tag("gamePhase", "EGamePhase", _THIRD_PHASE),
            es.struct_array_tag(
                "cost",
                "ItemAmount",
                (
                    es.tag_list(
                        es.asset_reference_tag("ItemClass", es.PART_A_PATH),
                        synthetic.property_tag("Amount", "StrProperty", synthetic.fstring("5")),
                    ),
                ),
            ),
        ),
    ],
    ids=["unshaped-token", "no-token", "instance-path-item", "negative-amount", "string-amount"],
)
def test_an_unreadable_entry_is_skipped_and_counted_never_fatal(bad_entry: bytes) -> None:
    """Non-negotiable 7: unknown content is flagged and skipped, never fatal.

    The WHOLE entry is skipped rather than published short of a line: a phase
    published without one of its cost lines would understate what it owes, and
    nothing downstream could tell. The readable entries beside it still arrive,
    so a reader that discarded the whole array on one bad entry reddens too.
    """
    tag = es.struct_array_tag(
        es.PHASE_COSTS_PROPERTY,
        "PhaseCost",
        (es.phase_cost(es.OWED_PHASE, ((es.PART_A_PATH, 3),)), bad_entry),
    )
    reading = _phase_costs(es.save_blob(manager_tags=(tag,)))

    assert reading is not None
    assert sorted(reading.by_phase) == [es.OWED_PHASE]
    assert _amounts(reading, es.OWED_PHASE) == [(es.PART_A, Fraction(3))]
    assert reading.skipped_count == 1


def test_a_phase_written_twice_is_dropped_and_counted_never_merged() -> None:
    """Two entries for one phase are ambiguous: neither is published, both are counted."""
    entries = (
        (es.OWED_PHASE, ((es.PART_A_PATH, 3),)),
        (_THIRD_PHASE, ((es.PART_B_PATH, 4),)),
        (es.OWED_PHASE, ((es.PART_A_PATH, 9),)),
    )
    reading = _phase_costs(es.save_blob(manager_tags=(es.phase_costs_tag(entries),)))

    assert reading is not None
    assert sorted(reading.by_phase) == [_THIRD_PHASE]
    assert reading.skipped_count == _BOTH_COPIES


def test_the_phase_cost_carrier_is_reachable_from_the_adr_carrier_table() -> None:
    """THE CONTROL WHOSE ABSENCE LET A ZERO-MATCH UNLOCK READER SHIP (CS-1039).

    The carrier key is the class a SAVE writes, measured into ADR 0016's
    carrier table. This arm parses that table with the unlock arm's own parser
    and asserts the key pairs that class with that property - so a key naming
    a C++ declaring class reddens here rather than passing every fixture and
    matching nothing on a real world.
    """
    measured = test_world._adr_carrier_paths()  # noqa: SLF001
    carrier, name = world.PHASE_COST_CARRIER

    assert name in measured, f"ADR 0016's carrier table records no {name}"
    assert objects.class_name_of(measured[name]) == carrier
    assert objects.class_name_of(es.PHASE_MANAGER_CLASS) == carrier


def test_the_array_leaves_the_unread_list_exactly_when_it_is_published() -> None:
    """CS-1340 acceptance: named unread for as long as the reader does not publish it.

    The reader now publishes it, so the name has left
    :data:`~clockspeed.save.world.UNLOCK_CARRIERS_UNREAD`; the published table
    above is what makes that true rather than a list edit. The warning still
    rides on every load, because the other unread carriers are still unread.
    """
    model = world.load_world_from_bytes(es.save_blob(manager_tags=(es.phase_costs_tag(),)))

    published = model.phase_costs is not None
    listed = world.PHASE_COST_CARRIER[1] in world.UNLOCK_CARRIERS_UNREAD
    assert published
    assert listed is not published
    assert world.WARN_UNLOCK_GRAMMAR_UNMEASURED in {warning.code for warning in model.warnings}


def test_the_phase_cost_reading_renders_counts_only() -> None:
    """Non-negotiable 12: the reading renders counts, never a token or an item."""
    reading = _phase_costs(es.save_blob(manager_tags=(es.phase_costs_tag(),)))
    assert reading is not None
    line = reading.by_phase[es.OWED_PHASE][0]

    for rendered in (repr(reading), repr(line)):
        leaked = [
            text
            for text in (es.PAID_PHASE, es.OWED_PHASE, es.PART_A, es.PART_B)
            if text in rendered
        ]
        assert leaked == []
    assert repr(reading) == "PhaseCostReading(phases=2, lines=3, skipped_count=0)"
