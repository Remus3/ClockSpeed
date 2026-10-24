"""CS-1340 - the phase model's costs come from the save, under the measured meaning.

WHAT WAS MISSING. ``clockspeed/progress/phases.py`` shipped
``UnmeasuredPhaseCosts``, so every phase published null under an "unmeasured"
reason whatever the world held. The save layer now publishes
``mGamePhaseCosts`` (``clockspeed.save.world.WorldModel.phase_costs``) and
:class:`clockspeed.progress.phases.SavePhaseCosts` builds the table from it, so
``phase_costs_available`` reads True on a world that carries the array and
False, under a named reason, on one that does not.

THE MEASURED MEANING, AND WHAT THE SOURCE DOES WITH IT. ADR 0016 records that
each amount is what the world STILL OWES on that phase. The phase model's
figures are the quantity still to build, so a line the save says is paid -
amount zero - is dropped from the entry, and a phase paid in full publishes an
EMPTY entry, null under ``REASON_EMPTY_COST_ENTRY``: nothing is left to build.
A paid line kept would null its whole phase as a non-positive cost, which
would hide what the phase still owes on its other lines.

CS-1348 - THE DELIVERED READING. The save layer publishes the elevator's input
inventory (``WorldModel.elevator_input``) and the source publishes it as
``PhaseCostTable.delivered``, keyed by every item the entries owe, so an owed
item the elevator holds none of is an exact zero. No elevator is no reading:
None, never zero, and ``delivered_available`` reads False.

Every world here is built from ``tests/save/elevator_synthetic.py`` and loaded
through the real save reader, so the arm grades the seam end to end, with no
game install and no save file (CLAUDE.md section 7).
"""

from __future__ import annotations

from fractions import Fraction
from typing import Final

from clockspeed.data.schematics import CostLine, normalize_schematics
from clockspeed.progress import phases
from clockspeed.save import world
from tests.data.test_schematics import phase_dependency
from tests.progress.test_milestones import KEY_DEPENDENCIES, schematic_document, schematic_entry
from tests.progress.test_phases import (
    CONSTRUCTOR,
    COSTED_PHASE,
    PLATE_COST,
    PLATE_ITEM,
    SMELTER,
    TWO_HOURS_IN_MINUTES,
    selection,
    synthetic_registry,
)
from tests.save import elevator_synthetic as es

#: The synthetic plate as a shipped-shaped asset path whose ClassName is the
#: registry's plate key, so the save's line joins the hand-worked chain.
PLATE_PATH: Final = f"/Game/Synthetic/Parts/Desc_SynthPlate.{PLATE_ITEM}"


#: The phase vocabulary the synthetic install knows: every phase these fixtures
#: cost. The CS-1340 repair arms below pass a narrower one on purpose.
INSTALLED: Final = frozenset({es.PAID_PHASE, es.OWED_PHASE, COSTED_PHASE})


def _source(model: world.WorldModel) -> phases.SavePhaseCosts:
    """The shipped save source over ``model``, against :data:`INSTALLED`.

    Args:
        model: The loaded world.

    Returns:
        The source.
    """
    return phases.SavePhaseCosts(model, INSTALLED)


def _world(entries: tuple[es.PhaseEntry, ...] | None) -> world.WorldModel:
    """Load a synthetic world whose phase manager carries ``entries``, or no array.

    Args:
        entries: The array's entries, or None for a manager without the array.

    Returns:
        The loaded world.
    """
    tags = () if entries is None else (es.phase_costs_tag(entries),)
    return world.load_world_from_bytes(es.save_blob(manager_tags=tags))


def test_phase_costs_available_reads_true_on_a_world_that_carries_the_array() -> None:
    """CS-1340 acceptance: the shipped source reads True from a real reading."""
    source = _source(_world(es.DEFAULT_ENTRIES))

    assert phases.phase_costs_available(source) is True


def test_a_world_without_the_array_reads_false_under_a_named_reason() -> None:
    """No array, no table: every figure null under its named reason, never zero."""
    source = _source(_world(None))
    cost = phases.phase_cost(source, synthetic_registry(), COSTED_PHASE, selection())

    assert phases.phase_costs_available(source) is False
    assert cost.phase_costs_available is False
    assert [cost.machine.reason, cost.miner.reason, cost.resource.reason] == [
        phases.REASON_NO_PHASE_COST_TABLE
    ] * 3
    assert cost.required.values is None
    table = source.phase_costs()
    assert table.entries is None
    assert table.reason == phases.REASON_NO_PHASE_COST_TABLE


def test_the_table_carries_what_is_owed_and_drops_what_is_paid() -> None:
    """The owed lines arrive as exact CostLines; a paid line is not a requirement."""
    entries = (
        (es.PAID_PHASE, ((es.PART_A_PATH, 0),)),
        (es.OWED_PHASE, ((es.PART_A_PATH, 2500), (es.PART_B_PATH, 0), (es.PART_B_PATH, 7))),
    )
    table = _source(_world(entries)).phase_costs()

    assert table.reason is None
    assert table.entries is not None
    assert dict(table.entries) == {
        es.OWED_PHASE: (CostLine(es.PART_A, Fraction(2500)), CostLine(es.PART_B, Fraction(7))),
        es.PAID_PHASE: (),
    }
    kinds = {type(line.amount).__name__ for lines in table.entries.values() for line in lines}
    assert kinds == {"Fraction"}


def test_a_phase_paid_in_full_is_null_as_an_empty_entry_never_a_zero_figure() -> None:
    """A phase with nothing owed has nothing to build, and says so by a reason."""
    source = _source(_world(((COSTED_PHASE, ((PLATE_PATH, 0),)),)))
    cost = phases.phase_cost(source, synthetic_registry(), COSTED_PHASE, selection())

    assert cost.phase_costs_available is True
    assert [cost.machine.reason, cost.miner.reason, cost.resource.reason] == [
        phases.REASON_EMPTY_COST_ENTRY
    ] * 3


def test_an_owed_phase_drives_the_hand_worked_chain_end_to_end() -> None:
    """The save's owed amount reaches the required rate and the three figures.

    The oracle is ``tests/progress/test_phases.py``'s hand-worked chain: 1000
    plates over two hours is 25/3 a minute, which needs 5/12 constructors and
    5/6 smelters. The save carries the amount; nothing here re-derives it.
    """
    source = _source(_world(((COSTED_PHASE, ((PLATE_PATH, PLATE_COST),)),)))
    cost = phases.phase_cost(source, synthetic_registry(), COSTED_PHASE, selection())

    assert cost.required.values is not None
    assert dict(cost.required.values) == {PLATE_ITEM: Fraction(PLATE_COST, TWO_HOURS_IN_MINUTES)}
    assert cost.machine.values is not None
    assert dict(cost.machine.values) == {CONSTRUCTOR: Fraction(5, 12), SMELTER: Fraction(5, 6)}
    assert cost.phase_costs_available is True


# ---------------------------------------------------------------------------
# CS-1348 - the delivered reading comes from the elevator's input inventory
# ---------------------------------------------------------------------------

#: Units of the first part sitting in the elevator's input inventory.
HELD_UNITS: Final = 7


def _elevator_world(
    entries: tuple[es.PhaseEntry, ...] | None, slots: tuple[tuple[str, int], ...] | None
) -> world.WorldModel:
    """Load a synthetic world with a phase-cost array and an elevator, either optional.

    Args:
        entries: The array's entries, or None for a manager without the array.
        slots: The elevator input slots, or None for no elevator.

    Returns:
        The loaded world.
    """
    tags = () if entries is None else (es.phase_costs_tag(entries),)
    return world.load_world_from_bytes(es.save_blob(manager_tags=tags, slots=slots))


def test_delivered_available_reads_true_from_the_elevator_including_a_zero_count() -> None:
    """CS-1348 acceptance: True from the producer, a zero count among the counts.

    The table's delivered mapping is keyed by every item the table's own
    entries owe, so a cost item the elevator holds none of reads an exact
    ZERO rather than going missing - and the item it does hold reads its
    count. Both are exact Fractions.
    """
    held = ((es.PART_A_PATH, HELD_UNITS), *es.EMPTY_SLOTS[1:])
    source = _source(_elevator_world(es.DEFAULT_ENTRIES, held))
    table = source.phase_costs()
    cost = phases.phase_cost(source, synthetic_registry(), COSTED_PHASE, selection())

    assert table.delivered is not None
    assert dict(table.delivered) == {es.PART_A: Fraction(HELD_UNITS), es.PART_B: Fraction(0)}
    kinds = sorted({type(count).__name__ for count in table.delivered.values()})
    assert kinds == ["Fraction"]
    assert cost.delivered_available is True


def test_an_elevator_of_empty_slots_is_a_reading_of_zero_and_reads_true() -> None:
    """The measured shape - every slot empty - is zero delivered, never no reading."""
    source = _source(_elevator_world(es.DEFAULT_ENTRIES, es.EMPTY_SLOTS))
    table = source.phase_costs()
    cost = phases.phase_cost(source, synthetic_registry(), es.OWED_PHASE, selection())

    assert table.delivered is not None
    assert dict(table.delivered) == {es.PART_A: Fraction(0), es.PART_B: Fraction(0)}
    assert cost.delivered_available is True


def test_a_world_with_no_elevator_publishes_none_and_reads_false_never_zero() -> None:
    """No reading is None - not an empty mapping, and not a zero count per item."""
    source = _source(_elevator_world(es.DEFAULT_ENTRIES, None))
    table = source.phase_costs()
    cost = phases.phase_cost(source, synthetic_registry(), es.OWED_PHASE, selection())

    assert table.delivered is None
    assert cost.delivered_available is False
    assert cost.phase_costs_available is True


def test_the_delivered_reading_stands_without_a_phase_cost_table() -> None:
    """The pinned development world's shape: an elevator, and no array.

    The two readings are independent: the flag follows the elevator and
    ``phase_costs_available`` follows the array, so this world reads True
    beside False. With no table there is no cost item to key a zero by, so
    an empty elevator is an empty reading - still present.
    """
    source = _source(_elevator_world(None, es.EMPTY_SLOTS))
    table = source.phase_costs()
    cost = phases.phase_cost(source, synthetic_registry(), COSTED_PHASE, selection())

    assert table.entries is None
    assert table.delivered is not None
    assert dict(table.delivered) == {}
    assert cost.delivered_available is True
    assert cost.phase_costs_available is False


def test_a_delivered_reading_takes_nothing_off_the_required_figure() -> None:
    """The model subtracts no delivered reading: the owed amount drives the rate alone."""
    held = ((PLATE_PATH, HELD_UNITS),)
    source = _source(_elevator_world(((COSTED_PHASE, ((PLATE_PATH, PLATE_COST),)),), held))
    cost = phases.phase_cost(source, synthetic_registry(), COSTED_PHASE, selection())

    assert cost.delivered_available is True
    assert cost.required.values is not None
    assert dict(cost.required.values) == {PLATE_ITEM: Fraction(PLATE_COST, TWO_HOURS_IN_MINUTES)}


# ---------------------------------------------------------------------------
# CS-1340 repair - unread and unmapped content is flagged, never authoritative
# ---------------------------------------------------------------------------

#: An installed phase vocabulary that names none of the fixtures' phases - the
#: measured shape of a pre-1.0 table read against the pinned build's docs.
FOREIGN_INSTALL: Final = frozenset({"EGP_SynthInstalledOnly"})

#: How many unreadable elements the all-unreadable fixture writes.
UNREADABLE_ELEMENTS: Final = 2


def _null_reasons(cost: phases.PhaseCost) -> list[str | None]:
    """The three rendered figures' reasons, in A3 key order.

    Args:
        cost: The phase cost.

    Returns:
        The machine, miner and resource reasons.
    """
    return [cost.machine.reason, cost.miner.reason, cost.resource.reason]


def _all_bad_world() -> world.WorldModel:
    """A world whose phase-cost array holds two elements and neither reads.

    Returns:
        The loaded world.
    """
    bad = es.tag_list(
        es.struct_array_tag("cost", "ItemAmount", (es.item_amount(es.PART_A_PATH, 5),))
    )
    tag = es.struct_array_tag(es.PHASE_COSTS_PROPERTY, "PhaseCost", (bad,) * UNREADABLE_ELEMENTS)
    return world.load_world_from_bytes(es.save_blob(manager_tags=(tag,)))


def test_an_array_with_no_readable_entry_is_not_a_usable_table() -> None:
    """Non-negotiable 7: nothing readable is not "a table with no entry for this phase".

    Before the repair this read as available with an empty table, every phase
    "no-cost-entry", and the skip count dropped. Now no table is published, the
    reason names the content as unread, and the table carries the count.
    """
    source = _source(_all_bad_world())
    table = source.phase_costs()
    cost = phases.phase_cost(source, synthetic_registry(), es.OWED_PHASE, selection())

    assert phases.phase_costs_available(source) is False
    assert table.entries is None
    assert table.reason == phases.REASON_PHASE_COSTS_UNREAD
    assert table.skipped_count == UNREADABLE_ELEMENTS
    assert _null_reasons(cost) == [phases.REASON_PHASE_COSTS_UNREAD] * 3


def test_a_phase_missing_beside_a_skipped_entry_is_unread_not_absent() -> None:
    """A phase the table lacks while an entry was skipped may BE the skipped one.

    The readable phase still costs; the missing one says its entry may be the
    unread one, and the table carries the skip count, never dropped.
    """
    bad = es.tag_list(
        es.enum_byte_tag("gamePhase", "EGamePhase", es.PAID_PHASE),
        es.int_array_tag("cost", (5,)),
    )
    tag = es.struct_array_tag(
        es.PHASE_COSTS_PROPERTY,
        "PhaseCost",
        (es.phase_cost(es.OWED_PHASE, ((es.PART_A_PATH, 3),)), bad),
    )
    source = _source(world.load_world_from_bytes(es.save_blob(manager_tags=(tag,))))
    table = source.phase_costs()
    missing = phases.phase_cost(source, synthetic_registry(), es.PAID_PHASE, selection())

    assert table.entries is not None
    assert sorted(table.entries) == [es.OWED_PHASE]
    assert table.skipped_count == 1
    assert _null_reasons(missing) == [phases.REASON_COST_ENTRY_UNREAD] * 3
    assert missing.phase_costs_available is True


def test_an_array_present_but_unreadable_as_one_reads_unread_not_unwritten() -> None:
    """The save layer's unread flag reaches the reason; "no table" is kept for no array."""
    garbled = world.load_world_from_bytes(
        es.save_blob(manager_tags=(es.int_tag(es.PHASE_COSTS_PROPERTY, 5),))
    )
    unwritten = world.load_world_from_bytes(es.save_blob(manager_tags=()))

    assert _source(garbled).phase_costs().reason == phases.REASON_PHASE_COSTS_UNREAD
    assert _source(unwritten).phase_costs().reason == phases.REASON_NO_PHASE_COST_TABLE


def test_a_table_naming_no_installed_phase_is_not_authoritative() -> None:
    """A pre-1.0 table read against an install that knows none of its phases.

    The measured case: a save carrying ``EGP_`` phases the pinned build's docs
    do not name. No table is presented, every phase is null under the unmapped
    reason, and the table names which phases were withheld - never silently
    treated as the current phases, and never mapped onto them.
    """
    source = phases.SavePhaseCosts(_world(es.DEFAULT_ENTRIES), FOREIGN_INSTALL)
    table = source.phase_costs()
    cost = phases.phase_cost(source, synthetic_registry(), es.OWED_PHASE, selection())

    assert phases.phase_costs_available(source) is False
    assert table.entries is None
    assert table.reason == phases.REASON_UNMAPPED_PHASE
    assert table.unmapped == frozenset({es.PAID_PHASE, es.OWED_PHASE})
    assert _null_reasons(cost) == [phases.REASON_UNMAPPED_PHASE] * 3


def test_an_unmapped_phase_beside_a_mapped_one_is_withheld_and_named() -> None:
    """Only the phases the install knows are presented; the others are flagged by name."""
    source = phases.SavePhaseCosts(_world(es.DEFAULT_ENTRIES), frozenset({es.OWED_PHASE}))
    table = source.phase_costs()
    withheld = phases.phase_cost(source, synthetic_registry(), es.PAID_PHASE, selection())

    assert table.entries is not None
    assert sorted(table.entries) == [es.OWED_PHASE]
    assert table.unmapped == frozenset({es.PAID_PHASE})
    assert _null_reasons(withheld) == [phases.REASON_UNMAPPED_PHASE] * 3


def test_a_part_the_install_does_not_know_is_null_under_its_own_reason() -> None:
    """A mapped phase owing an item the registry lacks is null, never solved without it."""
    source = _source(_world(((COSTED_PHASE, ((es.PART_A_PATH, 9),)),)))
    cost = phases.phase_cost(source, synthetic_registry(), COSTED_PHASE, selection())

    assert _null_reasons(cost) == [phases.REASON_UNRESOLVED_COST_ITEM] * 3
    assert cost.machine.detail == es.PART_A


def test_the_installed_phases_are_the_catalog_phase_dependency_tokens() -> None:
    """The vocabulary a source checks against is read off the installed schematics.

    One synthetic schematic gates on a phase and one gates on none, so the
    vocabulary is exactly the one token - never a token invented here.
    """
    catalog = normalize_schematics(
        schematic_document(
            [
                schematic_entry(
                    "Schematic_SynthPhaseGated_C",
                    **{KEY_DEPENDENCIES: [phase_dependency(COSTED_PHASE)]},
                ),
                schematic_entry("Schematic_SynthUngated_C"),
            ]
        )
    )

    assert phases.installed_phases(catalog) == frozenset({COSTED_PHASE})
