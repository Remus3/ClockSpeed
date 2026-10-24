"""Synthetic saves for the phase-cost carrier and the space elevator - CS-1340, CS-1348.

HAND-AUTHORED, NEVER A SLICE OF A REAL SAVE (CLAUDE.md section 7). Every byte
below is built from the public primitives in ``tests/save/synthetic.py`` and
the legacy tag grammar ``tests/save/test_container_elements.py`` and
``tests/save/test_inventory_item.py`` already encode, so the whole module runs
on a machine with no game install and no save library.

WHAT IS MEASURED AND WHAT IS INVENTED. The CLASS PATHS of the two carriers and
the SHAPES of their values are the ones
``docs/adr/0016-unlock-arrays-carriers-and-serialized-grammar.md`` records:
``mGamePhaseCosts`` is an array of ``PhaseCost`` structs whose ``gamePhase`` is
a ``ByteProperty`` naming an ``EGamePhase`` member and whose ``cost`` is an
array of ``ItemAmount`` structs carrying an ``ItemClass`` asset reference and
an ``Amount`` integer; the elevator's ``mInputInventory`` reference lands on an
inventory component carrying ``mInventoryStacks``. The instance names, the
phase tokens and the item paths are INVENTED - none names a real asset - so a
rendering that carries one can only have got it from here.

The pair is the one the decodable fixture was built at, taken from the fixture
rather than written down, for the reason ``tests/save/test_world.py`` gives.
"""

from __future__ import annotations

import struct
from typing import Final

from clockspeed.save import objects
from tests.save import synthetic

#: The measured carrier class paths (ADR 0016 records them).
PHASE_MANAGER_CLASS: Final = (
    "/Game/FactoryGame/Schematics/Progression/BP_GamePhaseManager.BP_GamePhaseManager_C"
)
ELEVATOR_CLASS: Final = (
    "/Game/FactoryGame/Buildable/Factory/SpaceElevator/Build_SpaceElevator.Build_SpaceElevator_C"
)
INVENTORY_CLASS: Final = "/Script/FactoryGame.FGInventoryComponent"

#: A class that is NOT the phase manager, for the wrong-owner arm.
STRANGER_CLASS: Final = "/Script/FactoryGame.FGSessionInformationModel"

#: The measured property and interior names.
PHASE_COSTS_PROPERTY: Final = "mGamePhaseCosts"
INPUT_PROPERTY: Final = "mInputInventory"
STACKS_PROPERTY: Final = "mInventoryStacks"

ROOT: Final = "Persistent_Level:PersistentLevel"
LEVEL_NAME: Final = "Persistent_Level:SyntheticElevatorCell_0"
MANAGER_INSTANCE: Final = "Persistent_Level:PersistentLevel.SyntheticPhaseManager_0"
ELEVATOR_INSTANCE: Final = "Persistent_Level:PersistentLevel.SyntheticElevator_0"
INPUT_INSTANCE: Final = "Persistent_Level:PersistentLevel.SyntheticElevator_0.InputInventory"

#: Invented phase tokens, in the measured ``EGP_`` shape.
PAID_PHASE: Final = "EGP_SynthPhasePaid"
OWED_PHASE: Final = "EGP_SynthPhaseOwed"

#: Invented item asset paths, in the measured ``/Game/...`` asset shape.
PART_A_PATH: Final = "/Game/Synthetic/Parts/Desc_SynthPartA.Desc_SynthPartA_C"
PART_B_PATH: Final = "/Game/Synthetic/Parts/Desc_SynthPartB.Desc_SynthPartB_C"
PART_A: Final = "Desc_SynthPartA_C"
PART_B: Final = "Desc_SynthPartB_C"

_TRAILING: Final = b"\x11\x22\x33\x44\x55\x66\x77\x88"

#: One phase-cost entry: a phase token and its ``(item path, amount)`` lines.
PhaseEntry = tuple[str, tuple[tuple[str, int], ...]]

#: The default array: a phase the world has paid in full, then one it owes.
DEFAULT_ENTRIES: Final[tuple[PhaseEntry, ...]] = (
    (PAID_PHASE, ((PART_A_PATH, 0),)),
    (OWED_PHASE, ((PART_A_PATH, 2500), (PART_B_PATH, 100))),
)


def _i32(value: int) -> bytes:
    """One little-endian signed 32-bit field.

    Args:
        value: The integer.

    Returns:
        Its four bytes.
    """
    return struct.pack("<i", value)


def tag_list(*tags: bytes) -> bytes:
    """A nested tag list, terminator included.

    Args:
        *tags: The encoded tags.

    Returns:
        The list bytes.
    """
    return b"".join(tags) + synthetic.fstring(synthetic.PROPERTY_TERMINATOR)


def int_tag(name: str, value: int) -> bytes:
    """One ``IntProperty`` tag.

    Args:
        name: The property name.
        value: The int32.

    Returns:
        The whole tag.
    """
    return synthetic.property_tag(name, "IntProperty", _i32(value))


def enum_byte_tag(name: str, enum_word: str, member: str) -> bytes:
    """The enum-named shape of a ``ByteProperty`` - the measured ``gamePhase`` grammar.

    Args:
        name: The property name.
        enum_word: The enum the tag names.
        member: The member name carried as the value.

    Returns:
        The whole tag.
    """
    return synthetic.property_tag(
        name, "ByteProperty", synthetic.fstring(member), tag_extra=synthetic.fstring(enum_word)
    )


def asset_reference_tag(name: str, path: str) -> bytes:
    """One ``ObjectProperty`` naming a game asset, its level half EMPTY.

    Args:
        name: The property name.
        path: The object path.

    Returns:
        The whole tag.
    """
    value = synthetic.fstring("") + synthetic.fstring(path)
    return synthetic.property_tag(name, objects.REFERENCE_TYPE_WORD, value)


def record_reference_tag(name: str, path: str) -> bytes:
    """One top-level ``ObjectProperty`` naming a record in the persistent level.

    Args:
        name: The property name.
        path: The instance path the reference names.

    Returns:
        The whole tag.
    """
    value = synthetic.fstring(synthetic.MAP_NAME) + synthetic.fstring(path)
    return synthetic.property_tag(name, objects.REFERENCE_TYPE_WORD, value)


def int_array_tag(name: str, values: tuple[int, ...]) -> bytes:
    """A legacy ``ArrayProperty`` of ``IntProperty`` - elements that are NOT structs.

    Args:
        name: The property name.
        values: The int32 elements, in file order.

    Returns:
        The whole tag.
    """
    return synthetic.property_tag(
        name,
        "ArrayProperty",
        _i32(len(values)) + b"".join(_i32(value) for value in values),
        tag_extra=synthetic.fstring("IntProperty"),
    )


def struct_array_tag(name: str, struct_word: str, elements: tuple[bytes, ...]) -> bytes:
    """A legacy ``ArrayProperty`` of ``StructProperty`` carrying those element tag lists.

    Args:
        name: The property name.
        struct_word: The struct word the inner tag names.
        elements: The element tag lists, in file order.

    Returns:
        The whole tag.
    """
    region = b"".join(elements)
    inner = (
        synthetic.fstring(name)
        + synthetic.fstring(objects.STRUCT_TYPE_WORD)
        + _i32(len(region))
        + _i32(0)
        + synthetic.fstring(struct_word)
        + bytes(objects.GUID_BYTES)
        + b"\x00"
    )
    return synthetic.property_tag(
        name,
        "ArrayProperty",
        _i32(len(elements)) + inner + region,
        tag_extra=synthetic.fstring(objects.STRUCT_TYPE_WORD),
    )


def item_amount(path: str, amount: int) -> bytes:
    """One ``ItemAmount`` element: an asset reference and an integer amount.

    Args:
        path: The item's asset path.
        amount: The amount.

    Returns:
        The element tag list.
    """
    return tag_list(asset_reference_tag("ItemClass", path), int_tag("Amount", amount))


def phase_cost(phase: str, lines: tuple[tuple[str, int], ...]) -> bytes:
    """One ``PhaseCost`` element in the measured grammar.

    Args:
        phase: The ``EGamePhase`` member.
        lines: Each ``(item path, amount)``.

    Returns:
        The element tag list.
    """
    return tag_list(
        enum_byte_tag("gamePhase", "EGamePhase", phase),
        struct_array_tag("cost", "ItemAmount", tuple(item_amount(p, n) for p, n in lines)),
    )


def phase_costs_tag(entries: tuple[PhaseEntry, ...] = DEFAULT_ENTRIES) -> bytes:
    """The whole ``mGamePhaseCosts`` tag.

    Args:
        entries: Each ``(phase token, lines)``.

    Returns:
        The tag.
    """
    return struct_array_tag(
        PHASE_COSTS_PROPERTY, "PhaseCost", tuple(phase_cost(p, lines) for p, lines in entries)
    )


def native_string(text: str) -> bytes:
    """A string as the native item bytes write it: empty is a bare zero count.

    Args:
        text: ASCII text.

    Returns:
        The encoded string.
    """
    return _i32(0) if not text else synthetic.fstring(text)


def item_struct_tag(class_path: str) -> bytes:
    """The ``Item`` tag of one stack: a native ``InventoryItem`` in its NEW form.

    Args:
        class_path: The item class path, or empty for an empty slot.

    Returns:
        The whole tag.
    """
    interior = native_string("") + native_string(class_path) + _i32(0)
    words = objects._TAG_EXTRA_STRINGS[objects.STRUCT_TYPE_WORD]  # noqa: SLF001
    extra = b"".join(
        synthetic.fstring(objects.INVENTORY_ITEM_STRUCT_WORD) for _ in range(words)
    ) + bytes(objects.GUID_BYTES)
    return synthetic.property_tag("Item", objects.STRUCT_TYPE_WORD, interior, tag_extra=extra)


def stack(class_path: str, count: int) -> bytes:
    """One ``InventoryStack`` element.

    Args:
        class_path: The item class path, or empty for an empty slot.
        count: ``NumItems``.

    Returns:
        The element tag list.
    """
    return tag_list(item_struct_tag(class_path), int_tag("NumItems", count))


#: Six empty slots - the shape every measured elevator in the library carried.
EMPTY_SLOTS: Final[tuple[tuple[str, int], ...]] = (("", 0),) * 6


def _level_body(
    objects_: tuple[synthetic.SyntheticObject, ...],
    components: tuple[synthetic.SyntheticComponent, ...],
    payloads: tuple[bytes, ...],
) -> bytes:
    """A whole save whose one named level holds the supplied records.

    Args:
        objects_: The actor records.
        components: The component records, after the actors.
        payloads: One payload per record, actors first.

    Returns:
        The save bytes.
    """
    fixture = synthetic.SAVE_LEVELLED_DECODABLE
    header_version, save_version = fixture.header_version, fixture.save_version
    named = synthetic.SyntheticLevel(
        name=LEVEL_NAME, objects=objects_, components=components, payloads=payloads
    )
    persistent = synthetic.SyntheticLevel(
        name=None, second_collectables=(synthetic.SyntheticCollectable(),)
    )
    body = synthetic.build_levelled_body(
        (named,),
        persistent,
        header_version=header_version,
        save_version=save_version,
        grids=synthetic.LEVELLED_GRIDS,
    )
    head = synthetic.build_header(header_version=header_version, save_version=save_version)
    payload = synthetic.body_with_prefix(body, header_version)
    return head + synthetic.build_chunks(payload, framing=synthetic.default_framing(header_version))


def _actor_payload(tags: tuple[bytes, ...], components: tuple[str, ...] = ()) -> bytes:
    """One actor payload.

    Args:
        tags: The tags, in file order.
        components: The component paths the head lists.

    Returns:
        The payload.
    """
    return synthetic.tagged_property_payload(
        tags,
        head=synthetic.actor_payload_head(synthetic.MAP_NAME, ROOT, components),
        trailing=_TRAILING,
    )


def save_blob(
    *,
    manager_tags: tuple[bytes, ...] | None = (),
    extra_actors: tuple[tuple[str, str, tuple[bytes, ...]], ...] = (),
    slots: tuple[tuple[str, int], ...] | None = None,
    elevators: int = 1,
    input_target: str = INPUT_INSTANCE,
    inventory_tags: tuple[bytes, ...] | None = None,
    input_references: int = 1,
) -> bytes:
    """A save holding a phase manager, optional other actors and an optional elevator.

    Args:
        manager_tags: The phase manager's tags, or None for no manager record.
        extra_actors: Each ``(class path, instance, tags)`` of a further actor.
        slots: The elevator input inventory's stacks as ``(class path, count)``,
            or None for a save with no elevator at all.
        elevators: How many elevator actors to write when ``slots`` is given.
        input_target: The instance path the elevator's ``mInputInventory``
            reference names.
        inventory_tags: The input inventory component's tags, replacing the
            ``mInventoryStacks`` tag ``slots`` builds; None keeps that tag.
        input_references: How many ``mInputInventory`` tags each elevator
            writes - more than one is a repeated key.

    Returns:
        The save bytes.
    """
    actors: list[synthetic.SyntheticObject] = []
    payloads: list[bytes] = []
    if manager_tags is not None:
        actors.append(synthetic.SyntheticObject(PHASE_MANAGER_CLASS, ROOT, MANAGER_INSTANCE))
        payloads.append(_actor_payload(manager_tags))
    for class_path, instance, tags in extra_actors:
        actors.append(synthetic.SyntheticObject(class_path, ROOT, instance))
        payloads.append(_actor_payload(tags))
    components: list[synthetic.SyntheticComponent] = []
    component_payloads: list[bytes] = []
    if slots is not None:
        for index in range(elevators):
            instance = ELEVATOR_INSTANCE if index == 0 else f"{ELEVATOR_INSTANCE}{index}"
            actors.append(synthetic.SyntheticObject(ELEVATOR_CLASS, ROOT, instance))
            payloads.append(
                _actor_payload(
                    (record_reference_tag(INPUT_PROPERTY, input_target),) * input_references,
                    (INPUT_INSTANCE,),
                )
            )
        components.append(
            synthetic.SyntheticComponent(
                INVENTORY_CLASS, ROOT, INPUT_INSTANCE, parent_object_root=ELEVATOR_INSTANCE
            )
        )
        stacks = struct_array_tag(
            STACKS_PROPERTY, "InventoryStack", tuple(stack(path, n) for path, n in slots)
        )
        tags = (stacks,) if inventory_tags is None else inventory_tags
        component_payloads.append(synthetic.tagged_property_payload(tags, trailing=_TRAILING))
    return _level_body(tuple(actors), tuple(components), (*payloads, *component_payloads))


# ---------------------------------------------------------------------------
# CS-1348 amended - the target phase and its paid-off costs
# ---------------------------------------------------------------------------

#: The measured property names on the phase manager (ADR 0016, CS-1348 amended).
TARGET_PROPERTY: Final = "mTargetGamePhase"
PAID_OFF_PROPERTY: Final = "mTargetGamePhasePaidOffCosts"

#: An invented target phase in the measured ``GP_*`` asset shape, and its name
#: as the save's reference names it - the object path's final segment.
TARGET_PHASE: Final = "GP_SynthAssemblyPhase_2"
TARGET_PATH: Final = f"/Game/Synthetic/GamePhases/{TARGET_PHASE}.{TARGET_PHASE}"


def target_tag(path: str = TARGET_PATH) -> bytes:
    """The phase manager's top-level ``mTargetGamePhase`` asset reference.

    Args:
        path: The object path the reference names.

    Returns:
        The whole tag.
    """
    return asset_reference_tag(TARGET_PROPERTY, path)


def paid_off_tag(lines: tuple[tuple[str, int], ...]) -> bytes:
    """The ``mTargetGamePhasePaidOffCosts`` array of ``ItemAmount`` structs.

    Args:
        lines: Each ``(item path, amount)``, in file order.

    Returns:
        The whole tag.
    """
    return struct_array_tag(
        PAID_OFF_PROPERTY, "ItemAmount", tuple(item_amount(path, amount) for path, amount in lines)
    )
