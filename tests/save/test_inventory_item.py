"""The ``InventoryItem`` native interior, read as one of two measured forms - CS-400 S1.

WHAT IS READ. An inventory stack is a nested tag list carrying an ``Item`` tag
and a ``NumItems`` tag. The ``Item`` tag's struct word is ``InventoryItem``, a
struct the game serializes NATIVELY - raw bytes, no tags - so the tag-list
reader refuses it and, before this slice, it was counted unmeasured. Its two
forms were measured over the local library (the CS-400 S0 findings, ruled by
ADJ-G) and are read here:

  OLD   class reference (two strings), legacy state-actor reference (two
        strings), then the declared end.
  NEW   class reference (two strings), an int32 has-state flag; when it is 1, a
        ``/Script/`` struct reference (two strings), an int32 state size and a
        state tag list closed by the terminator exactly at that size; then the
        declared end.

THE READING CAN FAIL, AND MOST OF THIS MODULE MAKES IT FAIL. Every width comes
from a prefix, and each form must close EXACTLY at the tag's declared end. Both
forms are tried; exactly one must close. Both closing is refused as ambiguous,
neither closing as unclosed - flagged and counted, never raised.

EVERY BYTE HERE IS SYNTHETIC AND HAND-BUILT. No real-save byte, path or name.
The class paths below are invented and marked as such; a real item class path
is world content and is never asserted by value. NEEDS NO SAVE LIBRARY.
"""

from __future__ import annotations

import struct
from typing import Final

import pytest

from clockspeed.save import objects
from tests.save import test_properties

#: An invented item class path - NOT a real game asset. It carries a marker so
#: that a rendering carrying it can only have got it from this fixture.
_CLASS_PATH: Final = "/Game/Synthetic/ClockspeedItemLeakMarker.Desc_Synthetic_C"

#: The marker substring every rendering arm searches for.
_LEAK_MARKER: Final = "ClockspeedItemLeakMarker"

#: An invented state struct path. The ``/Script/`` lead is the grammar's; the
#: rest is not a real struct.
_STATE_STRUCT_PATH: Final = "/Script/Synthetic.SyntheticItemState"

#: The stack's own struct word. Invented on purpose: the dispatch is keyed on
#: the ITEM word alone, so the enclosing word must not matter.
_STACK_WORD: Final = "SyntheticStackStruct"

#: A count chosen to be neither 0 nor 1.
_NUM_ITEMS: Final = 37


def _i32(value: int) -> bytes:
    """Encode one little-endian int32.

    Args:
        value: The integer.

    Returns:
        Its four bytes.
    """
    return struct.pack("<i", value)


def _fstring(text: str) -> bytes:
    """One length-prefixed string in the payload reader's shape.

    Args:
        text: ASCII text.

    Returns:
        The encoded string.
    """
    return test_properties._fstring(text)  # noqa: SLF001


def _struct_tag(name: str, struct_word: str, interior: bytes) -> bytes:
    """One legacy-grammar ``StructProperty`` tag, from the shipped constants.

    Args:
        name: The property name.
        struct_word: The struct word the tag carries.
        interior: The value bytes.

    Returns:
        The whole tag.
    """
    words = objects._TAG_EXTRA_STRINGS[objects.STRUCT_TYPE_WORD]  # noqa: SLF001
    extra = b"".join(_fstring(struct_word) for _ in range(words)) + bytes(objects.GUID_BYTES)
    head = test_properties._tag_head(  # noqa: SLF001
        name, objects.STRUCT_TYPE_WORD, len(interior), extra
    )
    return head + interior


def _tag_list(*tags: bytes) -> bytes:
    """A nested tag list, terminator included.

    Args:
        *tags: The encoded tags.

    Returns:
        The list bytes.
    """
    return b"".join(tags) + _fstring(objects._PAYLOAD_TERMINATOR)  # noqa: SLF001


def _int_tag(name: str, value: int) -> bytes:
    """One IntProperty tag.

    Args:
        name: The property name.
        value: The int32.

    Returns:
        The whole tag.
    """
    return test_properties._scalar_tag(name, "IntProperty", _i32(value))  # noqa: SLF001


def _native_string(text: str) -> bytes:
    """A string as the native item bytes write it: empty is a bare zero count.

    The shared fixture encoder spells "" as a one-byte NUL string; the measured
    native layout spells it as an int32 0, which is what this plants.

    Args:
        text: ASCII text.

    Returns:
        The encoded string.
    """
    return _i32(0) if not text else _fstring(text)


def _ref(level: str, path: str) -> bytes:
    """A two-string object reference.

    Args:
        level: The level string.
        path: The path string.

    Returns:
        The encoded pair.
    """
    return _native_string(level) + _native_string(path)


def _new_form(class_path: str = _CLASS_PATH, *, state: bytes | None = None) -> bytes:
    """NEW-form native bytes, with or without a state block.

    Args:
        class_path: The class path to plant.
        state: The state tag list bytes, or None for has-state 0.

    Returns:
        The native interior.
    """
    if state is None:
        return _ref("", class_path) + _i32(0)
    return _ref("", class_path) + _i32(1) + _ref("", _STATE_STRUCT_PATH) + _i32(len(state)) + state


def _old_form(class_path: str = _CLASS_PATH, *, actor: tuple[str, str] = ("", "")) -> bytes:
    """OLD-form native bytes.

    Args:
        class_path: The class path to plant.
        actor: The legacy state-actor reference.

    Returns:
        The native interior.
    """
    return _ref("", class_path) + _ref(*actor)


def _state_list() -> bytes:
    """A synthetic state tag list closed by the terminator.

    Returns:
        The list bytes.
    """
    return _tag_list(_int_tag("SyntheticStateField", 5))


def _stack_result(item_bytes: bytes, num_items: int = _NUM_ITEMS) -> objects.StructValue:
    """Decode a component payload holding one stack whose Item carries ``item_bytes``.

    Args:
        item_bytes: The Item tag's native interior.
        num_items: The NumItems value.

    Returns:
        The stack's decoded interior.
    """
    stack = _tag_list(
        _struct_tag("Item", objects.INVENTORY_ITEM_STRUCT_WORD, item_bytes),
        _int_tag("NumItems", num_items),
    )
    payload = _struct_tag("Stack", _STACK_WORD, stack) + _fstring(
        objects._PAYLOAD_TERMINATOR  # noqa: SLF001
    )
    body = test_properties._synthetic_body(payload)  # noqa: SLF001
    record = test_properties._synthetic_record(payload, actor=False)  # noqa: SLF001
    schema = test_properties._synthetic_map(test_properties._SYNTHETIC_SCHEMA)  # noqa: SLF001
    result = objects.read_properties(body, record, schema)
    interiors = len(result.struct_interiors)
    assert interiors == 1, f"{interiors} stack interiors decoded where the fixture wrote one"
    return result.struct_interiors[0]


def _decoded_item(stack: objects.StructValue) -> objects.InventoryItem:
    """The stack's Item, asserted to be a decoded InventoryItem.

    Args:
        stack: The decoded stack interior.

    Returns:
        The item.
    """
    item = stack.properties.get("Item")
    decoded = isinstance(item, objects.InventoryItem)
    assert decoded, f"the Item came back as {type(item).__name__}, not a decoded InventoryItem"
    assert isinstance(item, objects.InventoryItem)
    return item


def _refusal_reason(stack: objects.StructValue) -> str:
    """The stack's Item, asserted to be a refusal; its closed-vocabulary reason.

    Args:
        stack: The decoded stack interior.

    Returns:
        The reason word.
    """
    item = stack.properties.get("Item")
    refused = isinstance(item, objects.InventoryItemRefusal)
    assert refused, f"the Item came back as {type(item).__name__}, not a refusal"
    assert isinstance(item, objects.InventoryItemRefusal)
    unmeasured = stack.unmeasured
    assert unmeasured == 1, f"a refused Item moved the stack's unmeasured count to {unmeasured}"
    return item.reason


# ---------------------------------------------------------------------------
# The two forms decode
# ---------------------------------------------------------------------------


def test_a_new_form_item_decodes_its_class_beside_num_items() -> None:
    """The first failing test: NEW form, has-state 0, class and count both read."""
    stack = _stack_result(_new_form())

    item = _decoded_item(stack)
    class_matches = item.class_path == _CLASS_PATH
    assert class_matches, "the decoded class path is not the planted one"
    level_empty = item.level_reference == ""
    assert level_empty, "the planted empty level string did not decode as empty"
    assert item.state_undecoded is False
    assert stack.properties["NumItems"] == _NUM_ITEMS
    assert stack.unmeasured == 0, "a decoded Item still counted as unmeasured"
    assert stack.disagreed == 0


def test_an_old_form_item_decodes_its_class_beside_num_items() -> None:
    """The OLD twin: class reference, empty legacy state actor."""
    stack = _stack_result(_old_form())

    item = _decoded_item(stack)
    class_matches = item.class_path == _CLASS_PATH
    assert class_matches, "the decoded class path is not the planted one"
    assert item.state_undecoded is False
    assert stack.properties["NumItems"] == _NUM_ITEMS
    assert stack.unmeasured == 0


def test_a_new_form_item_carrying_state_closes_with_state_undecoded() -> None:
    """Has-state 1: the state block is bounded by its size and counted undecoded."""
    stack = _stack_result(_new_form(state=_state_list()))

    item = _decoded_item(stack)
    class_matches = item.class_path == _CLASS_PATH
    assert class_matches, "the class did not survive a state block after it"
    assert item.state_undecoded is True


def test_an_old_form_item_with_a_legacy_state_actor_is_state_undecoded() -> None:
    """A non-empty legacy state actor is presence-only, never a reference.

    EITHER HALF ALONE SETS THE FLAG, so a reader keyed on only one string of the
    actor reference is caught whichever string it dropped.
    """
    for actor in (
        ("SyntheticLevel", "SyntheticLevel.SyntheticActor"),
        ("", "SyntheticLevel.SyntheticActor"),
        ("SyntheticLevel", ""),
    ):
        stack = _stack_result(_old_form(actor=actor))

        item = _decoded_item(stack)
        assert item.state_undecoded is True, f"actor halves {tuple(map(bool, actor))} not flagged"
        assert objects.ObjectReference not in type(item).__mro__


@pytest.mark.parametrize("form", ["old", "new"])
def test_a_non_empty_level_string_is_not_read_as_the_class(form: str) -> None:
    """The class is the SECOND string of its reference; the level is carried apart.

    Args:
        form: Which form to build.
    """
    level = "SyntheticItemLevel"
    tail = _ref("", "") if form == "old" else _i32(0)
    stack = _stack_result(_ref(level, _CLASS_PATH) + tail)

    item = _decoded_item(stack)
    class_matches = item.class_path == _CLASS_PATH
    level_matches = item.level_reference == level
    assert class_matches, "the class path was not taken from the second string"
    assert level_matches, "the level string was not carried as the level"


def test_an_item_inside_an_inventory_array_element_decodes_through_the_payload() -> None:
    """An Item one container deep - the mInventoryStacks shape - reads in full.

    Two stack elements in one legacy ``ArrayProperty`` of ``StructProperty``,
    one NEW form and one OLD, each beside its NumItems.
    """
    elements = (
        _tag_list(
            _struct_tag("Item", objects.INVENTORY_ITEM_STRUCT_WORD, _new_form()),
            _int_tag("NumItems", _NUM_ITEMS),
        ),
        _tag_list(
            _struct_tag("Item", objects.INVENTORY_ITEM_STRUCT_WORD, _old_form("")),
            _int_tag("NumItems", 0),
        ),
    )
    region = b"".join(elements)
    inner_tag = (
        _fstring("mInventoryStacks")
        + _fstring(objects.STRUCT_TYPE_WORD)
        + _i32(len(region))
        + _i32(0)
        + _fstring(_STACK_WORD)
        + bytes(objects.GUID_BYTES)
        + b"\x00"
    )
    array = test_properties._array_tag(  # noqa: SLF001
        "mInventoryStacks", objects.STRUCT_TYPE_WORD, _i32(len(elements)) + inner_tag + region
    )
    payload = array + _fstring(objects._PAYLOAD_TERMINATOR)  # noqa: SLF001
    body = test_properties._synthetic_body(payload)  # noqa: SLF001
    record = test_properties._synthetic_record(payload, actor=False)  # noqa: SLF001
    schema = test_properties._synthetic_map(test_properties._SYNTHETIC_SCHEMA)  # noqa: SLF001
    result = objects.read_properties(body, record, schema)

    container = result.properties.get("mInventoryStacks")
    is_container = isinstance(container, objects.ContainerValue)
    assert is_container, f"the array came back as {type(container).__name__}"
    assert isinstance(container, objects.ContainerValue)
    stacks = [element.value for element in container.elements]
    assert len(stacks) == len(elements)
    first, second = stacks
    assert isinstance(first, objects.StructValue)
    assert isinstance(second, objects.StructValue)
    class_matches = _decoded_item(first).class_path == _CLASS_PATH
    assert class_matches, "the array element's NEW-form class is not the planted one"
    assert first.properties["NumItems"] == _NUM_ITEMS
    empty_slot = _decoded_item(second).class_path == ""
    assert empty_slot, "the array element's OLD-form empty slot did not read as empty"
    assert second.properties["NumItems"] == 0


def test_the_public_seam_refuses_bounds_past_the_body_without_raising() -> None:
    """``read_inventory_item`` is exported, so it guards its own bounds.

    Through the payload path the tag reader already bounds the region, so the
    guard is inert there; called directly with an end past the body, the form
    readers would hand ``struct.unpack_from`` an offset outside the buffer.
    """
    body = _new_form()
    cases = ((0, len(body) + objects.INT32_SIZE), (-1, len(body)), (len(body), 0))
    for at, end in cases:
        result = objects.read_inventory_item(body, at, end)
        refused = isinstance(result, objects.InventoryItemRefusal)
        assert refused, f"bounds ({at}, end) were not refused"
        assert isinstance(result, objects.InventoryItemRefusal)
        assert result.reason == objects.ITEM_FORM_UNCLOSED


@pytest.mark.parametrize("form", ["old", "new"])
def test_an_empty_slot_decodes_to_an_empty_class_path(form: str) -> None:
    """A null class with NumItems 0 is an empty slot, read under either form.

    Args:
        form: Which form to build.
    """
    item_bytes = _old_form("") if form == "old" else _new_form("")
    stack = _stack_result(item_bytes, num_items=0)

    item = _decoded_item(stack)
    assert item.class_path == ""
    assert stack.properties["NumItems"] == 0


def test_the_item_is_not_an_object_reference_and_joins_no_reference_population() -> None:
    """An item class is not an object in the world - ADJ-G S0-a."""
    stack = _stack_result(_new_form())
    item = _decoded_item(stack)

    assert objects.ObjectReference not in type(item).__mro__
    assert not hasattr(item, "start"), "the item type carries a position field"
    assert not hasattr(item, "offset"), "the item type carries a position field"


# ---------------------------------------------------------------------------
# The reading can fail
# ---------------------------------------------------------------------------


def _overrun_prefix(item_bytes: bytes) -> bytes:
    """Raise the class string's length prefix by one, so it overruns its text.

    Args:
        item_bytes: A valid native interior.

    Returns:
        The mutant.
    """
    at = objects.INT32_SIZE  # the class string's prefix follows the empty level
    (count,) = struct.unpack_from("<i", item_bytes, at)
    return item_bytes[:at] + _i32(count + 1) + item_bytes[at + objects.INT32_SIZE :]


_MUTANTS: Final = {
    "plus_one": lambda b: b + b"\x00",
    "minus_one": lambda b: b[:-1],
    "overrun_prefix": _overrun_prefix,
}


@pytest.mark.parametrize("mutant", sorted(_MUTANTS))
@pytest.mark.parametrize("form", ["old", "new", "new_with_state"])
def test_a_width_mutant_is_refused_under_both_forms(form: str, mutant: str) -> None:
    """A +1, -1 or overrunning-prefix mutant closes under neither form.

    Args:
        form: Which valid form the mutant starts from.
        mutant: Which mutation is applied.
    """
    valid = {
        "old": _old_form(),
        "new": _new_form(),
        "new_with_state": _new_form(state=_state_list()),
    }[form]
    stack = _stack_result(_MUTANTS[mutant](valid))

    reason = _refusal_reason(stack)
    assert reason == objects.ITEM_FORM_UNCLOSED


@pytest.mark.parametrize("delta", [-1, 1])
def test_a_state_size_that_disagrees_with_the_declared_end_is_refused(delta: int) -> None:
    """The state size and the tag's declared end are two prefixes that must agree.

    Args:
        delta: How far the state size is moved off the truth.
    """
    state = _state_list()
    head = _ref("", _CLASS_PATH) + _i32(1) + _ref("", _STATE_STRUCT_PATH)
    stack = _stack_result(head + _i32(len(state) + delta) + state)

    assert _refusal_reason(stack) == objects.ITEM_FORM_UNCLOSED


def test_a_has_state_flag_of_two_is_refused() -> None:
    """Has-state takes 0 or 1; any other value is refused, never guessed.

    THE STATE BLOCK AFTER THE FLAG IS VALID, so the only thing wrong with each
    run is the flag. An earlier version wrote the flag with nothing after it and
    was refused for being short, which let ``has_state != 0`` survive.
    """
    for flag in (2, -1):
        valid_tail = _ref("", _STATE_STRUCT_PATH) + _i32(len(_state_list())) + _state_list()
        control = _decoded_item(_stack_result(_ref("", _CLASS_PATH) + _i32(1) + valid_tail))
        assert control.state_undecoded is True, "the control run with flag 1 did not decode"
        stack = _stack_result(_ref("", _CLASS_PATH) + _i32(flag) + valid_tail)

        reason = _refusal_reason(stack)
        assert reason == objects.ITEM_FORM_UNCLOSED, f"has-state {flag} was not refused"


def test_a_state_size_below_the_terminator_width_is_refused() -> None:
    """The state size has a floor: the terminator alone.

    The run below sizes the state at five bytes and plants them so that the
    size field and those five bytes together spell the terminator. Without the
    floor, the terminator check reads back across the size field and passes.
    """
    terminator = _fstring(objects._PAYLOAD_TERMINATOR)  # noqa: SLF001
    tail_len = len(terminator) - objects.INT32_SIZE
    size_field, tail = terminator[: objects.INT32_SIZE], terminator[objects.INT32_SIZE :]
    planted_size = struct.unpack("<i", size_field)[0]
    assert planted_size == tail_len, "the plant does not size the state at its own tail"
    item_bytes = _ref("", _CLASS_PATH) + _i32(1) + _ref("", _STATE_STRUCT_PATH) + size_field + tail

    assert _refusal_reason(_stack_result(item_bytes)) == objects.ITEM_FORM_UNCLOSED


def test_a_state_struct_outside_script_is_refused() -> None:
    """The state struct reference must name a ``/Script/`` struct."""
    state = _state_list()
    item_bytes = (
        _ref("", _CLASS_PATH)
        + _i32(1)
        + _ref("", "/Game/Synthetic.NotAScriptStruct")
        + _i32(len(state))
        + state
    )
    stack = _stack_result(item_bytes)

    assert _refusal_reason(stack) == objects.ITEM_FORM_UNCLOSED


def test_a_state_block_not_closed_by_the_terminator_is_refused() -> None:
    """The state block must end in the terminator exactly at its size."""
    state = _state_list()[:-1] + b"\x01"
    stack = _stack_result(_new_form(state=state))

    assert _refusal_reason(stack) == objects.ITEM_FORM_UNCLOSED


def test_a_run_closing_under_both_forms_is_refused_as_ambiguous(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Both forms closing is refused rather than one being picked.

    No byte run closes under both through the shared string reader - the NEW
    has-state field is the OLD state actor's level length, which forces a
    one-byte level string, and the NEW level prefix then spans that byte plus
    the OLD path prefix, a count far past the end. So the ambiguity is planted
    by making the OLD reader close as well, and what is graded is the
    arbitration through the full payload path.

    Args:
        monkeypatch: Replaces the OLD-form reader for this test.
    """
    planted = objects.InventoryItem(level_reference="", class_path="", state_undecoded=False)
    monkeypatch.setattr(objects, "_read_item_old_form", lambda _b, _a, _e: planted)
    stack = _stack_result(_new_form())

    assert _refusal_reason(stack) == objects.ITEM_FORM_AMBIGUOUS


def test_the_refusal_reasons_are_a_closed_vocabulary() -> None:
    """Two reasons, distinct, and nothing else."""
    assert (
        frozenset({objects.ITEM_FORM_AMBIGUOUS, objects.ITEM_FORM_UNCLOSED})
        == objects.ITEM_REFUSAL_REASONS
    )
    reasons = (objects.ITEM_FORM_AMBIGUOUS, objects.ITEM_FORM_UNCLOSED)
    assert len(set(reasons)) == len(reasons), "the two reasons collide"


def test_an_item_tag_declaring_native_false_stays_on_the_existing_path() -> None:
    """Native flag False is unmeasured for this word; it is not read natively."""
    body = _new_form()
    header = (objects.STRUCT_TYPE_WORD, 0, len(body), None, (), "InventoryItem", False)

    value, _words = objects._decode_interior_tag(  # noqa: SLF001
        body, header, 0, len(body), 0, type_tree=True
    )

    native_read = isinstance(value, (objects.InventoryItem, objects.InventoryItemRefusal))
    assert not native_read, "a tag declaring native False was read as a native item"


def test_a_different_struct_word_is_not_read_natively() -> None:
    """The native reader is keyed on the one measured word, nothing else."""
    stack = _tag_list(
        _struct_tag("Item", "SyntheticOtherItemWord", _new_form()),
        _int_tag("NumItems", _NUM_ITEMS),
    )
    payload = _struct_tag("Stack", _STACK_WORD, stack) + _fstring(
        objects._PAYLOAD_TERMINATOR  # noqa: SLF001
    )
    body = test_properties._synthetic_body(payload)  # noqa: SLF001
    record = test_properties._synthetic_record(payload, actor=False)  # noqa: SLF001
    schema = test_properties._synthetic_map(test_properties._SYNTHETIC_SCHEMA)  # noqa: SLF001
    result = objects.read_properties(body, record, schema)

    interior = result.struct_interiors[0]
    assert "Item" not in interior.properties
    assert interior.unmeasured == 1


def test_the_native_form_stays_out_of_the_forms_read() -> None:
    """One named word is read; the native FORM is still read nowhere else."""
    assert objects.STRUCT_FORM_NATIVE not in objects.STRUCT_FORMS_READ
    assert objects.STRUCT_TYPE_WORD not in objects.MEASURED_VALUE_TYPES


# ---------------------------------------------------------------------------
# Echo - the class path is world content
# ---------------------------------------------------------------------------


def test_no_rendering_of_an_item_or_its_refusal_carries_the_class_path() -> None:
    """Repr and str withhold both strings; the refusal renders its reason only."""
    decoded = _decoded_item(_stack_result(_new_form()))
    refused = _stack_result(_new_form() + b"\x00").properties["Item"]

    renderings = (repr(decoded), str(decoded), f"{decoded}", repr(refused), str(refused))
    leaks = sum(_LEAK_MARKER in rendering for rendering in renderings)
    assert leaks == 0, f"{leaks} renderings carry the planted class path"
    nonvacuous = "class_path_len=" in repr(decoded)
    assert nonvacuous, "the item repr renders nothing at all"
