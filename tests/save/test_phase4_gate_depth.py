"""CS-400 clause 1 DEPTH - a building's inventory reads through the published world.

WHAT THE OPERATOR RULED. Clause 1 ("a real world parses") waits until a
building's inventory is ACTUALLY READABLE; ``tests/save/test_phase4_gate.py``
carries the coverage half and stays PARTIAL until the final adjudication. ADJ-G
ruled what readable means (Q1): through the published ``world.WorldModel`` only,
an actor whose reference RESOLVES (the CS-400 S2 join) to a record carrying
``mInventoryStacks`` exposes, per stack element, the item class and the count.
An empty slot (no class, count 0) is reported as one; a stack whose item cannot
be read is counted with a closed-vocabulary reason and never guessed.

THIS MODULE IS THE GATE ARM FOR THAT RULING, AND IT STAYS IN THE SAVE LAYER. It
imports nothing from ``clockspeed.audit``: the audit consumes the same model,
and a gate graded through its consumer would grade the consumer.

TWO HALVES.

  SYNTHETIC - needs no install and no save library. A building actor, its
    inventory component and three stacks (a NEW-form item, an OLD-form item and
    a NEW-form empty slot), on both tag grammars, built by
    ``tests/save/synthetic.py``. Each is walked building -> join -> component ->
    array element -> item, by value.

  LIBRARY - skip-if-absent, COUNTS ONLY, PER SAVE AND PER VERSION PAIR, NEVER
    POOLED. The POPULATION is derived from a TAG WALK written in this module out
    of the format description - every ``Item`` tag of type ``StructProperty``
    and struct word ``InventoryItem`` inside the declared extent of an
    ``mInventoryStacks`` array tag - and NEVER from decoder success (the CS-829
    fence). The decoded count is read from the published world model. Per save:
    decoded == population, refused == 0, ambiguous == 0, and a class is
    non-empty exactly when the count is positive. No count is written down here:
    the library changes while the operator plays, so a pinned number would be
    a lie with a timestamp on it.

WHAT THE TAG WALK SHARES WITH THE SHIPPED READER, stated as the bound it is. It
shares no code - its string, type-name and tag-header readers are this module's
own - but it shares the FORMAT DESCRIPTION, so a misreading of the grammar both
were written from is invisible to it. The synthetic controls below prove it
counts independently of the decoder (a decoder forced to refuse, or switched
off, leaves the population unmoved) and that it keys on the struct word.

NO SAVE BYTE, PATH OR WORLD STRING CROSSES AN ASSERTION. Every library failure
is reduced to a type NAME or an integer and rendered with ``pytrace=False``.
"""

from __future__ import annotations

import struct
from collections.abc import Mapping
from dataclasses import dataclass, fields
from functools import lru_cache
from pathlib import Path
from types import MappingProxyType
from typing import Final

import pytest

from clockspeed.data import locate
from clockspeed.save import chunks, header, objects, world
from tests.save import reach_guard, synthetic

#: Reaches the save library and is graded for containment, name to what it does.
_GRADED_LIBRARY_REACH: Final = MappingProxyType(
    {
        "_library_save_paths": "resolves the save root and the account directory, and globs",
        "_sweep_library": "reads, parses and loads every save in the library",
    }
)

#: Reaches or touches a primitive without being a grader-able helper. EMPTY, and
#: deliberately so - see ``tests/save/test_trailing_run.py``.
_EXEMPT_LIBRARY_REACH: Final[Mapping[str, str]] = MappingProxyType({})

# ---------------------------------------------------------------------------
# The measured words, SPELLED AGAIN here rather than imported from the reader
# or the builder, so the tag walk below shares no constant with either.
# ---------------------------------------------------------------------------

_STACKS_NAME: Final = "mInventoryStacks"
_ITEM_NAME: Final = "Item"
_COUNT_NAME: Final = "NumItems"
_ITEM_STRUCT_WORD: Final = "InventoryItem"
_STRUCT_TYPE_WORD: Final = "StructProperty"
_ARRAY_TYPE_WORD: Final = "ArrayProperty"

#: The pairs whose tags spell their type as a recursive name. MEASURED by the
#: CS-G05 repair; spelled here as the tag walk's own copy.
_TYPE_TREE_PAIRS: Final = frozenset({(14, 60)})

_INT32: Final = 4
_GUID_WIDTH: Final = 16
_FLAG_ARRAY_INDEX: Final = 0x01
_MAX_TYPE_NAME_PARAMS: Final = 8
_MAX_TYPE_NAME_DEPTH: Final = 8


def _length_prefixed(text: str) -> bytes:
    """One ASCII string as the format writes it: int32 length, text, NUL.

    Args:
        text: Non-empty ASCII text.

    Returns:
        The encoded string.
    """
    data = text.encode("ascii") + b"\x00"
    return struct.pack("<i", len(data)) + data


_STACKS_NEEDLE: Final = _length_prefixed(_STACKS_NAME)
_ITEM_NEEDLE: Final = _length_prefixed(_ITEM_NAME)

# ---------------------------------------------------------------------------
# The independent tag walk
# ---------------------------------------------------------------------------


def _read_string(body: bytes, at: int, end: int) -> tuple[str, int] | None:
    """Read one length-prefixed string, ASCII or UTF-16, bounded by ``end``.

    Args:
        body: The bytes.
        at: The prefix's first byte.
        end: The first byte the string may not reach.

    Returns:
        The text (NUL dropped) and the byte past it, or None if it overruns.
    """
    if at + _INT32 > end:
        return None
    (count,) = struct.unpack_from("<i", body, at)
    at += _INT32
    width = count if count >= 0 else -2 * count
    if at + width > end:
        return None
    if count == 0:
        return ("", at)
    if count > 0:
        return (body[at : at + count - 1].decode("ascii", errors="replace"), at + width)
    return (body[at : at + width - 2].decode("utf-16-le", errors="replace"), at + width)


def _read_type_name(
    body: bytes, at: int, end: int, depth: int = 0
) -> tuple[str, tuple[str, ...], int] | None:
    """Read one recursive type name: a word, an int32 count, that many names.

    Args:
        body: The bytes.
        at: The name's first byte.
        end: The bound.
        depth: The nesting so far.

    Returns:
        The word, its top-level parameter words, and the byte past the name.
    """
    if depth > _MAX_TYPE_NAME_DEPTH:
        return None
    word = _read_string(body, at, end)
    if word is None or word[1] + _INT32 > end:
        return None
    (count,) = struct.unpack_from("<i", body, word[1])
    cursor = word[1] + _INT32
    if not 0 <= count <= _MAX_TYPE_NAME_PARAMS:
        return None
    params: list[str] = []
    for _ in range(count):
        nested = _read_type_name(body, cursor, end, depth + 1)
        if nested is None:
            return None
        params.append(nested[0])
        cursor = nested[2]
    return (word[0], tuple(params), cursor)


@dataclass(frozen=True)
class _TagHead:
    """One tag header as the walk needs it. Shipped vocabulary and ints only.

    Attributes:
        type_word: The tag's type word.
        word: The struct word of a struct tag, the inner word of an array tag,
            or "" for anything else.
        value_at: Where the value begins.
        value_end: The first byte past the value.
    """

    type_word: str
    word: str
    value_at: int
    value_end: int


def _legacy_head(body: bytes, at: int, end: int) -> _TagHead | None:
    """Read a legacy tag header whose name ends at ``at``.

    Args:
        body: The bytes.
        at: The type word's first byte.
        end: The bound.

    Returns:
        The header, or None for a tag this walk does not need or cannot read.
    """
    type_word = _read_string(body, at, end)
    if type_word is None or type_word[0] not in (_STRUCT_TYPE_WORD, _ARRAY_TYPE_WORD):
        return None
    cursor = type_word[1]
    if cursor + 2 * _INT32 > end:
        return None
    (size,) = struct.unpack_from("<i", body, cursor)
    cursor += 2 * _INT32
    word = _read_string(body, cursor, end)
    if word is None:
        return None
    cursor = word[1] + (_GUID_WIDTH if type_word[0] == _STRUCT_TYPE_WORD else 0)
    if cursor + 1 > end:
        return None
    cursor += 1 + (_GUID_WIDTH if body[cursor] else 0)
    if size < 0 or cursor + size > end:
        return None
    return _TagHead(type_word[0], word[0], cursor, cursor + size)


def _tree_head(body: bytes, at: int, end: int) -> _TagHead | None:
    """Read a complete-type-name tag header whose name ends at ``at``.

    Args:
        body: The bytes.
        at: The type name's first byte.
        end: The bound.

    Returns:
        The header, or None for a tag this walk cannot read.
    """
    named = _read_type_name(body, at, end)
    if named is None:
        return None
    type_word, params, cursor = named
    if cursor + _INT32 + 1 > end:
        return None
    (size,) = struct.unpack_from("<i", body, cursor)
    flags = body[cursor + _INT32]
    cursor += _INT32 + 1 + (_INT32 if flags & _FLAG_ARRAY_INDEX else 0)
    if size < 0 or cursor + size > end:
        return None
    return _TagHead(type_word, params[0] if params else "", cursor, cursor + size)


def _head(body: bytes, at: int, end: int, *, type_tree: bool) -> _TagHead | None:
    """Read one tag header in the named grammar.

    Args:
        body: The bytes.
        at: Just past the tag's name.
        end: The bound.
        type_tree: Which grammar.

    Returns:
        The header, or None.
    """
    return _tree_head(body, at, end) if type_tree else _legacy_head(body, at, end)


def _items_in(body: bytes, start: int, end: int, *, type_tree: bool) -> int:
    """Count ``Item`` tags of the item struct word inside one array's extent.

    A matched tag is stepped over WHOLE by its declared size, so nothing inside
    an item's own state bytes is counted again.

    Args:
        body: The bytes.
        start: The array value's first byte.
        end: The first byte past it.
        type_tree: Which grammar.

    Returns:
        The count.
    """
    count = 0
    cursor = start
    while (hit := body.find(_ITEM_NEEDLE, cursor, end)) != -1:
        head = _head(body, hit + len(_ITEM_NEEDLE), end, type_tree=type_tree)
        if head is not None and (head.type_word, head.word) == (
            _STRUCT_TYPE_WORD,
            _ITEM_STRUCT_WORD,
        ):
            count += 1
            cursor = head.value_end
        else:
            cursor = hit + 1
    return count


def _item_tag_population(body: bytes, *, type_tree: bool) -> int:
    """THE POPULATION - every item tag inside every ``mInventoryStacks`` array.

    Derived from the tag grammar alone: no decoder runs, so no decoder's
    success or refusal can move this number.

    Args:
        body: The decompressed body.
        type_tree: Which grammar.

    Returns:
        The count.
    """
    population = 0
    cursor = 0
    while (hit := body.find(_STACKS_NEEDLE, cursor)) != -1:
        head = _head(body, hit + len(_STACKS_NEEDLE), len(body), type_tree=type_tree)
        if head is not None and (head.type_word, head.word) == (
            _ARRAY_TYPE_WORD,
            _STRUCT_TYPE_WORD,
        ):
            population += _items_in(body, head.value_at, head.value_end, type_tree=type_tree)
            cursor = head.value_end
        else:
            cursor = hit + 1
    return population


# ---------------------------------------------------------------------------
# The decoded side - through the published world model ONLY
# ---------------------------------------------------------------------------


@dataclass
class _Decoded:
    """What the published model says about every ``mInventoryStacks`` element.

    INTEGERS ONLY. No field here can hold a path, a class or a name.

    Attributes:
        arrays: ``mInventoryStacks`` containers published.
        declared: Elements those containers declared.
        elements: Elements those containers published.
        decoded: Elements whose ``Item`` is a decoded item.
        refused: Elements whose ``Item`` is a refusal.
        ambiguous: Of those, refused as ambiguous.
        absent: Elements carrying no ``Item`` at all.
        other: Elements that are not a struct, or whose ``Item`` is neither.
        state_undecoded: Decoded items whose state was left undecoded.
        empty_slots: Decoded items with no class and a count of zero.
        disagreed: Decoded items whose class presence disagrees with the count
            (non-empty class with count 0, empty class with a count, or no
            integer count at all).
    """

    arrays: int = 0
    declared: int = 0
    elements: int = 0
    decoded: int = 0
    refused: int = 0
    ambiguous: int = 0
    absent: int = 0
    other: int = 0
    state_undecoded: int = 0
    empty_slots: int = 0
    disagreed: int = 0

    def add_stack(self, value: object) -> None:
        """Tally one array element.

        Args:
            value: The element's published value.
        """
        self.elements += 1
        if not isinstance(value, objects.StructValue):
            self.other += 1
            return
        item = value.properties.get(_ITEM_NAME)
        if item is None:
            self.absent += 1
        elif isinstance(item, objects.InventoryItemRefusal):
            self.refused += 1
            self.ambiguous += item.reason == objects.ITEM_FORM_AMBIGUOUS
        elif isinstance(item, objects.InventoryItem):
            self.decoded += 1
            self.state_undecoded += item.state_undecoded
            count = value.properties.get(_COUNT_NAME)
            has_class = item.class_path != ""
            agrees = isinstance(count, int) and has_class == (count > 0)
            self.disagreed += not agrees
            self.empty_slots += agrees and not has_class
        else:
            self.other += 1

    def visit(self, name: str | None, value: object) -> None:
        """Walk one published value, tallying every stack array it holds.

        Args:
            name: The property name the value was published under, or None.
            value: The value.
        """
        if isinstance(value, world.ContainerContents):
            if name == _STACKS_NAME:
                self.arrays += 1
                self.declared += value.element_count
                for entry in value.entries:
                    self.add_stack(entry.value)
                return
            for entry in value.entries:
                self.visit(None, entry.value)
        elif isinstance(value, objects.StructValue):
            for key, nested in value.properties.items():
                self.visit(key, nested)


def _decoded_of(model: world.WorldModel) -> _Decoded:
    """Tally every published stack array of a loaded world.

    Args:
        model: The world.

    Returns:
        The tally.
    """
    tally = _Decoded()
    for entry in model.properties.by_record_index.values():
        for name, value in entry.values.items():
            tally.visit(name, value)
        for interior in entry.struct_interiors:
            tally.visit(None, interior)
    return tally


@dataclass(frozen=True)
class _SaveTally:
    """One save's verdict inputs. INTEGERS ONLY - never a name or a path.

    Attributes:
        header_version: The pair's header half.
        save_version: The pair's save half.
        ordinal: The save's position in sorted order - a count, not a name.
        population: Item tags the independent walk found.
        decoded: The published model's tally.
    """

    header_version: int
    save_version: int
    ordinal: int
    population: int
    decoded: _Decoded


def _tally_bytes(data: bytes, ordinal: int = 0) -> _SaveTally:
    """Derive the population and the decoded tally of one whole save.

    Args:
        data: The save's bytes.
        ordinal: Its position in the sweep.

    Returns:
        The tally.
    """
    parsed = header.parse_header(data)
    pair = (parsed.header_version, parsed.save_version)
    body = chunks.decompress_body(
        data, parsed.body_offset, header_version=parsed.header_version
    ).payload
    population = _item_tag_population(body, type_tree=pair in _TYPE_TREE_PAIRS)
    return _SaveTally(
        header_version=pair[0],
        save_version=pair[1],
        ordinal=ordinal,
        population=population,
        decoded=_decoded_of(world.load_world_from_bytes(data)),
    )


# ---------------------------------------------------------------------------
# The synthetic half - needs no install and no save library
# ---------------------------------------------------------------------------


def _stacks_of_the_building(model: world.WorldModel) -> tuple[object, ...]:
    """Walk building -> join -> component -> ``mInventoryStacks`` elements.

    Every index is DERIVED from the loaded table, so the walk cannot agree with
    a join that picked the wrong record by sharing its arithmetic.

    Args:
        model: The loaded synthetic world.

    Returns:
        Each element's published value, in element order.
    """
    (actor_index,) = (
        index
        for index, record in enumerate(model.objects.records)
        if record.instance_name == synthetic.INVENTORY_BUILDING_INSTANCE
    )
    entry = model.properties.by_record_index[actor_index]
    names = tuple(reference.property_name for reference in entry.references)
    assert names == (synthetic.INVENTORY_REFERENCE_NAME,), "the building's reference did not read"
    (target,) = entry.reference_targets
    assert target.state == world.TARGET_RESOLVED, "the building's reference did not resolve"
    component_index = target.record_index
    assert component_index is not None
    assert model.objects.records[component_index].kind == objects.KIND_COMPONENT
    owner_has_stacks = synthetic.INVENTORY_STACKS_NAME in entry.values
    assert not owner_has_stacks, "the building itself carries the stacks; the join proves nothing"
    stacks = model.properties.by_record_index[component_index].values.get(
        synthetic.INVENTORY_STACKS_NAME
    )
    assert isinstance(stacks, world.ContainerContents), "the component published no stack array"
    return tuple(element.value for element in stacks.entries)


def _item_of(value: object) -> objects.InventoryItem:
    """One element's decoded item, asserted to be one.

    Args:
        value: The element's published value.

    Returns:
        The item.
    """
    assert isinstance(value, objects.StructValue), "an element is not a struct"
    item = value.properties.get(synthetic.INVENTORY_ITEM_NAME)
    decoded = isinstance(item, objects.InventoryItem)
    assert decoded, f"an element's Item came back as {type(item).__name__}"
    assert isinstance(item, objects.InventoryItem)
    return item


@pytest.mark.parametrize("fixture", synthetic.INVENTORY_SAVES, ids=lambda save: save.name)
def test_a_synthetic_building_inventory_reads_end_to_end(
    fixture: synthetic.SyntheticSave,
) -> None:
    """THE SLICE'S CLAIM: building -> join -> component -> stack -> item and count.

    By value on every stack - class and count - and on both tag grammars.

    Args:
        fixture: One inventory fixture.
    """
    elements = _stacks_of_the_building(world.load_world_from_bytes(fixture.blob))

    assert len(elements) == len(synthetic.INVENTORY_STACKS)
    for value, stack in zip(elements, synthetic.INVENTORY_STACKS, strict=True):
        item = _item_of(value)
        assert isinstance(value, objects.StructValue)
        class_matches = item.class_path == stack.class_path
        assert class_matches, "a stack's class is not the one the fixture planted"
        count = value.properties.get(synthetic.INVENTORY_COUNT_NAME)
        assert count == stack.num_items
        assert item.state_undecoded is False


@pytest.mark.parametrize("fixture", synthetic.INVENTORY_SAVES, ids=lambda save: save.name)
def test_an_empty_slot_reads_as_an_empty_slot_and_not_as_an_absent_item(
    fixture: synthetic.SyntheticSave,
) -> None:
    """ADJ-G Q1 (ii) and Q4: null class with count 0 is EMPTY, a third state from absent.

    Args:
        fixture: One inventory fixture.
    """
    tally = _decoded_of(world.load_world_from_bytes(fixture.blob))
    planted_empty = sum(1 for stack in synthetic.INVENTORY_STACKS if not stack.class_path)

    assert planted_empty >= 1, "the fixture stopped planting an empty slot"
    assert tally.empty_slots == planted_empty
    assert tally.absent == 0
    assert tally.decoded == len(synthetic.INVENTORY_STACKS)


def test_the_fixture_plants_both_native_forms() -> None:
    """One inventory carries both forms, as one real save does - or the arm grades one."""
    forms = {stack.form for stack in synthetic.INVENTORY_STACKS}

    assert forms == set(synthetic.INVENTORY_FORMS)


def test_with_the_native_read_switched_off_the_same_walk_yields_no_item(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """NON-VACUITY: the end-to-end arm passes because the item DECODES.

    The native read is keyed on the one measured struct word; renaming the key
    is the reader as it stood before CS-400 S1. The same fixture, walked the
    same way, must then carry no item at all.

    Args:
        monkeypatch: Renames the dispatch key for this test.
    """
    monkeypatch.setattr(objects, "INVENTORY_ITEM_STRUCT_WORD", "SyntheticNoSuchWord")
    elements = _stacks_of_the_building(
        world.load_world_from_bytes(synthetic.SAVE_LEVELLED_INVENTORY.blob)
    )

    items = sum(
        1
        for value in elements
        if isinstance(value, objects.StructValue)
        and isinstance(value.properties.get(synthetic.INVENTORY_ITEM_NAME), objects.InventoryItem)
    )
    assert len(elements) == len(synthetic.INVENTORY_STACKS)
    assert items == 0


@pytest.mark.parametrize("fixture", synthetic.INVENTORY_SAVES, ids=lambda save: save.name)
def test_the_tag_walk_population_equals_the_decoded_count_on_the_fixture(
    fixture: synthetic.SyntheticSave,
) -> None:
    """The library arm's machinery, run where every number is known.

    Args:
        fixture: One inventory fixture.
    """
    tally = _tally_bytes(fixture.blob)

    assert tally.population == len(synthetic.INVENTORY_STACKS)
    assert tally.decoded.decoded == tally.population
    assert tally.decoded.declared == tally.decoded.elements == tally.population
    assert tally.decoded.refused == tally.decoded.disagreed == 0


def test_the_population_does_not_move_when_the_decoder_refuses_everything(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """THE CS-829 FENCE, FORCED: the population is not decoder success.

    Every item read is replaced by a refusal. A population derived from what
    decoded would fall to zero with the decoded count and the equality would
    still hold; this one stays put and the equality breaks.

    Args:
        monkeypatch: Forces every native read to refuse.
    """
    refusal = objects.InventoryItemRefusal(reason=objects.ITEM_FORM_UNCLOSED)
    monkeypatch.setattr(objects, "read_inventory_item", lambda _body, _at, _end: refusal)

    tally = _tally_bytes(synthetic.SAVE_LEVELLED_INVENTORY.blob)

    assert tally.population == len(synthetic.INVENTORY_STACKS)
    assert tally.decoded.decoded == 0
    assert tally.decoded.refused == tally.population


def test_the_population_keys_on_the_item_struct_word() -> None:
    """The walk counts ``InventoryItem`` struct tags, not any tag named Item.

    The word is renamed IN PLACE, same length, so every offset and size in the
    body is unchanged and only the word differs.
    """
    fixture = synthetic.SAVE_LEVELLED_INVENTORY
    parsed = header.parse_header(fixture.blob)
    body = chunks.decompress_body(
        fixture.blob, parsed.body_offset, header_version=parsed.header_version
    ).payload
    word = _length_prefixed(_ITEM_STRUCT_WORD)
    renamed = _length_prefixed("InventoryItxm")
    assert len(renamed) == len(word)

    before = _item_tag_population(body, type_tree=False)
    after = _item_tag_population(body.replace(word, renamed), type_tree=False)

    assert before == len(synthetic.INVENTORY_STACKS)
    assert after == 0


def test_the_population_is_scoped_to_the_stack_array() -> None:
    """An item tag outside any ``mInventoryStacks`` extent is not counted.

    The array's name is renamed in place, same length, so the same item tags
    sit in an array of another name.
    """
    fixture = synthetic.SAVE_LEVELLED_INVENTORY
    parsed = header.parse_header(fixture.blob)
    body = chunks.decompress_body(
        fixture.blob, parsed.body_offset, header_version=parsed.header_version
    ).payload
    renamed = _length_prefixed("mInventoryStackz")
    assert len(renamed) == len(_STACKS_NEEDLE)

    assert _item_tag_population(body.replace(_STACKS_NEEDLE, renamed), type_tree=False) == 0


def test_the_tally_types_hold_integers_only() -> None:
    """Non-negotiables 11-12: nothing a failure renders can carry a world string."""
    for kind in (_Decoded, _SaveTally):
        annotations = {field.name: str(field.type) for field in fields(kind)}
        texty = sorted(name for name, annotation in annotations.items() if "str" in annotation)
        assert texty == []


def test_the_tag_walk_shares_no_constant_with_the_builder_or_the_reader() -> None:
    """The population's words are this module's own spelling, and they agree.

    Agreement is checked HERE rather than by import, so a rename on either side
    is red instead of silently carried into the walk.
    """
    assert _ITEM_STRUCT_WORD == objects.INVENTORY_ITEM_STRUCT_WORD
    assert _ITEM_STRUCT_WORD == synthetic.INVENTORY_ITEM_STRUCT_WORD
    assert _STACKS_NAME == synthetic.INVENTORY_STACKS_NAME
    assert (_ITEM_NAME, _COUNT_NAME) == (
        synthetic.INVENTORY_ITEM_NAME,
        synthetic.INVENTORY_COUNT_NAME,
    )


# ---------------------------------------------------------------------------
# The library half - skip-if-absent, COUNTS ONLY, per save and per pair
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _DepthSweep:
    """What the library sweep observed. INTEGERS AND TYPE NAMES ONLY.

    Attributes:
        tallies: One per loaded save, in sorted order.
        failures: The type names of any unexpected failure.
    """

    tallies: tuple[_SaveTally, ...]
    failures: tuple[str, ...]


def _library_save_paths() -> tuple[Path, ...]:
    """Every save file on this machine, or an empty tuple.

    IT HOLDS EVERY ``Exception`` AND EVERY ``SystemExit``, and every discovery
    call sits INSIDE the ``try``: the account directory's NAME is the platform
    account id, and a failure unwinding through a frame that holds it is an echo
    path under non-negotiable 3.

    Returns:
        The save paths, sorted, or an empty tuple when there is no library.
    """
    try:
        root = locate.resolve_save_root()
        account = locate.resolve_account_dir(root) if root is not None else None
        return () if account is None else tuple(sorted(account.glob("*.sav")))
    except (Exception, SystemExit):
        return ()


@lru_cache(maxsize=1)
def _sweep_library() -> _DepthSweep | None:
    """Tally every save of a measured pair, COUNTS ONLY.

    Returns:
        The sweep, or None when no save library is reachable.
    """
    saves = _library_save_paths()
    if not saves:
        return None
    tallies: list[_SaveTally] = []
    failures: list[str] = []
    for ordinal, path in enumerate(saves):
        try:
            data = path.read_bytes()
            parsed = header.parse_header(data)
        except (OSError, header.HeaderError):
            continue
        except (Exception, SystemExit) as exc:
            failures.append(type(exc).__name__)
            continue
        if (parsed.header_version, parsed.save_version) not in objects.MEASURED_BODY_LAYOUTS:
            continue
        # BROAD BY DESIGN: a narrower catch lets an unexpected type escape
        # carrying the save bytes.
        try:
            tallies.append(_tally_bytes(data, ordinal))
        except (Exception, SystemExit) as exc:
            failures.append(type(exc).__name__)
    return _DepthSweep(tallies=tuple(tallies), failures=tuple(sorted(set(failures))))


def _sweep_or_skip() -> _DepthSweep:
    """The sweep, or a skip when this machine has no save library.

    Returns:
        The sweep.
    """
    sweep = _sweep_library()
    if sweep is None:
        pytest.skip("no save library on this machine")
    return sweep


def _fail_on(offenders: list[tuple[int, int, int, int, int]], clause: str) -> None:
    """Fail with integers only, one row per offending save, never pooled.

    Args:
        offenders: ``(header, save, ordinal, observed, expected)`` per save.
        clause: A tracked-source phrase naming the clause.
    """
    if offenders:
        rows = "; ".join(
            f"pair ({h},{s}) save #{o}: {got} vs {want}" for h, s, o, got, want in offenders
        )
        pytest.fail(f"{len(offenders)} saves break '{clause}': {rows}", pytrace=False)


def test_every_library_reaching_function_here_is_declared() -> None:
    """The reach guard, keyed on the RISKY primitives rather than the safe route.

    NEEDS NO SAVE LIBRARY - it is a claim about this module's source.
    """
    reach_guard._assert_library_reach_is_declared(  # noqa: SLF001
        Path(__file__), graded=_GRADED_LIBRARY_REACH, exempt=_EXEMPT_LIBRARY_REACH
    )


def test_the_guard_catches_a_spliced_uncontained_helper(tmp_path: Path) -> None:
    """The guard's POWER in THIS module, forced rather than asserted about.

    NEEDS NO SAVE LIBRARY. The splice is the known-bad shape - the locators and
    the glob outside every ``try`` - run against a COPY in ``tmp_path``.

    Args:
        tmp_path: Where the spliced copy is written.
    """
    spliced = tmp_path / "spliced.py"
    spliced.write_text(
        Path(__file__).read_text(encoding="utf-8") + "\n\ndef _spliced_uncontained_helper():\n"
        '    """A helper carrying the known-bad shape."""\n'
        "    root = locate.resolve_save_root()\n"
        "    account = locate.resolve_account_dir(root)\n"
        '    for path in sorted(account.glob("*.sav")):\n'
        "        try:\n"
        "            return header.parse_header(path.read_bytes())\n"
        "        except (OSError, header.HeaderError):\n"
        "            continue\n"
        "    return None\n",
        encoding="utf-8",
    )

    with pytest.raises(AssertionError) as caught:
        reach_guard._assert_library_reach_is_declared(  # noqa: SLF001
            spliced, graded=_GRADED_LIBRARY_REACH, exempt=_EXEMPT_LIBRARY_REACH
        )
    named = "_spliced_uncontained_helper" in str(caught.value)
    assert named

    reach_guard._assert_library_reach_is_declared(  # noqa: SLF001
        Path(__file__), graded=_GRADED_LIBRARY_REACH, exempt=_EXEMPT_LIBRARY_REACH
    )


def test_the_library_sweep_has_a_population_on_every_pair_it_reaches() -> None:
    """THE NON-VACUITY CONTROL, and it runs before every claim below.

    An equality over an empty population passes for that reason alone, so each
    pair the library holds must carry at least one item tag somewhere.
    """
    sweep = _sweep_or_skip()
    failures = len(sweep.failures)
    names = ", ".join(sweep.failures)
    if failures:
        pytest.fail(f"{failures} unexpected failure types: {names}", pytrace=False)
    loaded = len(sweep.tallies)
    assert loaded > 0, "no save of a measured pair loaded"
    by_pair: dict[tuple[int, int], int] = {}
    for tally in sweep.tallies:
        pair = (tally.header_version, tally.save_version)
        by_pair[pair] = by_pair.get(pair, 0) + tally.population
    empty = sorted(pair for pair, population in by_pair.items() if population == 0)
    if empty:
        pytest.fail(f"pairs with no item tag in any save: {empty}", pytrace=False)


def test_every_library_save_decodes_exactly_its_derived_item_population() -> None:
    """THE CLAUSE: per save, decoded == the tag walk's population. Never pooled."""
    sweep = _sweep_or_skip()

    offenders = [
        (t.header_version, t.save_version, t.ordinal, t.decoded.decoded, t.population)
        for t in sweep.tallies
        if t.decoded.decoded != t.population
    ]
    _fail_on(offenders, "decoded equals the derived population")


def test_no_library_item_is_refused_or_ambiguous() -> None:
    """Per save: refused == 0 and ambiguous == 0, each recorded apart."""
    sweep = _sweep_or_skip()

    refused = [
        (t.header_version, t.save_version, t.ordinal, t.decoded.refused, 0)
        for t in sweep.tallies
        if t.decoded.refused
    ]
    ambiguous = [
        (t.header_version, t.save_version, t.ordinal, t.decoded.ambiguous, 0)
        for t in sweep.tallies
        if t.decoded.ambiguous
    ]
    _fail_on(ambiguous, "no item is refused as ambiguous")
    _fail_on(refused, "no item is refused")


def test_a_library_class_is_present_exactly_when_its_count_is_positive() -> None:
    """Per save: non-empty class iff NumItems > 0, on every decoded item."""
    sweep = _sweep_or_skip()

    offenders = [
        (t.header_version, t.save_version, t.ordinal, t.decoded.disagreed, 0)
        for t in sweep.tallies
        if t.decoded.disagreed
    ]
    _fail_on(offenders, "class present iff count positive")


def test_every_library_stack_array_publishes_every_element_it_declares() -> None:
    """Per save: no element of a stack array is dropped, and none is unreadable."""
    sweep = _sweep_or_skip()

    dropped = [
        (t.header_version, t.save_version, t.ordinal, t.decoded.elements, t.decoded.declared)
        for t in sweep.tallies
        if t.decoded.elements != t.decoded.declared
    ]
    other = [
        (t.header_version, t.save_version, t.ordinal, t.decoded.other, 0)
        for t in sweep.tallies
        if t.decoded.other
    ]
    _fail_on(dropped, "published elements equal declared elements")
    _fail_on(other, "every element is a struct carrying an item, a refusal or nothing")
