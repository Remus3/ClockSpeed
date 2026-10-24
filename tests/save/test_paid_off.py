"""CS-1348 amended - the save layer publishes the target phase and what is paid off on it.

THE AMENDMENT. A distinct adjudicator read the shipped headers:
``mTargetGamePhasePaidOffCosts`` is an array of ``ItemAmount`` carried with
``SaveGame``, and its elements name NO phase - they belong to whichever phase
``mTargetGamePhase`` names. So the save layer publishes both:
``WorldModel.target_phase`` (the target phase's shipped asset path) and
``WorldModel.paid_off`` (:class:`~clockspeed.save.world.PaidOffReading` - that
phase, as the save's reference names it, to exact Fraction counts).

NEVER A GUESS (non-negotiable 7). No library save writes the paid-off array
(ADR 0016 records the survey), so an ABSENT array publishes None, never
"nothing paid". A present array that does not decode, two carriers, an unread
manager payload, a skipped element, or no readable target phase each publish
None and raise a named warning. A PRESENT empty array is a reading of nothing
paid - the one exact empty this reader publishes.

SYNTHETIC ONLY - every fixture comes from ``tests/save/elevator_synthetic.py``.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Final

import pytest

from clockspeed.save import objects, world
from tests.save import elevator_synthetic as es
from tests.save import synthetic, test_world

#: Amounts paid off on the target phase; the zero is a written reading.
_PAID_A: Final = 2500
_PAID_B: Final = 0

#: How many elements the two-skip arm writes that do not read.
_TWO_SKIPPED: Final = 2


def _model(
    *tags: bytes, extra: tuple[tuple[str, str, tuple[bytes, ...]], ...] = ()
) -> world.WorldModel:
    """Load a synthetic world whose phase manager carries ``tags``.

    Args:
        *tags: The manager's tags, in file order.
        extra: Further actors, as ``(class path, instance, tags)``.

    Returns:
        The loaded world.
    """
    return world.load_world_from_bytes(es.save_blob(manager_tags=tags, extra_actors=extra))


def _flag_counts(model: world.WorldModel, code: str) -> list[int]:
    """The count of every world warning carrying ``code``, in stream order.

    Args:
        model: The loaded world.
        code: The warning code.

    Returns:
        One count per warning with that code; empty when none was raised.
    """
    return [warning.count for warning in model.warnings if warning.code == code]


def _paid_flags(model: world.WorldModel) -> list[tuple[str, int]]:
    """Every paid-off flag the world raised, as ``(code, count)``, in stream order.

    Args:
        model: The loaded world.

    Returns:
        The flags.
    """
    codes = {
        world.WARN_PAID_OFF_UNREAD,
        world.WARN_PAID_OFF_ELEMENT_SKIPPED,
        world.WARN_PAID_OFF_TARGET_UNREAD,
    }
    return [(w.code, w.count) for w in model.warnings if w.code in codes]


def _i32(value: int) -> bytes:
    """One little-endian int32.

    Args:
        value: The integer.

    Returns:
        Its four bytes.
    """
    return value.to_bytes(4, "little", signed=True)


def test_the_paid_off_array_publishes_the_target_phase_to_exact_counts() -> None:
    """CS-1348 amended: the target phase as the save names it, to exact Fractions.

    The zero is KEPT: the save wrote it, so it is a reading of nothing paid on
    that item, never a zero this reader invented.
    """
    lines = ((es.PART_A_PATH, _PAID_A), (es.PART_B_PATH, _PAID_B))
    model = _model(es.target_tag(), es.paid_off_tag(lines))
    reading = model.paid_off

    assert reading is not None
    assert reading.phase == es.TARGET_PHASE
    assert dict(reading.items) == {es.PART_A: Fraction(_PAID_A), es.PART_B: Fraction(_PAID_B)}
    kinds = sorted({type(count).__name__ for count in reading.items.values()})
    assert kinds == ["Fraction"]
    assert list(reading.items) == sorted(reading.items)
    assert model.target_phase == es.TARGET_PATH
    assert _paid_flags(model) == []


def test_an_absent_paid_off_array_publishes_none_never_nothing_paid() -> None:
    """No library save writes the array, so its absence is no reading - and no flag.

    The target phase still publishes: the two carriers are read apart.
    """
    model = _model(es.target_tag())

    assert model.paid_off is None
    assert model.target_phase == es.TARGET_PATH
    assert _paid_flags(model) == []


def test_a_present_empty_array_is_a_reading_of_nothing_paid() -> None:
    """A WRITTEN empty array is a reading: nothing is paid off on the target phase."""
    reading = _model(es.target_tag(), es.paid_off_tag(())).paid_off

    assert reading is not None
    assert reading.phase == es.TARGET_PHASE
    assert dict(reading.items) == {}


@pytest.mark.parametrize(
    "tag",
    [
        synthetic.property_tag(es.PAID_OFF_PROPERTY, "IntProperty", _i32(5)),
        synthetic.property_tag(es.PAID_OFF_PROPERTY, "TextProperty", b"\x00" * 9),
        es.int_array_tag(es.PAID_OFF_PROPERTY, ()),
        synthetic.property_tag(
            es.PAID_OFF_PROPERTY,
            "SetProperty",
            _i32(0) + _i32(0),
            tag_extra=synthetic.fstring("StructProperty"),
        ),
    ],
    ids=["scalar", "unmeasured-type", "empty-int-array", "empty-set-of-structs"],
)
def test_a_paid_off_array_the_reader_cannot_decode_is_flagged_unread(tag: bytes) -> None:
    """Present and undecodable is never absent: None, and the unread flag."""
    model = _model(es.target_tag(), tag)

    assert model.paid_off is None
    assert _paid_flags(model) == [(world.WARN_PAID_OFF_UNREAD, 1)]


def test_two_carriers_of_the_paid_off_array_publish_none_and_flag() -> None:
    """Two managers carrying it are ambiguous: never merged, never one picked."""
    tags = (es.target_tag(), es.paid_off_tag(((es.PART_A_PATH, 1),)))
    second = (
        es.PHASE_MANAGER_CLASS,
        "Persistent_Level:PersistentLevel.SyntheticPhaseManager_1",
        tags,
    )
    model = _model(*tags, extra=(second,))

    assert model.paid_off is None
    assert _paid_flags(model) == [(world.WARN_PAID_OFF_UNREAD, 1)]


def test_an_unread_manager_beside_the_carrier_publishes_none_and_flags() -> None:
    """A second manager whose payload did not read may hold the array too."""
    cut = es.paid_off_tag(((es.PART_A_PATH, 1),))[: -len(synthetic.DECODABLE_TRAILING_RUN) - 1]
    second = (
        es.PHASE_MANAGER_CLASS,
        "Persistent_Level:PersistentLevel.SyntheticPhaseManager_1",
        (cut,),
    )
    model = _model(es.target_tag(), es.paid_off_tag(((es.PART_A_PATH, 1),)), extra=(second,))

    assert model.paid_off is None
    assert _paid_flags(model) == [(world.WARN_PAID_OFF_UNREAD, 1)]


@pytest.mark.parametrize(
    "bad",
    [
        es.item_amount("Persistent_Level:PersistentLevel.Thing_0", 5),
        es.item_amount("/Game/Synthetic:PersistentLevel.Desc_SynthPartA_C", 5),
        es.item_amount(es.PART_A_PATH, -1),
        es.tag_list(
            es.asset_reference_tag("ItemClass", es.PART_A_PATH),
            synthetic.property_tag("Amount", "StrProperty", synthetic.fstring("5")),
        ),
        es.tag_list(es.int_tag("Amount", 5)),
        es.item_amount(es.PART_B_PATH, 3),
    ],
    ids=[
        "instance-path-item",
        "game-rooted-instance-path-item",
        "negative-amount",
        "string-amount",
        "no-item",
        "repeated-item",
    ],
)
def test_a_skipped_element_withholds_the_reading_and_flags_its_count(bad: bytes) -> None:
    """Non-negotiable 7: one element that does not read withholds the whole reading.

    A paid-off reading short of one element would understate what is paid, so
    the reading is None and the flag carries how many elements were skipped.
    The good element beside the bad one is the control: alone, it publishes.
    """
    good = es.item_amount(es.PART_B_PATH, 3)
    control = _model(
        es.target_tag(), es.struct_array_tag(es.PAID_OFF_PROPERTY, "ItemAmount", (good,))
    )
    assert control.paid_off is not None

    tag = es.struct_array_tag(es.PAID_OFF_PROPERTY, "ItemAmount", (good, bad))
    model = _model(es.target_tag(), tag)

    assert model.paid_off is None
    assert _paid_flags(model) == [(world.WARN_PAID_OFF_ELEMENT_SKIPPED, 1)]


def test_every_skipped_element_is_counted() -> None:
    """The flag's count is the number skipped, not a presence bit."""
    bad = es.item_amount(es.PART_A_PATH, -1)
    tag = es.struct_array_tag(es.PAID_OFF_PROPERTY, "ItemAmount", (bad,) * _TWO_SKIPPED)
    model = _model(es.target_tag(), tag)

    assert model.paid_off is None
    assert _paid_flags(model) == [(world.WARN_PAID_OFF_ELEMENT_SKIPPED, _TWO_SKIPPED)]


@pytest.mark.parametrize(
    "target",
    [
        (),
        (es.target_tag("Persistent_Level:PersistentLevel.GP_Planted_0"),),
        (es.target_tag("/Synthetic/GP_X.GP_X"),),
        # Under /Game/ and carrying the level separator: a record, not an asset.
        (es.target_tag("/Game/Synthetic:PersistentLevel.GP_Planted_0"),),
    ],
    ids=["no-target", "instance-path-target", "target-outside-game", "game-rooted-instance-target"],
)
def test_paid_off_with_no_readable_target_phase_publishes_none_and_flags(
    target: tuple[bytes, ...],
) -> None:
    """The elements name no phase, so without a readable target they belong to none."""
    model = _model(*target, es.paid_off_tag(((es.PART_A_PATH, 1),)))

    assert model.paid_off is None
    assert _paid_flags(model) == [(world.WARN_PAID_OFF_TARGET_UNREAD, 1)]
    assert model.target_phase is None


def test_the_target_phase_is_refused_when_it_names_no_shipped_asset() -> None:
    """A target reference to a record instance never crosses the seam."""
    model = _model(es.target_tag("Persistent_Level:PersistentLevel.GP_Planted_0"))

    assert model.target_phase is None
    assert _model().target_phase is None


def test_two_managers_publish_no_target_phase() -> None:
    """Two managers each naming a target are ambiguous; neither is claimed."""
    second = (
        es.PHASE_MANAGER_CLASS,
        "Persistent_Level:PersistentLevel.SyntheticPhaseManager_1",
        (es.target_tag(),),
    )

    assert _model(es.target_tag(), extra=(second,)).target_phase is None


def test_both_carriers_are_reachable_from_the_adr_carrier_table() -> None:
    """Each key is the class a SAVE writes, bound to ADR 0016's measured table."""
    measured = test_world._adr_carrier_paths()  # noqa: SLF001

    for carrier, name in (world.TARGET_PHASE_CARRIER, world.PAID_OFF_CARRIER):
        assert name in measured, f"ADR 0016's carrier table records no {name}"
        assert objects.class_name_of(measured[name]) == carrier


def test_both_carriers_leave_the_unread_list_exactly_when_published() -> None:
    """Each is named unread for as long as no reader publishes it; both are read now."""
    model = _model(es.target_tag(), es.paid_off_tag(((es.PART_A_PATH, 1),)))

    assert model.target_phase is not None
    assert model.paid_off is not None
    assert world.TARGET_PHASE_CARRIER[1] not in world.UNLOCK_CARRIERS_UNREAD
    assert world.PAID_OFF_CARRIER[1] not in world.UNLOCK_CARRIERS_UNREAD
    assert world.WARN_UNLOCK_GRAMMAR_UNMEASURED in {w.code for w in model.warnings}


def test_the_paid_off_reading_renders_counts_only() -> None:
    """Non-negotiable 12: the reading renders counts, never a phase or an item."""
    reading = _model(es.target_tag(), es.paid_off_tag(((es.PART_A_PATH, 1),))).paid_off
    assert reading is not None
    rendered = repr(reading)

    assert es.TARGET_PHASE not in rendered
    assert es.PART_A not in rendered
    assert rendered == "PaidOffReading(items=1)"


def test_two_target_tags_on_one_manager_publish_no_target_phase() -> None:
    """A manager naming two targets is ambiguous: neither is the target, and nothing is paid."""
    model = _model(
        es.target_tag(),
        es.target_tag("/Game/Synthetic/GamePhases/GP_Other.GP_Other"),
        es.paid_off_tag(((es.PART_A_PATH, 1),)),
    )

    assert model.target_phase is None
    assert model.paid_off is None
    assert _paid_flags(model) == [(world.WARN_PAID_OFF_TARGET_UNREAD, 1)]
