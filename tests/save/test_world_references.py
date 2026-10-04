"""CS-400 S2 - the world model publishes where each actor reference lands.

WHAT WAS MISSING. ``objects.index_records`` and ``objects.resolve_references``
already follow a reference to the records bearing its path, but nothing above
the save layer could ask: :class:`world.RecordProperties` carried the ordered
references and no target, so a consumer wanting a building's inventory
component would have had to call into ``objects`` itself - a reach past its
neighbour (CLAUDE.md section 2.1). The join is now published on the world model
as a RECORD INDEX into ``WorldModel.objects.records``, never as an offset.

THREE STATES, NEVER COLLAPSED. A reference whose path is borne by exactly one
record is RESOLVED to that record's index; by none, UNRESOLVED; by more than
one, AMBIGUOUS, carrying every candidate index and claiming none of them.
``objects.ReferenceResolution`` counts ambiguity as a subset of resolved; the
published state does not, because a consumer reading "resolved" must be able
to take the one index it is handed.

SYNTHETIC ONLY. Every string below is invented, and the whole file runs on a
machine with no game install and no save library.
"""

from __future__ import annotations

import ast
import inspect
from typing import Final

from clockspeed.save import objects, world
from tests.assertion_rendering_guard import annotation_names, declared_fields
from tests.repr_rendering_guard import CARRIER_TYPES
from tests.save import synthetic

# ---------------------------------------------------------------------------
# The fixture - one actor whose references land in each of the three states
# ---------------------------------------------------------------------------

_HEADER: Final = 14
_SAVE: Final = 52

_ROOT: Final = "Persistent_Level:PersistentLevel"
_LEVEL_NAME: Final = "Persistent_Level:SyntheticJoinCell_0"

_ACTOR_CLASS: Final = "/Synthetic/Parts/Build_SyntheticJoin.Build_SyntheticJoin_C"
_ACTOR_INSTANCE: Final = "Persistent_Level:PersistentLevel.Build_SyntheticJoin_C_0"

_COMPONENT_CLASS: Final = "/Synthetic/Parts/Build_SyntheticJoin.SyntheticJoinInventory_C"
_COMPONENT_INSTANCE: Final = "Persistent_Level:PersistentLevel.Build_SyntheticJoin_C_0.Inventory"

#: Borne by TWO component records, which is the measured shape of an ambiguous
#: instance name (see ``objects.RecordIndex``).
_TWIN_INSTANCE: Final = "Persistent_Level:PersistentLevel.Build_SyntheticJoin_C_0.Twin"

#: Borne by no record at all.
_ABSENT_INSTANCE: Final = "Persistent_Level:PersistentLevel.SyntheticNobody_0"

_RESOLVED_TAG: Final = "mSyntheticStorageInventory"
_AMBIGUOUS_TAG: Final = "mSyntheticTwin"
_UNRESOLVED_TAG: Final = "mSyntheticNobody"

_TRAILING: Final = b"\x11\x22\x33\x44\x55\x66\x77\x88"

#: Record order in the named level: the actor, then each component, which is
#: the order ``SyntheticLevel.payloads`` is paired in. Indices are DERIVED from
#: the loaded table below rather than taken from this order.
_REFERENCE_COUNT: Final = 3
_TWIN_COUNT: Final = 2


def _reference_tag(name: str, path: str) -> bytes:
    """One top-level ObjectProperty tag naming ``path`` in the persistent level.

    Args:
        name: The tag's property name.
        path: The object path the reference names.

    Returns:
        The whole tag.
    """
    value = synthetic.fstring(synthetic.MAP_NAME) + synthetic.fstring(path)
    return synthetic.property_tag(name, objects.REFERENCE_TYPE_WORD, value)


def _component(instance: str) -> synthetic.SyntheticComponent:
    """One component record owned by the actor.

    Args:
        instance: Its instance name.

    Returns:
        The record.
    """
    return synthetic.SyntheticComponent(
        _COMPONENT_CLASS, _ROOT, instance, parent_object_root=_ACTOR_INSTANCE
    )


def _blob(tags: tuple[bytes, ...]) -> bytes:
    """A whole (14,52) save whose one named level holds the actor and its components.

    Args:
        tags: The actor payload's tags, in file order.

    Returns:
        The save bytes.
    """
    actor_payload = synthetic.tagged_property_payload(
        tags,
        head=synthetic.actor_payload_head(
            synthetic.MAP_NAME, _ROOT, (_COMPONENT_INSTANCE, _TWIN_INSTANCE)
        ),
        trailing=_TRAILING,
    )
    empty_component = synthetic.tagged_property_payload((), trailing=_TRAILING)
    components = (
        _component(_COMPONENT_INSTANCE),
        _component(_TWIN_INSTANCE),
        _component(_TWIN_INSTANCE),
    )
    named = synthetic.SyntheticLevel(
        name=_LEVEL_NAME,
        objects=(synthetic.SyntheticObject(_ACTOR_CLASS, _ROOT, _ACTOR_INSTANCE),),
        components=components,
        payloads=(actor_payload, *(empty_component,) * len(components)),
    )
    persistent = synthetic.SyntheticLevel(
        name=None, second_collectables=(synthetic.SyntheticCollectable(),)
    )
    body = synthetic.build_levelled_body(
        (named,),
        persistent,
        header_version=_HEADER,
        save_version=_SAVE,
        grids=synthetic.LEVELLED_GRIDS,
    )
    head = synthetic.build_header(header_version=_HEADER, save_version=_SAVE)
    payload = synthetic.body_with_prefix(body, _HEADER)
    framing = synthetic.default_framing(_HEADER)
    return head + synthetic.build_chunks(payload, framing=framing)


def _three_state_world() -> world.WorldModel:
    """Load the fixture whose actor carries one reference in each state.

    Returns:
        The loaded world.
    """
    return world.load_world_from_bytes(
        _blob(
            (
                _reference_tag(_RESOLVED_TAG, _COMPONENT_INSTANCE),
                _reference_tag(_UNRESOLVED_TAG, _ABSENT_INSTANCE),
                _reference_tag(_AMBIGUOUS_TAG, _TWIN_INSTANCE),
            )
        )
    )


def _indices_of(model: world.WorldModel, instance: str) -> tuple[int, ...]:
    """Every record index bearing an instance name, derived from the table.

    Args:
        model: The loaded world.
        instance: The instance name.

    Returns:
        The indices, in table order.
    """
    return tuple(
        index
        for index, record in enumerate(model.objects.records)
        if record.instance_name == instance
    )


def _actor_entry(model: world.WorldModel) -> world.RecordProperties:
    """The actor's published entry.

    Args:
        model: The loaded world.

    Returns:
        The entry.
    """
    (index,) = _indices_of(model, _ACTOR_INSTANCE)
    return model.properties.by_record_index[index]


# ---------------------------------------------------------------------------
# The join
# ---------------------------------------------------------------------------


def test_an_actor_reference_publishes_its_component_record_index() -> None:
    """The first failing test of the slice: the join exists on the world model.

    The component's index is DERIVED from the loaded table, so the arm cannot
    agree with a join that picked the wrong record by sharing its arithmetic.
    """
    model = world.load_world_from_bytes(
        _blob((_reference_tag(_RESOLVED_TAG, _COMPONENT_INSTANCE),))
    )
    (component_index,) = _indices_of(model, _COMPONENT_INSTANCE)
    entry = _actor_entry(model)

    assert len(entry.references) == 1, "the fixture's one reference did not decode"
    (target,) = entry.reference_targets
    state = target.state
    index = target.record_index
    assert state == world.TARGET_RESOLVED
    assert index == component_index
    assert target.record_indices == (component_index,)
    component_record = model.objects.records[component_index]
    assert component_record.kind == objects.KIND_COMPONENT, "the target is not a component"


def test_targets_align_with_references_one_per_tag_in_tag_order() -> None:
    """``reference_targets[i]`` is where ``references[i]`` landed - no reordering."""
    model = _three_state_world()
    entry = _actor_entry(model)

    names = tuple(reference.property_name for reference in entry.references)
    states = tuple(target.state for target in entry.reference_targets)
    assert names == (_RESOLVED_TAG, _UNRESOLVED_TAG, _AMBIGUOUS_TAG)
    assert len(entry.reference_targets) == _REFERENCE_COUNT
    assert states == (world.TARGET_RESOLVED, world.TARGET_UNRESOLVED, world.TARGET_AMBIGUOUS)


def test_an_unresolved_reference_carries_no_index_and_never_raises() -> None:
    """Non-negotiable 7: a path no record bears is flagged, not fatal, not guessed."""
    entry = _actor_entry(_three_state_world())
    target = entry.reference_targets[1]

    assert target.state == world.TARGET_UNRESOLVED
    assert target.record_indices == ()
    assert target.record_index is None


def test_an_ambiguous_reference_keeps_every_candidate_and_claims_none() -> None:
    """Ambiguity is NOT resolved and NOT unresolved - it is its own state.

    Collapsing it into resolved would hand a consumer one of two records as if
    it were THE record; collapsing it into unresolved would throw away two
    real candidates. Both are the confident wrong answer non-negotiable 7
    forbids.
    """
    model = _three_state_world()
    twins = _indices_of(model, _TWIN_INSTANCE)
    target = _actor_entry(model).reference_targets[2]

    assert len(twins) == _TWIN_COUNT, "the fixture stopped carrying an ambiguous name"
    assert target.state == world.TARGET_AMBIGUOUS
    assert target.record_indices == twins
    assert target.record_index is None


def test_the_three_states_are_distinct_and_closed() -> None:
    """The vocabulary is three distinct words and every target uses one of them."""
    entry = _actor_entry(_three_state_world())
    vocabulary = set(world.TARGET_STATES)

    assert len(vocabulary) == len(world.TARGET_STATES) == _REFERENCE_COUNT
    assert {target.state for target in entry.reference_targets} == vocabulary


def test_every_record_carries_targets_aligned_with_its_references() -> None:
    """Totality: no published entry has a reference without a target."""
    model = _three_state_world()
    misaligned = sum(
        1
        for entry in model.properties.by_record_index.values()
        if len(entry.reference_targets) != len(entry.references)
    )
    assert misaligned == 0


def test_a_record_built_without_the_join_defaults_to_no_targets() -> None:
    """Callers constructing ``RecordProperties`` by keyword keep working."""
    entry = world.RecordProperties(values={}, schema_name="", resolved=None, payload_read=True)
    assert entry.reference_targets == ()


# ---------------------------------------------------------------------------
# What the published type may and may not carry
# ---------------------------------------------------------------------------


def test_the_target_type_is_exported_and_annotates_no_carrier_or_position() -> None:
    """No ``bytes``, no ``Path``, and no offset-shaped field on the new type.

    A position into the decompressed body is exactly what this layer promised
    no consumer would see (``world.WorldProperties``), so a field whose name
    speaks of an offset, a start or a length is refused here by name.
    """
    assert "ReferenceTarget" in world.__all__
    tree = ast.parse(inspect.getsource(world))
    (node,) = (
        item
        for item in ast.walk(tree)
        if isinstance(item, ast.ClassDef) and item.name == "ReferenceTarget"
    )
    annotations = declared_fields(node)
    carriers = sorted(
        field
        for field, annotation in annotations.items()
        if annotation_names(annotation) & CARRIER_TYPES
    )
    positional = sorted(
        field
        for field in annotations
        if any(word in field for word in ("offset", "start", "length", "position", "byte"))
    )
    assert carriers == []
    assert positional == []
    assert set(annotations) == {"state", "record_indices"}


def test_the_target_repr_renders_counts_and_state_only() -> None:
    """``repr`` names the state and a count; no path or name reaches it."""
    entry = _actor_entry(_three_state_world())
    rendered = " ".join(repr(target) for target in entry.reference_targets)
    rendered += repr(entry)

    leaked = sum(
        1
        for marker in (_COMPONENT_INSTANCE, _TWIN_INSTANCE, _ABSENT_INSTANCE, "SyntheticJoin")
        if marker in rendered
    )
    has_count = "reference_targets=3" in repr(entry)
    assert leaked == 0
    assert has_count


# ---------------------------------------------------------------------------
# CS-400 S2b - the component -> parent-actor join
# ---------------------------------------------------------------------------
#
# WHY A SECOND JOIN. Measured on the local library (counts only): a miner's,
# a water pump's and a truck station's inventory carrier is named by NONE of
# its parent actor's top-level reference tags - the link lives in the actor
# head's component list, which ``objects.resolve_references`` steps over by
# design (CS-834). The carrier's own record names its parent, so the save
# layer publishes that join too, through the same ``objects.RecordIndex``, and
# ``audit/`` never matches a path itself.

_SECOND_ACTOR_INSTANCE: Final = "Persistent_Level:PersistentLevel.Build_SyntheticJoin_C_1"
_ORPHAN_PARENT: Final = "Persistent_Level:PersistentLevel.SyntheticNoParent_0"
_ORPHAN_INSTANCE: Final = "Persistent_Level:PersistentLevel.SyntheticNoParent_0.Inventory"
_SHARED_ACTOR_INSTANCE: Final = "Persistent_Level:PersistentLevel.Build_SyntheticJoin_C_9"
_SHARED_CHILD_INSTANCE: Final = "Persistent_Level:PersistentLevel.Build_SyntheticJoin_C_9.Inventory"
_SECOND_CHILD_INSTANCE: Final = "Persistent_Level:PersistentLevel.Build_SyntheticJoin_C_1.Inventory"


def _parent_world() -> world.WorldModel:
    """Load a level whose components' parents land in each of the three states.

    Actors: ``_ACTOR_INSTANCE``, ``_SECOND_ACTOR_INSTANCE`` and TWO records
    bearing ``_SHARED_ACTOR_INSTANCE``. Components: one child of each named
    actor, one child of the shared name, and one whose parent no record bears.

    Returns:
        The loaded world.
    """
    actors = (
        synthetic.SyntheticObject(_ACTOR_CLASS, _ROOT, _ACTOR_INSTANCE),
        synthetic.SyntheticObject(_ACTOR_CLASS, _ROOT, _SECOND_ACTOR_INSTANCE),
        synthetic.SyntheticObject(_ACTOR_CLASS, _ROOT, _SHARED_ACTOR_INSTANCE),
        synthetic.SyntheticObject(_ACTOR_CLASS, _ROOT, _SHARED_ACTOR_INSTANCE),
    )
    components = (
        synthetic.SyntheticComponent(
            _COMPONENT_CLASS, _ROOT, _COMPONENT_INSTANCE, parent_object_root=_ACTOR_INSTANCE
        ),
        synthetic.SyntheticComponent(
            _COMPONENT_CLASS,
            _ROOT,
            _SECOND_CHILD_INSTANCE,
            parent_object_root=_SECOND_ACTOR_INSTANCE,
        ),
        synthetic.SyntheticComponent(
            _COMPONENT_CLASS,
            _ROOT,
            _SHARED_CHILD_INSTANCE,
            parent_object_root=_SHARED_ACTOR_INSTANCE,
        ),
        synthetic.SyntheticComponent(
            _COMPONENT_CLASS, _ROOT, _ORPHAN_INSTANCE, parent_object_root=_ORPHAN_PARENT
        ),
    )
    actor_payload = synthetic.tagged_property_payload(
        (), head=synthetic.actor_payload_head(synthetic.MAP_NAME, _ROOT, ()), trailing=_TRAILING
    )
    empty_component = synthetic.tagged_property_payload((), trailing=_TRAILING)
    named = synthetic.SyntheticLevel(
        name=_LEVEL_NAME,
        objects=actors,
        components=components,
        payloads=(*(actor_payload,) * len(actors), *(empty_component,) * len(components)),
    )
    persistent = synthetic.SyntheticLevel(
        name=None, second_collectables=(synthetic.SyntheticCollectable(),)
    )
    body = synthetic.build_levelled_body(
        (named,),
        persistent,
        header_version=_HEADER,
        save_version=_SAVE,
        grids=synthetic.LEVELLED_GRIDS,
    )
    head = synthetic.build_header(header_version=_HEADER, save_version=_SAVE)
    payload = synthetic.body_with_prefix(body, _HEADER)
    return world.load_world_from_bytes(
        head + synthetic.build_chunks(payload, framing=synthetic.default_framing(_HEADER))
    )


def _parent_state(model: world.WorldModel, instance: str) -> str:
    """The published parent state of the one component bearing ``instance``.

    Args:
        model: The loaded world.
        instance: The component's instance name.

    Returns:
        The state word.
    """
    (index,) = _indices_of(model, instance)
    return model.parents.by_record_index[index].state


def _parent_indices(model: world.WorldModel, instance: str) -> tuple[int, ...]:
    """The published parent candidates of the one component bearing ``instance``.

    Args:
        model: The loaded world.
        instance: The component's instance name.

    Returns:
        The candidate record indices.
    """
    (index,) = _indices_of(model, instance)
    return model.parents.by_record_index[index].record_indices


def test_a_component_publishes_its_parent_actor_record_index() -> None:
    """The first failing test of S2b: the parent join exists on the world model.

    The actor's index is DERIVED from the loaded table, so the arm cannot agree
    with a join that picked the wrong record by sharing its arithmetic.
    """
    model = _parent_world()
    (actor_index,) = _indices_of(model, _ACTOR_INSTANCE)
    (second_index,) = _indices_of(model, _SECOND_ACTOR_INSTANCE)

    assert _parent_state(model, _COMPONENT_INSTANCE) == world.TARGET_RESOLVED
    assert _parent_indices(model, _COMPONENT_INSTANCE) == (actor_index,)
    assert _parent_indices(model, _SECOND_CHILD_INSTANCE) == (second_index,)
    assert model.objects.records[actor_index].kind == objects.KIND_ACTOR


def test_a_parent_no_record_bears_is_unresolved_and_never_raises() -> None:
    model = _parent_world()

    assert _parent_state(model, _ORPHAN_INSTANCE) == world.TARGET_UNRESOLVED
    assert _parent_indices(model, _ORPHAN_INSTANCE) == ()


def test_a_parent_borne_by_two_records_is_ambiguous_and_claims_neither() -> None:
    model = _parent_world()
    shared = _indices_of(model, _SHARED_ACTOR_INSTANCE)

    assert len(shared) == _TWIN_COUNT, "the fixture stopped carrying an ambiguous parent"
    assert _parent_state(model, _SHARED_CHILD_INSTANCE) == world.TARGET_AMBIGUOUS
    assert _parent_indices(model, _SHARED_CHILD_INSTANCE) == shared


def test_the_parent_join_is_total_over_components_and_holds_no_actor() -> None:
    """One entry per record carrying a parent path, and none for an actor."""
    model = _parent_world()
    expected = sorted(
        index for index, record in enumerate(model.objects.records) if record.parent is not None
    )
    components = sum(1 for record in model.objects.records if record.kind == objects.KIND_COMPONENT)

    assert sorted(model.parents.by_record_index) == expected
    assert len(expected) == components
    assert model.parents.total == components


def test_a_world_built_without_the_parent_join_defaults_to_empty() -> None:
    """Callers constructing ``WorldModel`` by keyword keep working."""
    assert world.EMPTY_WORLD_PARENTS.total == 0
    assert dict(world.EMPTY_WORLD_PARENTS.by_record_index) == {}


def test_the_parent_join_type_is_exported_and_annotates_no_carrier_or_position() -> None:
    assert "WorldParents" in world.__all__
    assert "EMPTY_WORLD_PARENTS" in world.__all__
    tree = ast.parse(inspect.getsource(world))
    (node,) = (
        item
        for item in ast.walk(tree)
        if isinstance(item, ast.ClassDef) and item.name == "WorldParents"
    )
    annotations = declared_fields(node)
    carriers = sorted(
        field
        for field, annotation in annotations.items()
        if annotation_names(annotation) & CARRIER_TYPES
    )
    positional = sorted(
        field
        for field in annotations
        if any(word in field for word in ("offset", "start", "length", "position", "byte"))
    )
    assert carriers == []
    assert positional == []
    assert set(annotations) == {"by_record_index"}


def test_the_parent_join_repr_renders_counts_only() -> None:
    model = _parent_world()
    rendered = repr(model.parents) + repr(model)

    leaked = sum(
        1
        for marker in (_ACTOR_INSTANCE, _ORPHAN_PARENT, _SHARED_ACTOR_INSTANCE, "SyntheticJoin")
        if marker in rendered
    )
    assert leaked == 0
    assert "resolved=2" in repr(model.parents)
    assert "unresolved=1" in repr(model.parents)
    assert "ambiguous=1" in repr(model.parents)
