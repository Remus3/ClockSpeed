"""CS-1043 - the space-elevator phase cost: distinct keys, and null over zero.

The acceptance clause these arms answer: a phase cost renders machine, miner
and resource as DISTINCT KEYS, and a phase with no cost entry is NULL rather
than zero.

EVERY FIXTURE IS HAND-AUTHORED AND OBVIOUSLY SYNTHETIC - an asset path under an
invented directory, an invented trailing token and an invented amount. Nothing
here opens a save, a docs file or the game install, which is the first rule of
``tests/progress/__init__.py``.

THE ITEM KEYS ARE NOT WRITTEN BY HAND, AND THAT IS THE POINT OF THE BLOB. The
distinct-keys property has to be graded over the SHIPPED key rule rather than a
rule this module invented beside it, so every fixture cost is built by handing
a synthetic blob to ``clockspeed.data.blobs.parse_item_amounts`` and letting it
derive each ``item_key`` exactly as it does for shipped data. A hand-written
key would make these arms agree with themselves and with nothing else.

THE NULL ARM CARRIES ITS OWN DISCRIMINATING CONTROL. An ``is None`` assertion
for an absent phase passes unchanged against a function that returns None for
every input, so the same arm asserts that a phase which IS a key, with an empty
cost sequence, publishes a model carrying no entry. An absent phase and a phase
that costs nothing are different answers and the pair is what separates them.

THE DELIVERY FLAG IS GRADED IN BOTH DIRECTIONS. A stored ``False`` satisfies the
false half forever, so the true half is built from an entry whose delivered
count is ZERO - which also reddens a derivation that asks whether that count is
truthy instead of whether it is present.
"""

from __future__ import annotations

from typing import Final

from clockspeed.data.blobs import ItemAmount, parse_item_amounts
from clockspeed.progress.phases import (
    WARN_PHASE_COST_ITEM_DUPLICATED,
    WARN_PHASE_COST_ITEM_UNREADABLE,
    PhaseCost,
    PhaseCostEntry,
    phase_cost_of,
)

#: The invented directory root every synthetic path below shares. It is the
#: probe the repr arm greps for, so it must appear in no shipped path.
SYNTHETIC_ROOT: Final = "/Game/CsSynth/"

#: A synthetic phase asset path in the shape ADR 0016 measured
#: ``mCurrentGamePhase`` to carry - an object reference naming a ``GP_*`` asset.
PHASE: Final = "/Game/CsSynth/Phases/GP_CsSynthPhase.GP_CsSynthPhase_C"

#: A second synthetic phase path that no fixture here ever makes a key of.
ABSENT_PHASE: Final = "/Game/CsSynth/Phases/GP_CsSynthAbsent.GP_CsSynthAbsent_C"

#: A machine descriptor, a miner descriptor and a resource descriptor, each
#: under a DIFFERENT invented directory and each with a DIFFERENT trailing
#: token, so a model that keyed by directory - or collapsed the three into one
#: bucket - cannot satisfy the distinct-keys arm. The trailing single quote is
#: the ``Type'Path'`` wrapper's own, kept so the shipped key rule's quote strip
#: is exercised rather than assumed.
MACHINE_PATH: Final = "/Game/CsSynth/Machines/Desc_CsAssembler.Desc_CsAssembler_C'"
MINER_PATH: Final = "/Game/CsSynth/Miners/Desc_CsMinerMk7.Desc_CsMinerMk7_C'"
RESOURCE_PATH: Final = "/Game/CsSynth/Resources/Desc_CsSynthOre.Desc_CsSynthOre_C'"

#: A fourth path, under a fourth directory, whose trailing token is the SAME as
#: the machine descriptor's. This is the duplicate-key fixture, and it is a
#: different PATH on purpose: two entries sharing a key is the interesting case
#: and two identical entries is not.
DUPLICATE_PATH: Final = "/Game/CsSynth/Duplicates/Desc_CsAssembler.Desc_CsAssembler_C'"

#: What the shipped key rule derives from each path above - the token after the
#: final dot with the wrapper quote stripped.
MACHINE_KEY: Final = "Desc_CsAssembler_C"
MINER_KEY: Final = "Desc_CsMinerMk7_C"
RESOURCE_KEY: Final = "Desc_CsSynthOre_C"

#: Three different amounts, so a model that summed two buckets, or read one
#: entry's amount for another's, lands on a value the dict equality rejects.
MACHINE_AMOUNT: Final = 4
MINER_AMOUNT: Final = 9
RESOURCE_AMOUNT: Final = 17


def _blob(*entries: tuple[str, int]) -> str:
    """Wrap synthetic item-amount entries in the measured blob grammar."""
    inner = ",".join(f'(ItemClass="{path}",Amount={amount})' for path, amount in entries)
    return f"({inner})"


def _machine_miner_resource() -> tuple[ItemAmount, ...]:
    """One machine, one miner and one resource descriptor, keys derived."""
    return parse_item_amounts(
        _blob(
            (MACHINE_PATH, MACHINE_AMOUNT),
            (MINER_PATH, MINER_AMOUNT),
            (RESOURCE_PATH, RESOURCE_AMOUNT),
        )
    )


def test_a_phase_cost_renders_machine_miner_and_resource_as_distinct_keys() -> None:
    """Catches a cost model that collapses distinct descriptors into one bucket.

    Graded by DICT EQUALITY against a three-key literal rather than by three
    membership checks: a model that summed two descriptors into one key, or
    keyed by the directory instead of the shipped trailing token, satisfies
    every membership check and dies here.
    """
    items = _machine_miner_resource()
    cost = phase_cost_of(PHASE, {PHASE: items})
    assert cost is not None
    required = dict(cost.required_by_item)
    assert required == {
        MACHINE_KEY: MACHINE_AMOUNT,
        MINER_KEY: MINER_AMOUNT,
        RESOURCE_KEY: RESOURCE_AMOUNT,
    }
    entry_count = len(cost.entries)
    assert entry_count == len(items)


def test_a_phase_with_no_cost_entry_is_null_rather_than_zero() -> None:
    """Catches an absent phase answered with a zero-valued cost, and the inverse.

    The ``is None`` half alone passes against a function that returns None for
    every input, so the discriminating control sits in the same arm: a phase
    that IS a key, carrying an empty cost sequence, publishes a model with no
    entry in it rather than nothing at all.
    """
    absent = phase_cost_of(ABSENT_PHASE, {})
    assert absent is None
    present = phase_cost_of(PHASE, {PHASE: ()})
    assert present is not None
    entry_count = len(present.entries)
    assert entry_count == 0


def test_the_delivery_flag_is_derived_from_the_entries_rather_than_written() -> None:
    """Catches a stored ``False`` standing in for an unread delivered count.

    The false half passes forever against a literal field, so the true half is
    built from an entry whose delivered count is ZERO. That value also reddens
    a derivation that asks whether the count is truthy instead of whether it is
    present, which is the same collapse one field over.
    """
    undelivered = phase_cost_of(PHASE, {PHASE: _machine_miner_resource()})
    assert undelivered is not None
    unavailable = undelivered.delivered_available
    assert unavailable is False
    delivered = PhaseCost(
        phase=PHASE,
        entries=(
            PhaseCostEntry(
                item_key=MACHINE_KEY,
                raw_path=MACHINE_PATH,
                required=MACHINE_AMOUNT,
                delivered=0,
            ),
        ),
        warnings=(),
    )
    available = delivered.delivered_available
    assert available is True


def test_a_duplicated_item_key_is_flagged_and_keeps_the_first_amount() -> None:
    """Catches a repeated item key silently summed, and one silently dropped.

    Two entries under different directories whose shipped trailing token is the
    same one. The mapping keeps the FIRST amount - the module docstring records
    why summing would be an arithmetic nothing in this project has measured -
    and the WARNING is asserted rather than only the shortened mapping, because
    a mapping short by one entry with no flag on it is exactly the silent
    wrong-answer defect the fourth rule of ``tests/progress/__init__.py`` names.
    """
    items = parse_item_amounts(
        _blob(
            (MACHINE_PATH, MACHINE_AMOUNT),
            (DUPLICATE_PATH, MINER_AMOUNT),
        )
    )
    cost = phase_cost_of(PHASE, {PHASE: items})
    assert cost is not None
    required = dict(cost.required_by_item)
    assert required == {MACHINE_KEY: MACHINE_AMOUNT}
    entry_count = len(cost.entries)
    assert entry_count == len(items)
    codes = [warning.code for warning in cost.warnings]
    assert WARN_PHASE_COST_ITEM_DUPLICATED in codes


def test_a_cost_element_of_the_wrong_type_is_flagged_and_skipped() -> None:
    """Catches an unmodelled cost element crashing, and one dropped in silence.

    Non-negotiable 7: unknown game content is flagged and skipped, never fatal
    and never silently wrong. The readable siblings either side of the bad
    element are the control that the skip is PER ELEMENT rather than wholesale,
    and the warning is asserted rather than only the shortened mapping.
    """
    items = _machine_miner_resource()
    cost = phase_cost_of(PHASE, {PHASE: (items[0], MACHINE_PATH, items[1])})
    assert cost is not None
    required = dict(cost.required_by_item)
    assert required == {MACHINE_KEY: MACHINE_AMOUNT, MINER_KEY: MINER_AMOUNT}
    codes = [warning.code for warning in cost.warnings]
    assert WARN_PHASE_COST_ITEM_UNREADABLE in codes


def test_no_asset_path_renders_in_the_repr() -> None:
    """Catches a phase path or a cost item path reaching a rendered line.

    Non-negotiables 11 and 12: a path may cross this seam and may not reach a
    repr, a log line or an exception, and a test runner reprs a value before a
    human chooses what to print. The entry list is the control that a path WAS
    there to leak - an empty model renders nothing either way, so the arm would
    pass on a model that had never read anything.
    """
    cost = phase_cost_of(PHASE, {PHASE: _machine_miner_resource()})
    assert cost is not None
    rendered = repr(cost)
    leaked = SYNTHETIC_ROOT in rendered
    assert leaked is False
    carried = any(SYNTHETIC_ROOT in entry.raw_path for entry in cost.entries)
    assert carried is True
