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

Every world here is built from ``tests/save/elevator_synthetic.py`` and loaded
through the real save reader, so the arm grades the seam end to end, with no
game install and no save file (CLAUDE.md section 7).
"""

from __future__ import annotations

from fractions import Fraction
from typing import Final

from clockspeed.data.schematics import CostLine
from clockspeed.progress import phases
from clockspeed.save import world
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
    source = phases.SavePhaseCosts(_world(es.DEFAULT_ENTRIES))

    assert phases.phase_costs_available(source) is True


def test_a_world_without_the_array_reads_false_under_a_named_reason() -> None:
    """No array, no table: every figure null under its named reason, never zero."""
    source = phases.SavePhaseCosts(_world(None))
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
    table = phases.SavePhaseCosts(_world(entries)).phase_costs()

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
    source = phases.SavePhaseCosts(_world(((COSTED_PHASE, ((PLATE_PATH, 0),)),)))
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
    source = phases.SavePhaseCosts(_world(((COSTED_PHASE, ((PLATE_PATH, PLATE_COST),)),)))
    cost = phases.phase_cost(source, synthetic_registry(), COSTED_PHASE, selection())

    assert cost.required.values is not None
    assert dict(cost.required.values) == {PLATE_ITEM: Fraction(PLATE_COST, TWO_HOURS_IN_MINUTES)}
    assert cost.machine.values is not None
    assert dict(cost.machine.values) == {CONSTRUCTOR: Fraction(5, 12), SMELTER: Fraction(5, 6)}
    assert cost.phase_costs_available is True
