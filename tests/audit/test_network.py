"""CS-1041: which node a miner sits on, joined by REFERENCE and never by distance.

Every fixture here is a hand-built synthetic ``WorldModel``. Nothing in this
module opens a save, a docs file or the install - see ``tests/audit/__init__.py``
for the four rules.

WHY A NEAREST-NEIGHBOUR ARM EXISTS AT ALL. Non-negotiable 7 forbids a proximity
fallback by name: nearest-neighbour renders a wrong answer that reads like a
right one, and a suite that cannot tell the two apart grades nothing. So the
fixture below is built so the two answers DISAGREE - the miner references the
FAR node and stands beside the near one - and two arms split the claim. One
grades the membership the reference join produces. The other grades that this
fixture can discriminate at all, by computing the proximity answer in the test
and asserting it differs, so the day someone flattens the fixture's geometry the
discrimination arm goes red rather than the acceptance arm going quietly vacuous.

STRUCTURE AND MEMBERSHIP ARE GRADED APART. A single arm asserting the whole
published tuple would let one half mask the other: a model that produced the
right count of entries in the wrong order, or the right mined set over a
truncated population, satisfies half of it. So the population's SHAPE - one
entry per published node, in order, carrying that node's class - is one arm, and
WHICH entries read mined is another.

WHY THIS MODULE IMPORTS A PRIVATE NAME. ``_INSTANCE_SEPARATOR`` is the save
layer's OWN rule for the character separating a level from the object inside it,
and ``clockspeed/audit/network.py`` restates it rather than importing it, because
reaching into the save package for a one-character constant would be the
reach-past-your-neighbour the seam discipline forbids. The restatement is pinned
here instead of trusted: this module is the only place in the package that
reaches for the save layer's own copy, on exactly the terms test_placement.py
reaches for its class-name helper, and the arm exists so the two cannot drift
apart silently.

WHAT THIS MODULE DELIBERATELY DOES NOT ASSERT is the property NAME a miner uses
to name its node. ``docs/adr/0003-s4-node-actors-in-save.md`` measured
``mExtractResourceNode`` at ZERO occurrences across three worlds and four game
builds, so no measured name exists in this tree to build a filter from. The join
is therefore over the TYPED reference population and is name-agnostic, and the
arms grade it that way.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import fields, is_dataclass
from types import MappingProxyType

from clockspeed.audit import network
from clockspeed.save import objects
from clockspeed.save.header import SaveHeader
from clockspeed.save.objects import ObjectReference
from clockspeed.save.world import _INSTANCE_SEPARATOR as SAVE_LAYER_INSTANCE_SEPARATOR
from clockspeed.save.world import (
    EMPTY_UNLOCK_STATE,
    NODE_CLASS_NAMES,
    RecordProperties,
    ResourceNode,
    WorldModel,
    WorldProperties,
)

# An invented 22-character base64url literal. Never a real world token.
SYNTHETIC_TOKEN = "ClockspeedNetworkTok1"  # noqa: S105 - an invented marker, not a secret

#: An obviously invented level prefix. No real world name appears in this file.
SYNTHETIC_LEVEL = "SyntheticLevel:SyntheticPersistent"

#: The referenced node's instance path, and the marker the refusal sweep hunts.
REFERENCED_NODE_INSTANCE = f"{SYNTHETIC_LEVEL}.SyntheticNodeQx72Alpha_C_7001"

#: The bare node's instance path - named by nothing, and nearer to the miner.
BARE_NODE_INSTANCE = f"{SYNTHETIC_LEVEL}.SyntheticNodeQx72Beta_C_7002"

#: The miner's own instance path.
MINER_INSTANCE = f"{SYNTHETIC_LEVEL}.SyntheticMinerQx72_C_7003"

#: A shipped asset path: no instance separator, so it names no record.
ASSET_PATH = "/Game/FactoryGame/Synthetic/SyntheticAssetQx72.SyntheticAssetQx72_C"

#: The property name the fixture's reference tag carries. INVENTED on purpose -
#: see the module docstring - so an implementation that filtered on a hardcoded
#: name would fail every arm here.
INVENTED_TAG_NAME = "mSyntheticQx72NodeTag"

#: The miner stands HERE, beside the bare node and far from the one it names.
MINER_POSITION = (900.0, 0.0, 0.0)

#: The referenced node, far away.
REFERENCED_NODE_POSITION = (0.0, 0.0, 0.0)

#: The bare node, right next to the miner.
BARE_NODE_POSITION = (1000.0, 0.0, 0.0)

FLOAT_MARKER = 8675309.5
MINER_CLASS = "Build_MinerMk1_C"


def node_class() -> str:
    """Pick one measured node class, deterministically.

    Returns:
        The class name every node fixture here is built with.
    """
    return sorted(NODE_CLASS_NAMES)[0]


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


def node(instance_name: str, position: tuple[float, float, float]) -> ResourceNode:
    """Build one published resource node.

    Args:
        instance_name: The node's instance path.
        position: Its world coordinates.

    Returns:
        The node.
    """
    return ResourceNode(
        class_name=node_class(),
        instance_name=instance_name,
        translation=position,
        rotation=(0.0, 0.0, 0.0, 1.0),
        scale=(1.0, 1.0, 1.0),
    )


def record(
    type_path: str,
    instance_name: str,
    position: tuple[float, float, float] = (0.0, 0.0, 0.0),
) -> objects.ObjectRecord:
    """Build one synthetic object record, CARRYING ITS TRANSFORM.

    The transform is not decoration. A nearest-neighbour implementation needs
    the miner's coordinates to compute the forbidden answer at all, and a
    fixture that withheld them would make that mutation crash rather than
    answer wrongly - which would redden the arm for the wrong reason and leave
    the proximity claim ungraded.

    Args:
        type_path: The class path.
        instance_name: The instance path.
        position: The record's world coordinates.

    Returns:
        The record.
    """
    return objects.ObjectRecord(
        kind=objects.KIND_ACTOR,
        type_path=type_path,
        root_object=instance_name,
        instance_name=instance_name,
        transform=objects.Transform(
            rotation=(0.0, 0.0, 0.0, 1.0),
            translation=position,
            scale=(1.0, 1.0, 1.0),
        ),
        parent=None,
        object_type=1,
        was_placed_in_level=0,
        body_offset=0,
        body_length=0,
    )


def entry(
    *references: ObjectReference,
    payload_read: bool = True,
) -> RecordProperties:
    """Build one record's published properties around a reference population.

    Args:
        references: The typed, tag-ordered references.
        payload_read: Whether the payload read under the measured grammar.

    Returns:
        The properties.
    """
    return RecordProperties(
        values=MappingProxyType({}),
        schema_name="SyntheticSchema",
        resolved=None,
        payload_read=payload_read,
        warning_codes=() if payload_read else (objects.WARN_UNPARSED_PROPERTY_PAYLOAD,),
        references=references,
    )


def reference(object_path: str, name: str = INVENTED_TAG_NAME) -> ObjectReference:
    """Build one decoded ObjectProperty value.

    Args:
        object_path: The value's second string - the join key.
        name: The tag's own name.

    Returns:
        The reference.
    """
    return ObjectReference(
        property_name=name,
        level_reference=SYNTHETIC_LEVEL,
        object_path=object_path,
    )


def world(
    *,
    nodes: tuple[ResourceNode, ...] = (),
    records: tuple[objects.ObjectRecord, ...] = (),
    by_record_index: Mapping[int, RecordProperties] | None = None,
) -> WorldModel:
    """Build a synthetic world model holding exactly what a test needs.

    Args:
        nodes: The published resource nodes.
        records: The object records.
        by_record_index: The per-record properties.

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
        nodes=nodes,
        warnings=(),
        properties=WorldProperties(by_record_index=MappingProxyType(dict(by_record_index or {}))),
    )


def one_node_one_miner() -> WorldModel:
    """Build THE acceptance fixture: one referenced node, one bare node, one miner.

    The miner stands beside the BARE node and references the FAR one, so the
    reference answer and the proximity answer disagree on every node.

    Returns:
        The model.
    """
    return world(
        nodes=(
            node(REFERENCED_NODE_INSTANCE, REFERENCED_NODE_POSITION),
            node(BARE_NODE_INSTANCE, BARE_NODE_POSITION),
        ),
        records=(
            record(node_class(), REFERENCED_NODE_INSTANCE, REFERENCED_NODE_POSITION),
            record(node_class(), BARE_NODE_INSTANCE, BARE_NODE_POSITION),
            record(MINER_CLASS, MINER_INSTANCE, MINER_POSITION),
        ),
        by_record_index={2: entry(reference(REFERENCED_NODE_INSTANCE))},
    )


def nearest_node_index(nodes: tuple[ResourceNode, ...]) -> int:
    """The index of the node nearest the miner - the FORBIDDEN answer.

    Computed here, in the test, and never in the shipped module. It exists so
    an arm can assert the shipped answer DIFFERS from it.

    Args:
        nodes: The published nodes.

    Returns:
        The index of the nearest one.
    """
    distances = [math.dist(node_entry.translation, MINER_POSITION) for node_entry in nodes]
    return distances.index(min(distances))


def reachable(value: object, seen: set[int] | None = None) -> list[object]:
    """Every value reachable from one object, the object itself included.

    STRUCTURAL on purpose - see the same helper in ``test_inventory.py``.

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


# ---------------------------------------------------------------------------
# Membership - WHICH nodes read mined
# ---------------------------------------------------------------------------


def test_a_referenced_node_reads_mined() -> None:
    result = network.network_of(one_node_one_miner())

    assert result.nodes[0].mined is True


def test_a_bare_node_reads_unmined() -> None:
    result = network.network_of(one_node_one_miner())

    assert result.nodes[1].mined is False


def test_the_mined_count_is_one_over_this_fixture() -> None:
    result = network.network_of(one_node_one_miner())

    assert result.mined_count == 1


# ---------------------------------------------------------------------------
# The forbidden fallback - the fixture must be able to tell the two apart
# ---------------------------------------------------------------------------


def test_the_proximity_answer_disagrees_with_the_published_one() -> None:
    """The discrimination control: this fixture CAN redden under nearest-neighbour."""
    model = one_node_one_miner()
    result = network.network_of(model)
    nearest = nearest_node_index(model.nodes)

    mined_indices = {index for index, use in enumerate(result.nodes) if use.mined}

    assert nearest not in mined_indices
    assert mined_indices == {0}


def test_a_node_nearer_the_miner_is_not_mined_for_being_near() -> None:
    model = one_node_one_miner()
    result = network.network_of(model)

    assert result.nodes[nearest_node_index(model.nodes)].mined is False


# ---------------------------------------------------------------------------
# Which population the join is in
# ---------------------------------------------------------------------------


def test_a_reference_carrying_no_instance_separator_joins_nothing() -> None:
    model = world(
        nodes=(node(REFERENCED_NODE_INSTANCE, REFERENCED_NODE_POSITION),),
        records=(record(MINER_CLASS, MINER_INSTANCE),),
        by_record_index={0: entry(reference(ASSET_PATH))},
    )

    result = network.network_of(model)

    assert result.nodes[0].mined is False
    assert result.instance_references_considered == 0
    assert result.reference_tags_considered == 1


def test_the_local_instance_separator_agrees_with_the_save_layers_own() -> None:
    assert network.INSTANCE_SEPARATOR == SAVE_LAYER_INSTANCE_SEPARATOR


def test_an_instance_path_naming_no_published_node_joins_nothing() -> None:
    model = world(
        nodes=(node(REFERENCED_NODE_INSTANCE, REFERENCED_NODE_POSITION),),
        records=(record(MINER_CLASS, MINER_INSTANCE),),
        by_record_index={0: entry(reference(MINER_INSTANCE))},
    )

    result = network.network_of(model)

    assert result.nodes[0].mined is False
    assert result.instance_references_considered == 1


# ---------------------------------------------------------------------------
# Structure - the SHAPE of the published population, graded apart
# ---------------------------------------------------------------------------


def test_one_entry_is_published_per_node_in_order() -> None:
    model = one_node_one_miner()
    result = network.network_of(model)

    assert len(result.nodes) == len(model.nodes)
    assert result.nodes_considered == len(model.nodes)


def test_every_entry_carries_its_own_nodes_class_name() -> None:
    model = one_node_one_miner()
    result = network.network_of(model)

    assert [use.class_name for use in result.nodes] == [n.class_name for n in model.nodes]


def test_two_runs_over_one_model_return_equal_models() -> None:
    model = one_node_one_miner()

    assert network.network_of(model) == network.network_of(model)


# ---------------------------------------------------------------------------
# Saying nothing, out loud
# ---------------------------------------------------------------------------


def test_a_world_whose_nodes_are_all_bare_is_flagged() -> None:
    model = world(
        nodes=(node(BARE_NODE_INSTANCE, BARE_NODE_POSITION),),
        records=(record(MINER_CLASS, MINER_INSTANCE),),
        by_record_index={0: entry()},
    )

    result = network.network_of(model)

    codes = {warning.code for warning in result.warnings}
    assert network.WARN_NETWORK_NO_NODE_JOINED in codes


def test_a_joined_world_is_not_flagged_as_unjoined() -> None:
    result = network.network_of(one_node_one_miner())

    codes = {warning.code for warning in result.warnings}
    assert network.WARN_NETWORK_NO_NODE_JOINED not in codes


def test_a_world_with_no_published_node_says_so_separately() -> None:
    result = network.network_of(world())

    codes = {warning.code for warning in result.warnings}
    assert network.WARN_NETWORK_NO_NODE_POPULATION in codes
    assert network.WARN_NETWORK_NO_NODE_JOINED not in codes


def test_the_unread_payload_count_travels_as_the_honest_denominator() -> None:
    model = world(
        nodes=(node(REFERENCED_NODE_INSTANCE, REFERENCED_NODE_POSITION),),
        records=(record(MINER_CLASS, MINER_INSTANCE),),
        by_record_index={0: entry(payload_read=False)},
    )

    result = network.network_of(model)

    assert result.unread_payload_count == 1
    assert result.records_considered == 1
    codes = {warning.code for warning in result.warnings}
    assert network.WARN_NETWORK_PAYLOAD_UNREAD in codes


def test_the_two_unanswered_questions_are_declared_rather_than_dropped() -> None:
    """CS-1041's item LINE names four questions and its acceptance grades two."""
    result = network.network_of(one_node_one_miner())

    assert result.belt_topology_available is False
    assert result.circuit_topology_available is False
    codes = {warning.code for warning in result.warnings}
    assert network.WARN_NETWORK_TOPOLOGY_UNAVAILABLE in codes


# ---------------------------------------------------------------------------
# Refusals, asserted structurally
# ---------------------------------------------------------------------------


def test_no_record_instance_name_reaches_the_network_model() -> None:
    model = one_node_one_miner()
    result = network.network_of(model)

    planted = [
        value
        for value in reachable(model)
        if isinstance(value, str) and REFERENCED_NODE_INSTANCE in value
    ]
    assert planted, "the walk cannot see the marker in the INPUT, so its absence proves nothing"

    leaked = [
        value
        for value in reachable(result)
        if isinstance(value, str) and REFERENCED_NODE_INSTANCE in value
    ]
    assert not leaked


def test_no_float_reaches_any_network_output_field() -> None:
    model = world(
        nodes=(node(REFERENCED_NODE_INSTANCE, (FLOAT_MARKER, 0.0, 0.0)),),
        records=(record(MINER_CLASS, MINER_INSTANCE),),
        by_record_index={0: entry(reference(REFERENCED_NODE_INSTANCE))},
    )
    result = network.network_of(model)

    control = [value for value in reachable(model) if type(value) is float]
    assert control, "the walk cannot see a float in the INPUT, so its absence proves nothing"

    assert not [value for value in reachable(result) if type(value) is float]


def test_no_network_type_annotates_a_carrier_field() -> None:
    for declared in (network.NodeUse, network.WorldNetwork):
        for field in fields(declared):
            assert "bytes" not in str(field.type)
            assert "Path" not in str(field.type)
