"""CS-978: the placement model over one world - geometry, counts, bounds, refusals.

Every fixture here is a hand-built synthetic ``WorldModel``. Nothing in this
module opens a save, a docs file or the install, and nothing here needs the game
to be present - see ``tests/audit/__init__.py`` for the four rules.

THE COORDINATE ASSERTIONS ARE ABOUT A STRING AND THAT IS THE POINT. The wire
forbids a JSON float (``clockspeed/surface/api/world.py``: a bare JSON number is
the IEEE double non-negotiable 6 keeps out of the answer path) and a rounding
done inside this layer cannot be undone by a consumer, so the model publishes
the shortest round-trip decimal rendering of the stored value. A test that
compared floats would be green against a model that published floats, which is
the one defect these arms exist to catch.
"""

from __future__ import annotations

import math
import struct
from collections.abc import Callable, Mapping
from dataclasses import fields, is_dataclass
from pathlib import Path
from typing import Final

import pytest

from clockspeed.audit import placement
from clockspeed.save import objects
from clockspeed.save.header import SaveHeader
from clockspeed.save.world import (
    EMPTY_UNLOCK_STATE,
    WARN_NODE_SEMANTICS_UNAVAILABLE,
    ResourceNode,
    WorldModel,
)

# An invented 22-character base64url literal. Never a real world token.
SYNTHETIC_TOKEN = "ClockspeedAuditToken0"  # noqa: S105 - an invented marker, not a secret

# The markers the refusal arms hunt for. Each is a value a correct model can
# never carry, planted in the INPUT so the walk has a control.
INSTANCE_NAME_MARKER = "SyntheticInstanceNameMarkerQx71"
PATH_MARKER = "SyntheticPathMarkerQx71"
BODY_OFFSET_MARKER = 987654321
BODY_LENGTH_MARKER = 987654322


#: The orientation every fixture carries unless it says otherwise. Exactly
#: representable in float32, so a rendered expectation is exact rather than
#: approximately right.
IDENTITY_ROTATION: Final = (0.0, 0.0, 0.0, 1.0)
IDENTITY_SCALE: Final = (1.0, 1.0, 1.0)

#: A distinctive orientation, every component exactly representable. Chosen so
#: an arm that asserted the identity by accident would fail. DELIBERATELY NOT A
#: UNIT QUATERNION (CS-1021): the placement model transcribes and never
#: normalises, so a non-unit value grades that transcription exactly as well as
#: a unit one would. It is a needle, not an orientation the game produces.
#:
#: RE-PICKED UNDER CS-1037, WITH ``PLANTED_SCALE``. The earlier pair shared
#: ``0.5``, so the float sweep's membership control for one of seven components
#: was satisfied by the other block. Every component below is now a distinct
#: multiple of 1/32 with a distinct magnitude, none of whose renderings contains
#: another - ``test_every_planted_needle_is_unique_to_the_value_it_proves``
#: measures that rather than trusting it.
PLANTED_ROTATION: Final = (0.40625, -0.28125, 0.15625, 0.84375)
PLANTED_SCALE: Final = (2.21875, 0.71875, -1.34375)

#: The component counts each orientation block carries. Named so an arm states
#: its expectation rather than comparing two collections that are both empty.
ROTATION_COMPONENTS: Final = 4
SCALE_COMPONENTS: Final = 3

#: One node and one built placement. Named so an arm that grades "both
#: populations widened" states its expectation rather than asserting non-empty.
BOTH_POPULATIONS: Final = 2


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
    rotation: tuple[float, float, float, float] = IDENTITY_ROTATION,
    scale: tuple[float, float, float] = IDENTITY_SCALE,
) -> objects.ObjectRecord:
    """Build one synthetic actor record.

    Args:
        type_path: The class path, namespaced or bare.
        translation: The placement, or None for a record carrying no transform.
        instance_name: The instance name. Defaults to the refusal marker, so
            EVERY fixture in this module plants it without having to say so.
        rotation: The quaternion, in file order. Defaults to the identity.
        scale: The per-axis scale. Defaults to unity.

    Returns:
        The record.
    """
    transform = (
        None
        if translation is None
        else objects.Transform(
            rotation=rotation,
            translation=translation,
            scale=scale,
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
        body_offset=BODY_OFFSET_MARKER,
        body_length=BODY_LENGTH_MARKER,
    )


def table(records: tuple[objects.ObjectRecord, ...]) -> objects.ObjectTable:
    """Build a synthetic object table around the given records.

    Args:
        records: The records, in order.

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
        level_count=1,
    )


def world(
    *,
    nodes: tuple[ResourceNode, ...] = (),
    records: tuple[objects.ObjectRecord, ...] = (),
) -> WorldModel:
    """Build a synthetic world model holding exactly what a test needs.

    Args:
        nodes: The resource nodes.
        records: The object records.

    Returns:
        The model.
    """
    return WorldModel(
        token=SYNTHETIC_TOKEN,
        header=header(),
        objects=table(records),
        unlocks=EMPTY_UNLOCK_STATE,
        nodes=nodes,
        warnings=(),
    )


def node(
    class_name: str,
    translation: tuple[float, float, float],
    *,
    rotation: tuple[float, float, float, float] = IDENTITY_ROTATION,
    scale: tuple[float, float, float] = IDENTITY_SCALE,
) -> ResourceNode:
    """Build one synthetic resource node carrying the instance-name marker.

    Args:
        class_name: One of the measured node classes.
        translation: The placement.
        rotation: The quaternion, in file order. Defaults to the identity.
        scale: The per-axis scale. Defaults to unity.

    Returns:
        The node.
    """
    return ResourceNode(
        class_name=class_name,
        instance_name=INSTANCE_NAME_MARKER,
        translation=translation,
        rotation=rotation,
        scale=scale,
    )


def reachable(value: object, seen: set[int] | None = None) -> list[object]:
    """Every value reachable from one object, the object itself included.

    Walks dataclass fields, mappings and sequences. STRUCTURAL on purpose: an
    assertion that named today's field list would pass unchanged the day a field
    is added, which is the defect these arms exist to catch.

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


#: The two off-allowlist buildables the arm below plants. Named so the
#: assertion compares against a stated expectation rather than a literal.
EXPECTED_SKIPPED: Final = 2


def test_a_built_class_off_the_allowlist_is_counted_rather_than_dropped() -> None:
    """Every skipped buildable is reported, so the view states its own coverage.

    THE ALLOWLIST IS THE RIGHT SHAPE AND THE SILENCE WAS NOT. In the world this
    project develops against the great majority of built actors are belts,
    pipes, poles and power lines; plotting them would bury everything a reader
    acts on, and dropping them without a word renders a fraction of a factory
    as though it were the whole of it. The count is the difference between a
    view that is filtered and a view that is wrong.
    """
    model = world(
        records=(
            actor("Build_MinerMk1_C", (1.0, 2.0, 3.0)),
            actor("Build_ConveyorBeltMk2_C", (4.0, 5.0, 6.0)),
            actor("Build_PowerLine_C", (7.0, 8.0, 9.0)),
        )
    )

    result = placement.placement_of(model)

    assert len(result.built_placements) == 1, result.built_placements
    codes = {warning.code: warning.count for warning in result.warnings}
    skipped = codes.get(placement.WARN_BUILT_CLASS_NOT_PLOTTED)
    assert skipped == EXPECTED_SKIPPED, (
        f"{EXPECTED_SKIPPED} buildables were skipped and the model reports {skipped}"
    )


def test_every_node_becomes_one_placement_carrying_its_class_and_coordinates() -> None:
    model = world(
        nodes=(
            node("BP_ResourceNode_C", (1.0, 2.0, 3.0)),
            node("BP_ResourceDeposit_C", (-4.5, 5.25, -6.75)),
        )
    )

    result = placement.placement_of(model)

    assert [(entry.class_name, entry.x, entry.y, entry.z) for entry in result.node_placements] == [
        ("BP_ResourceNode_C", "1.0", "2.0", "3.0"),
        ("BP_ResourceDeposit_C", "-4.5", "5.25", "-6.75"),
    ]


def test_a_coordinate_leaves_as_the_shortest_round_trip_decimal_string() -> None:
    # A float32 value widened to a double. Its shortest round-trip rendering has
    # a long tail, and a model that rounded it would publish a coordinate no
    # consumer can undo.
    stored = struct.unpack("<f", struct.pack("<f", 0.1))[0]
    model = world(nodes=(node("BP_ResourceNode_C", (stored, 0.0, 0.0)),))

    rendered = placement.placement_of(model).node_placements[0].x

    assert rendered == repr(stored)
    assert float(rendered) == stored


def test_no_float_reaches_any_placement_output_field() -> None:
    model = world(
        nodes=(node("BP_ResourceNode_C", (1.5, 2.5, 3.5)),),
        records=(actor("Build_MinerMk1_C", (4.5, 5.5, 6.5)),),
    )

    floats_out = [item for item in reachable(placement.placement_of(model)) if type(item) is float]
    floats_in = [item for item in reachable(model) if type(item) is float]

    # The control: the walk CAN see a float, and the input is full of them.
    assert floats_in != []
    assert floats_out == []


def test_no_node_instance_name_reaches_the_placement_model() -> None:
    model = world(
        nodes=(node("BP_ResourceNode_C", (1.0, 2.0, 3.0)),),
        records=(actor("Build_MinerMk1_C", (4.0, 5.0, 6.0)),),
    )
    result = placement.placement_of(model)

    strings_out = [item for item in reachable(result) if isinstance(item, str)]
    leaked = [item for item in strings_out if INSTANCE_NAME_MARKER in item]

    assert [item for item in reachable(model) if item == INSTANCE_NAME_MARKER] != []
    assert leaked == []
    assert INSTANCE_NAME_MARKER not in repr(result)


def test_no_record_index_offset_or_path_reaches_the_placement_model() -> None:
    model = world(records=(actor("Build_MinerMk1_C", (1.0, 2.0, 3.0)),))
    result = placement.placement_of(model)
    walked = reachable(result)

    positions = [item for item in walked if item in (BODY_OFFSET_MARKER, BODY_LENGTH_MARKER)]
    paths = [item for item in walked if isinstance(item, (Path, bytes, bytearray))]
    path_strings = [item for item in walked if isinstance(item, str) and PATH_MARKER in item]

    assert [item for item in reachable(model) if item == BODY_OFFSET_MARKER] != []
    assert positions == []
    assert paths == []
    assert path_strings == []


def test_no_placement_type_annotates_a_carrier_field() -> None:
    # `bytes` and `Path` are the two annotations that can render raw save
    # content or a home directory. Graded on the ANNOTATION rather than on a
    # value, so a carrier that happens to be empty in every fixture is caught.
    carriers = {"bytes", "bytearray", "Path", "pathlib.Path"}
    declared = {
        field.type if isinstance(field.type, str) else getattr(field.type, "__name__", "")
        for published in (
            placement.Placement,
            placement.AxisBounds,
            placement.WorldBounds,
            placement.WorldPlacement,
        )
        for field in fields(published)
    }

    assert declared & carriers == set()


def test_only_an_allowlisted_built_class_is_published() -> None:
    model = world(
        records=(
            actor("Build_MinerMk1_C", (1.0, 1.0, 1.0)),
            actor("/Game/Synthetic/Build_NotOnTheAllowlist.Build_NotOnTheAllowlist_C", (2.0,) * 3),
            actor("Build_SmelterMk1_C", (3.0, 3.0, 3.0)),
        )
    )

    result = placement.placement_of(model)

    assert [entry.class_name for entry in result.built_placements] == [
        "Build_MinerMk1_C",
        "Build_SmelterMk1_C",
    ]


def test_a_namespaced_allowlisted_path_still_matches_on_its_class_name() -> None:
    model = world(
        records=(
            actor(
                "/Game/FactoryGame/Buildable/Factory/MinerMk1/Build_MinerMk1.Build_MinerMk1_C",
                (7.0, 8.0, 9.0),
            ),
        )
    )

    result = placement.placement_of(model)

    assert [entry.class_name for entry in result.built_placements] == ["Build_MinerMk1_C"]


def test_the_allowlist_is_a_closed_frozenset_and_not_a_denylist() -> None:
    # An allowlist over class names is the whole design. A denylist leaks: one
    # defect wore four different fields across four green commits in this
    # project's own history, and only an allowlist of good values held.
    assert type(placement.BUILT_CLASS_ALLOWLIST) is frozenset
    assert frozenset() != placement.BUILT_CLASS_ALLOWLIST
    assert all(name.startswith("Build_") for name in placement.BUILT_CLASS_ALLOWLIST)


def test_per_class_counts_cover_both_populations() -> None:
    model = world(
        nodes=(
            node("BP_ResourceNode_C", (1.0, 1.0, 1.0)),
            node("BP_ResourceNode_C", (2.0, 2.0, 2.0)),
            node("BP_FrackingCore_C", (3.0, 3.0, 3.0)),
        ),
        records=(
            actor("Build_MinerMk1_C", (4.0, 4.0, 4.0)),
            actor("Build_MinerMk1_C", (5.0, 5.0, 5.0)),
        ),
    )

    result = placement.placement_of(model)

    assert dict(result.node_counts) == {"BP_FrackingCore_C": 1, "BP_ResourceNode_C": 2}
    assert dict(result.built_counts) == {"Build_MinerMk1_C": 2}


def test_bounds_span_every_placement_on_every_axis() -> None:
    model = world(
        nodes=(node("BP_ResourceNode_C", (-10.0, 0.0, 5.0)),),
        records=(actor("Build_MinerMk1_C", (20.0, -30.0, 2.0)),),
    )

    bounds = placement.placement_of(model).bounds

    assert bounds is not None
    assert (bounds.x.min_value, bounds.x.max_value) == ("-10.0", "20.0")
    assert (bounds.y.min_value, bounds.y.max_value) == ("-30.0", "0.0")
    assert (bounds.z.min_value, bounds.z.max_value) == ("2.0", "5.0")


def test_an_empty_world_yields_a_valid_model_rather_than_an_exception() -> None:
    result = placement.placement_of(world())

    assert result.node_placements == ()
    assert result.built_placements == ()
    assert dict(result.node_counts) == {}
    assert dict(result.built_counts) == {}


def test_an_empty_world_has_no_bounds_and_says_so_rather_than_boxing_none() -> None:
    result = placement.placement_of(world())

    # A box whose six fields are None is the forbidden shape: it reads as a
    # bounding box that was computed and came back empty. Absence of the box,
    # plus the code naming why, is the honest rendering.
    assert result.bounds is None
    assert placement.WARN_PLACEMENT_BOUNDS_UNDEFINED in [
        warning.code for warning in result.warnings
    ]


def test_a_world_with_no_built_actor_still_yields_bounds_over_its_nodes() -> None:
    model = world(nodes=(node("BP_ResourceNodeGeyser_C", (1.0, 2.0, 3.0)),))

    result = placement.placement_of(model)

    assert result.built_placements == ()
    assert result.bounds is not None
    assert result.bounds.x.min_value == "1.0"
    assert placement.WARN_PLACEMENT_BOUNDS_UNDEFINED not in [
        warning.code for warning in result.warnings
    ]


def test_node_semantics_unavailable_is_flagged_rather_than_left_to_inference() -> None:
    # ADR 0003 measured that a node's resource type and purity are NOT IN A
    # SAVE. Without this flag a consumer showing unlabelled dots would read the
    # absence of labels as all there is to know.
    model = world(nodes=(node("BP_ResourceNode_C", (1.0, 1.0, 1.0)),))

    warnings = {warning.code: warning for warning in placement.placement_of(model).warnings}

    assert WARN_NODE_SEMANTICS_UNAVAILABLE in warnings
    assert warnings[WARN_NODE_SEMANTICS_UNAVAILABLE].count == 1
    assert warnings[WARN_NODE_SEMANTICS_UNAVAILABLE].detail != ""


def test_the_semantics_flag_is_a_field_as_well_as_a_warning() -> None:
    result = placement.placement_of(world(nodes=(node("BP_ResourceNode_C", (0.0, 0.0, 0.0)),)))

    assert result.node_semantics_available is False


def test_an_allowlisted_record_with_no_transform_is_skipped_and_flagged() -> None:
    model = world(
        records=(
            actor("Build_MinerMk1_C", None),
            actor("Build_MinerMk1_C", (1.0, 1.0, 1.0)),
        )
    )

    result = placement.placement_of(model)
    warnings = {warning.code: warning for warning in result.warnings}

    assert len(result.built_placements) == 1
    assert placement.WARN_BUILT_TRANSFORM_ABSENT in warnings
    assert warnings[placement.WARN_BUILT_TRANSFORM_ABSENT].count == 1


@pytest.mark.parametrize("bad", [math.inf, -math.inf, math.nan])
def test_a_non_finite_coordinate_is_skipped_and_flagged_rather_than_widening_bounds(
    bad: float,
) -> None:
    model = world(
        nodes=(
            node("BP_ResourceNode_C", (bad, 0.0, 0.0)),
            node("BP_ResourceNode_C", (1.0, 2.0, 3.0)),
        )
    )

    result = placement.placement_of(model)
    codes = [warning.code for warning in result.warnings]

    assert len(result.node_placements) == 1
    assert placement.WARN_PLACEMENT_COORDINATE_NON_FINITE in codes
    assert result.bounds is not None
    assert result.bounds.x.max_value == "1.0"


def test_the_local_class_name_rule_agrees_with_the_save_layers_own() -> None:
    # This layer consumes the world MODEL, not the save package, so it owns its
    # own path-to-class-name reduction. The two must agree or a built actor is
    # matched against the allowlist by a different rule than the one the save
    # layer matched a node with. This arm is the anti-drift pin; it is the only
    # place in this package that reaches for the save layer's own helper.
    samples = (
        "Build_MinerMk1_C",
        "/Game/FactoryGame/Buildable/Factory/MinerMk1/Build_MinerMk1.Build_MinerMk1_C",
        "Modded/Thing.Build_SyntheticModded_C",
        "",
    )

    assert [placement.class_name_of_path(item) for item in samples] == [
        objects.class_name_of(item) for item in samples
    ]


def test_two_runs_over_one_model_return_equal_models() -> None:
    model = world(
        nodes=(
            node("BP_ResourceNode_C", (1.0, 2.0, 3.0)),
            node("BP_FrackingSatellite_C", (4.0, 5.0, 6.0)),
        ),
        records=(
            actor("Build_SmelterMk1_C", (7.0, 8.0, 9.0)),
            actor("Build_MinerMk1_C", (10.0, 11.0, 12.0)),
        ),
    )

    first = placement.placement_of(model)
    second = placement.placement_of(model)

    assert first == second
    assert list(first.node_counts.items()) == list(second.node_counts.items())
    assert list(first.built_counts.items()) == list(second.built_counts.items())


def test_the_counts_iterate_in_a_stable_sorted_order() -> None:
    model = world(
        nodes=(
            node("BP_ResourceNodeGeyser_C", (1.0, 1.0, 1.0)),
            node("BP_FrackingCore_C", (2.0, 2.0, 2.0)),
            node("BP_ResourceNode_C", (3.0, 3.0, 3.0)),
        )
    )

    keys = list(placement.placement_of(model).node_counts)

    assert keys == sorted(keys)


# ---------------------------------------------------------------------------
# CS-1013: orientation - the rotation and the scale the audit seam used to drop
# ---------------------------------------------------------------------------


def test_a_built_placement_carries_its_rotation_and_scale_as_exact_strings() -> None:
    """``Transform`` parsed all three blocks and this seam published one of them.

    The rotation and the scale are the SAME KIND OF VALUE as a coordinate - a
    stored float the wire may not carry as a JSON number - so they leave on the
    same terms, as shortest round-trip decimal strings.
    """
    model = world(
        records=(
            actor(
                "Build_MinerMk1_C",
                (1.0, 2.0, 3.0),
                rotation=PLANTED_ROTATION,
                scale=PLANTED_SCALE,
            ),
        )
    )

    placed = placement.placement_of(model).built_placements[0]
    rotation = placed.rotation
    scale = placed.scale

    assert rotation is not None, "the rotation was withheld"
    assert scale is not None, "the scale was withheld"
    assert rotation == tuple(repr(part) for part in PLANTED_ROTATION), rotation
    assert scale == tuple(repr(part) for part in PLANTED_SCALE), scale
    assert len(rotation) == ROTATION_COMPONENTS
    assert len(scale) == SCALE_COMPONENTS


def test_an_orientation_component_leaves_as_the_shortest_round_trip_decimal() -> None:
    """A rounding done here cannot be undone by a consumer, so the arm is exact."""
    stored = struct.unpack("<f", struct.pack("<f", 0.1))[0]
    model = world(
        records=(
            actor(
                "Build_MinerMk1_C",
                (0.0, 0.0, 0.0),
                rotation=(stored, 0.0, 0.0, 1.0),
                scale=(stored, 1.0, 1.0),
            ),
        )
    )

    placed = placement.placement_of(model).built_placements[0]
    rotation = placed.rotation
    scale = placed.scale

    assert rotation is not None, "the rotation was withheld"
    assert scale is not None, "the scale was withheld"
    assert rotation[0] == repr(stored)
    assert scale[0] == repr(stored)
    assert float(rotation[0]) == stored
    assert float(scale[0]) == stored


def test_a_node_placement_carries_its_orientation_on_the_same_terms_as_a_building() -> None:
    """A node's rotation was dropped by ``_node_or_none``, not absent from the file.

    An earlier cut of this slice called the null structural. It was the same
    defect one seam lower: ``clockspeed/save/world.py`` had ``record.transform``
    bound and read one of its three blocks. There is no node special case left.
    """
    model = world(nodes=(node("BP_ResourceNode_C", (1.0, 2.0, 3.0), rotation=PLANTED_ROTATION),))

    placed = placement.placement_of(model).node_placements[0]
    rotation = placed.rotation

    assert rotation is not None, "a node placement lost its rotation"
    assert rotation == tuple(repr(part) for part in PLANTED_ROTATION), rotation
    assert placed.scale == tuple(repr(part) for part in IDENTITY_SCALE), placed.scale


def test_the_node_orientation_flag_declares_a_capability_the_rows_actually_have() -> None:
    """The flag and the rows are asserted TOGETHER, because either alone is a lie.

    A True flag over rows carrying nulls, and populated rows under a False flag,
    are both states a consumer would be misled by. The earlier arm asserted only
    the warning half and was mislabelled a field arm; there is no warning now,
    because nothing about a node's orientation is unavailable.
    """
    result = placement.placement_of(
        world(nodes=(node("BP_ResourceNode_C", (1.0, 2.0, 3.0), rotation=PLANTED_ROTATION),))
    )

    assert result.node_orientation_available is True
    unoriented = [
        entry for entry in result.node_placements if entry.rotation is None or entry.scale is None
    ]
    assert unoriented == [], "the flag claims an orientation these rows do not carry"


def test_no_advisory_claims_a_node_orientation_is_unavailable() -> None:
    """The code was retired with the defect. A warning that always fires says nothing.

    Graded on the served vocabulary rather than on a deleted constant, so the
    arm still means something if somebody reintroduces the idea under a new
    spelling.
    """
    model = world(nodes=(node("BP_ResourceNode_C", (1.0, 2.0, 3.0)),))

    result = placement.placement_of(model)
    codes = [warning.code for warning in result.warnings]

    # The control: this world DOES raise an advisory, so an empty vocabulary is
    # not what makes the assertion below pass.
    assert codes != [], "the fixture raised nothing, so this arm grades nothing"
    assert [code for code in codes if "orientation-unavailable" in code] == [], sorted(codes)


#: The field-name suffix every population of ``WorldPlacement`` carries.
_POPULATION_SUFFIX: Final = "_placements"


def _published_populations() -> tuple[str, ...]:
    """The populations ``WorldPlacement`` publishes, read off its own fields.

    Returns:
        Each ``*_placements`` field's prefix, in field order.
    """
    return tuple(
        field.name.removesuffix(_POPULATION_SUFFIX)
        for field in fields(placement.WorldPlacement)
        if field.name.endswith(_POPULATION_SUFFIX)
    )


#: The populations ``placement_of`` walks. The orientation rules below hold
#: identically for each, and the arms that follow drive each, because the
#: function counts them in separate loops behind separate copies of the same
#: guard - CS-1020, where the node copy was graded by nothing at all.
#:
#: DERIVED, NOT ENUMERATED (CS-1036). A literal pair here was the defect class
#: CS-1020 was filed over one level up: a third population the model grew would
#: have left every parametrized arm green. Read off the model instead, a new
#: population joins every arm and reddens it until a fixture can build it.
POPULATIONS: Final = _published_populations()

#: One measured class per population. Distinct on purpose: a helper that fed the
#: wrong class to the wrong loop would build a world with no placement in it,
#: and an arm over an empty population passes for that reason alone.
NODE_CLASS: Final = "BP_ResourceNode_C"
BUILT_CLASS: Final = "Build_MinerMk1_C"


def _node_world(
    translation: tuple[float, float, float],
    rotation: tuple[float, float, float, float],
    scale: tuple[float, float, float],
) -> WorldModel:
    """One node placement.

    Args:
        translation: The placement.
        rotation: The quaternion, in file order.
        scale: The per-axis scale.

    Returns:
        The model.
    """
    return world(nodes=(node(NODE_CLASS, translation, rotation=rotation, scale=scale),))


def _built_world(
    translation: tuple[float, float, float],
    rotation: tuple[float, float, float, float],
    scale: tuple[float, float, float],
) -> WorldModel:
    """One built placement.

    Args:
        translation: The placement.
        rotation: The quaternion, in file order.
        scale: The per-axis scale.

    Returns:
        The model.
    """
    return world(records=(actor(BUILT_CLASS, translation, rotation=rotation, scale=scale),))


#: How a fixture builds a one-placement world for each population. HAND-WRITTEN
#: BECAUSE IT MUST BE - a builder is fixture code - and GRADED against the
#: model's own population set by
#: ``test_every_population_the_model_publishes_is_driven_by_a_fixture``, so a
#: population the model grows has no silent default to fall into. The earlier
#: cut built every population that was not the node one as a built actor.
FIXTURE_BUILDERS: Final[Mapping[str, Callable[..., WorldModel]]] = {
    "node": _node_world,
    "built": _built_world,
}


def one_placement_world(
    population: str,
    translation: tuple[float, float, float],
    *,
    rotation: tuple[float, float, float, float] = IDENTITY_ROTATION,
    scale: tuple[float, float, float] = IDENTITY_SCALE,
) -> WorldModel:
    """Build a world holding exactly one placement, in the named population.

    Args:
        population: One of :data:`POPULATIONS`.
        translation: The placement.
        rotation: The quaternion, in file order. Defaults to the identity.
        scale: The per-axis scale. Defaults to unity.

    Returns:
        The model.
    """
    assert population in POPULATIONS, population
    build = FIXTURE_BUILDERS.get(population)
    assert build is not None, "no fixture builds the population " + population
    return build(translation, rotation, scale)


def placements_in(
    result: placement.WorldPlacement,
    population: str,
) -> tuple[placement.Placement, ...]:
    """The rows the named population contributed.

    SELECTED, NEVER HARDCODED. The node loop appends to ``node_placements`` and
    the built loop to ``built_placements``, so an arm that read
    ``built_placements`` under the node population would assert over an empty
    tuple and grade nothing.

    Args:
        result: The computed placement model.
        population: One of :data:`POPULATIONS`.

    Returns:
        That population's rows, in model order.
    """
    assert population in POPULATIONS, population
    selected: tuple[placement.Placement, ...] = getattr(result, population + _POPULATION_SUFFIX)
    return selected


def test_every_population_the_model_publishes_is_driven_by_a_fixture() -> None:
    """CS-1036. The population set is the model's, and each member has a builder.

    The set is read off the ``*_placements`` fields of ``WorldPlacement``, so a
    third population the shipped model grows joins every parametrized arm below
    on its own - and this arm, and every one of those, turns red until a
    fixture builder exists for it. CS-1020 is what that prevents: the function
    grew a second loop and a hand-enumerated test population did not follow.
    """
    published = _published_populations()
    assert published != (), "the model publishes no population, so this arm grades nothing"
    assert published == POPULATIONS, "the arms drive " + str(POPULATIONS)

    unbuilt = [name for name in published if name not in FIXTURE_BUILDERS]
    assert unbuilt == [], "populations no fixture can build: " + str(unbuilt)


@pytest.mark.parametrize("population", POPULATIONS)
@pytest.mark.parametrize("bad", [math.inf, -math.inf, math.nan])
def test_a_non_finite_rotation_withholds_the_rotation_and_keeps_the_placement(
    bad: float,
    population: str,
) -> None:
    """A non-finite ROTATION is not a non-finite coordinate and is not treated as one.

    Skipping the whole placement would remove a row from the map over a field
    the map does not measure, which is a worse answer than a null.
    """
    model = one_placement_world(
        population,
        (1.0, 2.0, 3.0),
        rotation=(bad, 0.0, 0.0, 1.0),
        scale=PLANTED_SCALE,
    )

    result = placement.placement_of(model)
    codes = {warning.code: warning.count for warning in result.warnings}
    rows = placements_in(result, population)

    assert len(rows) == 1, rows
    placed = rows[0]
    assert (placed.x, placed.y, placed.z) == ("1.0", "2.0", "3.0")
    assert placed.rotation is None, placed.rotation
    assert placed.scale == tuple(repr(part) for part in PLANTED_SCALE), placed.scale
    assert codes.get(placement.WARN_PLACEMENT_ORIENTATION_NON_FINITE) == 1
    assert placement.WARN_PLACEMENT_COORDINATE_NON_FINITE not in codes, sorted(codes)


@pytest.mark.parametrize("population", POPULATIONS)
@pytest.mark.parametrize("bad", [math.inf, -math.inf, math.nan])
def test_a_non_finite_scale_withholds_the_scale_and_keeps_the_rotation(
    bad: float,
    population: str,
) -> None:
    """The two blocks are refused independently; one bad axis costs one block."""
    model = one_placement_world(
        population,
        (1.0, 2.0, 3.0),
        rotation=PLANTED_ROTATION,
        scale=(1.0, bad, 1.0),
    )

    result = placement.placement_of(model)
    codes = {warning.code: warning.count for warning in result.warnings}
    placed = placements_in(result, population)[0]

    assert placed.scale is None, placed.scale
    assert placed.rotation == tuple(repr(part) for part in PLANTED_ROTATION), placed.rotation
    assert codes.get(placement.WARN_PLACEMENT_ORIENTATION_NON_FINITE) == 1


@pytest.mark.parametrize("population", POPULATIONS)
def test_one_placement_losing_both_blocks_is_counted_once_and_not_twice(
    population: str,
) -> None:
    """The advisory counts PLACEMENTS that lost orientation, not components."""
    model = one_placement_world(
        population,
        (1.0, 2.0, 3.0),
        rotation=(math.inf, 0.0, 0.0, 1.0),
        scale=(math.nan, 1.0, 1.0),
    )

    result = placement.placement_of(model)
    codes = {warning.code: warning.count for warning in result.warnings}
    placed = placements_in(result, population)[0]

    assert placed.rotation is None
    assert placed.scale is None
    assert codes.get(placement.WARN_PLACEMENT_ORIENTATION_NON_FINITE) == 1


@pytest.mark.parametrize("population", POPULATIONS)
def test_a_non_finite_orientation_never_widens_the_bounds(population: str) -> None:
    """The bounding box is a claim about COORDINATES, and orientation is not one."""
    model = one_placement_world(
        population,
        (1.0, 2.0, 3.0),
        rotation=(math.inf, math.inf, math.inf, math.inf),
        scale=(math.inf, math.inf, math.inf),
    )

    result = placement.placement_of(model)

    # THE POPULATION AXIS IS NOT DECORATIVE. ``bounds`` is fed from the shared
    # ``triples`` list and never from either placement tuple, so an arm that
    # asserted on the box alone passed with THIS population emptied outright -
    # measured under a mutation that dropped the node append. Pinning the row
    # first is what makes the [node] and [built] cases independent measurements
    # rather than the same assertion run twice.
    rows = placements_in(result, population)
    assert len(rows) == 1, str(rows)

    bounds = result.bounds

    assert bounds is not None
    assert (bounds.x.max_value, bounds.y.max_value, bounds.z.max_value) == ("1.0", "2.0", "3.0")


@pytest.mark.parametrize("population", POPULATIONS)
def test_a_non_finite_coordinate_still_skips_the_whole_placement(population: str) -> None:
    """The COORDINATE rule is unchanged by the orientation rule beside it.

    One non-finite coordinate poisons the world bounding box, which is why that
    placement is skipped outright while a non-finite orientation is not. THE
    ASYMMETRY IS COORDINATE AGAINST ORIENTATION, NOT NODE AGAINST BUILT: both
    loops obey the same rule, which is why this arm drives both populations
    rather than asserting a difference between them.
    """
    model = one_placement_world(
        population,
        (math.inf, 2.0, 3.0),
        rotation=PLANTED_ROTATION,
        scale=PLANTED_SCALE,
    )

    result = placement.placement_of(model)
    codes = {warning.code: warning.count for warning in result.warnings}

    assert placements_in(result, population) == ()
    assert codes.get(placement.WARN_PLACEMENT_COORDINATE_NON_FINITE) == 1
    assert placement.WARN_PLACEMENT_ORIENTATION_NON_FINITE not in codes, sorted(codes)


def test_no_orientation_component_reaches_the_model_as_a_float() -> None:
    """The structural float sweep, aimed at the two blocks this slice added.

    ABSENCE MUST NOT SATISFY THIS ARM. A seam that ignored rotation and scale
    entirely would leave nothing for the sweep to find and pass for that reason
    alone, which is how the earlier cut of this arm survived mutation. So the
    arm first asserts that the components ARE here and ARE the planted ones,
    and only then that none of them is a float.
    """
    model = world(
        records=(
            actor(
                "Build_MinerMk1_C",
                (1.5, 2.5, 3.5),
                rotation=PLANTED_ROTATION,
                scale=PLANTED_SCALE,
            ),
        )
    )

    placed = placement.placement_of(model).built_placements[0]
    walked = reachable(placed)
    components = [item for item in walked if isinstance(item, str)]

    # The live control. Every planted component must be present as a STRING, so
    # a model that dropped the blocks fails here rather than passing below -
    # and present EXACTLY ONCE (CS-1037), because membership is satisfied by a
    # sibling: while a rotation and a scale component shared ``0.5``, a model
    # that dropped that rotation component still passed off the scale.
    planted = tuple(repr(part) for part in (*PLANTED_ROTATION, *PLANTED_SCALE))
    miscounted = [part for part in planted if components.count(part) != 1]
    assert miscounted == [], "planted components absent or ambiguous: " + str(miscounted)

    assert [item for item in walked if type(item) is float] == []
    assert [item for item in reachable(model) if type(item) is float] != []


def test_every_planted_needle_is_unique_to_the_value_it_proves() -> None:
    """CS-1037. No planted component may share, or contain, another's rendering.

    Both planted families are swept together, because the collision this repairs
    was ACROSS them: a rotation component and a scale component rendered the
    same string. Containment is refused as well as equality, since a control
    that hunts a substring is satisfied by any rendering that contains it.
    """
    families = {"rotation": PLANTED_ROTATION, "scale": PLANTED_SCALE}
    needles = [(family, repr(part)) for family, parts in families.items() for part in parts]
    swept = len(needles)
    assert swept == ROTATION_COMPONENTS + SCALE_COMPONENTS, "needles swept: " + str(swept)

    clashes = [
        (first, second)
        for index, (_family, first) in enumerate(needles)
        for other, (_sibling, second) in enumerate(needles)
        if index != other and first in second
    ]
    assert clashes == [], "planted renderings that equal or contain another: " + str(clashes)


def test_widening_the_model_did_not_widen_what_it_withholds() -> None:
    """The privacy list is unchanged: no instance name, index, offset or path.

    THE ARM ASSERTS THAT SOMETHING WIDENED BEFORE IT ASSERTS THAT NOTHING ELSE
    DID. A model that never grew an orientation withholds the markers trivially
    and would pass this arm while the feature was absent - the vacuity the
    earlier cut shipped. The control below fails first in that world.
    """
    model = world(
        nodes=(node("BP_ResourceNode_C", (1.0, 2.0, 3.0), rotation=PLANTED_ROTATION),),
        records=(
            actor(
                "Build_MinerMk1_C",
                (4.0, 5.0, 6.0),
                rotation=PLANTED_ROTATION,
                scale=PLANTED_SCALE,
            ),
        ),
    )

    result = placement.placement_of(model)
    walked = reachable(result)

    # The live control: BOTH populations really did widen, so the sweep below is
    # walking a model that carries the new fields.
    widened = [
        entry
        for entry in (*result.node_placements, *result.built_placements)
        if entry.rotation is not None and entry.scale is not None
    ]
    assert len(widened) == BOTH_POPULATIONS, "nothing widened, so the sweep is vacuous"

    assert [item for item in walked if item in (BODY_OFFSET_MARKER, BODY_LENGTH_MARKER)] == []
    assert [item for item in walked if isinstance(item, str) and INSTANCE_NAME_MARKER in item] == []
    assert [item for item in walked if isinstance(item, str) and PATH_MARKER in item] == []
    assert [item for item in walked if isinstance(item, (Path, bytes, bytearray))] == []
