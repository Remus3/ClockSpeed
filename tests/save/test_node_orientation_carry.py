"""CS-1019 - a resource node carries its OWN orientation out of the save layer.

WHAT THIS MODULE GRADES. ``world._node_or_none`` builds a
:class:`clockspeed.save.world.ResourceNode` from a record's transform, and since
CS-1013 it copies the rotation quaternion and the per-axis scale as well as the
translation. Until this module the only arm that observed that copy was
``tests/surface/test_map.py``, two seams away - a defect there reads as a map
defect. These arms grade the save layer directly: a distinct quaternion and a
non-unit scale are packed into an actor record's float32 bytes, the whole save
is parsed, and the returned node must carry both whole tuples.

WHY THE VALUES ARE WHAT THEY ARE. Every component is a dyadic rational, so the
float32 round trip is exact and an equality assert cannot fail on rounding.
Every rotation component differs from the identity ``(0, 0, 0, 1)`` and every
scale component differs from one, so a reader that substitutes the identity, or
a unit scale, in ANY single component is caught. The two nodes differ from each
other in every component, so a reader that hands one node its neighbour's
orientation is caught too.

WHAT THIS MODULE DOES NOT GRADE. Whether the quaternion is unit norm is not
asserted and is not this item - the fixture quaternion deliberately is not one.

THE FLOOR. The record-level arm asserts the parsed record's own transform
carries the planted values. It stays green when ``_node_or_none`` substitutes an
identity, which is what localises a red node arm to that one function rather
than to the packer or the transform reader.

Fixtures are synthetic only (CLAUDE.md section 7). The install lookup is pointed
at paths that do not exist, so the run is the same on a machine with no game.
"""

from __future__ import annotations

import struct
from collections.abc import Iterator
from pathlib import Path
from typing import Final

import pytest

from clockspeed.data.locate import ENV_ACCOUNT_DIR, ENV_GAME_DIR, ENV_LOCAL_CONFIG, ENV_SAVE_ROOT
from clockspeed.save import usmap, world
from tests.save import synthetic

_ROOT: Final = "Persistent_Level:PersistentLevel"

#: Two measured node class names (ADR 0003) under a synthetic namespace.
_NODE_CLASS_PATH: Final = "/Synthetic/World/BP_ResourceNode.BP_ResourceNode_C"
_NODE_CLASS_NAME: Final = "BP_ResourceNode_C"
_SECOND_CLASS_PATH: Final = "/Synthetic/World/BP_ResourceDeposit.BP_ResourceDeposit_C"
_SECOND_CLASS_NAME: Final = "BP_ResourceDeposit_C"

#: What a reader that drops the block would substitute.
_IDENTITY_ROTATION: Final = (0.0, 0.0, 0.0, 1.0)
_UNIT_SCALE: Final = (1.0, 1.0, 1.0)

_ROTATION: Final = (0.5, -0.25, 0.125, 0.75)
_TRANSLATION: Final = (-64.0, 32.0, 8.25)
_SCALE: Final = (2.0, 0.5, 4.0)

_SECOND_ROTATION: Final = (-0.375, 0.625, -0.5, 0.25)
_SECOND_TRANSLATION: Final = (1024.0, -512.0, 16.5)
_SECOND_SCALE: Final = (0.25, 8.0, 3.0)

#: The fixture save holds exactly the two node records above.
_RECORD_COUNT: Final = 2


@pytest.fixture(autouse=True)
def _no_install(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[None]:
    """Point every install override at an absent path and clear the map cache both ways.

    The cache is cleared again on teardown, before ``monkeypatch`` restores the
    environment, so a later test in the same process does not inherit the None
    this environment resolved to.
    """
    missing = tmp_path / "absent"
    for variable in (ENV_GAME_DIR, ENV_SAVE_ROOT, ENV_ACCOUNT_DIR):
        monkeypatch.setenv(variable, str(missing))
    monkeypatch.setenv(ENV_LOCAL_CONFIG, str(tmp_path / "absent.json"))
    usmap.clear_cache()
    yield
    usmap.clear_cache()


def _first() -> synthetic.SyntheticObject:
    """The first node record, carrying the first planted orientation."""
    return synthetic.SyntheticObject(
        _NODE_CLASS_PATH,
        _ROOT,
        "SyntheticNode_0",
        rotation=_ROTATION,
        translation=_TRANSLATION,
        scale=_SCALE,
    )


def _second() -> synthetic.SyntheticObject:
    """A second node record of another class, carrying the second planted orientation."""
    return synthetic.SyntheticObject(
        _SECOND_CLASS_PATH,
        _ROOT,
        "SyntheticDeposit_0",
        rotation=_SECOND_ROTATION,
        translation=_SECOND_TRANSLATION,
        scale=_SECOND_SCALE,
    )


def _model() -> world.WorldModel:
    """Parse a whole synthetic save holding the two node records, flat body."""
    blob = synthetic.build_save(objects=(_first(), _second()))
    return world.load_world_from_bytes(blob, body_layout=world.BODY_LAYOUT_FLAT)


def _f32_exact(value: float) -> bool:
    """Whether a value survives a float32 pack and unpack unchanged."""
    (back,) = struct.unpack("<f", struct.pack("<f", value))
    return bool(back == value)


def test_the_planted_orientations_are_exact_and_distinct_in_every_component() -> None:
    """The anti-vacuity control: no planted component can collide with a substitute.

    A component equal to the identity's, or to its neighbour's, would let a
    substituting reader pass on that component, so each is asserted distinct.
    """
    planted = (*_ROTATION, *_SCALE, *_SECOND_ROTATION, *_SECOND_SCALE)
    inexact = [value for value in planted if not _f32_exact(value)]
    assert inexact == [], "a planted component is not float32 exact"

    for rotation in (_ROTATION, _SECOND_ROTATION):
        shared = [a for a, b in zip(rotation, _IDENTITY_ROTATION, strict=True) if a == b]
        assert shared == [], "a planted rotation shares a component with the identity"
    for scale in (_SCALE, _SECOND_SCALE):
        shared = [a for a, b in zip(scale, _UNIT_SCALE, strict=True) if a == b]
        assert shared == [], "a planted scale shares a component with the unit scale"

    shared_rotation = [a for a, b in zip(_ROTATION, _SECOND_ROTATION, strict=True) if a == b]
    shared_scale = [a for a, b in zip(_SCALE, _SECOND_SCALE, strict=True) if a == b]
    assert shared_rotation == [], "the two planted rotations share a component"
    assert shared_scale == [], "the two planted scales share a component"


def test_the_record_bytes_carry_the_planted_transform_block() -> None:
    """The packer writes the planted quaternion, translation and scale as one f32 block."""
    delta = synthetic.transform_delta(60)
    encoded = _first().encode(delta)
    block = struct.pack("<10f", *_ROTATION, *_TRANSLATION, *_SCALE)

    found = encoded.count(block)
    assert found == 1, "the planted transform block occurs this many times: " + str(found)


def test_the_parsed_records_carry_the_planted_transforms() -> None:
    """The floor: the transform reader delivers both planted blocks to the record table.

    Green under a ``_node_or_none`` identity substitute, which is what makes a
    red node arm below a statement about that one function.
    """
    model = _model()
    transforms = tuple(record.transform for record in model.objects.records)
    count = len(transforms)
    assert count == _RECORD_COUNT, "records parsed: " + str(count)

    first, second = transforms
    assert first is not None
    assert second is not None
    first_rotation = first.rotation
    first_scale = first.scale
    second_rotation = second.rotation
    second_scale = second.scale
    assert first_rotation == _ROTATION, str(first_rotation)
    assert first_scale == _SCALE, str(first_scale)
    assert second_rotation == _SECOND_ROTATION, str(second_rotation)
    assert second_scale == _SECOND_SCALE, str(second_scale)


def test_a_resource_node_carries_its_own_quaternion() -> None:
    """CS-1019. The returned node carries the planted quaternion, not the identity."""
    model = _model()
    classes = tuple(node.class_name for node in model.nodes)
    assert classes == (_NODE_CLASS_NAME, _SECOND_CLASS_NAME), str(classes)

    rotation = model.nodes[0].rotation
    assert rotation == _ROTATION, str(rotation)
    assert rotation != _IDENTITY_ROTATION, "the node was handed the identity quaternion"


def test_a_resource_node_carries_its_own_scale() -> None:
    """The scale is copied from the same transform, not substituted with a unit scale."""
    model = _model()
    classes = tuple(node.class_name for node in model.nodes)
    assert classes == (_NODE_CLASS_NAME, _SECOND_CLASS_NAME), str(classes)

    scale = model.nodes[0].scale
    translation = model.nodes[0].translation
    assert scale == _SCALE, str(scale)
    assert translation == _TRANSLATION, str(translation)


def test_each_node_carries_its_own_orientation_not_its_neighbours() -> None:
    """Two nodes, distinct in every component, each keep their own whole transform."""
    model = _model()
    classes = tuple(node.class_name for node in model.nodes)
    assert classes == (_NODE_CLASS_NAME, _SECOND_CLASS_NAME), str(classes)

    carried = tuple((node.rotation, node.translation, node.scale) for node in model.nodes)
    expected = (
        (_ROTATION, _TRANSLATION, _SCALE),
        (_SECOND_ROTATION, _SECOND_TRANSLATION, _SECOND_SCALE),
    )
    assert carried == expected, str(carried)
