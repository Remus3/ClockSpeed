"""CS-978: the inventory model over one world - per-item totals and the denominator.

Every fixture here is a hand-built synthetic ``WorldModel``. Nothing in this
module opens a save, a docs file or the install - see ``tests/audit/__init__.py``
for the four rules.

WHAT THE DENOMINATOR ARMS ARE FOR. ``WorldProperties.unread_payload_count``'s
own docstring calls itself "the honest denominator for anything computed off
these values", and a total published without it is a partial sum presented as a
fact. So the arms below grade the total AND the two numbers that say how
complete it is, because a model that got the sum right and dropped the
denominator is the defect this item exists to avoid rather than a lesser version
of the fix.

WHAT THIS MODULE DELIBERATELY DOES NOT ASSERT is that a real save yields a
total. Measured and recorded in ``docs/LEDGER.md`` and ``docs/GATED.md``: no
building record carries an ``InventoryStack`` - a building holds an
``ObjectProperty`` REFERENCE to a separate record - and a ``StructProperty``
element inside a container is bounded, typed and deliberately NOT decoded
(``clockspeed/save/objects.py`` ``ContainerElement.value``). The recognition
vocabulary this layer owns is therefore graded against synthetic containers of
the shape it claims to read, and the warning that says a real world may yield
nothing is graded too.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import fields, is_dataclass
from pathlib import Path
from types import MappingProxyType

from clockspeed.audit import inventory
from clockspeed.save import objects
from clockspeed.save.header import SaveHeader
from clockspeed.save.world import (
    EMPTY_UNLOCK_STATE,
    ContainerContents,
    ContainerEntry,
    RecordProperties,
    WorldModel,
    WorldProperties,
)

# An invented 22-character base64url literal. Never a real world token.
SYNTHETIC_TOKEN = "ClockspeedAuditToken1"  # noqa: S105 - an invented marker, not a secret

INSTANCE_NAME_MARKER = "SyntheticInstanceNameMarkerQx72"
PATH_MARKER = "SyntheticPathMarkerQx72"
BODY_OFFSET_MARKER = 987654323
BODY_LENGTH_MARKER = 987654324
RECORD_INDEX_MARKER = 987654325


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


def record() -> objects.ObjectRecord:
    """Build one synthetic record planting every refusal marker.

    Returns:
        The record.
    """
    return objects.ObjectRecord(
        kind=objects.KIND_ACTOR,
        type_path="Build_SyntheticStore_C",
        root_object=PATH_MARKER,
        instance_name=INSTANCE_NAME_MARKER,
        transform=None,
        parent=None,
        object_type=1,
        was_placed_in_level=0,
        body_offset=BODY_OFFSET_MARKER,
        body_length=BODY_LENGTH_MARKER,
    )


def stack(item_key: object, amount: object) -> objects.StructValue:
    """Build one synthetic struct interior of the shape this layer claims to read.

    Args:
        item_key: The value under the item-key property name.
        amount: The value under the count property name.

    Returns:
        The struct value.
    """
    return objects.StructValue(
        struct_word="SyntheticInventoryStack",
        form=objects.STRUCT_FORM_TAG_LIST,
        properties=MappingProxyType(
            {
                next(iter(sorted(inventory.ITEM_KEY_PROPERTY_NAMES))): item_key,
                next(iter(sorted(inventory.ITEM_COUNT_PROPERTY_NAMES))): amount,
            }
        ),
        depth=1,
    )


def container(*values: object) -> ContainerContents:
    """Build one published container holding the given element values.

    Args:
        values: One value per element half, in order. None means the save layer
            did not decode that element, which is a fact rather than an empty.

    Returns:
        The container.
    """
    return ContainerContents(
        type_word="ArrayProperty",
        element_words=("StructProperty",),
        element_count=len(values),
        entries=tuple(
            ContainerEntry(type_word="StructProperty", length=8, value=value) for value in values
        ),
        element_shape=objects.ELEMENT_SHAPE_SOLVED_WIDTH,
        struct_word="SyntheticInventoryStack",
    )


def world(
    *,
    by_record_index: Mapping[int, RecordProperties] | None = None,
    records: tuple[objects.ObjectRecord, ...] = (),
) -> WorldModel:
    """Build a synthetic world model holding exactly what a test needs.

    Args:
        by_record_index: The per-record properties, or None for none at all.
        records: The object records.

    Returns:
        The model.
    """
    return WorldModel(
        token=SYNTHETIC_TOKEN,
        header=header(),
        objects=objects.ObjectTable(
            records=records,
            unknown_classes=(),
            warnings=(),
            declared_body_length=0,
            body_consumed=0,
            body_prefix_width=8,
            transform_delta=0,
            save_version=52,
            header_version=14,
            level_count=1,
        ),
        unlocks=EMPTY_UNLOCK_STATE,
        nodes=(),
        warnings=(),
        properties=WorldProperties(by_record_index=MappingProxyType(dict(by_record_index or {}))),
    )


def entry(
    values: Mapping[str, object],
    *,
    payload_read: bool = True,
) -> RecordProperties:
    """Build one record's published properties.

    Args:
        values: The decoded property values.
        payload_read: Whether the payload read under the measured grammar.

    Returns:
        The properties.
    """
    return RecordProperties(
        values=MappingProxyType(dict(values)),
        schema_name="SyntheticSchema",
        resolved=None,
        payload_read=payload_read,
        warning_codes=() if payload_read else (objects.WARN_UNPARSED_PROPERTY_PAYLOAD,),
    )


def reachable(value: object, seen: set[int] | None = None) -> list[object]:
    """Every value reachable from one object, the object itself included.

    STRUCTURAL on purpose - see the same helper in ``test_placement.py``.

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
        return found
    if isinstance(value, (str, bytes, bytearray)):
        return found
    if isinstance(value, Mapping):
        for key, item in value.items():
            found.extend(reachable(key, seen))
            found.extend(reachable(item, seen))
        return found
    if isinstance(value, (tuple, list, set, frozenset)):
        for item in value:
            found.extend(reachable(item, seen))
    return found


def test_container_contents_aggregate_into_one_total_per_item_key() -> None:
    model = world(
        by_record_index={
            0: entry({"mSyntheticStacks": container(stack("Desc_OreIron_C", 300))}),
            1: entry({"mSyntheticStacks": container(stack("Desc_OreIron_C", 45))}),
        }
    )

    result = inventory.inventory_of(model)

    assert [(item.item_key, item.count) for item in result.items] == [("Desc_OreIron_C", 345)]


def test_totals_are_sorted_deterministically_by_item_key() -> None:
    model = world(
        by_record_index={
            0: entry(
                {
                    "mSyntheticStacks": container(
                        stack("Desc_Water_C", 1),
                        stack("Desc_IronIngot_C", 2),
                        stack("Desc_Cable_C", 3),
                    )
                }
            )
        }
    )

    keys = [item.item_key for item in inventory.inventory_of(model).items]

    assert keys == sorted(keys)
    assert keys == ["Desc_Cable_C", "Desc_IronIngot_C", "Desc_Water_C"]


def test_an_item_key_path_reduces_to_its_class_name() -> None:
    model = world(
        by_record_index={
            0: entry(
                {
                    "mSyntheticStacks": container(
                        stack("/Game/Synthetic/Desc_OreIron.Desc_OreIron_C", 7)
                    )
                }
            )
        }
    )

    assert [item.item_key for item in inventory.inventory_of(model).items] == ["Desc_OreIron_C"]


def test_an_object_reference_item_key_reduces_to_its_class_name() -> None:
    reference = objects.ObjectReference(
        property_name="ItemClass",
        level_reference=PATH_MARKER,
        object_path="/Game/Synthetic/Desc_Coal.Desc_Coal_C",
    )
    model = world(by_record_index={0: entry({"mSyntheticStacks": container(stack(reference, 9))})})

    result = inventory.inventory_of(model)

    assert [(item.item_key, item.count) for item in result.items] == [("Desc_Coal_C", 9)]


def test_a_boolean_count_is_not_an_integer_count() -> None:
    # isinstance(True, int) is True, so a naive count check accepts a boolean
    # and publishes a total of 1 for a flag that means nothing of the kind.
    model = world(
        by_record_index={0: entry({"mSyntheticStacks": container(stack("Desc_OreIron_C", True))})}
    )

    result = inventory.inventory_of(model)

    assert result.items == ()
    assert inventory.WARN_INVENTORY_TOTAL_EMPTY in [warning.code for warning in result.warnings]


def test_a_struct_missing_either_half_of_the_pair_contributes_nothing() -> None:
    lonely_key = objects.StructValue(
        struct_word="SyntheticInventoryStack",
        form=objects.STRUCT_FORM_TAG_LIST,
        properties=MappingProxyType({"ItemClass": "Desc_OreIron_C"}),
    )
    lonely_count = objects.StructValue(
        struct_word="SyntheticInventoryStack",
        form=objects.STRUCT_FORM_TAG_LIST,
        properties=MappingProxyType({"Amount": 12}),
    )
    model = world(
        by_record_index={0: entry({"mSyntheticStacks": container(lonely_key, lonely_count)})}
    )

    assert inventory.inventory_of(model).items == ()


def test_an_empty_item_key_is_refused_rather_than_totalled_under_a_blank() -> None:
    # ADR 0009 measured that an UNRESOLVED object reference carries an EMPTY
    # object path. Keying a total by "" would pool every unresolved reference in
    # the world into one row that looks like a real item.
    unresolved = objects.ObjectReference(
        property_name="ItemClass", level_reference=PATH_MARKER, object_path=""
    )
    model = world(by_record_index={0: entry({"mSyntheticStacks": container(stack(unresolved, 6))})})

    assert inventory.inventory_of(model).items == ()


def test_the_unread_payload_count_travels_as_the_honest_denominator() -> None:
    model = world(
        by_record_index={
            0: entry({"mSyntheticStacks": container(stack("Desc_OreIron_C", 5))}),
            1: entry({}, payload_read=False),
            2: entry({}, payload_read=False),
        }
    )

    result = inventory.inventory_of(model)

    expected_unread = 2
    expected_records = 3
    assert result.unread_payload_count == expected_unread
    assert result.records_considered == expected_records
    assert inventory.WARN_INVENTORY_PAYLOAD_UNREAD in [warning.code for warning in result.warnings]


def test_the_container_count_actually_read_travels_beside_the_total() -> None:
    model = world(
        by_record_index={
            0: entry(
                {
                    "mSyntheticStacks": container(stack("Desc_OreIron_C", 1)),
                    "mOtherStacks": container(stack("Desc_Coal_C", 2)),
                }
            ),
            1: entry({"mSyntheticStacks": container(stack("Desc_OreIron_C", 3))}),
        }
    )

    result = inventory.inventory_of(model)

    expected_containers = 3
    assert result.containers_read == expected_containers


def test_an_undecoded_container_entry_is_counted_rather_than_dropped() -> None:
    # None on a ContainerEntry means "not decoded", never "empty". A total that
    # silently skipped one would be short by an unknown amount.
    model = world(
        by_record_index={
            0: entry({"mSyntheticStacks": container(stack("Desc_OreIron_C", 4), None)})
        }
    )

    result = inventory.inventory_of(model)

    assert result.undecoded_entry_count == 1
    assert inventory.WARN_INVENTORY_ENTRY_UNDECODED in [warning.code for warning in result.warnings]


def test_an_empty_total_is_flagged_rather_than_presented_as_an_empty_world() -> None:
    result = inventory.inventory_of(world())

    assert result.items == ()
    warnings = {warning.code: warning for warning in result.warnings}
    assert inventory.WARN_INVENTORY_TOTAL_EMPTY in warnings
    assert warnings[inventory.WARN_INVENTORY_TOTAL_EMPTY].detail != ""


def test_a_recovered_total_is_not_flagged_as_empty() -> None:
    model = world(
        by_record_index={0: entry({"mSyntheticStacks": container(stack("Desc_OreIron_C", 1))})}
    )

    codes = [warning.code for warning in inventory.inventory_of(model).warnings]

    assert inventory.WARN_INVENTORY_TOTAL_EMPTY not in codes


def test_no_display_name_is_invented_for_an_item_key() -> None:
    # A display name is a registry join and is NOT this layer's job. A field
    # here would be filled in by inference the first time somebody wanted one.
    declared = {field.name for field in fields(inventory.ItemTotal)}

    assert declared == {"item_key", "count"}


def test_a_nested_container_inside_a_struct_interior_is_reached() -> None:
    nested = objects.StructValue(
        struct_word="SyntheticOuter",
        form=objects.STRUCT_FORM_TAG_LIST,
        properties=MappingProxyType({"mInner": container(stack("Desc_Screw_C", 11))}),
    )
    model = world(by_record_index={0: entry({"mOuter": nested})})

    result = inventory.inventory_of(model)

    assert [(item.item_key, item.count) for item in result.items] == [("Desc_Screw_C", 11)]


def test_no_float_reaches_any_inventory_output_field() -> None:
    model = world(
        by_record_index={
            0: entry(
                {
                    "mSyntheticStacks": container(stack("Desc_OreIron_C", 3)),
                    "mSomeScalar": 1.5,
                }
            )
        }
    )

    result = inventory.inventory_of(model)
    floats_out = [item for item in reachable(result) if type(item) is float]

    assert [item for item in reachable(model) if type(item) is float] != []
    assert floats_out == []


def test_no_record_instance_name_reaches_the_inventory_model() -> None:
    model = world(
        by_record_index={0: entry({"mSyntheticStacks": container(stack("Desc_OreIron_C", 3))})},
        records=(record(),),
    )

    result = inventory.inventory_of(model)
    leaked = [
        item for item in reachable(result) if isinstance(item, str) and INSTANCE_NAME_MARKER in item
    ]

    assert [item for item in reachable(model) if item == INSTANCE_NAME_MARKER] != []
    assert leaked == []
    assert INSTANCE_NAME_MARKER not in repr(result)


def test_no_record_index_offset_or_path_reaches_the_inventory_model() -> None:
    model = world(
        by_record_index={
            RECORD_INDEX_MARKER: entry({"mSyntheticStacks": container(stack("Desc_OreIron_C", 3))})
        },
        records=(record(),),
    )

    result = inventory.inventory_of(model)
    walked = reachable(result)
    positions = [
        item
        for item in walked
        if item in (BODY_OFFSET_MARKER, BODY_LENGTH_MARKER, RECORD_INDEX_MARKER)
    ]

    assert [item for item in reachable(model) if item == RECORD_INDEX_MARKER] != []
    assert positions == []
    assert [item for item in walked if isinstance(item, (Path, bytes, bytearray))] == []
    assert [item for item in walked if isinstance(item, str) and PATH_MARKER in item] == []


def test_no_inventory_type_annotates_a_carrier_field() -> None:
    carriers = {"bytes", "bytearray", "Path", "pathlib.Path"}
    declared = {
        field.type if isinstance(field.type, str) else getattr(field.type, "__name__", "")
        for published in (inventory.ItemTotal, inventory.WorldInventory)
        for field in fields(published)
    }

    assert declared & carriers == set()


def test_the_recognition_vocabularies_are_closed_frozensets() -> None:
    assert type(inventory.ITEM_KEY_PROPERTY_NAMES) is frozenset
    assert type(inventory.ITEM_COUNT_PROPERTY_NAMES) is frozenset
    assert frozenset() != inventory.ITEM_KEY_PROPERTY_NAMES
    assert frozenset() != inventory.ITEM_COUNT_PROPERTY_NAMES


def test_two_runs_over_one_model_return_equal_models() -> None:
    model = world(
        by_record_index={
            0: entry(
                {
                    "mSyntheticStacks": container(
                        stack("Desc_Water_C", 1),
                        stack("Desc_Cable_C", 2),
                        stack("Desc_Water_C", 3),
                    )
                }
            ),
            1: entry({}, payload_read=False),
        }
    )

    first = inventory.inventory_of(model)
    second = inventory.inventory_of(model)

    assert first == second
    assert [item.item_key for item in first.items] == [item.item_key for item in second.items]
