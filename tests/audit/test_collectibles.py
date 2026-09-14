"""CS-1042: what is still out there to collect - the subtraction, and its conservation.

Every fixture here is a hand-built synthetic ``WorldModel``. Nothing in this
module opens a save, a docs file or the install, and nothing here needs the game
to be present - see ``tests/audit/__init__.py`` for the four rules.

THE ARM THAT MATTERS GRADES THE SUBTRACTION AND NOT THE PLOTTING. The save's
collectable section records what has ALREADY BEEN COLLECTED, so UNCOLLECTED is
the live records carrying transforms MINUS those pairs. An arm asserting only
that three collectibles render passes on an implementation that ignores the
collected list entirely, which is the whole defect - so
``test_the_collected_pair_is_subtracted_and_exactly_the_other_two_are_served``
names the two survivors by CLASS and holds the third at zero.

THE PARTITION IS THE SECOND HALF, AND IT IS WHY A COUNT WOULD NOT DO. Some pairs
carry an EMPTY instance half, published as ``""`` with no Optional and no flag,
so a consumer joining on ``instance_name`` treats it as an ordinary non-match and
cannot detect that it dropped the row. An Optional, a flag and a count are each
individually IGNORABLE. What is graded here instead is a partition with
conservation: every collectable row lands in exactly one bucket, the arm asserts
``joinable + unjoinable == len(collectables)``, and
``test_a_partition_that_drops_a_row_cannot_be_constructed`` shows that a
non-conserving partition is not a value this layer can build at all.

AND THE EMPTY HALF IS NOT ALLOWED TO SUBTRACT ANYTHING.
``test_an_empty_instance_half_subtracts_no_record``
is the one arm with a fixture only that check can refuse: a live actor whose own
instance name is the empty string, beside a collected pair whose instance half is
also empty. An implementation that keys the subtraction on every pair's second
string joins those two and deletes a live row from the world.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import fields, is_dataclass
from typing import Final

import pytest

from clockspeed.audit import collectibles, placement
from clockspeed.save import objects, world
from clockspeed.save.header import SaveHeader
from clockspeed.save.world import EMPTY_UNLOCK_STATE, WorldModel

# An invented 22-character base64url literal. Never a real world token.
SYNTHETIC_TOKEN = "ClockspeedAuditToken1"  # noqa: S105 - an invented marker, not a secret

#: Planted in the INPUT so the refusal walk has a control that it can see one.
INSTANCE_NAME_MARKER: Final = "SyntheticInstanceNameMarkerZv44"
PATH_MARKER: Final = "SyntheticPathMarkerZv44"
LEVEL_NAME_MARKER: Final = "SyntheticLevelNameMarkerZv44"

#: Three allowlisted collectible classes, distinct so the served population can
#: be named by class rather than counted in a pool.
CRYSTAL_CLASS: Final = "BP_Crystal_C"
SHRINE_CLASS: Final = "BP_MercerShrine_C"
DROP_POD_CLASS: Final = "BP_DropPod_C"

#: A class this view does not serve. A conveyor is built rather than collected,
#: and it is the population ``clockspeed/audit/footprint.py`` exists for.
OFF_LIST_CLASS: Final = "Build_ConveyorBeltMk1_C"

IDENTITY_ROTATION: Final = (0.0, 0.0, 0.0, 1.0)
IDENTITY_SCALE: Final = (1.0, 1.0, 1.0)

#: Named so an arm states its expectation rather than comparing two collections
#: that could both be empty.
TWO_SURVIVORS: Final = 2
THREE_ROWS: Final = 3


def header() -> SaveHeader:
    """Build a synthetic header carrying no operator-authored string at all.

    Returns:
        The header.
    """
    return SaveHeader(
        header_version=14,
        save_version=52,
        build_changelist=0,
        map_name="SyntheticMap",
        world_token=SYNTHETIC_TOKEN,
        play_duration=0,
        datetime_ticks=0,
        byte_after_datetime_ticks=0,
        editor_object_version=0,
        is_modded=0,
        body_offset=0,
        warnings=(),
    )


def actor(
    type_path: str,
    translation: tuple[float, float, float] | None,
    *,
    instance_name: str = INSTANCE_NAME_MARKER,
) -> objects.ObjectRecord:
    """Build one synthetic actor record.

    Args:
        type_path: The class path, namespaced or bare.
        translation: The placement, or None for a record carrying no transform.
        instance_name: The instance name. Defaults to the refusal marker, so a
            fixture plants it without having to say so.

    Returns:
        The record.
    """
    transform = (
        None
        if translation is None
        else objects.Transform(
            rotation=IDENTITY_ROTATION,
            translation=translation,
            scale=IDENTITY_SCALE,
        )
    )
    return objects.ObjectRecord(
        kind=objects.KIND_ACTOR,
        type_path=type_path,
        root_object=PATH_MARKER,
        instance_name=instance_name,
        transform=transform,
        parent=None,
        object_type=1,
        was_placed_in_level=0,
        body_offset=0,
        body_length=0,
    )


def collected(instance_name: str) -> objects.Collectable:
    """Build one synthetic collected pair naming an actor instance.

    Args:
        instance_name: The pair's second string - the half a consumer joins on.

    Returns:
        The pair.
    """
    return objects.Collectable(level_name=LEVEL_NAME_MARKER, instance_name=instance_name)


def table(
    records: tuple[objects.ObjectRecord, ...],
    pairs: tuple[objects.Collectable, ...] = (),
    *,
    level_count: int = 1,
) -> objects.ObjectTable:
    """Build a synthetic object table around the given records and pairs.

    Args:
        records: The records, in order.
        pairs: The collectable entries, in file order.
        level_count: How many levels the walk consumed. 0 is what the FLAT
            reader leaves behind and is this module's provenance control.

    Returns:
        The table.
    """
    return objects.ObjectTable(
        records=records,
        unknown_classes=(),
        warnings=(),
        declared_body_length=0,
        body_consumed=0,
        body_prefix_width=8,
        transform_delta=0,
        save_version=52,
        header_version=14,
        level_count=level_count,
        collectables=pairs,
    )


def world_of(
    records: tuple[objects.ObjectRecord, ...],
    pairs: tuple[objects.Collectable, ...] = (),
    *,
    level_count: int = 1,
) -> WorldModel:
    """Build a synthetic world model holding exactly what a test needs.

    Args:
        records: The object records.
        pairs: The collectable entries.
        level_count: Passed straight through to :func:`table`.

    Returns:
        The model.
    """
    return WorldModel(
        token=SYNTHETIC_TOKEN,
        header=header(),
        objects=table(records, pairs, level_count=level_count),
        unlocks=EMPTY_UNLOCK_STATE,
        nodes=(),
        warnings=(),
    )


def codes(result: collectibles.WorldCollectibles) -> set[str]:
    """The warning codes a result carries.

    Args:
        result: The published model.

    Returns:
        The set of codes.
    """
    return {warning.code for warning in result.warnings}


def reachable(value: object, seen: set[int] | None = None) -> list[object]:
    """Every value reachable from one object, the object itself included.

    STRUCTURAL on purpose: an assertion that named today's field list would pass
    unchanged the day a field is added, which is the defect the refusal arm
    exists to catch.

    Args:
        value: The root.
        seen: Identities already walked, to survive a cycle.

    Returns:
        Every reachable value.
    """
    seen = set() if seen is None else seen
    if id(value) in seen:
        return []
    seen.add(id(value))
    found: list[object] = [value]
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            found.extend(reachable(getattr(value, field.name), seen))
    elif isinstance(value, Mapping):
        for key, item in value.items():
            found.extend(reachable(key, seen))
            found.extend(reachable(item, seen))
    elif isinstance(value, (list, tuple, set, frozenset)):
        for item in value:
            found.extend(reachable(item, seen))
    return found


# ---------------------------------------------------------------------------
# The subtraction - the acceptance clause this item exists for
# ---------------------------------------------------------------------------


def test_the_collected_pair_is_subtracted_and_exactly_the_other_two_are_served() -> None:
    model = world_of(
        (
            actor(CRYSTAL_CLASS, (1.0, 2.0, 3.0), instance_name="SyntheticCrystalZv44"),
            actor(SHRINE_CLASS, (4.0, 5.0, 6.0), instance_name="SyntheticShrineZv44"),
            actor(DROP_POD_CLASS, (7.0, 8.0, 9.0), instance_name="SyntheticDropPodZv44"),
        ),
        (collected("SyntheticShrineZv44"),),
    )

    result = collectibles.collectibles_of(model)

    served = dict(result.uncollected_counts)
    assert served == {CRYSTAL_CLASS: 1, DROP_POD_CLASS: 1}, (
        "the collected pair names the shrine, so the shrine must not be served and the"
        " other two must be; a plot-everything implementation serves all three"
    )
    assert len(result.uncollected) == TWO_SURVIVORS
    assert result.records.collected == 1, "the subtraction removed no record"


def test_a_world_whose_collected_list_is_empty_serves_every_collectible() -> None:
    model = world_of(
        (
            actor(CRYSTAL_CLASS, (1.0, 2.0, 3.0), instance_name="SyntheticCrystalZv44"),
            actor(SHRINE_CLASS, (4.0, 5.0, 6.0), instance_name="SyntheticShrineZv44"),
            actor(DROP_POD_CLASS, (7.0, 8.0, 9.0), instance_name="SyntheticDropPodZv44"),
        )
    )

    result = collectibles.collectibles_of(model)

    assert len(result.uncollected) == THREE_ROWS, (
        "with nothing collected the subtraction must remove nothing; this is the control"
        " that keeps the arm above from passing on a reader that serves nothing at all"
    )
    assert result.records.collected == 0


# ---------------------------------------------------------------------------
# The allowlist and its published skipped count - PER CLASS, never over the pool
# ---------------------------------------------------------------------------


def test_a_class_outside_the_allowlist_moves_the_skipped_count_for_that_class() -> None:
    without = collectibles.collectibles_of(world_of((actor(CRYSTAL_CLASS, (1.0, 2.0, 3.0)),)))
    with_off_list = collectibles.collectibles_of(
        world_of(
            (
                actor(CRYSTAL_CLASS, (1.0, 2.0, 3.0)),
                actor(OFF_LIST_CLASS, (4.0, 5.0, 6.0)),
            )
        )
    )

    assert OFF_LIST_CLASS not in without.skipped_counts, "the control already carried the class"
    assert with_off_list.skipped_counts[OFF_LIST_CLASS] == 1, (
        "a class off the allowlist must be COUNTED under its own name, never silently"
        " dropped and never pooled into a total whose strongest member meets it"
    )
    assert OFF_LIST_CLASS not in with_off_list.uncollected_counts
    assert collectibles.WARN_COLLECTIBLE_CLASS_NOT_SERVED in codes(with_off_list)


def test_the_allowlist_shares_no_class_with_the_resource_node_population() -> None:
    overlap = collectibles.COLLECTIBLE_CLASS_ALLOWLIST & world.NODE_CLASS_NAMES

    assert not overlap, (
        f"{overlap} would be published twice under two meanings - once as a resource node"
        " by the placement view and once as an uncollected pickup here"
    )


# ---------------------------------------------------------------------------
# The partition, and the empty instance half it exists for
# ---------------------------------------------------------------------------


def test_every_collectable_row_lands_in_exactly_one_bucket() -> None:
    pairs = (
        collected("SyntheticShrineZv44"),
        collected("SyntheticCrystalZv44"),
        collected(""),
    )
    model = world_of((actor(CRYSTAL_CLASS, (1.0, 2.0, 3.0)),), pairs)

    partition = collectibles.collectibles_of(model).collected_partition

    assert partition.joinable + partition.unjoinable == len(model.objects.collectables), (
        "a row reached neither bucket, which is exactly the drop a consumer joining on"
        " instance_name cannot detect"
    )
    assert partition.unjoinable == 1, "the pair with the empty instance half was joined anyway"


def test_a_partition_that_drops_a_row_cannot_be_constructed() -> None:
    with pytest.raises(collectibles.ConservationError):
        collectibles.CollectedPartition(joinable=1, unjoinable=0, declared=2)


def test_an_empty_instance_half_subtracts_no_record() -> None:
    model = world_of((actor(CRYSTAL_CLASS, (1.0, 2.0, 3.0), instance_name=""),), (collected(""),))

    result = collectibles.collectibles_of(model)

    assert len(result.uncollected) == 1, (
        "the pair's empty instance half joined the record's empty instance name and"
        " deleted a live row; an empty half is unjoinable and enters no key set"
    )
    assert result.records.collected == 0
    assert result.collected_partition.unjoinable == 1
    assert collectibles.WARN_COLLECTED_ENTRY_UNJOINABLE in codes(result)


# ---------------------------------------------------------------------------
# Reader provenance - empty means "saw none", never "has none"
# ---------------------------------------------------------------------------


def test_the_flat_reader_is_reported_as_unavailable_rather_than_as_no_collected_state() -> None:
    model = world_of((actor(CRYSTAL_CLASS, (1.0, 2.0, 3.0)),), level_count=0)

    result = collectibles.collectibles_of(model)

    assert result.collected_state_available is False, (
        "parse_object_headers walks no collectable block at all, so its empty list is"
        " 'this reader saw none' and reporting it as a measured zero is silently wrong"
    )
    assert collectibles.WARN_COLLECTED_STATE_UNAVAILABLE in codes(result)


def test_a_levelled_read_with_no_collectable_entry_is_available_rather_than_unavailable() -> None:
    model = world_of((actor(CRYSTAL_CLASS, (1.0, 2.0, 3.0)),), level_count=1)

    result = collectibles.collectibles_of(model)

    assert result.collected_state_available is True, (
        "a levelled walk read the blocks and found none collected, which is a measured"
        " zero; collapsing it into the flat reader's silence loses the distinction"
    )
    assert collectibles.WARN_COLLECTED_STATE_UNAVAILABLE not in codes(result)


# ---------------------------------------------------------------------------
# The record census - the second conservation
# ---------------------------------------------------------------------------


def test_every_record_lands_in_exactly_one_census_bucket() -> None:
    records = (
        actor(CRYSTAL_CLASS, (1.0, 2.0, 3.0), instance_name="SyntheticCrystalZv44"),
        actor(SHRINE_CLASS, (4.0, 5.0, 6.0), instance_name="SyntheticShrineZv44"),
        actor(DROP_POD_CLASS, None, instance_name="SyntheticDropPodZv44"),
        actor(CRYSTAL_CLASS, (math.inf, 0.0, 0.0), instance_name="SyntheticBadZv44"),
        actor(OFF_LIST_CLASS, (7.0, 8.0, 9.0)),
    )
    model = world_of(records, (collected("SyntheticShrineZv44"),))

    census = collectibles.collectibles_of(model).records

    assert census.total == len(records), "a record reached no bucket or reached two"
    assert (census.served, census.collected, census.skipped) == (1, 1, 1)
    assert (census.transform_absent, census.coordinate_non_finite) == (1, 1)


def test_a_census_that_drops_a_record_cannot_be_constructed() -> None:
    with pytest.raises(collectibles.ConservationError):
        collectibles.RecordCensus(
            served=1,
            collected=0,
            skipped=0,
            transform_absent=0,
            coordinate_non_finite=0,
            declared=2,
        )


# ---------------------------------------------------------------------------
# Non-negotiable 7 - a silence is flagged rather than published as a zero
# ---------------------------------------------------------------------------


def test_nothing_served_is_flagged_rather_than_published_as_a_silent_empty() -> None:
    result = collectibles.collectibles_of(world_of(()))

    assert result.uncollected == ()
    assert collectibles.WARN_COLLECTIBLE_NONE_SERVED in codes(result), (
        "an empty served list is indistinguishable from a world that genuinely holds no"
        " uncollected item unless the model says which it is"
    )


def test_a_collectible_carrying_no_transform_is_counted_rather_than_placed() -> None:
    result = collectibles.collectibles_of(world_of((actor(SHRINE_CLASS, None),)))

    assert result.uncollected == ()
    assert result.records.transform_absent == 1
    assert collectibles.WARN_COLLECTIBLE_TRANSFORM_ABSENT in codes(result)


def test_a_non_finite_coordinate_is_refused_and_counted() -> None:
    result = collectibles.collectibles_of(world_of((actor(SHRINE_CLASS, (0.0, math.nan, 0.0)),)))

    assert result.uncollected == ()
    assert result.records.coordinate_non_finite == 1
    assert collectibles.WARN_COLLECTIBLE_COORDINATE_NON_FINITE in codes(result)


# ---------------------------------------------------------------------------
# What never leaves this layer
# ---------------------------------------------------------------------------


def test_no_instance_name_and_no_float_reach_the_published_model() -> None:
    model = world_of(
        (actor(CRYSTAL_CLASS, (1.5, 2.5, 3.5)),),
        (collected(INSTANCE_NAME_MARKER),),
    )
    control = reachable(model)
    assert INSTANCE_NAME_MARKER in control, "the walk cannot see a planted name even in the input"
    assert any(isinstance(item, float) for item in control), "the walk cannot see a float"

    published = reachable(collectibles.collectibles_of(model))

    assert INSTANCE_NAME_MARKER not in published, "an instance name reached the published model"
    assert PATH_MARKER not in published, "an object path reached the published model"
    assert LEVEL_NAME_MARKER not in published, "a level name reached the published model"
    assert not [item for item in published if isinstance(item, float)], (
        "a float reached the published model; a coordinate leaves as an exact decimal"
        " string, which is the rendering placement.decimal_string owns"
    )


def test_a_served_row_is_the_layers_own_placement_type() -> None:
    result = collectibles.collectibles_of(world_of((actor(CRYSTAL_CLASS, (1.5, 2.5, 3.5)),)))

    row = result.uncollected[0]
    assert isinstance(row, placement.Placement)
    assert (row.x, row.y, row.z) == ("1.5", "2.5", "3.5")
    assert result.coordinate_units == placement.COORDINATE_UNITS
