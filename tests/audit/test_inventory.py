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
total. That is the save layer's phase-4 depth gate's claim, not this layer's.
Here a building is a synthetic record whose published reference target (CS-400,
``clockspeed.save.world.ReferenceTarget``) names a synthetic carrier record
holding ``InventoryStack`` interiors in the save's own spelling - ``Item`` as a
decoded ``objects.InventoryItem`` and ``NumItems`` as an int - so the per-building
view, the three ``Item`` states and every exclusion reason are graded on the
shape the save layer publishes, with no save and no install.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import fields, is_dataclass
from pathlib import Path
from types import MappingProxyType

from clockspeed.audit import inventory
from clockspeed.save import objects
from clockspeed.save import world as world_layer
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


def test_a_struct_missing_either_half_of_the_pair_is_excluded_by_reason() -> None:
    # BOTH HALVES OR NEITHER, and the half that is missing is COUNTED: a count
    # with no Item tag is the ADJ-G Q4 third state, and an Item with no count
    # says nothing about how much. Neither contributes and neither vanishes.
    lonely_key = objects.StructValue(
        struct_word="SyntheticInventoryStack",
        form=objects.STRUCT_FORM_TAG_LIST,
        properties=MappingProxyType({"Item": item("/Game/Synthetic/Desc_OreIron.Desc_OreIron_C")}),
    )
    lonely_count = objects.StructValue(
        struct_word="SyntheticInventoryStack",
        form=objects.STRUCT_FORM_TAG_LIST,
        properties=MappingProxyType({"NumItems": 12}),
    )
    model = world(
        by_record_index={0: entry({"mSyntheticStacks": container(lonely_key, lonely_count)})}
    )

    result = inventory.inventory_of(model)

    assert result.items == ()
    assert result.excluded == (
        (inventory.EXCLUDED_COUNT_UNREAD, 1),
        (inventory.EXCLUDED_ITEM_ABSENT, 1),
    )


def test_the_docs_blob_spelling_is_not_read_as_a_save_stack() -> None:
    # ItemClass / Amount is the SHIPPED DOCS BLOB's grammar, never measured in a
    # save. A struct carrying only those names is not a stack at all here.
    docs_shaped = objects.StructValue(
        struct_word="SyntheticInventoryStack",
        form=objects.STRUCT_FORM_TAG_LIST,
        properties=MappingProxyType({"ItemClass": "Desc_OreIron_C", "Amount": 12}),
    )
    model = world(by_record_index={0: entry({"mSyntheticStacks": container(docs_shaped)})})

    result = inventory.inventory_of(model)

    assert result.items == ()
    assert result.stack_count == 0


def test_an_empty_item_key_is_refused_rather_than_totalled_under_a_blank() -> None:
    # ADR 0009 measured that an UNRESOLVED object reference carries an EMPTY
    # object path. Keying a total by "" would pool every unresolved reference in
    # the world into one row that looks like a real item.
    unresolved = objects.ObjectReference(
        property_name="Item", level_reference=PATH_MARKER, object_path=""
    )
    model = world(by_record_index={0: entry({"mSyntheticStacks": container(stack(unresolved, 6))})})

    result = inventory.inventory_of(model)

    assert result.items == ()
    assert result.excluded == ((inventory.EXCLUDED_COUNT_DISAGREES, 1),)


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


def test_each_count_carrying_warning_serves_the_count_it_aggregates() -> None:
    # CS-1035. The unread raise and the undecoded raise each pass a count to
    # ``_warning``, whose default is 1. An arm that grades presence alone stays
    # green when either argument is dropped, so each served ``.count`` is graded
    # here against a fixture where the true count is NOT 1 - at 1 the dropped
    # argument and the default are the same value and the mutant is equivalent.
    # The two counts are also distinct from each other, so an argument swapped
    # between the two raises reddens too.
    model = world(
        by_record_index={
            0: entry({"mSyntheticStacks": container(stack("Desc_OreIron_C", 5), None, None, None)}),
            1: entry({}, payload_read=False),
            2: entry({}, payload_read=False),
        }
    )

    result = inventory.inventory_of(model)

    expected_unread = 2
    expected_undecoded = 3
    served = [
        (warning.code, warning.count)
        for warning in result.warnings
        if warning.code
        in (inventory.WARN_INVENTORY_PAYLOAD_UNREAD, inventory.WARN_INVENTORY_ENTRY_UNDECODED)
    ]
    assert served == [
        (inventory.WARN_INVENTORY_PAYLOAD_UNREAD, expected_unread),
        (inventory.WARN_INVENTORY_ENTRY_UNDECODED, expected_undecoded),
    ]
    # The warning count and the model field are one fact and must not diverge.
    assert result.unread_payload_count == expected_unread
    assert result.undecoded_entry_count == expected_undecoded


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


# ---------------------------------------------------------------------------
# CS-400 S3 - per-building inventory through the published join, save spelling
# ---------------------------------------------------------------------------

#: The save's own spelling, measured by CS-400 S0 over the local library: an
#: ``InventoryStack`` interior carries ``Item`` (a native ``InventoryItem``) and
#: ``NumItems`` (an int). Restated here as literals ON PURPOSE - an arm that read
#: the names back off the module under test could not catch a wrong spelling.
SAVE_ITEM_NAME = "Item"
SAVE_COUNT_NAME = "NumItems"

ORE_PATH = "/Game/Synthetic/Desc_SyntheticOre.Desc_SyntheticOre_C"
ORE_KEY = "Desc_SyntheticOre_C"
PLATE_PATH = "/Game/Synthetic/Desc_SyntheticPlate.Desc_SyntheticPlate_C"
PLATE_KEY = "Desc_SyntheticPlate_C"

BUILDING_CLASS_PATH = "/Game/Synthetic/Build_SyntheticStore.Build_SyntheticStore_C"
BUILDING_CLASS = "Build_SyntheticStore_C"
COMPONENT_CLASS_PATH = "/Script/Synthetic.SyntheticInventoryComponent"


def item(class_path: str, *, state_undecoded: bool = False) -> objects.InventoryItem:
    """Build one decoded native ``Item`` the way the save layer publishes it.

    Args:
        class_path: The item class path; empty for an empty slot.
        state_undecoded: Whether item state was present and left undecoded.

    Returns:
        The item.
    """
    return objects.InventoryItem(
        level_reference="", class_path=class_path, state_undecoded=state_undecoded
    )


def save_stack(**values: object) -> objects.StructValue:
    """Build one ``InventoryStack`` interior holding exactly the given tags.

    Args:
        values: The interior's properties by name. A name left out is a tag the
            save did not write, which is the item-absent state.

    Returns:
        The struct value.
    """
    return objects.StructValue(
        struct_word="InventoryStack",
        form=objects.STRUCT_FORM_TAG_LIST,
        properties=MappingProxyType(dict(values)),
        depth=1,
    )


def full(class_path: str, count: int, **kwargs: bool) -> objects.StructValue:
    """One stack carrying a decoded item and a count.

    Args:
        class_path: The item class path.
        count: ``NumItems``.
        kwargs: Forwarded to :func:`item`.

    Returns:
        The struct value.
    """
    return save_stack(**{SAVE_ITEM_NAME: item(class_path, **kwargs), SAVE_COUNT_NAME: count})


def actor_record(type_path: str, kind: str = objects.KIND_ACTOR) -> objects.ObjectRecord:
    """Build one synthetic record of the given class.

    Args:
        type_path: The record's class path.
        kind: The record kind; an ACTOR unless a component is asked for.

    Returns:
        The record.
    """
    return objects.ObjectRecord(
        kind=kind,
        type_path=type_path,
        root_object="Persistent_Level",
        instance_name="Persistent_Level:PersistentLevel.Synthetic_0",
        transform=None,
        parent=None,
        object_type=1,
        was_placed_in_level=0,
        body_offset=0,
        body_length=0,
    )


def joined(
    values: Mapping[str, object], targets: tuple[world_layer.ReferenceTarget, ...]
) -> RecordProperties:
    """Build one actor's properties carrying one reference per target.

    Args:
        values: The decoded property values.
        targets: Where each reference landed, in reference order.

    Returns:
        The properties, with ``references`` and ``reference_targets`` aligned.
    """
    references = tuple(
        objects.ObjectReference(
            property_name="mSyntheticInventory",
            level_reference="Persistent_Level",
            object_path="Persistent_Level:PersistentLevel.Synthetic_0.Inventory" + str(position),
        )
        for position in range(len(targets))
    )
    return RecordProperties(
        values=MappingProxyType(dict(values)),
        schema_name="SyntheticSchema",
        resolved=None,
        payload_read=True,
        references=references,
        reference_targets=targets,
    )


def component_record() -> objects.ObjectRecord:
    """Build one synthetic COMPONENT record - an inventory carrier's kind.

    Returns:
        The record.
    """
    return actor_record(COMPONENT_CLASS_PATH, objects.KIND_COMPONENT)


def resolved(index: int) -> world_layer.ReferenceTarget:
    """A reference resolved to exactly one record.

    Args:
        index: The target record index.

    Returns:
        The target.
    """
    return world_layer.ReferenceTarget(state=world_layer.TARGET_RESOLVED, record_indices=(index,))


def building_world(
    *stacks: object, targets: tuple[world_layer.ReferenceTarget, ...] = ()
) -> WorldModel:
    """A building at index 0 whose reference resolves to a carrier at index 1.

    Args:
        stacks: The carrier's ``mInventoryStacks`` element values.
        targets: The building's reference targets; one resolving to 1 when empty.

    Returns:
        The model.
    """
    return world(
        by_record_index={
            0: joined({}, targets or (resolved(1),)),
            1: entry({"mInventoryStacks": container(*stacks)}),
        },
        records=(actor_record(BUILDING_CLASS_PATH), component_record()),
    )


def rows_of(building: inventory.BuildingInventory) -> list[tuple[str, int]]:
    """One building's item rows as (key, count) pairs.

    Args:
        building: The per-building view.

    Returns:
        The rows.
    """
    return [(total.item_key, total.count) for total in building.items]


def test_a_building_reaching_two_stacks_yields_two_item_rows() -> None:
    model = building_world(full(ORE_PATH, 300), full(PLATE_PATH, 45))

    result = inventory.inventory_of(model)

    assert len(result.buildings) == 1
    building = result.buildings[0]
    assert building.class_name == BUILDING_CLASS
    assert rows_of(building) == [(ORE_KEY, 300), (PLATE_KEY, 45)]
    assert [(total.item_key, total.count) for total in result.items] == [
        (ORE_KEY, 300),
        (PLATE_KEY, 45),
    ]
    assert inventory.WARN_INVENTORY_TOTAL_EMPTY not in [warning.code for warning in result.warnings]


def test_the_recognition_vocabulary_is_the_save_spelling() -> None:
    # Pinned by LITERAL: CS-400 S0 measured Item / NumItems on every
    # mInventoryStacks element, and the docs-blob seed ItemClass / Amount
    # matched nothing in a save.
    assert frozenset({SAVE_ITEM_NAME}) == inventory.ITEM_KEY_PROPERTY_NAMES
    assert frozenset({SAVE_COUNT_NAME}) == inventory.ITEM_COUNT_PROPERTY_NAMES


def test_an_empty_slot_is_reported_as_empty_and_never_as_an_item() -> None:
    model = building_world(full(ORE_PATH, 3), full("", 0), full("", 0))

    result = inventory.inventory_of(model)

    expected_empty = 2
    expected_stacks = 3
    assert rows_of(result.buildings[0]) == [(ORE_KEY, 3)]
    assert result.buildings[0].empty_slot_count == expected_empty
    assert result.buildings[0].stack_count == expected_stacks
    assert result.buildings[0].excluded == ()
    assert result.empty_slot_count == expected_empty
    assert result.excluded == ()
    assert [(total.item_key, total.count) for total in result.items] == [(ORE_KEY, 3)]


def test_a_world_of_only_empty_slots_is_flagged_as_an_empty_total() -> None:
    result = inventory.inventory_of(building_world(full("", 0)))

    assert result.items == ()
    assert result.empty_slot_count == 1
    assert inventory.WARN_INVENTORY_TOTAL_EMPTY in [warning.code for warning in result.warnings]
    assert inventory.WARN_INVENTORY_STACK_EXCLUDED not in [
        warning.code for warning in result.warnings
    ]


def test_an_absent_item_is_flagged_item_absent_and_never_an_empty_slot() -> None:
    # ADJ-G Q4: the THIRD state. A stack whose Item tag is missing altogether is
    # neither an empty slot nor an unknown item.
    absent = save_stack(**{SAVE_COUNT_NAME: 0})
    model = building_world(full(ORE_PATH, 2), absent)

    result = inventory.inventory_of(model)

    assert result.empty_slot_count == 0
    assert result.excluded == ((inventory.EXCLUDED_ITEM_ABSENT, 1),)
    assert result.buildings[0].excluded == ((inventory.EXCLUDED_ITEM_ABSENT, 1),)
    assert result.buildings[0].empty_slot_count == 0
    assert rows_of(result.buildings[0]) == [(ORE_KEY, 2)]
    served = [
        (warning.code, warning.count)
        for warning in result.warnings
        if warning.code == inventory.WARN_INVENTORY_STACK_EXCLUDED
    ]
    assert served == [(inventory.WARN_INVENTORY_STACK_EXCLUDED, 1)]


def test_an_undecoded_item_state_is_counted_and_the_item_still_contributes() -> None:
    model = building_world(
        full(ORE_PATH, 5, state_undecoded=True),
        full(PLATE_PATH, 7),
        full("", 0, state_undecoded=True),
    )

    result = inventory.inventory_of(model)

    expected_undecoded = 2
    assert result.state_undecoded_count == expected_undecoded
    assert result.buildings[0].state_undecoded_count == expected_undecoded
    assert rows_of(result.buildings[0]) == [(ORE_KEY, 5), (PLATE_KEY, 7)]


def test_each_save_layer_refusal_is_counted_under_its_own_reason_and_excluded() -> None:
    ambiguous = save_stack(
        **{
            SAVE_ITEM_NAME: objects.InventoryItemRefusal(reason=objects.ITEM_FORM_AMBIGUOUS),
            SAVE_COUNT_NAME: 4,
        }
    )
    unclosed = save_stack(
        **{
            SAVE_ITEM_NAME: objects.InventoryItemRefusal(reason=objects.ITEM_FORM_UNCLOSED),
            SAVE_COUNT_NAME: 9,
        }
    )
    model = building_world(full(ORE_PATH, 1), ambiguous, unclosed, unclosed)

    result = inventory.inventory_of(model)

    expected_unclosed = 2
    expected_excluded = 3
    assert result.excluded == (
        (objects.ITEM_FORM_AMBIGUOUS, 1),
        (objects.ITEM_FORM_UNCLOSED, expected_unclosed),
    )
    assert result.buildings[0].excluded == result.excluded
    assert result.buildings[0].excluded_count == expected_excluded
    assert [(total.item_key, total.count) for total in result.items] == [(ORE_KEY, 1)]
    assert result.total_count == 1


def test_a_refusal_reason_outside_the_save_vocabulary_is_unrecognised() -> None:
    planted = save_stack(
        **{
            SAVE_ITEM_NAME: objects.InventoryItemRefusal(reason="synthetic_unknown_reason"),
            SAVE_COUNT_NAME: 1,
        }
    )

    result = inventory.inventory_of(building_world(planted))

    assert result.excluded == ((inventory.EXCLUDED_ITEM_UNRECOGNISED, 1),)


def test_a_class_and_count_that_contradict_each_other_are_excluded() -> None:
    model = building_world(full(ORE_PATH, 0), full("", 5), full(PLATE_PATH, -2))

    result = inventory.inventory_of(model)

    expected_disagreeing = 3
    assert result.items == ()
    assert result.empty_slot_count == 0
    assert result.excluded == ((inventory.EXCLUDED_COUNT_DISAGREES, expected_disagreeing),)


def test_an_unread_or_boolean_count_and_an_unreadable_item_are_excluded() -> None:
    model = building_world(
        save_stack(**{SAVE_ITEM_NAME: item(ORE_PATH), SAVE_COUNT_NAME: True}),
        save_stack(**{SAVE_ITEM_NAME: item(ORE_PATH), SAVE_COUNT_NAME: "3"}),
        save_stack(**{SAVE_ITEM_NAME: 42, SAVE_COUNT_NAME: 3}),
    )

    result = inventory.inventory_of(model)

    expected_unread = 2
    assert result.items == ()
    assert result.excluded == (
        (inventory.EXCLUDED_COUNT_UNREAD, expected_unread),
        (inventory.EXCLUDED_ITEM_UNRECOGNISED, 1),
    )


def test_every_exclusion_reason_is_in_the_closed_vocabulary() -> None:
    assert type(inventory.STACK_EXCLUSION_REASONS) is frozenset
    assert objects.ITEM_REFUSAL_REASONS <= inventory.STACK_EXCLUSION_REASONS
    assert {
        inventory.EXCLUDED_ITEM_ABSENT,
        inventory.EXCLUDED_COUNT_UNREAD,
        inventory.EXCLUDED_ITEM_UNRECOGNISED,
        inventory.EXCLUDED_COUNT_DISAGREES,
    } <= inventory.STACK_EXCLUSION_REASONS


def test_an_unresolved_or_ambiguous_reference_is_counted_and_never_followed() -> None:
    unresolved = world_layer.ReferenceTarget(state=world_layer.TARGET_UNRESOLVED, record_indices=())
    ambiguous = world_layer.ReferenceTarget(
        state=world_layer.TARGET_AMBIGUOUS, record_indices=(1, 2)
    )
    model = world(
        by_record_index={
            0: joined({}, (unresolved, ambiguous)),
            1: entry({"mInventoryStacks": container(full(ORE_PATH, 8))}),
            2: entry({"mInventoryStacks": container(full(PLATE_PATH, 9))}),
        },
        records=(
            actor_record(BUILDING_CLASS_PATH),
            component_record(),
            component_record(),
        ),
    )

    result = inventory.inventory_of(model)

    assert result.buildings == ()
    assert result.references_unresolved == 1
    assert result.references_ambiguous == 1
    assert result.references_resolved == 0
    # The carriers are still in the world total: it never goes through the join.
    assert [(total.item_key, total.count) for total in result.items] == [
        (ORE_KEY, 8),
        (PLATE_KEY, 9),
    ]


def test_targets_misaligned_with_their_references_are_never_followed() -> None:
    misaligned = RecordProperties(
        values=MappingProxyType({}),
        schema_name="SyntheticSchema",
        resolved=None,
        payload_read=True,
        references=joined({}, (resolved(1), resolved(1))).references,
        reference_targets=(resolved(1),),
    )
    model = world(
        by_record_index={
            0: misaligned,
            1: entry({"mInventoryStacks": container(full(ORE_PATH, 8))}),
        },
        records=(actor_record(BUILDING_CLASS_PATH), component_record()),
    )

    result = inventory.inventory_of(model)

    expected_unjoined = 2
    assert result.buildings == ()
    assert result.references_unjoined == expected_unjoined
    assert result.references_resolved == 0


def test_an_unknown_target_state_is_counted_unjoined_and_never_followed() -> None:
    planted = world_layer.ReferenceTarget(state="synthetic_state", record_indices=(1,))

    result = inventory.inventory_of(building_world(full(ORE_PATH, 1), targets=(planted,)))

    assert result.buildings == ()
    assert result.references_unjoined == 1


def test_a_building_reaches_each_carrier_once_and_sums_two_carriers() -> None:
    model = world(
        by_record_index={
            0: joined({}, (resolved(1), resolved(2), resolved(1))),
            1: entry({"mInventoryStacks": container(full(ORE_PATH, 10))}),
            2: entry({"mInventoryStacks": container(full(ORE_PATH, 5), full(PLATE_PATH, 1))}),
        },
        records=(
            actor_record(BUILDING_CLASS_PATH),
            component_record(),
            component_record(),
        ),
    )

    result = inventory.inventory_of(model)

    expected_carriers = 2
    expected_resolved = 3
    building = result.buildings[0]
    assert building.carriers_reached == expected_carriers
    assert rows_of(building) == [(ORE_KEY, 15), (PLATE_KEY, 1)]
    assert result.references_resolved == expected_resolved


def partition_holds(result: inventory.WorldInventory) -> list[str]:
    """Which half of the ownership invariant fails, by name only.

    The per-building sums plus the unattributed and conflict sums must equal the
    world total EXACTLY, for stacks and for items alike - the merger's
    acceptance for CS-400 S3.

    Args:
        result: The inventory model.

    Returns:
        ``"stacks"`` and/or ``"items"`` for each half that does not hold.
    """
    building_stacks = sum(building.stack_count for building in result.buildings)
    building_items = sum(total.count for building in result.buildings for total in building.items)
    failing: list[str] = []
    if (
        building_stacks + result.unattributed_stack_count + result.conflict_stack_count
        != result.stack_count
    ):
        failing.append("stacks")
    if (
        building_items + result.unattributed_item_count + result.conflict_item_count
        != result.total_count
    ):
        failing.append("items")
    return failing


def test_a_carrier_claimed_by_two_actors_is_a_conflict_in_neither_view() -> None:
    model = world(
        by_record_index={
            0: joined({}, (resolved(2),)),
            1: joined({}, (resolved(2),)),
            2: entry({"mInventoryStacks": container(full(ORE_PATH, 10), full("", 0))}),
        },
        records=(
            actor_record(BUILDING_CLASS_PATH),
            actor_record(BUILDING_CLASS_PATH),
            component_record(),
        ),
    )

    result = inventory.inventory_of(model)

    expected_stacks = 2
    assert result.buildings == ()
    assert result.conflict_carrier_count == 1
    assert result.conflict_stack_count == expected_stacks
    assert result.conflict_item_count == 10  # noqa: PLR2004 - the planted count
    assert result.unattributed_carrier_count == 0
    # The world total still holds the carrier exactly once.
    assert [(total.item_key, total.count) for total in result.items] == [(ORE_KEY, 10)]
    assert partition_holds(result) == []


def test_a_component_reference_never_claims_a_carrier() -> None:
    # MEASURED: a factory connection COMPONENT names the inventory it feeds,
    # and following it made one carrier reachable from several records. Only
    # an ACTOR's reference claims; the connection's is counted as resolved.
    model = world(
        by_record_index={
            0: joined({}, (resolved(2),)),
            1: joined({}, (resolved(2),)),
            2: entry({"mInventoryStacks": container(full(ORE_PATH, 4))}),
        },
        records=(actor_record(BUILDING_CLASS_PATH), component_record(), component_record()),
    )

    result = inventory.inventory_of(model)

    expected_resolved = 2
    assert [rows_of(building) for building in result.buildings] == [[(ORE_KEY, 4)]]
    assert result.conflict_carrier_count == 0
    assert result.references_resolved == expected_resolved
    assert partition_holds(result) == []


def test_a_carrier_no_actor_claims_is_counted_unattributed() -> None:
    model = world(
        by_record_index={
            0: joined({}, (resolved(1),)),
            1: entry({"mInventoryStacks": container(full(ORE_PATH, 3))}),
            2: entry({"mInventoryStacks": container(full(PLATE_PATH, 6), full("", 0))}),
        },
        records=(actor_record(BUILDING_CLASS_PATH), component_record(), component_record()),
    )

    result = inventory.inventory_of(model)

    expected_carriers = 2
    expected_stacks = 2
    assert result.carrier_count == expected_carriers
    assert result.unattributed_carrier_count == 1
    assert result.unattributed_stack_count == expected_stacks
    assert result.unattributed_item_count == 6  # noqa: PLR2004 - the planted count
    assert [rows_of(building) for building in result.buildings] == [[(ORE_KEY, 3)]]
    assert partition_holds(result) == []


def test_a_record_outside_the_table_claims_nothing() -> None:
    # Its kind cannot be read, so it is not known to be an actor.
    model = world(
        by_record_index={
            5: joined({}, (resolved(1),)),
            1: entry({"mInventoryStacks": container(full(ORE_PATH, 1))}),
        },
    )

    result = inventory.inventory_of(model)

    assert result.buildings == ()
    assert result.unattributed_carrier_count == 1
    assert partition_holds(result) == []


def test_a_resolved_target_with_no_properties_entry_is_counted() -> None:
    model = world(
        by_record_index={
            0: joined({}, (resolved(7), resolved(1), resolved(8))),
            1: entry({"mInventoryStacks": container(full(ORE_PATH, 2))}),
        },
        records=(actor_record(BUILDING_CLASS_PATH), component_record()),
    )

    result = inventory.inventory_of(model)

    expected_unwalked = 2
    assert result.references_to_unwalked == expected_unwalked
    # Counting the first unwalked target must not stop the walk of the rest.
    assert [rows_of(building) for building in result.buildings] == [[(ORE_KEY, 2)]]


def test_a_building_carries_its_own_container_and_undecoded_counts() -> None:
    model = building_world(full(ORE_PATH, 2), None, None)

    result = inventory.inventory_of(model)

    expected_undecoded = 2
    building = result.buildings[0]
    assert building.containers_read == 1
    assert building.undecoded_entry_count == expected_undecoded
    assert result.undecoded_entry_count == expected_undecoded


def test_a_disagreeing_stack_is_never_counted_as_state_undecoded() -> None:
    model = building_world(full(ORE_PATH, 0, state_undecoded=True))

    result = inventory.inventory_of(model)

    assert result.excluded == ((inventory.EXCLUDED_COUNT_DISAGREES, 1),)
    assert result.state_undecoded_count == 0
    assert result.buildings[0].state_undecoded_count == 0


def test_the_partition_invariant_holds_over_every_shape_at_once() -> None:
    model = world(
        by_record_index={
            0: joined({}, (resolved(3), resolved(4))),
            1: joined({}, (resolved(5),)),
            2: joined({}, (resolved(5), resolved(6))),
            3: entry({"mInventoryStacks": container(full(ORE_PATH, 7), full("", 0))}),
            4: entry({"mInventoryStacks": container(full(PLATE_PATH, 2), save_stack(NumItems=1))}),
            5: entry({"mInventoryStacks": container(full(ORE_PATH, 11))}),
            6: entry({"mInventoryStacks": container(full(PLATE_PATH, 13), full(ORE_PATH, 0))}),
            7: entry({"mInventoryStacks": container(full(ORE_PATH, 17))}),
        },
        records=(
            actor_record(BUILDING_CLASS_PATH),
            actor_record(BUILDING_CLASS_PATH),
            actor_record(BUILDING_CLASS_PATH),
            component_record(),
            component_record(),
            component_record(),
            component_record(),
            component_record(),
        ),
    )

    result = inventory.inventory_of(model)

    expected_buildings = 2
    expected_conflict_items = 11
    expected_unattributed_items = 17
    assert len(result.buildings) == expected_buildings
    assert result.conflict_item_count == expected_conflict_items
    assert result.unattributed_item_count == expected_unattributed_items
    assert partition_holds(result) == []


def test_no_item_class_path_reaches_any_repr() -> None:
    # Q7: an item class path is WORLD CONTENT for echo purposes. Only the
    # reduced key is published. ``ItemTotal``'s generated repr renders that
    # key - the ACCEPTED DISCLOSURE ``tests/repr_rendering_guard.py`` records
    # for it - so this arm grades the world and building reprs, which withhold
    # it, and never ``ItemTotal``'s.
    planted_path = "/Game/" + PATH_MARKER + "/Desc_SyntheticOre.Desc_SyntheticOre_C"
    model = building_world(full(planted_path, 2))

    result = inventory.inventory_of(model)
    walked = reachable(result)
    leaked = sum(1 for value in walked if isinstance(value, str) and PATH_MARKER in value)
    rendered = repr(result) + repr(result.buildings)

    assert leaked == 0
    assert PATH_MARKER not in rendered
    assert ORE_KEY not in rendered
    assert BUILDING_CLASS not in rendered


def test_no_record_index_reaches_the_per_building_view() -> None:
    model = world(
        by_record_index={
            0: joined({}, (resolved(RECORD_INDEX_MARKER),)),
            RECORD_INDEX_MARKER: entry({"mInventoryStacks": container(full(ORE_PATH, 1))}),
        },
        records=(actor_record(BUILDING_CLASS_PATH),),
    )

    result = inventory.inventory_of(model)
    positions = sum(1 for value in reachable(result) if value == RECORD_INDEX_MARKER)

    assert len(result.buildings) == 1
    assert positions == 0


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
